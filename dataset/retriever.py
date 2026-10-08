import os
from typing import Any, Dict, List, Optional
from .normalizer import normalize_paper, is_valid_paper
from .loader import load_from_file, load_from_url
from .pubmed_api import fetch_pubmed_by_ids, search_pubmed
from .validator import verify_dataset

DEFAULT_DATASET_PATHS = [
    "dataset.json",
    "pubmed_sample.json"
]

class DatasetRetriever:
    """
    Isolated retrieval and normalization module for PubMed/GitHub datasets.
    Provides methods to load from local JSON/CSV files, remote GitHub raw URLs,
    or live NCBI PubMed E-utilities API.
    """

    def __init__(self, default_file: Optional[str] = None):
        self.default_file = default_file
        if not self.default_file:
            # Look in parent/current dir for default files
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            for candidate in DEFAULT_DATASET_PATHS:
                full_cand = os.path.join(base_dir, candidate)
                if os.path.exists(full_cand):
                    self.default_file = full_cand
                    break

    def get_papers(
        self,
        filepath: Optional[str] = None,
        limit: Optional[int] = None,
        valid_only: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Retrieves papers from a local dataset file and returns normalized records.

        :param filepath: Path to JSON or CSV dataset file. If None, uses default discovered file.
        :param limit: Maximum number of records to return.
        :param valid_only: If True, only returns complete records (with paper_id, title, and abstract).
        :return: List of normalized paper dictionaries following the required schema.
        """
        target_path = filepath or self.default_file
        if not target_path or not os.path.exists(target_path):
            raise FileNotFoundError(f"Dataset file not found: {target_path}")

        raw_records = load_from_file(target_path)
        normalized_papers: List[Dict[str, Any]] = []

        for raw in raw_records:
            paper = normalize_paper(raw, source="PubMed")
            if valid_only and not is_valid_paper(paper):
                continue
            normalized_papers.append(paper)
            if limit and len(normalized_papers) >= limit:
                break

        return normalized_papers

    def get_paper_by_id(
        self,
        paper_id: str,
        filepath: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Finds a specific paper by its paper_id (PMID) in the dataset.
        """
        papers = self.get_papers(filepath=filepath, valid_only=False)
        target_id = str(paper_id).strip()
        for p in papers:
            if p.get("paper_id") == target_id:
                return p
        return None

    def fetch_from_github(
        self,
        raw_url: str,
        limit: Optional[int] = None,
        valid_only: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Fetches dataset JSON from a remote GitHub raw URL or web endpoint,
        normalizes each paper, and returns the list.
        """
        raw_records = load_from_url(raw_url)
        normalized_papers: List[Dict[str, Any]] = []

        for raw in raw_records:
            paper = normalize_paper(raw, source="PubMed")
            if valid_only and not is_valid_paper(paper):
                continue
            normalized_papers.append(paper)
            if limit and len(normalized_papers) >= limit:
                break

        return normalized_papers

    def fetch_from_pubmed(
        self,
        pmids: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Fetches papers directly from NCBI PubMed API by PMIDs.
        """
        return fetch_pubmed_by_ids(pmids)

    def search_pubmed(
        self,
        query: str,
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Queries PubMed directly via NCBI E-utilities for articles matching the search term.
        """
        return search_pubmed(query=query, max_results=max_results)

    def verify(
        self,
        papers: List[Dict[str, Any]],
        raw_source_records: Optional[List[Dict[str, Any]]] = None
    ):
        """
        Verifies the dataset against all 5 integrity requirements.
        """
        return verify_dataset(papers, raw_source_records)
