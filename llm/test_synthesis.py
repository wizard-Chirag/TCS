import os
import sys
from pathlib import Path
from typing import List, Set, Tuple

# Add project root directory to sys.path to ensure module imports work cleanly
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from dotenv import load_dotenv
from llm.extractor import Evidence, GEMINI_MODEL
from llm.synthesis import (
    EvidenceClaim,
    PaperEvidence,
    Synthesis,
    synthesize_evidence,
)

# ==============================================================================
# BENCHMARK SET 1: SEMAGLUTIDE PAPERS (Test B & Test C)
# ==============================================================================

PAPER_1_SELECT = PaperEvidence(
    paper_id="37952401",
    title="Semaglutide and Cardiovascular Outcomes in Patients with Overweight or Obesity without Diabetes",
    publication_date="2023-11-11",
    source_url="https://pubmed.ncbi.nlm.nih.gov/37952401/",
    evidence=Evidence(
        objective="To evaluate whether weekly subcutaneous semaglutide (2.4 mg) reduces cardiovascular risk in patients with overweight or obesity and established cardiovascular disease without diabetes.",
        study_type="Double-blind, randomized, placebo-controlled trial (RCT)",
        population="17,604 non-diabetic patients aged 45 years or older with established cardiovascular disease and BMI >= 27",
        sample_size="17,604 patients (8,803 semaglutide, 8,801 placebo)",
        intervention="Subcutaneous once-weekly semaglutide 2.4 mg",
        comparator="Matching placebo",
        outcomes="Primary composite endpoint of death from cardiovascular causes, nonfatal myocardial infarction, or nonfatal stroke",
        key_findings="Semaglutide reduced primary cardiovascular composite endpoint events (6.5% vs 8.0%, HR 0.80; 95% CI 0.72-0.90; P<0.001). Adverse events leading to permanent discontinuation of trial product occurred in 16.6% of semaglutide vs 8.2% of placebo patients.",
        limitations="Enrolled exclusively patients with pre-existing established cardiovascular disease.",
        conclusion="Weekly semaglutide 2.4 mg was superior to placebo in reducing major adverse cardiovascular events over a mean follow-up of 39.8 months."
    )
)

PAPER_2_STEP1 = PaperEvidence(
    paper_id="33704233",
    title="Once-Weekly Semaglutide in Adults with Overweight or Obesity",
    publication_date="2021-03-18",
    source_url="https://pubmed.ncbi.nlm.nih.gov/33704233/",
    evidence=Evidence(
        objective="To assess the efficacy and safety of semaglutide 2.4 mg once weekly for body-weight management in adults with overweight or obesity without diabetes.",
        study_type="Double-blind, randomized, placebo-controlled trial (RCT)",
        population="1,961 adults with BMI >= 30, or BMI >= 27 with weight-related comorbidities, without diabetes",
        sample_size="1,961 participants (1,306 semaglutide, 655 placebo)",
        intervention="Subcutaneous once-weekly semaglutide 2.4 mg plus lifestyle intervention",
        comparator="Matching placebo plus lifestyle intervention",
        outcomes="Percentage change in body weight from baseline to week 68, waist circumference, blood pressure, lipid profiles, and adverse events",
        key_findings="Mean body weight change from baseline was -14.9% with semaglutide vs -2.4% with placebo (treatment difference -12.4 percentage points, P<0.001) after 68 weeks. Nausea and diarrhea were the most common adverse events.",
        limitations="Trial cohort was predominantly female (74.1%).",
        conclusion="In non-diabetic adults with overweight or obesity, weekly semaglutide 2.4 mg produced substantial, sustained weight loss accompanied by cardiometabolic improvements over 68 weeks."
    )
)

PAPER_3_REALWORLD = PaperEvidence(
    paper_id="35835672",
    title="Real-World Efficacy and Tolerability of Semaglutide 2.4 mg for Weight Management: A 12-Month Cohort Study",
    publication_date="2022-09-01",
    source_url="https://pubmed.ncbi.nlm.nih.gov/35835672/",
    evidence=Evidence(
        objective="To evaluate real-world weight loss outcomes and treatment adherence with semaglutide 2.4 mg in routine clinical practice.",
        study_type="Prospective observational cohort study",
        population="408 real-world clinic patients with overweight or obesity (mean BMI 38.1 kg/m2) treated in outpatient weight management centers",
        sample_size="408 patients",
        intervention="Subcutaneous once-weekly semaglutide 2.4 mg in routine practice",
        comparator=None,
        outcomes="Weight change at 6 and 12 months, patient-reported side effects, and overall treatment discontinuation rates",
        key_findings="At 12 months, mean weight loss was 10.9% (95% CI 9.5-12.3%). Discontinuation of treatment due to side effects or cost occurred in 22.5% of patients by 12 months.",
        limitations="Observational single-center design without a control group; high rate of financial/insurance-related dropouts.",
        conclusion="Semaglutide 2.4 mg produced significant weight loss in real-world clinical practice at 12 months, though magnitude was lower than 68-week RCTs."
    )
)


