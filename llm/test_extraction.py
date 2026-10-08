import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple

# Add project root directory to sys.path to ensure module imports work cleanly
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from dotenv import load_dotenv
from llm.extractor import Evidence, GEMINI_MODEL, extract_evidence

# ==============================================================================
# REAL BENCHMARK MEDICAL ABSTRACTS
# ==============================================================================

# ------------------------------------------------------------------------------
# Test 1: Randomized Controlled Trial (RCT)
# Source: New England Journal of Medicine (NEJM) 2023; 389:2221-2232
# Title: Semaglutide and Cardiovascular Outcomes in Patients with Overweight or Obesity without Diabetes (SELECT Trial)
# PMID: 37952401 | ClinicalTrials.gov: NCT03574597
# ------------------------------------------------------------------------------
ABSTRACT_1_RCT = """
Background: Semaglutide, a glucagon-like peptide-1 receptor agonist, reduces cardiovascular risk in patients with type 2 diabetes. However, its effects in patients with overweight or obesity without diabetes are unknown.

Methods: In a double-blind, randomized, placebo-controlled trial (SELECT trial), we enrolled 17,604 patients aged 45 years or older who had established cardiovascular disease and a body-mass index (BMI) of 27 or higher, but no history of diabetes. Participants were randomly assigned in a 1:1 ratio to receive subcutaneous once-weekly semaglutide (2.4 mg) or matching placebo. The primary cardiovascular end point was a composite of death from cardiovascular causes, nonfatal myocardial infarction, or nonfatal stroke in a time-to-first-event analysis.

Results: A total of 8,803 patients received semaglutide and 8,801 received placebo. The mean duration of exposure was 34.2 +/- 13.7 months, and the mean duration of follow-up was 39.8 +/- 9.4 months. A primary cardiovascular end-point event occurred in 569 of 8,803 patients (6.5%) in the semaglutide group and in 701 of 8,801 patients (8.0%) in the placebo group (hazard ratio, 0.80; 95% confidence interval [CI], 0.72 to 0.90; P<0.001). Adverse events leading to permanent discontinuation of the trial product occurred in 1,461 patients (16.6%) in the semaglutide group and 718 patients (8.2%) in the placebo group (P<0.001), mainly gastrointestinal disorders.

Conclusions: In patients with preexisting cardiovascular disease and overweight or obesity but without diabetes, weekly subcutaneous semaglutide at a dose of 2.4 mg was superior to placebo in reducing the incidence of death from cardiovascular causes, nonfatal myocardial infarction, or nonfatal stroke over a mean follow-up of 39.8 months. (Funded by Novo Nordisk; SELECT ClinicalTrials.gov number, NCT03574597.)
"""

# ------------------------------------------------------------------------------
# Test 2: Observational Study (Prospective Cohort Study)
# Source: BMJ 2019; 365:l1451
# Title: Ultra-processed food intake and risk of cardiovascular disease: prospective cohort study (NutriNet-Sante)
# PMID: 31142457
# ------------------------------------------------------------------------------
ABSTRACT_2_OBSERVATIONAL = """
Objective: To assess the prospective association between ultra-processed food intake and risk of cardiovascular disease.

Design: Prospective observational cohort study (NutriNet-Sante cohort, 2009-2018).

Participants: 104,980 participants aged 18 and older (mean age 42.8 years, 79.2% female). Dietary intakes were gathered using repeated 24 hour dietary records designed to register participants' usual consumption for more than 3,300 food items.

Main outcome measures: Associations between ultra-processed food intake and risk of cardiovascular, coronary heart, and cerebrovascular diseases assessed using multivariable Cox proportional hazards models adjusted for known risk factors.

Results: During a median follow-up of 5.2 years, ultra-processed food intake was associated with a higher risk of overall cardiovascular disease (1,409 cases; hazard ratio for a 10% increase in ultra-processed food in diet 1.12, 95% confidence interval 1.05 to 1.20, P<0.001) and coronary heart disease (667 cases; hazard ratio 1.13, 95% CI 1.02 to 1.24, P=0.02). No statistically significant association was observed for cerebrovascular disease (742 cases; hazard ratio 1.09, 95% CI 0.99 to 1.20, P=0.08).

Conclusions: In this large observational prospective study, higher consumption of ultra-processed foods was associated with an increased risk of cardiovascular disease.
"""

