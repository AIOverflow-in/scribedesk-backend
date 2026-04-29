from uuid import UUID, uuid4

from src.core.exceptions import NotFoundException
from src.core.logging import get_logger
from src.infrastructure.llm.service import LLMService
from src.infrastructure.persistence.postgres.models import Report, Template
from src.infrastructure.persistence.postgres.repos.reports_repo import ReportsRepository
from src.infrastructure.persistence.postgres.repos.sessions_repo import SessionsRepository
from src.infrastructure.persistence.postgres.repos.templates_repo import TemplatesRepository
from src.infrastructure.persistence.postgres.repos.user_repo import UserRepository
from src.modules.reports.ai import generate_report
from src.utils.formatters import calculate_age

logger = get_logger(__name__)


class ReportService:
    def __init__(
        self,
        reports_repo: ReportsRepository,
        sessions_repo: SessionsRepository,
        templates_repo: TemplatesRepository,
        user_repo: UserRepository,
        fast_llm: LLMService,
    ):
        self.reports_repo = reports_repo
        self.sessions_repo = sessions_repo
        self.templates_repo = templates_repo
        self.user_repo = user_repo
        self.fast_llm = fast_llm

    async def create(
        self,
        session_id: UUID,
        template_id: UUID,
        user_id: UUID,
        additional_context: str | None = None,
    ) -> Report:
        session = await self.sessions_repo.get_by_id(session_id, user_id)
        if not session:
            raise NotFoundException("Session not found")

        template = await self.templates_repo.get_by_id(template_id)
        if not template:
            raise NotFoundException("Template not found")

        transcripts_text = await self._build_transcripts_text(session_id)
        summary = session.clinical_summary or ""
        patient_info = self._build_patient_info(session)
        doctor_info = await self._build_doctor_info(user_id)

        content = await generate_report(
            llm=self.fast_llm,
            template_content=template.content,
            transcripts=transcripts_text,
            clinical_summary=summary,
            patient_info=patient_info,
            doctor_info=doctor_info,
            additional_context=additional_context or "",
        )

        report = Report(
            id=uuid4(),
            session_id=session_id,
            template_id=template_id,
            title=template.name,
            content=content,
        )
        return await self.reports_repo.create(report)

    async def get(self, report_id: UUID, user_id: UUID) -> Report:
        report = await self.reports_repo.get_by_id(report_id, user_id)
        if not report:
            raise NotFoundException("Report not found")
        return report

    async def delete(self, report_id: UUID, user_id: UUID) -> None:
        report = await self.get(report_id, user_id)
        await self.reports_repo.delete(report)

    async def list_by_session(self, session_id: UUID, user_id: UUID) -> list[Report]:
        session = await self.sessions_repo.get_by_id(session_id, user_id)
        if not session:
            raise NotFoundException("Session not found")
        return await self.reports_repo.list_by_session(session_id)

    # --- Private helpers ---

    async def _build_transcripts_text(self, session_id: UUID) -> str:
        texts, _ = await self.sessions_repo.get_transcripts_since(session_id, after_id=None)
        return " ".join(texts) if texts else "(no transcripts)"

    async def _build_doctor_info(self, user_id: UUID) -> str:
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            return "(doctor info unavailable)"

        lines = [f"Name: Dr. {user.first_name} {user.last_name or ''}".strip()]
        lines.append(f"Email: {user.email}")

        if user.speciality:
            lines.append(f"Speciality: {user.speciality}")

        if user.clinic:
            c = user.clinic
            parts = [c.name]
            if c.street:
                parts.append(c.street)
            if c.city:
                parts.append(c.city)
            if c.state:
                parts.append(c.state)
            if c.pincode:
                parts.append(c.pincode)
            lines.append(f"Clinic: {', '.join(parts)}")

        return "\n".join(lines)

    def _build_patient_info(self, session) -> str:
        if not session.patient:
            return "(no patient linked)"

        p = session.patient
        age = calculate_age(p.date_of_birth)
        parts = [f"Name: {p.full_name}"]
        if age:
            parts.append(f"Age: {age}")
        if p.gender:
            parts.append(f"Gender: {p.gender}")
        if p.blood_group:
            parts.append(f"Blood Group: {p.blood_group}")

        return "\n".join(parts)
