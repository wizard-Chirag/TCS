"""
Example script demonstrating the isolated dataset retrieval and normalization module.
Loads real records, formats them to the target schema, prints the JSON,
and validates all 5 requirements.
"""

import json
import os
import sys

# Ensure UTF-8 stdout on Windows console
if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Add parent directory to path so dataset package can be imported directly
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from dataset import DatasetRetriever, verify_dataset, load_from_file

def main():
    print("============================================================")
    print("PubMed Dataset Retrieval & Normalization Module - Demo")
    print("============================================================\n")

    retriever = DatasetRetriever()

    # Determine input dataset file to demonstrate
    dataset_file = os.path.join(parent_dir, "dataset.json")
    if not os.path.exists(dataset_file):
        dataset_file = os.path.join(parent_dir, "pubmed_sample.json")

    print(f"Loading and normalizing real records from: {dataset_file}\n")
    papers = retriever.get_papers(filepath=dataset_file, limit=5, valid_only=True)
    raw_source = load_from_file(dataset_file)

    print(f"Retrieved {len(papers)} normalized records.\n")
    print("--- SAMPLE NORMALIZED JSON OUTPUT (First 3 Records) ---\n")
    print(json.dumps(papers[:3], indent=2, ensure_ascii=False))

    print("\n------------------------------------------------------------")
    print("Running Verification Against 5 Core Requirements:")
    print("------------------------------------------------------------")

    is_valid, report = verify_dataset(papers, raw_source_records=raw_source)

    print(f"1. Every returned paper has a 'paper_id'  : {'PASS' if report['missing_paper_id'] == 0 else 'FAIL'}")
    print(f"2. Every returned paper has a 'title'     : {'PASS' if report['missing_title'] == 0 else 'FAIL'}")
    print(f"3. Every returned paper has an 'abstract' : {'PASS' if report['missing_abstract'] == 0 else 'FAIL'}")
    print(f"4. PMID-based URLs valid (https://...)    : {'PASS' if report['invalid_urls'] == 0 else 'FAIL'}")
    print(f"5. No abstract is accidentally truncated  : {'PASS' if report['truncated_abstracts'] == 0 else 'FAIL'}")
    print(f"\nOverall Validation Status: {'ALL CHECKS PASSED (SUCCESS)' if is_valid else 'FAILED'}")
    print(f"Total Papers Validated: {report['total_records']}")

if __name__ == "__main__":
    main()
