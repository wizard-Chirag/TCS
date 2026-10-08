"""
Isolated PubMed / GitHub Dataset Retrieval and Normalization Module.
Provides standardized loading, schema normalization, and validation
without external dependencies on LLM, UI, or backend pipelines.
"""

from .normalizer import normalize_paper, is_valid_paper
from .loader import load_from_file, load_from_url, load_robust_json, load_csv_file
from .pubmed_api import fetch_pubmed_by_ids, search_pubmed
from .validator import verify_dataset
from .retriever import DatasetRetriever

__all__ = [
    "DatasetRetriever",
    "normalize_paper",
    "is_valid_paper",
    "load_from_file",
    "load_from_url",
    "load_robust_json",
    "load_csv_file",
    "fetch_pubmed_by_ids",
    "search_pubmed",
    "verify_dataset",
]
