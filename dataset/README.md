# Dataset Retrieval & Normalization Module

An isolated, modular dataset layer designed to retrieve, normalize, and validate PubMed medical research papers for downstream hackathon tasks without modifying or depending on other teammate modules or LLM folders.

---

## 1. Module Architecture & Isolation

* **Self-Contained**: Stored entirely in `dataset/`. Does not depend on `llm/`, frontend, backend, or summarization pipelines.
* **No Side-Effects**: Does not modify existing teammate files or code.
* **Standardized Output**: Emits uniform, validated JSON objects with guaranteed schema and non-truncated original text.

```
dataset/
├── __init__.py          # Public API exports
├── normalizer.py        # Schema normalization, URL builder, empty/null handling
├── loader.py            # Robust JSON/CSV & GitHub raw URL loader
├── pubmed_api.py        # Live NCBI E-utilities API client (by ID or query)
├── retriever.py         # Unified DatasetRetriever class
├── validator.py         # Integrity verification against the 5 requirements
├── example.py           # Demonstration script printing real normalized JSON
├── test_retrieval.py    # Unittest suite validating all criteria
└── README.md            # This documentation
```

---

## 2. Standardized JSON Schema

Each paper dictionary follows this exact structure:

```json
{
  "paper_id": "25102193",
  "title": "Progressive retinal nonperfusion in ischemic central retinal vein occlusion.",
  "authors": [
    "Charles C Wykoff",
    "David M Brown",
    "Daniel E Croft"
  ],
  "date": "2015-01",
  "abstract": "Serial wide-field fluorescein angiography...",
  "url": "https://pubmed.ncbi.nlm.nih.gov/25102193/",
  "source": "PubMed"
}
```

### Field Specifications:
* `paper_id` (`string`): The PubMed Identifier (PMID).
* `title` (`string`): The full original title of the publication.
* `authors` (`list[string]`): List of author full names (`ForeName LastName`). Empty array `[]` if unavailable.
* `date` (`string | null`): Publication date string. `null` if unavailable.
* `abstract` (`string`): Full original abstract text. Preserves all sections without summarization or truncation.
* `url` (`string | null`): Canonical PubMed URL in format `https://pubmed.ncbi.nlm.nih.gov/<paper_id>/`.
* `source` (`string`): Always `"PubMed"`.

---

## 3. Usage Guide

### A. Load and Normalize from Local Dataset File

```python
from dataset import DatasetRetriever

retriever = DatasetRetriever()

# Loads and normalizes valid papers from dataset.json or pubmed_sample.json
papers = retriever.get_papers(filepath="dataset.json", limit=10, valid_only=True)

for paper in papers:
    print(f"[{paper['paper_id']}] {paper['title']}")
    print(f"URL: {paper['url']}")
    print(f"Abstract preview: {paper['abstract'][:150]}...\n")
```

### B. Fetch Live from PubMed via NCBI API

```python
from dataset import DatasetRetriever

retriever = DatasetRetriever()

# Fetch specific PMIDs directly from NCBI
papers = retriever.fetch_from_pubmed(["25102193", "25115430"])

# Or search PubMed by query
oncology_papers = retriever.search_pubmed("immunotherapy clinical trial", max_results=5)
```

### C. Fetch from a GitHub Raw URL

```python
from dataset import DatasetRetriever

retriever = DatasetRetriever()
github_raw_url = "https://raw.githubusercontent.com/.../dataset.json"
papers = retriever.fetch_from_github(github_raw_url, limit=10)
```

### D. Run Dataset Integrity Verification

```python
from dataset import verify_dataset

is_valid, report = verify_dataset(papers)
print(f"Passed: {is_valid}")
print(report)
```

---

## 4. Running the Example and Tests

Run the demo script:
```bash
python dataset/example.py
```

Run the unit test suite:
```bash
python dataset/test_retrieval.py
```
