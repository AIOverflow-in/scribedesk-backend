"""User profile routes — read profile, update profile, update clinic."""

from fastapi import APIRouter

from src.dependencies.auth import CurrentUserIdDep
from src.dependencies.services import UserServiceDep
from src.schemas.api.user import (
    ClinicUpdateRequest,
    ProfileUpdateRequest,
    UserProfileResponse,
)

router = APIRouter()


@router.get("/me", response_model=UserProfileResponse)
async def get_profile(
    user_id: CurrentUserIdDep,
    service: UserServiceDep,
):
    """Get full user profile with clinic details."""
    user = await service.get_profile(user_id=user_id)

    return UserProfileResponse.model_validate(user)


@router.patch("/me", response_model=UserProfileResponse)
async def update_profile(
    request: ProfileUpdateRequest,
    user_id: CurrentUserIdDep,
    service: UserServiceDep,
):
    """Update personal profile details."""
    user = await service.update_profile(
        user_id=user_id,
        data=request.model_dump(exclude_unset=True),
    )

    return UserProfileResponse.model_validate(user)


@router.patch("/me/clinic", response_model=UserProfileResponse)
async def update_clinic(
    request: ClinicUpdateRequest,
    user_id: CurrentUserIdDep,
    service: UserServiceDep,
):
    """Update clinic details."""
    user = await service.update_clinic(
        user_id=user_id,
        data=request.model_dump(exclude_unset=True),
    )

    return UserProfileResponse.model_validate(user)
