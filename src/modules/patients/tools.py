from uuid import UUID

from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.agent.events import EventEmitter
from src.infrastructure.persistence.postgres.database import async_session_maker
from src.infrastructure.persistence.postgres.models import Session


@tool
async def get_patient_history(patient_id: str, config: RunnableConfig) -> str:
    """
    Fetch past consultation session summaries for a patient.
    Use this when the user asks about a patient's medical history,
    previous visits, or past clinical summaries.
    """
    emitter = EventEmitter(config)
    await emitter.emit_status("Fetching patient history...")

    async with async_session_maker() as db:
        stmt = (
            select(Session)
            .where(Session.patient_id == UUID(patient_id))
            .options(selectinload(Session.patient))
            .order_by(Session.created_at.desc())
            .limit(20)
        )
        result = await db.execute(stmt)
        sessions = list(result.scalars().all())

    if not sessions:
        return "No past sessions found for this patient."

    lines = []
    for s in sessions:
        summary = s.clinical_summary or "No summary available"
        lines.append(
            f"Session ({s.created_at.strftime('%Y-%m-%d %H:%M')}) — {s.title}\n"
            f"Status: {s.status}\n"
            f"Summary: {summary[:500]}\n"
        )

    return "\n---\n".join(lines)
