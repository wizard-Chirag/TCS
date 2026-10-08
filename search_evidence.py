"""
Medical Literature Evidence Retrieval Module
Hackathon Project: Medical Literature Summarization Tool
Role: Search Person / Evidence Retrieval

This module queries SerpAPI to retrieve genuine, peer-reviewed medical papers
from PubMed. For every paper found, it fetches the full, authoritative abstract
and metadata (paper_id, title, authors, date, abstract, url, source) from PubMed
(NCBI E-Utilities) to ensure downstream LLM modules (e.g., Gemini) receive full
abstracts for evidence extraction.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse
import xml.etree.ElementTree as ET

import requests
from dotenv import load_dotenv

# Ensure safe UTF-8 output on Windows consoles for medical/scientific symbols (e.g. ≤, ≥, α, β)
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Automatically locate and load .env from the module's directory or parent paths
_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
_ENV_PATH = os.path.join(_MODULE_DIR, ".env")
if os.path.exists(_ENV_PATH):
    load_dotenv(dotenv_path=_ENV_PATH)
else:
    load_dotenv()

SERPAPI_SEARCH_URL = "https://serpapi.com/search.json"
NCBI_EFETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

DEFAULT_TIMEOUT_SECONDS = 30
DEFAULT_MIN_RESULTS = 5
DEFAULT_MAX_RESULTS = 10


# ============================================================================
# Custom Exceptions
# ============================================================================

class EvidenceRetrievalError(Exception):
    """Base exception for all evidence retrieval errors."""
    pass


class MissingApiKeyError(EvidenceRetrievalError):
    """Raised when the SERPAPI_API_KEY is missing or empty."""
    pass


class SerpApiError(EvidenceRetrievalError):
    """Raised when SerpAPI returns an HTTP error or error message."""
    pass


class SearchTimeoutError(EvidenceRetrievalError):
    """Raised when the request exceeds the allowed timeout."""
    pass


class NoResultsFoundError(EvidenceRetrievalError):
    """Raised when no verified medical evidence could be found."""
    pass


# ============================================================================
# URL Validation & Sanitization Helpers
# ============================================================================

def is_pubmed_url(url: str) -> bool:
    """
    Strictly verifies whether a given URL originates from PubMed / NCBI.
    Rejects general consumer health websites like Mayo Clinic, NHS, GoodRx, WebMD, etc.

    Valid patterns include:
      - pubmed.ncbi.nlm.nih.gov/...
      - ncbi.nlm.nih.gov/pubmed/...
      - ncbi.nlm.nih.gov/pmc/...
    """
    if not url or not isinstance(url, str):
        return False

    try:
        parsed = urlparse(url.strip())
        domain = (parsed.netloc or "").lower()
        path = (parsed.path or "").lower()

        # pubmed.ncbi.nlm.nih.gov
        if domain == "pubmed.ncbi.nlm.nih.gov" or domain.endswith(".pubmed.ncbi.nlm.nih.gov"):
            return True

        # ncbi.nlm.nih.gov with /pubmed/ or /pmc/ path
        if domain == "ncbi.nlm.nih.gov" or domain.endswith(".ncbi.nlm.nih.gov"):
            if path.startswith("/pubmed") or path.startswith("/pmc"):
                return True

        return False
    except Exception:
        return False


def extract_pmid(url: str) -> Optional[str]:
    """
    Extracts the numeric PubMed identifier (PMID) from a PubMed URL.
    Returns None if no valid PMID is found.
    """
    if not url:
        return None
    match = re.search(r'pubmed\.ncbi\.nlm\.nih\.gov/(\d+)', url)
    if match:
        return match.group(1)
    match = re.search(r'ncbi\.nlm\.nih\.gov/pubmed/(\d+)', url)
    if match:
        return match.group(1)
    return None


def clean_title(title: str) -> str:
    """
    Cleans title artifacts such as trailing periods, trailing ' - PubMed',
    and bracket wrappers often present on translated titles.
    """
    if not title:
        return ""
    # Strip HTML tags if present
    cleaned = re.sub(r'<[^>]+>', '', title)
    # Remove trailing search engine artifacts
    cleaned = re.sub(
        r'\s*-\s*(PubMed(\s*Central)?|NCBI)\s*$',
        '',
        cleaned.strip(),
        flags=re.IGNORECASE
    )
    # Remove outer bracket wrappers for translated titles
    cleaned = re.sub(r'^\[(.*?)\]\.?$', r'\1', cleaned.strip())
    # Remove trailing period
    cleaned = cleaned.rstrip(".")
    # Clean redundant whitespaces
    return re.sub(r'\s+', ' ', cleaned).strip()


# ============================================================================
# PubMed Abstract & Metadata Fetcher
# ============================================================================

def fetch_pubmed_details(pmids: List[str], timeout: int = DEFAULT_TIMEOUT_SECONDS) -> Dict[str, Dict[str, Any]]:
    """
    Fetches full metadata and abstracts directly from PubMed (NCBI E-Utilities)
    for a list of PMIDs in a single batched call.

    Returns a mapping:
      {
        "pmid": {
          "title": str,
          "authors": List[str],
          "date": str,
          "abstract": str
        }
      }
    """
    if not pmids:
        return {}

    clean_pmids = [p for p in pmids if p.isdigit()]
    if not clean_pmids:
        return {}

    params = {
        "db": "pubmed",
        "id": ",".join(clean_pmids),
        "retmode": "xml"
    }

    try:
        response = requests.get(NCBI_EFETCH_URL, params=params, timeout=timeout)
        response.raise_for_status()
    except requests.exceptions.Timeout as exc:
        raise SearchTimeoutError(
            f"PubMed E-Utilities request timed out after {timeout} seconds."
        ) from exc
    except requests.exceptions.RequestException as exc:
        raise EvidenceRetrievalError(
            f"Failed to fetch PubMed abstracts from NCBI E-Utilities: {exc}"
        ) from exc

    try:
        root = ET.fromstring(response.content)
    except ET.ParseError as exc:
        raise EvidenceRetrievalError(f"Failed to parse PubMed XML response: {exc}") from exc

    results: Dict[str, Dict[str, Any]] = {}

    for article in root.findall(".//PubmedArticle"):
        pmid = article.findtext(".//MedlineCitation/PMID")
        if not pmid:
            continue

        # Title
        title_el = article.find(".//Article/ArticleTitle")
        raw_title = "".join(title_el.itertext()).strip() if title_el is not None else ""
        title = clean_title(raw_title)

        # Authors
        authors: List[str] = []
        for author in article.findall(".//AuthorList/Author"):
            last_name = (author.findtext("LastName") or "").strip()
            fore_name = (author.findtext("ForeName") or author.findtext("Initials") or "").strip()
            collective = (author.findtext("CollectiveName") or "").strip()
            if last_name and fore_name:
                authors.append(f"{fore_name} {last_name}")
            elif last_name:
                authors.append(last_name)
            elif collective:
                authors.append(collective)

        # Date
        pub_date_el = article.find(".//JournalIssue/PubDate")
        date_str = ""
        if pub_date_el is not None:
            year = (pub_date_el.findtext("Year") or "").strip()
            month = (pub_date_el.findtext("Month") or "").strip()
            day = (pub_date_el.findtext("Day") or "").strip()
            medline_date = (pub_date_el.findtext("MedlineDate") or "").strip()
            if medline_date:
                date_str = medline_date
            elif year and month and day:
                date_str = f"{year}-{month}-{day}"
            elif year and month:
                date_str = f"{year} {month}"
            elif year:
                date_str = year

        # Abstract
        abstract_parts: List[str] = []
        for at in article.findall(".//Article/Abstract/AbstractText"):
            label = at.get("Label")
            text = "".join(at.itertext()).strip()
            if not text:
                continue
            if label:
                abstract_parts.append(f"{label}: {text}")
            else:
                abstract_parts.append(text)
        abstract = "\n\n".join(abstract_parts).strip()

        results[pmid] = {
            "title": title,
            "authors": authors,
            "date": date_str,
            "abstract": abstract
        }

    return results


# ============================================================================
# Main Retriever Class
# ============================================================================

class MedicalEvidenceRetriever:
    """
    Evidence retriever that queries SerpAPI for medical literature,
    strictly validates PubMed provenance, fetches full abstracts, and formats results.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        timeout: int = DEFAULT_TIMEOUT_SECONDS
    ):
        """
        Initializes the retriever.
        Reads SERPAPI_API_KEY from environment or explicit argument.
        """
        self.api_key = (api_key or os.getenv("SERPAPI_API_KEY") or "").strip()
        self.timeout = timeout

        if not self.api_key:
            raise MissingApiKeyError(
                "SERPAPI_API_KEY not found. Please set SERPAPI_API_KEY in your .env "
                "file or environment variables."
            )

    def _execute_serpapi_query(self, query: str, num_results: int) -> List[Dict[str, Any]]:
        """
        Sends an HTTP GET request to SerpAPI using engine=google.
        Handles timeout and API status errors.
        """
        params = {
            "engine": "google",
            "q": query,
            "api_key": self.api_key,
            "num": num_results
        }

        try:
            response = requests.get(
                SERPAPI_SEARCH_URL,
                params=params,
                timeout=self.timeout
            )
        except requests.exceptions.Timeout as exc:
            raise SearchTimeoutError(
                f"SerpAPI search timed out after {self.timeout} seconds for query: '{query}'"
            ) from exc
        except requests.exceptions.RequestException as exc:
            raise SerpApiError(f"Network error while connecting to SerpAPI: {exc}") from exc

        if response.status_code != 200:
            error_details = response.text
            try:
                err_json = response.json()
                if "error" in err_json:
                    error_details = err_json["error"]
            except Exception:
                pass
            raise SerpApiError(
                f"SerpAPI HTTP {response.status_code} error: {error_details}"
            )

        data = response.json()
        if "error" in data:
            raise SerpApiError(f"SerpAPI returned error: {data['error']}")

        return data.get("organic_results", [])

    def search(
        self,
        query: str,
        min_results: int = DEFAULT_MIN_RESULTS,
        max_results: int = DEFAULT_MAX_RESULTS,
        raise_on_empty: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Retrieves 5–10 normalized PubMed papers with full abstracts for the given medical question.

        Args:
            query: Medical question or search query (e.g. 'Does metformin reduce CV risk in T2D?')
            min_results: Minimum required results with abstracts (clamped between 1 and 10, default 5)
            max_results: Maximum number of papers to return (clamped between 5 and 10, default 10)
            raise_on_empty: If True, raises NoResultsFoundError if no papers with abstracts match.

        Returns:
            List of normalized dictionaries:
            [
              {
                "paper_id": "29278713",
                "title": "Is metformin beneficial for heart failure in patients with type 2 diabetes?",
                "authors": ["Milton Packer"],
                "date": "2018 Feb",
                "abstract": "Full abstract text...",
                "url": "https://pubmed.ncbi.nlm.nih.gov/29278713/",
                "source": "PubMed"
              }
            ]
        """
        query_text = (query or "").strip()
        if not query_text:
            if raise_on_empty:
                raise NoResultsFoundError("Empty query provided.")
            return []

        # Clamp max_results between 5 and 10
        max_results = max(5, min(10, max_results))
        min_results = max(1, min(min_results, max_results))

        # Query SerpAPI with higher initial sample size to guarantee enough papers with abstracts
        serpapi_fetch_count = min(20, max_results + 8)

        candidate_pmids: List[str] = []
        seen_pmids: set[str] = set()

        def extract_pmids_from_results(items: List[Dict[str, Any]]):
            for item in items:
                link = item.get("link", "")
                if not is_pubmed_url(link):
                    continue
                pmid = extract_pmid(link)
                if pmid and pmid not in seen_pmids:
                    seen_pmids.add(pmid)
                    candidate_pmids.append(pmid)

        # Step 1: Targeted PubMed search
        if "site:pubmed" not in query_text.lower() and "site:ncbi" not in query_text.lower():
            primary_query = f"{query_text} site:pubmed.ncbi.nlm.nih.gov"
        else:
            primary_query = query_text

        organic_items = self._execute_serpapi_query(primary_query, num_results=serpapi_fetch_count)
        extract_pmids_from_results(organic_items)

        # Step 2: Fallback query if fewer candidate PMIDs were discovered
        if len(candidate_pmids) < min_results:
            fallback_query = f"{query_text} PubMed"
            fallback_items = self._execute_serpapi_query(fallback_query, num_results=serpapi_fetch_count)
            extract_pmids_from_results(fallback_items)

        if not candidate_pmids:
            if raise_on_empty:
                raise NoResultsFoundError(
                    f"No verified PubMed articles found for query: '{query_text}'"
                )
            return []

        # Step 3: Fetch full metadata and abstracts from PubMed (NCBI E-Utilities)
        pubmed_details = fetch_pubmed_details(candidate_pmids, timeout=self.timeout)

        # Step 4: Assemble normalized records, strictly requiring non-empty abstract
        final_papers: List[Dict[str, Any]] = []

        for pmid in candidate_pmids:
            details = pubmed_details.get(pmid)
            if not details:
                continue

            abstract = details.get("abstract", "").strip()
            # The abstract is mandatory for downstream LLM / Gemini summarization
            if not abstract:
                continue

            final_papers.append({
                "paper_id": pmid,
                "title": details.get("title") or f"PubMed Article {pmid}",
                "authors": details.get("authors") or [],
                "date": details.get("date") or "",
                "abstract": abstract,
                "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                "source": "PubMed"
            })

            if len(final_papers) >= max_results:
                break

        if not final_papers and raise_on_empty:
            raise NoResultsFoundError(
                f"No papers with complete abstracts could be retrieved for: '{query_text}'"
            )

        return final_papers


# ============================================================================
# Module-level Convenience Functions (for easy teammate integration)
# ============================================================================

def retrieve_evidence(
    query: str,
    min_results: int = DEFAULT_MIN_RESULTS,
    max_results: int = DEFAULT_MAX_RESULTS,
    api_key: Optional[str] = None,
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
    raise_on_empty: bool = False
) -> List[Dict[str, Any]]:
    """
    Top-level helper function to retrieve 5–10 PubMed papers with full abstracts.

    Example:
        >>> from search_evidence import retrieve_evidence
        >>> papers = retrieve_evidence("Does metformin reduce cardiovascular risk in type 2 diabetes?")
        >>> print(papers[0]["paper_id"], papers[0]["abstract"])
    """
    retriever = MedicalEvidenceRetriever(api_key=api_key, timeout=timeout)
    return retriever.search(
        query=query,
        min_results=min_results,
        max_results=max_results,
        raise_on_empty=raise_on_empty
    )


def search_medical_papers(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Backward-compatible alias matching team naming conventions.
    """
    return retrieve_evidence(query=query, max_results=limit)


# ============================================================================
# CLI Execution
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Retrieve verified PubMed papers with full abstracts using SerpAPI and NCBI E-Utilities."
    )
    parser.add_argument(
        "query",
        nargs="?",
        default=None,
        help="Medical research question to search (e.g. 'Does metformin reduce cardiovascular risk in type 2 diabetes?')"
    )
    parser.add_argument(
        "--min-results",
        type=int,
        default=5,
        help="Minimum desired papers with abstracts (default: 5)"
    )
    parser.add_argument(
        "--max-results",
        type=int,
        default=10,
        help="Maximum desired papers (default: 10, max 10)"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=30,
        help="Request timeout in seconds (default: 30)"
    )

    args = parser.parse_args()

    query = args.query
    if not query:
        try:
            query = input("Enter medical question: ").strip()
        except (KeyboardInterrupt, EOFError):
            sys.exit(0)

    if not query:
        print("Error: No search query provided.", file=sys.stderr)
        sys.exit(1)

    try:
        papers = retrieve_evidence(
            query=query,
            min_results=args.min_results,
            max_results=args.max_results,
            timeout=args.timeout
        )

        if not papers:
            print("[]")
            print("Notice: No verified PubMed papers with abstracts found for this query.", file=sys.stderr)
            return

        print(json.dumps(papers, indent=2, ensure_ascii=False))

    except MissingApiKeyError as e:
        print(f"Configuration Error: {e}", file=sys.stderr)
        sys.exit(1)
    except SearchTimeoutError as e:
        print(f"Timeout Error: {e}", file=sys.stderr)
        sys.exit(2)
    except SerpApiError as e:
        print(f"API Error: {e}", file=sys.stderr)
        sys.exit(3)
    except EvidenceRetrievalError as e:
        print(f"Evidence Retrieval Error: {e}", file=sys.stderr)
        sys.exit(4)


if __name__ == "__main__":
    main()