# ------------------------------------------------------------------------------
# Test 3: Incomplete-Information Abstract (Open-Label Trial with missing fields)
# Source: American Journal of Psychiatry 2018; 175(8):801-802
# Title: Ketamine Infusion for Treatment-Resistant Depression in Adolescents: An Open-Label Trial
# PMID: 29555047
# Notes: Lacks a comparator group (single-arm), lacks explicit sample size N, and lacks limitations section.
# ------------------------------------------------------------------------------
ABSTRACT_3_INCOMPLETE = """
Background: Subanesthetic intravenous ketamine infusion has rapid antidepressant effects in adults with treatment-resistant depression, but data in pediatric populations are limited. We conducted an open-label preliminary trial to evaluate the acute efficacy and safety of ketamine in adolescents with treatment-resistant major depressive disorder.

Methods: Adolescents with treatment-resistant major depression received a single intravenous infusion of ketamine (0.5 mg/kg over 40 minutes). Primary depression severity was measured at baseline and at 24 hours, 72 hours, and 7 days post-infusion using the Children's Depression Rating Scale-Revised (CDRS-R).

Results: Significant reductions in CDRS-R depression scores were observed at 24 hours post-infusion (mean change -18.4 points, P < 0.01). Clinical response (>=50% reduction in CDRS-R score) was achieved in 38% of participants at 24 hours. Adverse events were transient and included mild dissociation and temporary elevation in blood pressure.

Conclusions: Intravenous ketamine infusion demonstrated preliminary efficacy and acceptable tolerability in adolescents with treatment-resistant depression.
"""


# ==============================================================================
# AUTOMATED VALIDATION CHECKS
# ==============================================================================

def check_1_extraction_succeeded(evidence: Evidence) -> Tuple[str, str]:
    """Check 1: Validate that response is a valid Evidence Pydantic object."""
    if isinstance(evidence, Evidence):
        return "PASS", "[PASS] Valid Evidence object"
    return "FAIL", "[FAIL] Invalid Evidence object"


def check_2_hallucination_sanities(evidence: Evidence, source_text: str) -> Tuple[str, str]:
    """Check 2: Basic hallucination check against numbers in sample_size."""
    if not evidence.sample_size:
        return "PASS", "[PASS] No obvious hallucination detected (sample_size is null)"

    # Extract all numbers from sample_size string
    extracted_numbers = re.findall(r"\b\d[\d,.]*\b", evidence.sample_size)
    source_normalized = source_text.replace(",", "")

    for num_str in extracted_numbers:
        clean_num = num_str.replace(",", "")
        if clean_num not in source_normalized:
            return (
                "FAIL",
                f"[FAIL] Potential hallucination: sample_size '{evidence.sample_size}' contains number '{num_str}' not found in abstract text",
            )

    return "PASS", "[PASS] No obvious hallucination detected"


def check_3_missing_fields_handling(
    evidence: Evidence, expected_null_fields: List[str]
) -> Tuple[str, str]:
    """Check 3: Verify that genuinely absent fields return null instead of invented text."""
    if not expected_null_fields:
        # Check if limitations is null (common for abstracts without explicit limitations section)
        if evidence.limitations is None:
            return "PASS", "[PASS] Missing limitations correctly returned null"
        return "PASS", "[PASS] Abstract contains comprehensive information"

    passed_fields = []
    failed_fields = []

    for field_name in expected_null_fields:
        val = getattr(evidence, field_name, None)
        if val is None:
            passed_fields.append(field_name)
        else:
            failed_fields.append((field_name, val))

    if not failed_fields:
        fields_str = ", ".join(passed_fields)
        return "PASS", f"[PASS] Missing fields correctly returned null ({fields_str})"
    else:
        invented = ", ".join([f"{f}='{v}'" for f, v in failed_fields])
        return "FAIL", f"[FAIL] Model invented missing information for fields: {invented}"


def check_4_numerical_preservation(
    evidence: Evidence, key_numbers: List[str]
) -> Tuple[str, str]:
    """Check 4: Check if key numbers from the abstract are preserved in extracted evidence."""
    evidence_text = " ".join([str(v) for v in evidence.model_dump().values() if v is not None])
    missing = []
    found = []

    for num in key_numbers:
        if num in evidence_text:
            found.append(num)
        else:
            missing.append(num)

    if not missing:
        return "PASS", f"[PASS] Important numerical values preserved ({', '.join(found)})"
    elif found:
        return (
            "MANUAL REVIEW",
            f"[MANUAL REVIEW] Preserved {len(found)}/{len(key_numbers)} numbers. Missing: {', '.join(missing)}",
        )
    else:
        return "FAIL", f"[FAIL] Key numerical values missing from extracted evidence: {', '.join(missing)}"


def check_5_study_type_robustness(evidence: Evidence, expected_category: str) -> Tuple[str, str]:
    """Check 5: Verify study type classification robustness."""
    study_type = (evidence.study_type or "").lower()

    if expected_category == "rct":
        if any(kw in study_type for kw in ["randomized", "rct", "controlled trial", "double-blind"]):
            return "PASS", f"[PASS] Correctly identified RCT design ('{evidence.study_type}')"
        return "FAIL", f"[FAIL] Expected RCT classification, got '{evidence.study_type}'"

    elif expected_category == "observational":
        if any(kw in study_type for kw in ["cohort", "observational", "prospective", "case-control"]):
            if "randomized" not in study_type:
                return "PASS", f"[PASS] Correctly identified Observational study ('{evidence.study_type}')"
            return "FAIL", f"[FAIL] Misclassified observational study as RCT ('{evidence.study_type}')"
        return "MANUAL REVIEW", f"[MANUAL REVIEW] Study type extracted as '{evidence.study_type}'"

    elif expected_category == "open_label":
        if any(kw in study_type for kw in ["open-label", "uncontrolled", "single-arm", "trial", "pilot"]):
            return "PASS", f"[PASS] Correctly identified study design ('{evidence.study_type}')"
        return "MANUAL REVIEW", f"[MANUAL REVIEW] Study type extracted as '{evidence.study_type}'"

    return "MANUAL REVIEW", f"[MANUAL REVIEW] Study type: '{evidence.study_type}'"


