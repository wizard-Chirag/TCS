"""
Test Suite for Medical Evidence Retrieval Module
Tests domain validation, PMID extraction, XML parsing, error handling, and live SerpAPI retrieval.
"""

import os
import unittest
from unittest.mock import MagicMock, patch

from search_evidence import (
    EvidenceRetrievalError,
    MedicalEvidenceRetriever,
    MissingApiKeyError,
    NoResultsFoundError,
    SearchTimeoutError,
    SerpApiError,
    clean_title,
    extract_pmid,
    fetch_pubmed_details,
    is_pubmed_url,
    retrieve_evidence,
    search_medical_papers,
)


class TestPubMedDomainAndPmidExtraction(unittest.TestCase):
    """Verifies that only genuine PubMed/NCBI URLs pass validation and yield PMIDs."""

    def test_valid_pubmed_urls_and_pmids(self):
        samples = [
            ("https://pubmed.ncbi.nlm.nih.gov/29278713/", "29278713"),
            ("https://pubmed.ncbi.nlm.nih.gov/24622715", "24622715"),
            ("http://pubmed.ncbi.nlm.nih.gov/11874944/", "11874944"),
            ("https://www.ncbi.nlm.nih.gov/pubmed/15787679", "15787679"),
        ]
        for url, expected_pmid in samples:
            with self.subTest(url=url):
                self.assertTrue(is_pubmed_url(url), f"Expected valid PubMed URL: {url}")
                self.assertEqual(extract_pmid(url), expected_pmid)

    def test_invalid_consumer_health_urls(self):
        invalid_samples = [
            "https://www.mayoclinic.org/drugs-supplements/metformin-oral-route/description/drg-20067074",
            "https://www.nhs.uk/medicines/metformin/",
            "https://www.goodrx.com/metformin/what-is-it",
            "https://www.webmd.com/drugs/2/drug-11283/metformin-oral/details",
            "https://www.healthline.com/health/type-2-diabetes/metformin-benefits",
            "https://diabetesjournals.org/care/article/26/1/243/22594/Is-Metformin-Cardioprotective",
            "https://www.youtube.com/watch?v=BKfzKwduEus",
            "https://en.wikipedia.org/wiki/Metformin",
            "",
            None,
        ]
        for url in invalid_samples:
            with self.subTest(url=url):
                self.assertFalse(is_pubmed_url(url), f"Expected non-PubMed URL rejected: {url}")
                self.assertIsNone(extract_pmid(url))


class TestCleanTitle(unittest.TestCase):
    """Verifies title artifact cleaning."""

    def test_clean_title(self):
        self.assertEqual(
            clean_title("Metformin and Cardiovascular Outcomes - PubMed"),
            "Metformin and Cardiovascular Outcomes"
        )
        self.assertEqual(
            clean_title("Treatment of T2DM - PubMed Central"),
            "Treatment of T2DM"
        )
        self.assertEqual(
            clean_title("[Cardioprotective effects of Metformin]."),
            "Cardioprotective effects of Metformin"
        )


class TestPubMedXmlParsing(unittest.TestCase):
    """Verifies parsing of PubMed E-Utilities XML responses."""

    def test_fetch_pubmed_details_known_pmid(self):
        # Test live NCBI fetch for known landmark paper
        details = fetch_pubmed_details(["29278713"])
        self.assertIn("29278713", details)
        paper = details["29278713"]
        self.assertTrue(paper["title"])
        self.assertIn("Milton Packer", paper["authors"])
        self.assertIn("2018", paper["date"])
        self.assertTrue(len(paper["abstract"]) > 100, "Abstract should be populated")


class TestErrorHandling(unittest.TestCase):
    """Tests custom exceptions for missing keys, timeouts, and API errors."""

    def test_missing_api_key_raises_error(self):
        with patch.dict(os.environ, {"SERPAPI_API_KEY": ""}, clear=True):
            with self.assertRaises(MissingApiKeyError):
                MedicalEvidenceRetriever(api_key="")

    @patch("requests.get")
    def test_serpapi_error_handling(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 401
        mock_resp.text = "Invalid API key"
        mock_resp.json.return_value = {"error": "Invalid API key"}
        mock_get.return_value = mock_resp

        retriever = MedicalEvidenceRetriever(api_key="dummy_key")
        with self.assertRaises(SerpApiError):
            retriever.search("metformin cardiovascular risk")

    @patch("requests.get")
    def test_timeout_handling(self, mock_get):
        import requests
        mock_get.side_effect = requests.exceptions.Timeout("Request timed out")

        retriever = MedicalEvidenceRetriever(api_key="dummy_key", timeout=1)
        with self.assertRaises(SearchTimeoutError):
            retriever.search("metformin cardiovascular risk")


class TestLiveEvidenceRetrievalWithAbstracts(unittest.TestCase):
    """
    Live test against SerpAPI + NCBI to verify the normalized JSON output schema.
    """

    def test_metformin_query_full_schema(self):
        api_key = os.getenv("SERPAPI_API_KEY")
        if not api_key:
            self.skipTest("SERPAPI_API_KEY not present in environment/.env")

        query = "Does metformin reduce cardiovascular risk in type 2 diabetes?"
        results = retrieve_evidence(query, min_results=5, max_results=10)

        # 1. Result count check: 5 to 10 results
        self.assertGreaterEqual(len(results), 5, "Expected at least 5 results")
        self.assertLessEqual(len(results), 10, "Expected at most 10 results")

        # 2. Check no duplicate paper_ids or URLs
        paper_ids = [r["paper_id"] for r in results]
        urls = [r["url"] for r in results]
        self.assertEqual(len(paper_ids), len(set(paper_ids)), "Duplicate paper_id found")
        self.assertEqual(len(urls), len(set(urls)), "Duplicate URL found")

        # 3. Check every item's exact schema
        for r in results:
            self.assertIn("paper_id", r)
            self.assertIn("title", r)
            self.assertIn("authors", r)
            self.assertIn("date", r)
            self.assertIn("abstract", r)
            self.assertIn("url", r)
            self.assertIn("source", r)

            # Field types and validations
            self.assertTrue(isinstance(r["paper_id"], str) and r["paper_id"].isdigit())
            self.assertTrue(isinstance(r["title"], str) and len(r["title"]) > 0)
            self.assertTrue(isinstance(r["authors"], list))
            self.assertTrue(isinstance(r["date"], str))
            self.assertTrue(isinstance(r["abstract"], str) and len(r["abstract"]) > 0, "Abstract is mandatory")
            self.assertTrue(is_pubmed_url(r["url"]))
            self.assertEqual(r["source"], "PubMed")


if __name__ == "__main__":
    unittest.main()