# ==============================================================================
# BENCHMARK SET 2: CONTROLLED GENUINE CONFLICT PAPERS (Test A)
# ==============================================================================

PAPER_CONFLICT_A = PaperEvidence(
    paper_id="PAPER_101",
    title="Effect of Treatment X on Mortality in Adult Heart Failure: A Multicenter RCT",
    publication_date="2023-01-01",
    source_url="https://pubmed.ncbi.nlm.nih.gov/101101/",
    evidence=Evidence(
        objective="To evaluate if Treatment X reduces all-cause mortality in adult heart failure patients.",
        study_type="Randomized Controlled Trial (RCT)",
        population="5,000 adult patients with heart failure",
        sample_size="5,000 patients",
        intervention="Treatment X 10mg daily",
        comparator="Placebo",
        outcomes="All-cause mortality at 2 years",
        key_findings="Treatment X significantly reduced all-cause mortality compared with placebo (HR 0.75; 95% CI 0.65 to 0.87; P<0.001).",
        conclusion="Treatment X reduces all-cause mortality in adult heart failure patients."
    )
)

PAPER_CONFLICT_B = PaperEvidence(
    paper_id="PAPER_102",
    title="Evaluation of Treatment X for All-Cause Mortality in Heart Failure: The HF-CANCEL Trial",
    publication_date="2023-06-01",
    source_url="https://pubmed.ncbi.nlm.nih.gov/102102/",
    evidence=Evidence(
        objective="To assess the effect of Treatment X on all-cause mortality in adult heart failure patients.",
        study_type="Randomized Controlled Trial (RCT)",
        population="4,800 adult patients with heart failure",
        sample_size="4,800 patients",
        intervention="Treatment X 10mg daily",
        comparator="Placebo",
        outcomes="All-cause mortality at 2 years",
        key_findings="Treatment X did not reduce all-cause mortality compared with placebo (HR 1.02; 95% CI 0.89 to 1.17; P=0.74).",
        conclusion="Treatment X did not reduce all-cause mortality in adult heart failure patients."
    )
)


# ==============================================================================
# VALIDATION EVALUATION FUNCTIONS
# ==============================================================================

def validate_genuine_conflict(synthesis_conflict: Synthesis) -> Tuple[str, str]:
    """Test A: Check if genuine evidence contradiction is placed in areas_of_conflict."""
    conflicts_text = " ".join(synthesis_conflict.areas_of_conflict).lower()
    has_conflict = any(kw in conflicts_text for kw in ["mortality", "all-cause", "treatment x", "reduce", "did not reduce"])

    if has_conflict and len(synthesis_conflict.areas_of_conflict) > 0:
        return "PASS", "[PASS] Genuine conflict correctly identified in areas_of_conflict"
    return "FAIL", f"[FAIL] Genuine conflict not found in areas_of_conflict ({synthesis_conflict.areas_of_conflict})"


def validate_different_study_conditions(synthesis_semaglutide: Synthesis) -> Tuple[str, str]:
    """Test B: Check that study condition differences (duration, setting) are NOT misclassified as conflicts."""
    conflicts_text = " ".join(synthesis_semaglutide.areas_of_conflict).lower()

    # Check if magnitude/duration differences were misclassified as conflicts
    misclassified = any(
        kw in conflicts_text
        for kw in ["15%", "10.9%", "68 weeks", "12 months", "cohort vs rct"]
    )

    # Check if important_differences correctly contains duration or study setting differences
    diffs_text = " ".join(synthesis_semaglutide.important_differences).lower()
    correctly_placed = any(
        kw in diffs_text
        for kw in ["follow-up", "duration", "68 weeks", "12 months", "observational", "real-world", "rct"]
    )

    if not misclassified and correctly_placed:
        return "PASS", "[PASS] Study condition differences correctly placed in important_differences, not areas_of_conflict"
    elif misclassified:
        return "FAIL", f"[FAIL] Misclassified study condition differences as genuine conflict: {synthesis_semaglutide.areas_of_conflict}"
    else:
        return "FAIL", "[FAIL] Study condition differences missing from important_differences"


def validate_discontinuation_reasons(synthesis_semaglutide: Synthesis) -> Tuple[str, str]:
    """Test C: Check that distinct discontinuation reasons are preserved and not merged."""
    findings_claims = [c.claim for c in synthesis_semaglutide.key_findings]

    # Check if 22.5% discontinuation was falsely reported as purely due to adverse events
    improper_merge = False
    for claim in findings_claims:
        claim_lower = claim.lower()
        if "22.5%" in claim_lower and "adverse event" in claim_lower and "cost" not in claim_lower and "side effect" not in claim_lower:
            improper_merge = True

    # Check if text explicitly preserves cost/side-effects vs adverse events distinction
    all_text = (
        " ".join(findings_claims) + " " +
        " ".join(synthesis_semaglutide.important_differences) + " " +
        " ".join(synthesis_semaglutide.areas_of_agreement)
    ).lower()

    preserves_distinction = ("cost" in all_text or "side effects or cost" in all_text or "different" in all_text or "not directly comparable" in all_text)

    if not improper_merge and preserves_distinction:
        return "PASS", "[PASS] Exact discontinuation reasons preserved without improper merging"
    elif improper_merge:
        return "FAIL", "[FAIL] Improperly merged 22.5% discontinuation as purely due to adverse events"
    else:
        return "FAIL", "[FAIL] Discontinuation reason distinction not preserved"


