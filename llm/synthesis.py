import os
from typing import List, Optional
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

# Reuse Evidence model, GEMINI_MODEL name, and error sanitizer from extractor
from llm.extractor import Evidence, GEMINI_MODEL, _sanitize_error

# Load environment variables
load_dotenv()


class PaperEvidence(BaseModel):
    """Container pairing a paper's identifier and metadata with its extracted Evidence object."""
    paper_id: str = Field(description="Unique identifier for the paper (e.g., PMID or DOI).")
    title: str = Field(description="Title of the research paper.")
    publication_date: Optional[str] = Field(default=None, description="Publication date or year.")
    source_url: Optional[str] = Field(default=None, description="Source URL or DOI link.")
    evidence: Evidence = Field(description="Extracted medical evidence object.")


class SynthesisRequest(BaseModel):
    """Input payload containing research question and paper evidence list."""
    research_question: str = Field(description="Target clinical or medical research question.")
    papers: List[PaperEvidence] = Field(description="List of papers with extracted evidence.")


class EvidenceClaim(BaseModel):
    """A synthesized finding backed by specific paper references."""
    claim: str = Field(description="Specific claim or finding synthesized across the supplied papers.")
    supporting_papers: List[str] = Field(
        default_factory=list,
        description="Exact paper_id strings of papers that support this claim."
    )
    contradicting_papers: List[str] = Field(
        default_factory=list,
        description="Exact paper_id strings of papers that contradict or oppose this claim."
    )


class Synthesis(BaseModel):
    """Structured cross-paper evidence synthesis response model."""
    overall_answer: str = Field(
        description="Comprehensive direct answer to the research question grounded strictly in the supplied evidence."
    )
    key_findings: List[EvidenceClaim] = Field(
        description="List of major synthesized claims with exact paper attribution."
    )
    areas_of_agreement: List[str] = Field(
        description="Points where multiple papers agree or demonstrate concordant findings."
    )
    areas_of_conflict: List[str] = Field(
        description="Points of direct, genuine evidence contradiction (e.g. Paper A shows reduction in X, Paper B shows no reduction in X under comparable conditions). Do NOT put magnitude or study design differences here."
    )
    important_differences: List[str] = Field(
        description="Key differences in study populations, follow-up durations, study designs, outcome definitions, or real-world vs RCT settings (NOT genuine contradictions)."
    )
    evidence_limitations: List[str] = Field(
        description="Limitations of the collective evidence base (e.g., lack of long-term data, specific population gaps)."
    )


SYNTHESIS_SYSTEM_INSTRUCTION = """You are a rigorous medical evidence synthesis system.
Your task is to synthesize extracted medical evidence from multiple research papers to answer a target research question.

CRITICAL GROUNDING & SYNTHESIS RULES:

1. STRICT ADHERENCE TO SUPPLIED EVIDENCE:
   - Use ONLY the information contained in the supplied papers and their extracted evidence.
   - Do NOT use outside medical knowledge or make ungrounded inferences.
   - Do NOT invent studies, results, statistics, populations, interventions, or conclusions.
   - Every claim in key_findings MUST be strictly supported by the cited paper_ids.

2. GENUINE CONFLICTS VS. CONTEXTUAL DIFFERENCES:
   - 'areas_of_conflict' MUST contain ONLY genuine evidence contradictions (e.g., Paper A finds a statistically significant reduction in outcome Y, while Paper B finds no significant reduction or worsening of outcome Y under comparable conditions).
   - Do NOT classify differences in magnitude (e.g., 15% vs 10% weight loss), follow-up duration (e.g., 68 weeks vs 12 months), study design (RCT vs observational cohort), population, or outcome definitions as conflicts or contradictions.
   - All variations in duration, study setting, magnitude, or design MUST be placed in 'important_differences', NOT in 'areas_of_conflict'.

3. PRESERVATION OF EXACT OUTCOMES & DISCONTINUATION REASONS:
   - Preserve the exact reasons for outcomes whenever specified.
   - Do NOT combine or equate different forms of treatment discontinuation (e.g., discontinuation due to adverse events vs. discontinuation due to cost vs. overall dropout).
   - If Paper A reports discontinuation due to adverse events (e.g. 16.6%) and Paper B reports discontinuation due to side effects or cost combined (e.g. 22.5%), state clearly that they measure different outcomes and are NOT directly comparable.
   - Never reinterpret general treatment discontinuation as discontinuation due to adverse events unless explicitly supported by the supplied paper evidence.

4. CLAIM-TO-SOURCE GROUNDING:
   - A paper must ONLY be listed in supporting_papers if its evidence explicitly supports the ENTIRE claim.
   - Example: A paper reporting common GI side effects must NOT be cited for a claim stating GI side effects caused treatment discontinuation unless its evidence explicitly states discontinuation occurred.

5. CONSERVATIVE REPORTING:
   - If evidence is insufficient, state: "Evidence is insufficient to determine..."
   - Do not fill evidence gaps using general medical knowledge.
   - Preserve causal language exactly: if a paper says 'associated with', do NOT rewrite it as 'causes'.
   - Do NOT calculate pooled effect sizes or perform meta-analyses.

6. OUTPUT FORMAT:
   - Return structured JSON matching the provided Synthesis schema.
"""


