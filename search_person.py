"""
Search Person / Evidence Retrieval Module Alias
Hackathon Project: Medical Literature Summarization Tool

Provides seamless backward compatibility and alias access to search_evidence.py.
"""

from search_evidence import (
    EvidenceRetrievalError,
    MedicalEvidenceRetriever,
    MissingApiKeyError,
    NoResultsFoundError,
    SearchTimeoutError,
    SerpApiError,
    extract_pmid,
    fetch_pubmed_details,
    is_pubmed_url,
    main,
    retrieve_evidence,
    search_medical_papers,
)

__all__ = [
    "retrieve_evidence",
    "search_medical_papers",
    "MedicalEvidenceRetriever",
    "EvidenceRetrievalError",
    "MissingApiKeyError",
    "SerpApiError",
    "SearchTimeoutError",
    "NoResultsFoundError",
    "is_pubmed_url",
    "extract_pmid",
    "fetch_pubmed_details",
]

if __name__ == "__main__":
    main()
