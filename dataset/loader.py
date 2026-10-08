import csv
import json
import os
import urllib.request
from typing import Any, Dict, List, Union

def load_robust_json(text_or_path: str) -> List[Dict[str, Any]]:
    """
    Loads JSON from a file path or raw JSON string.
    Robustly handles:
    - Standard single JSON array: [...]
    - Single JSON object: {...}
    - Concatenated JSON arrays/objects (e.g. [...] [...] without outer wrapper)
    - JSON Lines (one JSON object per line)
    """
    if os.path.exists(text_or_path):
        with open(text_or_path, "r", encoding="utf-8") as f:
            content = f.read().strip()
    else:
        content = text_or_path.strip()

    if not content:
        return []

    # 1. Try standard json.loads
    try:
        parsed = json.loads(content)
        if isinstance(parsed, list):
            return parsed
        elif isinstance(parsed, dict):
            return [parsed]
    except json.JSONDecodeError:
        pass

    # 2. Try parsing concatenated JSON objects or arrays using raw_decode
    items: List[Dict[str, Any]] = []
    decoder = json.JSONDecoder()
    pos = 0
    length = len(content)

    while pos < length:
        while pos < length and content[pos].isspace():
            pos += 1
        if pos >= length:
            break
        try:
            obj, end_pos = decoder.raw_decode(content, pos)
            pos = end_pos
            if isinstance(obj, list):
                items.extend(obj)
            elif isinstance(obj, dict):
                items.append(obj)
        except json.JSONDecodeError:
            # Fallback to line-by-line parsing
            break

    if items:
        return items

    # 3. Try parsing line-by-line (JSON Lines)
    lines = content.splitlines()
    for line in lines:
        line_str = line.strip()
        if not line_str:
            continue
        try:
            parsed_line = json.loads(line_str)
            if isinstance(parsed_line, list):
                items.extend(parsed_line)
            elif isinstance(parsed_line, dict):
                items.append(parsed_line)
        except json.JSONDecodeError:
            continue

    return items

def load_csv_file(filepath: str) -> List[Dict[str, Any]]:
    """
    Loads records from a CSV file (e.g. pubmed_sample.csv).
    """
    records: List[Dict[str, Any]] = []
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            authors_val = row.get("authors", "")
            if authors_val.startswith("[") and authors_val.endswith("]"):
                try:
                    authors_list = json.loads(authors_val)
                except Exception:
                    authors_list = [a.strip() for a in authors_val.strip("[]").split(",") if a.strip()]
            else:
                sep = ";" if ";" in authors_val else ","
                authors_list = [a.strip() for a in authors_val.split(sep) if a.strip()]

            records.append({
                "pmid": row.get("pmid"),
                "title": row.get("title"),
                "authors": authors_list,
                "date": row.get("date"),
                "abstract": row.get("abstract")
            })
    return records

def load_from_file(filepath: str) -> List[Dict[str, Any]]:
    """
    Loads records from either a JSON or CSV file based on file extension.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Dataset file not found: {filepath}")

    ext = os.path.splitext(filepath)[1].lower()
    if ext == ".csv":
        return load_csv_file(filepath)
    return load_robust_json(filepath)

def load_from_url(url: str, timeout: int = 15) -> List[Dict[str, Any]]:
    """
    Fetches raw dataset content from a remote URL (such as GitHub raw URL) and parses it.
    """
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "PubMed-Dataset-Retriever/1.0"}
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        content = resp.read().decode("utf-8")
    return load_robust_json(content)
