# PubMed Sample Dataset Documentation

## 1. Overview
This dataset contains **100 high-quality, verified medical research article abstracts** extracted directly from the National Center for Biotechnology Information (NCBI) PubMed database. It has been curated and cleaned specifically for downstream AI summarization, natural language processing, and medical search benchmarking.

---

## 2. Source of the PubMed Data
* **Source Organization:** National Center for Biotechnology Information (NCBI), National Library of Medicine (NLM), National Institutes of Health (NIH).
* **Source Service:** Official Entrez Programming Utilities (E-utilities) API.
* **Database:** PubMed (`db=pubmed`).

---

## 3. Exact Source API Endpoints Used
The dataset was retrieved programmatically using the official NCBI E-utilities REST endpoints:

1. **Discovery / Search Endpoint (`esearch.fcgi`):**
   ```http
   GET https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term=(clinical+trial[Publication+Type]+OR+randomized+controlled+trial[Publication+Type])+AND+hasabstract[Filter]+AND+english[Language]&retmax=130&sort=pub_date&retmode=json
   ```
2. **Fetch Endpoint (`efetch.fcgi`):**
   ```http
   GET https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id=42372807,42753671,42734448,...&retmode=xml
   ```

To ensure minimal overhead and strictly avoid downloading massive database baselines (50+ GB), the API was queried in a streaming, lightweight request returning only ~3.0 MB of source XML for the targeted candidate articles.

---

## 4. Number of Records Selected
* **Target Count:** 100 records (within the 50–200 required window).
* **Final Curated Records:** **100 records**.

---

## 5. Selection Criteria
Records were selected according to the following strict criteria:
* **Valid PMID:** Must contain an authentic, non-empty PubMed Identifier string.
* **Non-empty Title:** Must have a clear, non-empty publication title.
* **Non-empty Abstract:** Must include the full, original medical abstract text.
* **Author Details:** Must have parsed individual authors (`ForeName LastName`) or organizational collective names where available.
* **Publication Date:** Must have valid publication date metadata, prioritized in `YYYY-MM-DD` format.
* **Domain Relevance:** Filtered for clinical trials and randomized controlled trials (`clinical trial[Publication Type] OR randomized controlled trial[Publication Type]`), which provide rigorous, structured medical evidence ideal for summarization.
* **Uniqueness:** All records are deduplicated with 100% unique PMIDs.

---

## 6. Cleaning & Normalization Performed
* **XML & HTML Tag Stripping:** Removed embedded inline formatting tags (such as `<i>`, `<b>`, `<sup>`, `<sub>`, `<jats:sec>`, etc.) across titles and abstracts.
* **HTML Entity Decoding:** Unescaped entities (`&amp;` &rarr; `&`, `&gt;` &rarr; `>`, `&lt;` &rarr; `<`, Greek symbols, math operators).
* **Whitespace Normalization:** Standardized excessive whitespace, tabs, and spurious carriage returns while maintaining clear paragraph breaks between structured sections.
* **Section Header Preservation:** Retained all meaningful structured abstract section headers (e.g., `BACKGROUND`, `OBJECTIVE`, `METHODS`, `RESULTS`, `CONCLUSION`) formatted with uppercase labels.
* **Date Normalization:** Normalized 3-letter month abbreviations (e.g., `Jan` &rarr; `01`) and zero-padded day numbers to standard ISO 8601 (`YYYY-MM-DD`) format without inventing missing parts.
* **Zero Medical Alteration:** No semantic altering, summarization, or synthesis was performed. All text faithfully reflects the peer-reviewed literature.

---

## 7. Dataset Files

| File | Description | Format |
| :--- | :--- | :--- |
| `pubmed_sample.json` | Primary dataset formatted as a JSON array of objects | JSON (UTF-8) |
| `pubmed_sample.csv` | Tabular representation with 5 columns (`pmid,title,authors,date,abstract`) | CSV (UTF-8, RFC 4180) |
| `prepare_dataset.py` | Reproducible Python 3 script used to query the API and build the dataset | Python |

---

## 8. JSON Schema & Specification

### JSON Schema
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "PubMedSampleDataset",
  "type": "array",
  "items": {
    "type": "object",
    "required": ["pmid", "title", "authors", "date", "abstract"],
    "properties": {
      "pmid": {
        "type": "string",
        "description": "Unique PubMed Identifier (as a string)"
      },
      "title": {
        "type": "string",
        "description": "Cleaned article title without XML/HTML markup"
      },
      "authors": {
        "type": "array",
        "items": {
          "type": "string"
        },
        "description": "List of author names (ForeName LastName)"
      },
      "date": {
        "type": "string",
        "description": "Publication date, preferably YYYY-MM-DD"
      },
      "abstract": {
        "type": "string",
        "description": "Full, un-summarized abstract preserving structured headings"
      }
    }
  }
}
```

### Record Example
```json
{
  "pmid": "42372807",
  "title": "Chinese herbal medicine Xiangsu Hewei Granules in treating non-erosive gastroesophageal reflux disease with liver stomach stagnation heat syndrome: A multicentre, randomized, double-blind, placebo-controlled trial.",
  "authors": [
    "Zhi-Min Chen",
    "Junxiang Li",
    "Zhijun Huang"
  ],
  "date": "2026-06-29",
  "abstract": "AIM: To verify the efficacy and safety of Xiangsu Hewei Granules in treating NERD with liver stomach stagnation heat syndrome.\n\nMATERIALS AND METHODS: This randomized, double-blind, placebo-controlled, multicentre phase III trial included 480 patients...\n\nRESULTS: ...\n\nCONCLUSION: In this selected population of NERD patients..."
}
```

---

## 9. How the Backend Team Can Load the Dataset

### Python
```python
import json

# 1. Loading with standard library
with open("pubmed_sample.json", "r", encoding="utf-8") as f:
    dataset = json.load(f)

print(f"Loaded {len(dataset)} records.")
first_item = dataset[0]
print("PMID:", first_item["pmid"])
print("Title:", first_item["title"])
print("Authors:", first_item["authors"])
print("Date:", first_item["date"])
print("Abstract:", first_item["abstract"][:200], "...")

# 2. Loading with pandas (optional)
# import pandas as pd
# df = pd.read_json("pubmed_sample.json")
```

### Node.js / JavaScript
```javascript
const fs = require('fs');
const path = require('path');

const filePath = path.join(__dirname, 'pubmed_sample.json');
const rawData = fs.readFileSync(filePath, 'utf-8');
const dataset = JSON.parse(rawData);

console.log(`Loaded ${dataset.length} records.`);
console.log(`First record title: ${dataset[0].title}`);
```

---

## 10. Validation & Quality Audit Report

Every record was verified programmatically against the required schema:

| Validation Metric | Count / Status | Notes |
| :--- | :--- | :--- |
| **Total Records** | `100` | Target achieved (acceptable range: 50–200) |
| **Unique PMIDs** | `100` | 100% uniqueness verified |
| **Records with Titles** | `100` | 100% non-empty |
| **Records with Abstracts** | `100` | 100% non-empty |
| **Records with Authors** | `100` | 100% populated with author list |
| **Records with Dates** | `100` | 100% formatted dates present |
| **Duplicate PMID Count** | `0` | Zero duplicate entries |
| **Malformed Record Count**| `0` | All records adhere strictly to schema |
| **JSON Validity** | `Passed` | Fully verified via standard JSON parser |
