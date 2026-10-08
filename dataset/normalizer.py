import re
import html
from typing import Any, Dict, List, Optional

PUBMED_URL_TEMPLATE = "https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
PUBMED_URL_REGEX = re.compile(r"^https://pubmed\.ncbi\.nlm\.nih\.gov/\d+/?$")

def normalize_paper(raw: Dict[str, Any], source: str = "PubMed") -> Dict[str, Any]:
    """
    Normalizes an input raw paper dictionary into the standardized schema:
    {
      "paper_id": str | null,
      "title": str | null,
      "authors": list[str],
      "date": str | null,
      "abstract": str | null,
      "url": str | null,
      "source": "PubMed"
    }
    """
    if not isinstance(raw, dict):
        raise ValueError(f"Expected dict for raw paper, got {type(raw)}")

    # 1. paper_id (PMID)
    raw_id = raw.get("paper_id") or raw.get("pmid") or raw.get("id")
    paper_id: Optional[str] = None
    if raw_id is not None:
        paper_id_str = str(raw_id).strip()
        if paper_id_str:
            paper_id = paper_id_str

    # 2. title
    raw_title = raw.get("title")
    title: Optional[str] = None
    if raw_title is not None:
        title_str = str(raw_title).strip()
        if title_str:
            title = title_str

    # 3. authors
    raw_authors = raw.get("authors")
    authors: List[str] = []
    if isinstance(raw_authors, list):
        for a in raw_authors:
            if a is not None:
                a_str = str(a).strip()
                if a_str:
                    authors.append(a_str)
    elif isinstance(raw_authors, str) and raw_authors.strip():
        # Handle string authors separated by semicolon or comma
        sep = ";" if ";" in raw_authors else ","
        authors = [a.strip() for a in raw_authors.split(sep) if a.strip()]

    # 4. date
    raw_date = raw.get("date")
    date: Optional[str] = None
    if raw_date is not None:
        date_str = str(raw_date).strip()
        if date_str:
            date = date_str

    # 5. abstract - preserve full original abstract; never summarize or truncate
    raw_abstract = raw.get("abstract")
    abstract: Optional[str] = None
    if raw_abstract is not None:
        abstract_str = str(raw_abstract).strip()
        if abstract_str:
            abstract = abstract_str

    # 6. url - construct PubMed URL when PMID is available
    url: Optional[str] = None
    if paper_id and paper_id.isdigit():
        url = PUBMED_URL_TEMPLATE.format(pmid=paper_id)
    elif raw.get("url"):
        url = str(raw.get("url")).strip()

    return {
        "paper_id": paper_id,
        "title": title,
        "authors": authors,
        "date": date,
        "abstract": abstract,
        "url": url,
        "source": source
    }

def is_valid_paper(paper: Dict[str, Any]) -> bool:
    """
    Checks if a paper satisfies core integrity requirements:
    - Non-empty paper_id
    - Non-empty title
    - Non-empty abstract
    """
    return bool(
        paper.get("paper_id")
        and paper.get("title")
        and paper.get("abstract")
    )
