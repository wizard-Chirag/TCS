"""
Gemini LLM evidence extraction and synthesis package for Medical Literature Evidence Synthesizer.
"""

from .extractor import Evidence, extract_evidence, GEMINI_MODEL
from .synthesis import (
    PaperEvidence,
    SynthesisRequest,
    EvidenceClaim,
    Synthesis,
    synthesize_evidence,
)

__all__ = [
    "Evidence",
    "extract_evidence",
    "GEMINI_MODEL",
    "PaperEvidence",
    "SynthesisRequest",
    "EvidenceClaim",
    "Synthesis",
    "synthesize_evidence",
]
