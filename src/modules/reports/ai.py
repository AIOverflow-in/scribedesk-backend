"""LLM helper for report generation."""

from src.content.prompts.reports import ReportPrompts
from src.core.logging import get_logger
from src.infrastructure.llm.service import LLMService

logger = get_logger(__name__)


async def generate_report(
    llm: LLMService,
    template_content: str,
    transcripts: str,
    clinical_summary: str,
    patient_info: str,
    doctor_info: str,
    additional_context: str,
) -> str:
    prompt = ReportPrompts.GENERATE.format(
        template_content=template_content,
        transcripts=transcripts,
        clinical_summary=clinical_summary,
        patient_info=patient_info,
        doctor_info=doctor_info,
        additional_context=additional_context or "(none)",
    )

    result = await llm.generate_text(
        system="You are a medical scribe generating clinical documents.",
        user=prompt,
    )

    return result.strip()
