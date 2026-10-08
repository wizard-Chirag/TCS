# Medical Literature Summarization Tool
## Evidence Retrieval Module (Search Person)

A lightweight, robust Python module for retrieving verified medical literature and full abstracts from **PubMed** using SerpAPI and NCBI E-Utilities. Specifically built to feed structured literature into downstream LLM modules (e.g. Gemini) for medical evidence extraction.

---

### Key Features
- **Strict PubMed Provenance**: Validates paper provenance against `pubmed.ncbi.nlm.nih.gov` and `ncbi.nlm.nih.gov/pubmed|pmc`. Non-academic consumer health portals (Mayo Clinic, NHS, GoodRx, WebMD, etc.) are strictly filtered out and never labeled as PubMed.
- **Full Abstract Retrieval**: Rather than returning short search engine snippets, the module fetches the **complete, authoritative PubMed abstract** via NCBI E-Utilities (`efetch.fcgi`).
- **Normalized Schema**: Each paper object includes `paper_id`, `title`, `authors`, `date`, `abstract`, `url`, and `source`.
- **Deduplication**: Automatically deduplicates articles by PMID and normalized URL.
- **Configurable Limits**: Returns 5–10 highly relevant papers with complete abstracts per query.
- **Robust Error Handling**: Handles missing API keys, network timeouts, SerpAPI errors, and empty results with custom exceptions.

---

### Setup Instructions

#### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

#### 2. Configure Environment Variables
Copy `.env.example` to `.env` (or use existing `.env`) and add your SerpAPI key:
```env
SERPAPI_API_KEY=your_serpapi_api_key_here
```

---

### How to Run

#### Option A: Command Line Interface (CLI)
Run directly with a medical research question:
```bash
python search_evidence.py "Does metformin reduce cardiovascular risk in type 2 diabetes?"
```

Or run interactively (will prompt for a question):
```bash
python search_evidence.py
```

Optional CLI flags:
```bash
python search_evidence.py --max-results 10 --timeout 30 "Is pembrolizumab effective for metastatic melanoma?"
```

#### Option B: Import in Python Backend (FastAPI / Gemini Pipeline)
```python
from search_evidence import retrieve_evidence

# 1. Retrieve 5-10 verified PubMed papers with complete abstracts
papers = retrieve_evidence("Does metformin reduce cardiovascular risk in type 2 diabetes?")

for paper in papers:
    print(f"PMID: {paper['paper_id']}")
    print(f"Title: {paper['title']}")
    print(f"Authors: {', '.join(paper['authors'])}")
    print(f"Date: {paper['date']}")
    print(f"Abstract: {paper['abstract'][:150]}...")
    print(f"URL: {paper['url']}")
    print(f"Source: {paper['source']}")
```

Backward-compatible alias:
```python
from search_person import search_medical_papers

papers = search_medical_papers("Does metformin reduce cardiovascular risk in type 2 diabetes?", limit=10)
```

---

### Normalized Output Schema

Each paper returned strictly adheres to:
```json
[
  {
    "paper_id": "29278713",
    "title": "Is metformin beneficial for heart failure in patients with type 2 diabetes?",
    "authors": [
      "Milton Packer"
    ],
    "date": "2018 Feb",
    "abstract": "Heart failure is a common and serious cardiovascular complication of type 2 diabetes. Many antihyperglycemic drugs can increase the risk of heart failure. However, it is commonly believed that metformin - the first-line treatment for type 2 diabetes - reduces the risk of and improves the clinical course of heart failure...",
    "url": "https://pubmed.ncbi.nlm.nih.gov/29278713/",
    "source": "PubMed"
  }
]
```

---

### Error Handling

The module provides clear custom exceptions:
- `MissingApiKeyError`: Raised if `SERPAPI_API_KEY` is not found in `.env` or environment variables.
- `SearchTimeoutError`: Raised if SerpAPI or NCBI E-Utilities times out.
- `SerpApiError`: Raised if SerpAPI returns an HTTP error or API error code (e.g., quota exceeded).
- `NoResultsFoundError`: Raised when `raise_on_empty=True` is specified and no PubMed papers with abstracts match.

---

### Running Tests
To run the automated test suite:
```bash
python test_evidence_retrieval.py
```