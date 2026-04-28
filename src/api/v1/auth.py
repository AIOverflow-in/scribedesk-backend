"""Authentication routes — register, login, logout."""

from fastapi import APIRouter, Request, Response

from src.api.v1.helpers import handle_auth_result
from src.core.exceptions import UnauthorizedException
from src.dependencies.services import AuthServiceDep
from src.schemas.api.auth import AuthResponse, LoginRequest, RegisterRequest
from src.schemas.api.common import StatusResponse

router = APIRouter()


# --- Routes ---

@router.post("/register", response_model=AuthResponse)
async def register(
    request: RegisterRequest,
    response: Response,
    auth_service: AuthServiceDep,
):
    """Create a new account with user profile and clinic details."""
    token = await auth_service.register(data=request.model_dump())

    return handle_auth_result(response, token)


@router.post("/login", response_model=AuthResponse)
async def login(
    request: LoginRequest,
    response: Response,
    auth_service: AuthServiceDep,
):
    """Authenticate with email and password."""
    token = await auth_service.login(
        email=request.email,
        password=request.password,
    )

    if not token:
        raise UnauthorizedException("Invalid email or password")

    return handle_auth_result(response, token)


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