# ==============================================================================
# MAIN TEST RUNNER
# ==============================================================================

def main():
    load_dotenv(dotenv_path=ROOT_DIR / ".env")

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key or api_key == "YOUR_KEY_HERE":
        print("[ERROR] GEMINI_API_KEY is not configured in `.env`.")
        print("Please edit `.env` and set a valid API key before running the test.")
        sys.exit(1)

    print("=" * 60)
    print("CROSS-PAPER EVIDENCE SYNTHESIS TEST & GROUNDING VALIDATION")
    print(f"Target Model: {GEMINI_MODEL}")
    print("=" * 60)
    print()

    # --------------------------------------------------------------------------
    # RUN 1: MAIN SEMAGLUTIDE BENCHMARK SYNTHESIS
    # --------------------------------------------------------------------------
    research_question_1 = (
        "What are the efficacy, weight loss, and safety outcomes of once-weekly semaglutide 2.4 mg "
        "in non-diabetic adults with overweight or obesity?"
    )
    papers_1 = [PAPER_1_SELECT, PAPER_2_STEP1, PAPER_3_REALWORLD]

    print("Research Question:")
    print(f"  {research_question_1}")
    print()

    print("Papers:")
    for i, p in enumerate(papers_1, 1):
        print(f"  {i}. [{p.paper_id}] {p.title} ({p.evidence.study_type})")
    print()

    try:
        synthesis_1: Synthesis = synthesize_evidence(research_question_1, papers_1)
    except Exception as e:
        print(f"[ERROR] Semaglutide synthesis failed: {e}")
        sys.exit(1)

    print("=" * 60)
    print("SYNTHESIS RESULT")
    print("=" * 60)
    print()

    print("Overall Answer:")
    print(f"  {synthesis_1.overall_answer}")
    print()

    print("Key Findings:")
    for i, claim in enumerate(synthesis_1.key_findings, 1):
        print(f"  {i}. {claim.claim}")
        print(f"     Supporting papers   : {claim.supporting_papers}")
        print(f"     Contradicting papers : {claim.contradicting_papers}")
    print()

    print("Areas of Agreement:")
    for item in synthesis_1.areas_of_agreement:
        print(f"  - {item}")
    print()

    print("Areas of Conflict:")
    if synthesis_1.areas_of_conflict:
        for item in synthesis_1.areas_of_conflict:
            print(f"  - {item}")
    else:
        print("  - None (no genuine evidence contradictions present).")
    print()

    print("Important Differences:")
    for item in synthesis_1.important_differences:
        print(f"  - {item}")
    print()

    print("Evidence Limitations:")
    for item in synthesis_1.evidence_limitations:
        print(f"  - {item}")
    print()

    # --------------------------------------------------------------------------
    # RUN 2: CONTROLLED GENUINE CONFLICT SYNTHESIS (TEST A)
    # --------------------------------------------------------------------------
    research_question_2 = "Does Treatment X reduce all-cause mortality in adult heart failure patients?"
    papers_2 = [PAPER_CONFLICT_A, PAPER_CONFLICT_B]

    try:
        synthesis_2: Synthesis = synthesize_evidence(research_question_2, papers_2)
    except Exception as e:
        print(f"[ERROR] Conflict synthesis test failed: {e}")
        sys.exit(1)

    # --------------------------------------------------------------------------
    # GROUNDING VALIDATION CHECKS
    # --------------------------------------------------------------------------
    test_a_status, test_a_msg = validate_genuine_conflict(synthesis_2)
    test_b_status, test_b_msg = validate_different_study_conditions(synthesis_1)
    test_c_status, test_c_msg = validate_discontinuation_reasons(synthesis_1)

    print("=" * 60)
    print("SYNTHESIS GROUNDING VALIDATION")
    print("=" * 60)

    print(f"Genuine conflict test:")
    print(f"  [{test_a_status}] ({test_a_msg})")
    print()

    print(f"Different study conditions test:")
    print(f"  [{test_b_status}] ({test_b_msg})")
    print()

    print(f"Different discontinuation reasons test:")
    print(f"  [{test_c_status}] ({test_c_msg})")
    print()

    all_grounding_passed = all(
        s == "PASS" for s in [test_a_status, test_b_status, test_c_status]
    )

    print("Overall:")
    if all_grounding_passed:
        print("READY FOR INTEGRATION")
    else:
        print("NEEDS FIXES")
    print("=" * 60)


if __name__ == "__main__":
    main()
