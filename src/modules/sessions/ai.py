"""LLM-powered helpers for session title and summary generation."""

from uuid import UUID

from src.content.prompts.sessions import ScribePrompts
from src.core.logging import get_logger
from src.infrastructure.llm.service import LLMService
from src.infrastructure.persistence.postgres.repos.sessions_repo import SessionsRepository
from src.schemas.features.sessions import SessionTitleSchema

logger = get_logger(__name__)


async def generate_title(
    repo: SessionsRepository,
    llm: LLMService,
    session_id: UUID,
    user_id: UUID,
) -> str:
    """Generate a 3-word title from the first few transcripts."""
    session = await repo.get_by_id(session_id, user_id)
    if not session:
        return "Untitled Session"

    texts, _ = await repo.get_transcripts_since(session_id, after_id=None, limit=5)
    if not texts:
        return session.title

    transcripts_text = " ".join(texts)
    prompt = ScribePrompts.TITLE.format(transcripts=transcripts_text)

    result: SessionTitleSchema = await llm.generate_structured(
        system="You are a medical scribe.",
        user=prompt,
        schema=SessionTitleSchema,
    )

    await repo.update(session, {"title": result.title})
    logger.info(f"Generated title for session {session_id}: {result.title}")
    return result.title


async def generate_summary(
    repo: SessionsRepository,
    llm: LLMService,
    session_id: UUID,
    user_id: UUID,
) -> str:
    """Generate or update the clinical summary incrementally."""
    session = await repo.get_by_id(session_id, user_id)
    if not session:
        return ""

    texts, max_id = await repo.get_transcripts_since(
        session_id,
        after_id=session.last_summarized_transcript_id,
    )

    if not texts:
        return session.clinical_summary or ""

    transcripts_text = " ".join(texts)
    existing = session.clinical_summary or ""

    prompt = ScribePrompts.SUMMARY_UPDATE.format(
        existing_summary=existing,
        transcripts=transcripts_text,
    )

    updated_summary = await llm.generate_text(
        system="You are a medical scribe.",
        user=prompt,
    )

    updates = {"clinical_summary": updated_summary}
    if max_id is not None:
        updates["last_summarized_transcript_id"] = max_id

    await repo.update(session, updates)
    logger.info(f"Updated summary for session {session_id}")
    return updated_summary
