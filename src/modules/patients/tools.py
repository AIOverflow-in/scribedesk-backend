from uuid import UUID

from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.agent.events import EventEmitter
from src.infrastructure.persistence.postgres.database import async_session_maker
from src.infrastructure.persistence.postgres.models import Session


@tool
async def get_patient_history(config: RunnableConfig) -> str:
    """
    ALWAYS call this tool when the user asks about a patient's medical history, even if you think no patient is linked.
    The tool will tell you if there's no patient — you don't need to check beforehand.
    Returns past session summaries for the linked patient, or a message explaining why none is available.
    """
    emitter = EventEmitter(config)
    await emitter.emit_status("Fetching patient history...")

    patient_id = config.get("configurable", {}).get("patient_id")

    if not patient_id or patient_id.strip() == "":
        return "No patient is linked for this conversation."

    async with async_session_maker() as db:
        try:
            pid = UUID(patient_id)
        except ValueError:
            return "No patient is linked for this conversation."

        stmt = (
            select(Session)
            .where(Session.patient_id == pid)
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