def synthesize_evidence(
    research_question: str,
    papers: List[PaperEvidence],
    api_key: Optional[str] = None,
) -> Synthesis:
    """
    Synthesizes extracted evidence from multiple papers to answer a research question.

    Args:
        research_question (str): The target research question.
        papers (List[PaperEvidence]): List of papers with extracted Evidence objects.
        api_key (Optional[str]): Optional API key. Defaults to GEMINI_API_KEY env var.

    Returns:
        Synthesis: Structured Pydantic Synthesis model instance.

    Raises:
        ValueError: If input parameters are invalid or API key is missing.
        RuntimeError: If Gemini API call or response parsing fails.
    """
    # 1. Validate inputs
    if not research_question or not research_question.strip():
        raise ValueError("Research question cannot be empty or contain only whitespace.")
    if not papers:
        raise ValueError("At least one paper must be provided for evidence synthesis.")

    key_to_use = api_key or os.getenv("GEMINI_API_KEY")
    if not key_to_use or key_to_use == "YOUR_KEY_HERE":
        raise ValueError(
            "GEMINI_API_KEY is not set or contains default placeholder. "
            "Please configure your key in .env."
        )

    # 2. Format input payload for Gemini prompt
    papers_payload = []
    for p in papers:
        papers_payload.append({
            "paper_id": p.paper_id,
            "title": p.title,
            "publication_date": p.publication_date,
            "source_url": p.source_url,
            "evidence": p.evidence.model_dump(),
        })

    prompt_data = {
        "research_question": research_question.strip(),
        "papers": papers_payload,
    }

    prompt = (
        f"Synthesize the following paper evidence to answer the research question.\n\n"
        f"INPUT DATA:\n{prompt_data}"
    )

    # 3. Call Gemini API with structured output schema
    try:
        client = genai.Client(api_key=key_to_use)

        config = types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=Synthesis,
            temperature=0.0,
            system_instruction=SYNTHESIS_SYSTEM_INSTRUCTION,
        )

        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config=config,
        )
    except Exception as e:
        clean_msg = _sanitize_error(str(e), key_to_use)
        raise RuntimeError(f"Gemini API synthesis request failed: {clean_msg}") from None

    # 4. Parse response into Synthesis model
    try:
        if response.parsed is not None:
            if isinstance(response.parsed, Synthesis):
                return response.parsed
            elif isinstance(response.parsed, dict):
                return Synthesis.model_validate(response.parsed)

        if response.text:
            return Synthesis.model_validate_json(response.text)

        raise ValueError("Gemini API returned an empty response body.")
    except Exception as parse_err:
        clean_msg = _sanitize_error(str(parse_err), key_to_use)
        raise RuntimeError(f"Failed to parse synthesis response: {clean_msg}") from None
