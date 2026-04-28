"""Template CRUD routes — system + user templates."""

from uuid import UUID

from fastapi import APIRouter

from src.dependencies.auth import CurrentUserIdDep
from src.dependencies.services import TemplateServiceDep
from src.schemas.api.common import StatusResponse
from src.schemas.api.templates import (
    CreateTemplateRequest,
    TemplateResponse,
    UpdateTemplateRequest,
)

router = APIRouter()


@router.get("/templates", response_model=list[TemplateResponse])
async def list_templates(
    user_id: CurrentUserIdDep,
    service: TemplateServiceDep,
):
    """List system templates and the current user's custom templates."""
    templates = await service.list(user_id=user_id)

    return [TemplateResponse.model_validate(t) for t in templates]


@router.post("/templates", response_model=TemplateResponse, status_code=201)
async def create_template(
    request: CreateTemplateRequest,
    user_id: CurrentUserIdDep,
    service: TemplateServiceDep,
):
    """Create a custom template."""
    template = await service.create(
        user_id=user_id,
        data=request.model_dump(),
    )

    return TemplateResponse.model_validate(template)


@router.get("/templates/{template_id}", response_model=TemplateResponse)
async def get_template(
    template_id: UUID,
    service: TemplateServiceDep,
):
    """Get a single template by ID (system or user)."""
    template = await service.get(template_id=template_id)

    return TemplateResponse.model_validate(template)


@router.patch("/templates/{template_id}", response_model=TemplateResponse)
async def update_template(
    template_id: UUID,
    request: UpdateTemplateRequest,
    user_id: CurrentUserIdDep,
    service: TemplateServiceDep,
):
    """Update your own template (not system templates)."""
    template = await service.update(
        template_id=template_id,
        user_id=user_id,
        data=request.model_dump(exclude_unset=True),
    )

    return TemplateResponse.model_validate(template)


@router.delete("/templates/{template_id}", response_model=StatusResponse)
async def delete_template(
    template_id: UUID,
    user_id: CurrentUserIdDep,
    service: TemplateServiceDep,
):
    """Delete your own template (not system templates)."""
    await service.delete(template_id=template_id, user_id=user_id)

    return StatusResponse(status="success")
