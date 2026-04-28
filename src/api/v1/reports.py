"""Report generation routes."""

from uuid import UUID

from fastapi import APIRouter

from src.dependencies.auth import CurrentUserIdDep
from src.dependencies.services import ReportServiceDep
from src.schemas.api.reports import CreateReportRequest, ReportResponse

router = APIRouter()


@router.post("/reports", response_model=ReportResponse, status_code=201)
async def create_report(
    request: CreateReportRequest,
    user_id: CurrentUserIdDep,
    service: ReportServiceDep,
):
    """Generate a report from transcripts using a template."""
    report = await service.create(
        session_id=request.session_id,
        template_id=request.template_id,
        user_id=user_id,
        additional_context=request.additional_context,
    )

    return ReportResponse.model_validate(report)


@router.get("/reports/{report_id}", response_model=ReportResponse)
async def get_report(
    report_id: UUID,
    user_id: CurrentUserIdDep,
    service: ReportServiceDep,
):
    """Get a single report by ID."""
    report = await service.get(report_id=report_id, user_id=user_id)

    return ReportResponse.model_validate(report)
