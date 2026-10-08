"""
Unit test suite for the isolated dataset retrieval and normalization module.
Verifies all 5 core requirements and schema specifications.
"""

import os
import sys
import unittest

# Add parent directory to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from dataset import (
    DatasetRetriever,
    normalize_paper,
    is_valid_paper,
    verify_dataset,
    load_from_file,
)

class TestDatasetModule(unittest.TestCase):

    def setUp(self):
        self.retriever = DatasetRetriever()
        self.dataset_json_path = os.path.join(parent_dir, "dataset.json")
        self.pubmed_sample_path = os.path.join(parent_dir, "pubmed_sample.json")

    def test_schema_keys_and_types(self):
        """Verify that normalize_paper produces the exact required schema keys."""
        sample_raw = {
            "pmid": "12345678",
            "title": "Clinical Study on Efficacy",
            "authors": ["Alice Smith", "Bob Jones"],
            "date": "2024-01-15",
            "abstract": "Background and clinical findings..."
        }
        normalized = normalize_paper(sample_raw)

        expected_keys = {"paper_id", "title", "authors", "date", "abstract", "url", "source"}
        self.assertEqual(set(normalized.keys()), expected_keys)
        self.assertEqual(normalized["paper_id"], "12345678")
        self.assertEqual(normalized["title"], "Clinical Study on Efficacy")
        self.assertEqual(normalized["authors"], ["Alice Smith", "Bob Jones"])
        self.assertEqual(normalized["date"], "2024-01-15")
        self.assertEqual(normalized["abstract"], "Background and clinical findings...")
        self.assertEqual(normalized["url"], "https://pubmed.ncbi.nlm.nih.gov/12345678/")
        self.assertEqual(normalized["source"], "PubMed")

    def test_missing_fields_represented_as_null_or_empty_list(self):
        """Verify that genuinely missing fields map to null or [] without inventing information."""
        empty_raw = {}
        normalized = normalize_paper(empty_raw)

        self.assertIsNone(normalized["paper_id"])
        self.assertIsNone(normalized["title"])
        self.assertEqual(normalized["authors"], [])
        self.assertIsNone(normalized["date"])
        self.assertIsNone(normalized["abstract"])
        self.assertIsNone(normalized["url"])
        self.assertEqual(normalized["source"], "PubMed")

    def test_pubmed_url_format(self):
        """Requirement 4: Verify PMID-based URLs match https://pubmed.ncbi.nlm.nih.gov/<pmid>/."""
        raw = {"pmid": "25102193", "title": "Test", "abstract": "Test"}
        normalized = normalize_paper(raw)
        self.assertEqual(normalized["url"], "https://pubmed.ncbi.nlm.nih.gov/25102193/")

    def test_no_abstract_truncation(self):
        """Requirement 5: Verify full abstract is preserved identically without truncation."""
        long_abstract = "A " * 500 + "Concluding sentence."
        raw = {"pmid": "99999", "title": "Long abstract test", "abstract": long_abstract}
        normalized = normalize_paper(raw)
        self.assertEqual(normalized["abstract"], long_abstract)
        self.assertEqual(len(normalized["abstract"]), len(long_abstract))

    def test_load_real_records_dataset_json(self):
        """Verify loading and validating real records from dataset.json."""
        if os.path.exists(self.dataset_json_path):
            papers = self.retriever.get_papers(filepath=self.dataset_json_path, valid_only=True)
            self.assertGreater(len(papers), 0, "Should load at least 1 valid paper")

            raw_source = load_from_file(self.dataset_json_path)
            is_valid, report = verify_dataset(papers, raw_source_records=raw_source)

            # Check 1: Every returned paper has a paper_id
            self.assertEqual(report["missing_paper_id"], 0)
            for p in papers:
                self.assertIsNotNone(p.get("paper_id"))
                self.assertTrue(len(p["paper_id"]) > 0)

            # Check 2: Every returned paper has a title
            self.assertEqual(report["missing_title"], 0)
            for p in papers:
                self.assertIsNotNone(p.get("title"))
                self.assertTrue(len(p["title"]) > 0)

            # Check 3: Every returned paper has an abstract
            self.assertEqual(report["missing_abstract"], 0)
            for p in papers:
                self.assertIsNotNone(p.get("abstract"))
                self.assertTrue(len(p["abstract"]) > 0)

            # Check 4: PMID-based URLs are valid
            self.assertEqual(report["invalid_urls"], 0)

            # Check 5: No abstract is accidentally truncated
            self.assertEqual(report["truncated_abstracts"], 0)

            self.assertTrue(is_valid)

    def test_load_real_records_pubmed_sample(self):
        """Verify loading and validating real records from pubmed_sample.json."""
        if os.path.exists(self.pubmed_sample_path):
            papers = self.retriever.get_papers(filepath=self.pubmed_sample_path, valid_only=True)
            self.assertEqual(len(papers), 100)

            raw_source = load_from_file(self.pubmed_sample_path)
            is_valid, report = verify_dataset(papers, raw_source_records=raw_source)

            self.assertTrue(is_valid)
            self.assertEqual(report["missing_paper_id"], 0)
            self.assertEqual(report["missing_title"], 0)
            self.assertEqual(report["missing_abstract"], 0)
            self.assertEqual(report["invalid_urls"], 0)
            self.assertEqual(report["truncated_abstracts"], 0)

if __name__ == "__main__":
    unittest.main()
