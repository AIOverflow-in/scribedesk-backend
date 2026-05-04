"""Authentication routes — register, login, logout, Google OAuth, provider management."""

from uuid import UUID

from fastapi import APIRouter, Request, Response

from src.api.v1.helpers import handle_auth_result
from src.core.exceptions import UnauthorizedException
from src.dependencies.auth import CurrentUserIdDep
from src.dependencies.services import AuthServiceDep
from src.schemas.api.auth import (
    AuthResponse,
    ConnectProviderRequest,
    GoogleLoginRequest,
    LoginRequest,
    OnboardingRequest,
    ProviderResponse,
    ProvidersListResponse,
    RegisterRequest,
    SetPasswordRequest,
)
from src.schemas.api.common import StatusResponse

router = APIRouter()


# --- Email / Password Auth ---


@router.post("/register", response_model=AuthResponse)
async def register(
    request: RegisterRequest,
    response: Response,
    auth_service: AuthServiceDep,
):
    """Create a new account with email, password, profile, and clinic."""
    result = await auth_service.register(data=request.model_dump())

    return handle_auth_result(response, result.token)


@router.post("/login", response_model=AuthResponse)
async def login(
    request: LoginRequest,
    response: Response,
    auth_service: AuthServiceDep,
):
    """Authenticate with email and password."""
    result = await auth_service.login(
        email=request.email,
        password=request.password,
    )

    return handle_auth_result(response, result.token)


# --- Google OAuth ---


@router.post("/google", response_model=AuthResponse)
async def google_login(
    request: GoogleLoginRequest,
    response: Response,
    auth_service: AuthServiceDep,
):
    """Sign in or sign up with Google."""
    result = await auth_service.google_login(id_token_str=request.idToken)

    return handle_auth_result(
        response,
        result.token,
        onboarding_pending=result.onboarding_pending,
    )


@router.post("/providers/connect", response_model=StatusResponse)
async def connect_provider(
    request: ConnectProviderRequest,
    auth_service: AuthServiceDep,
    current_user_id: CurrentUserIdDep,
):
    """Link an OAuth provider (google, apple, microsoft) to the current account."""
    await auth_service.link_provider(
        user_id=UUID(current_user_id),
        provider=request.provider,
        token=request.token,
    )

    return StatusResponse(status="success")


@router.get("/providers", response_model=ProvidersListResponse)
async def list_providers(
    auth_service: AuthServiceDep,
    current_user_id: CurrentUserIdDep,
):
    """List all OAuth providers linked to the current account."""
    providers = await auth_service.get_providers(user_id=UUID(current_user_id))

    return ProvidersListResponse(
        providers=[ProviderResponse.model_validate(p) for p in providers],
    )


@router.delete("/providers/{provider_id}", response_model=StatusResponse)
async def disconnect_provider(
    provider_id: UUID,
    auth_service: AuthServiceDep,
    current_user_id: CurrentUserIdDep,
):
    """Disconnect an OAuth provider."""
    await auth_service.disconnect_provider(
        user_id=UUID(current_user_id),
        provider_id=provider_id,
    )

    return StatusResponse(status="success")


# --- Onboarding ---


@router.post("/onboarding", response_model=AuthResponse)
async def complete_onboarding(
    request: OnboardingRequest,
    auth_service: AuthServiceDep,
    current_user_id: CurrentUserIdDep,
):
    """Complete onboarding after Google signup — save profile and create clinic."""
    await auth_service.onboarding(
        user_id=UUID(current_user_id),
        profile=request.profile.model_dump(),
        clinic=request.clinic.model_dump(),
    )

    return AuthResponse(onboarding_pending=False)


# --- Password Management ---


@router.post("/set-password", response_model=StatusResponse)
async def set_password(
    request: SetPasswordRequest,
    auth_service: AuthServiceDep,
    current_user_id: CurrentUserIdDep,
):
    """Set or change the account password."""
    if request.password != request.confirm_password:
        raise UnauthorizedException("Passwords do not match")

    await auth_service.set_password(
        user_id=UUID(current_user_id),
        password=request.password,
    )

    return StatusResponse(status="success")


# --- Session ---


@router.post("/logout", response_model=StatusResponse)
async def logout(
    request: Request,
    response: Response,
    auth_service: AuthServiceDep,
):
    """Revoke the current session."""
    token = request.cookies.get("session")

    if token:
        await auth_service.logout(token)

    response.delete_cookie("session")
    return StatusResponse(status="success")