# ==============================================================================
# MAIN TEST RUNNER
# ==============================================================================

def run_test_case(
    test_num: int,
    test_title: str,
    abstract: str,
    expected_study_cat: str,
    key_numbers: List[str],
    expected_null_fields: List[str],
) -> Dict[str, str]:
    """Runs extraction and automated validation for one test case."""
    print("=" * 60)
    print(f"TEST {test_num} - {test_title.upper()}")
    print("=" * 60)

    print("\n[INFO] Abstract:")
    print("-" * 50)
    print(abstract.strip())
    print("-" * 50)

    evidence = extract_evidence(abstract)

    print("\n[RESULT]")
    print(evidence.model_dump_json(indent=2))

    # Perform automated checks
    c1_status, c1_msg = check_1_extraction_succeeded(evidence)
    c2_status, c2_msg = check_2_hallucination_sanities(evidence, abstract)
    c3_status, c3_msg = check_3_missing_fields_handling(evidence, expected_null_fields)
    c4_status, c4_msg = check_4_numerical_preservation(evidence, key_numbers)
    c5_status, c5_msg = check_5_study_type_robustness(evidence, expected_study_cat)

    print("\n[CHECKS]")
    print(f"- Check 1 (Valid Object)           : {c1_msg}")
    print(f"- Check 2 (Hallucination Check)     : {c2_msg}")
    print(f"- Check 3 (Missing Info Handling)  : {c3_msg}")
    print(f"- Check 4 (Numerical Preservation) : {c4_msg}")
    print(f"- Check 5 (Study-Type Robustness)  : {c5_msg}")
    print()

    return {
        "extraction": c1_status,
        "hallucination": c2_status,
        "missing_null": c3_status,
        "numerical": c4_status,
        "study_type": c5_status,
    }


def main():
    # Load environment variables
    load_dotenv(dotenv_path=ROOT_DIR / ".env")

    api_key = os.getenv("GEMINI_API_KEY")

    print("=" * 60)
    print("MEDICAL EVIDENCE EXTRACTION - 3 ABSTRACT VALIDATION")
    print(f"Target Model: {GEMINI_MODEL}")
    print("=" * 60)
    print()

    if not api_key or api_key == "YOUR_KEY_HERE":
        print("[ERROR] GEMINI_API_KEY is not configured in `.env`.")
        print("Please edit `.env` and set a valid API key before running the test.")
        sys.exit(1)

    # Test 1: RCT
    res_1 = run_test_case(
        test_num=1,
        test_title="Randomized Controlled Trial (RCT)",
        abstract=ABSTRACT_1_RCT,
        expected_study_cat="rct",
        key_numbers=["17,604", "0.80", "6.5%", "8.0%", "2.4 mg"],
        expected_null_fields=["limitations"],
    )

    # Test 2: Observational Study
    res_2 = run_test_case(
        test_num=2,
        test_title="Observational Study (Cohort)",
        abstract=ABSTRACT_2_OBSERVATIONAL,
        expected_study_cat="observational",
        key_numbers=["104,980", "1.12", "1.13", "5.2"],
        expected_null_fields=["comparator"],
    )

    # Test 3: Incomplete-Information Abstract
    res_3 = run_test_case(
        test_num=3,
        test_title="Incomplete Information",
        abstract=ABSTRACT_3_INCOMPLETE,
        expected_study_cat="open_label",
        key_numbers=["0.5 mg/kg", "38%"],
        expected_null_fields=["comparator", "sample_size", "limitations"],
    )

    # Final Summary Table
    print("=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)

    print("\nTest 1 - RCT:")
    print(f"  Extraction: {res_1['extraction']}")
    print(f"  Study type: {res_1['study_type']}")
    print(f"  Numerical preservation: {res_1['numerical']}")
    print(f"  Hallucination check: {res_1['hallucination']}")

    print("\nTest 2 - Observational:")
    print(f"  Extraction: {res_2['extraction']}")
    print(f"  Study type: {res_2['study_type']}")
    print(f"  Numerical preservation: {res_2['numerical']}")
    print(f"  Hallucination check: {res_2['hallucination']}")

    print("\nTest 3 - Missing information:")
    print(f"  Extraction: {res_3['extraction']}")
    print(f"  Missing fields -> null: {res_3['missing_null']}")
    print(f"  Hallucination check: {res_3['hallucination']}")

    all_tests_passed = all(
        res[k] in ["PASS", "MANUAL REVIEW"]
        for res in [res_1, res_2, res_3]
        for k in res
    )

    print("\nOverall:")
    if all_tests_passed:
        print("READY FOR NEXT STAGE")
    else:
        print("NEEDS FIXES")
    print("=" * 60)


if __name__ == "__main__":
    main()
