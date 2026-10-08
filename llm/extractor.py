import os
from typing import Optional
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

# Load environment variables from .env file
load_dotenv()

# ==============================================================================
# Model Configuration
# Model variable kept in ONE clearly identifiable place for easy modification.
# ==============================================================================
GEMINI_MODEL = "gemini-2.5-flash"


class Evidence(BaseModel):
    """Structured medical evidence extracted strictly from a research abstract."""

    objective: Optional[str] = Field(
        default=None,
        description="The main research question, hypothesis, or primary objective of the study."
    )
    study_type: Optional[str] = Field(
        default=None,
        description="The study design or type (e.g., Randomized Controlled Trial, Systematic Review, Cohort Study)."
    )
    population: Optional[str] = Field(
        default=None,
        description="The target population, patient demographics, or condition studied."
    )
    sample_size: Optional[str] = Field(
        default=None,
        description="The number of participants, subjects, or samples included in the study."
    )
    intervention: Optional[str] = Field(
        default=None,
        description="The treatment, procedure, exposure, or test being evaluated."
    )
    comparator: Optional[str] = Field(
        default=None,
        description="The control, placebo, standard care, or comparison group."
    )
    outcomes: Optional[str] = Field(
        default=None,
        description="The primary and secondary endpoints, measures, or variables evaluated."
    )
    key_findings: Optional[str] = Field(
        default=None,
        description="The primary quantitative and qualitative results, statistical findings, or effect sizes."
    )
    limitations: Optional[str] = Field(
        default=None,
        description="Any study weaknesses, potential biases, or constraints explicitly noted in the abstract."
    )
    conclusion: Optional[str] = Field(
        default=None,
        description="The overall conclusions or take-home messages stated by the authors."
    )


EXTRACTION_SYSTEM_INSTRUCTION = """You are a rigorous medical evidence extraction system.
Extract structured clinical evidence from the provided medical research abstract.

STRICT EXTRACTION RULES:
1. Extract ONLY information explicitly supported by the supplied abstract.
2. Do NOT use outside medical knowledge.
3. Do NOT infer facts that are not stated.
4. Do NOT invent sample sizes, statistics, populations, interventions, outcomes, limitations, or conclusions.
5. If information is absent or not mentioned in the abstract, return null for that field.
6. Preserve the exact meaning and uncertainty of the original paper.
7. If the abstract says "associated with", do NOT rewrite it as "causes".
8. Preserve important numerical values, confidence intervals, p-values, and statistics exactly as written when available.
9. Return structured JSON matching the provided schema.
"""


def _sanitize_error(error_msg: str, api_key: Optional[str]) -> str:
    """Helper to ensure API key is never leaked in exception messages."""
    if api_key and api_key in error_msg:
        return error_msg.replace(api_key, "[REDACTED_API_KEY]")
    return error_msg


def extract_evidence(abstract: str, api_key: Optional[str] = None) -> Evidence:
    """
    Extracts structured medical evidence from a single medical research abstract.

    Args:
        abstract (str): The raw medical research abstract text.
        api_key (Optional[str]): Optional API key. If not provided, loads from GEMINI_API_KEY env variable.

    Returns:
        Evidence: Structured Pydantic Evidence model instance.

    Raises:
        ValueError: If the abstract is empty or API key is missing.
        RuntimeError: If Gemini API call or response parsing fails.
    """
    # 1. Validate that the abstract is not empty
    if not abstract or not abstract.strip():
        raise ValueError("Abstract text cannot be empty or contain only whitespace.")

    # Get API key from environment if not explicitly passed
    key_to_use = api_key or os.getenv("GEMINI_API_KEY")
    if not key_to_use or key_to_use == "YOUR_KEY_HERE":
        raise ValueError(
            "GEMINI_API_KEY is not set or contains the default placeholder. "
            "Please configure a valid API key in your .env file."
        )

    # 2. Send abstract to Gemini API using official google-genai SDK
    try:
        client = genai.Client(api_key=key_to_use)

        prompt = f"Extract structured evidence from this medical abstract:\n\n{abstract.strip()}"

        config = types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=Evidence,
            temperature=0.0,
            system_instruction=EXTRACTION_SYSTEM_INSTRUCTION,
        )

        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config=config,
        )

    except Exception as e:
        clean_msg = _sanitize_error(str(e), key_to_use)
        raise RuntimeError(f"Gemini API request failed: {clean_msg}") from None

    # 3. Parse and validate response schema
    try:
        if response.parsed is not None:
            if isinstance(response.parsed, Evidence):
                return response.parsed
            elif isinstance(response.parsed, dict):
                return Evidence.model_validate(response.parsed)

        if response.text:
            return Evidence.model_validate_json(response.text)

        raise ValueError("Gemini API returned an empty response body.")

    except Exception as parse_error:
        clean_msg = _sanitize_error(str(parse_error), key_to_use)
        raise RuntimeError(f"Failed to parse structured evidence response: {clean_msg}") from None
