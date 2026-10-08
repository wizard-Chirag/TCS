import re
from typing import Any, Dict, List, Optional, Tuple

PUBMED_URL_REGEX = re.compile(r"^https://pubmed\.ncbi\.nlm\.nih\.gov/\d+/?$")

def verify_dataset(
    papers: List[Dict[str, Any]],
    raw_source_records: Optional[List[Dict[str, Any]]] = None
) -> Tuple[bool, Dict[str, Any]]:
    """
    Validates a list of normalized paper dictionaries against the required 5 criteria:
    1. Every returned paper has a paper_id.
    2. Every returned paper has a title.
    3. Every returned paper has an abstract.
    4. PMID-based URLs are valid in the expected format (https://pubmed.ncbi.nlm.nih.gov/<paper_id>/).
    5. No abstract is accidentally truncated.
    """
    total = len(papers)
    failures: List[str] = []

    missing_paper_id = 0
    missing_title = 0
    missing_abstract = 0
    invalid_urls = 0
    truncated_abstracts = 0

    # Build raw lookup if provided for exact comparison of abstract lengths
    raw_by_id: Dict[str, str] = {}
    if raw_source_records:
        for r in raw_source_records:
            pid = str(r.get("pmid") or r.get("paper_id") or "").strip()
            raw_abs = r.get("abstract")
            if pid and raw_abs:
                raw_by_id[pid] = str(raw_abs).strip()

    for idx, paper in enumerate(papers):
        # 1. paper_id
        paper_id = paper.get("paper_id")
        if not paper_id or not isinstance(paper_id, str) or not paper_id.strip():
            missing_paper_id += 1
            failures.append(f"Record {idx}: Missing or invalid paper_id")

        # 2. title
        title = paper.get("title")
        if not title or not isinstance(title, str) or not title.strip():
            missing_title += 1
            failures.append(f"Record {idx} (ID={paper_id}): Missing or empty title")

        # 3. abstract
        abstract = paper.get("abstract")
        if not abstract or not isinstance(abstract, str) or not abstract.strip():
            missing_abstract += 1
            failures.append(f"Record {idx} (ID={paper_id}): Missing or empty abstract")

        # 4. url format
        url = paper.get("url")
        if paper_id and paper_id.isdigit():
            expected_url = f"https://pubmed.ncbi.nlm.nih.gov/{paper_id}/"
            if url != expected_url:
                invalid_urls += 1
                failures.append(f"Record {idx} (ID={paper_id}): URL mismatch - got '{url}', expected '{expected_url}'")
            elif not PUBMED_URL_REGEX.match(url):
                invalid_urls += 1
                failures.append(f"Record {idx} (ID={paper_id}): URL regex mismatch - '{url}'")

        # 5. truncation check
        if abstract:
            abs_str = abstract.strip()
            # If raw source abstract is available, verify length matches or exceeds without truncation
            if paper_id and paper_id in raw_by_id:
                raw_abs = raw_by_id[paper_id]
                # Normalized abstract should not be shorter than raw stripped abstract
                if len(abs_str) < len(raw_abs):
                    truncated_abstracts += 1
                    failures.append(f"Record {idx} (ID={paper_id}): Abstract length shorter than raw source ({len(abs_str)} vs {len(raw_abs)})")
            
            # Check for suspicious truncation indicators at end of text
            truncation_suffixes = ("...", "…", "[truncated]", "[et al.]", "etc.")
            if abs_str.endswith(truncation_suffixes) and len(abs_str) < 100:
                truncated_abstracts += 1
                failures.append(f"Record {idx} (ID={paper_id}): Abstract ends suspiciously with truncation indicator")

    is_valid = (
        total > 0
        and missing_paper_id == 0
        and missing_title == 0
        and missing_abstract == 0
        and invalid_urls == 0
        and truncated_abstracts == 0
    )

    metrics = {
        "total_records": total,
        "missing_paper_id": missing_paper_id,
        "missing_title": missing_title,
        "missing_abstract": missing_abstract,
        "invalid_urls": invalid_urls,
        "truncated_abstracts": truncated_abstracts,
        "passed": is_valid,
        "failures": failures[:10]  # First 10 failures if any
    }

    return is_valid, metrics
