"""Authentication service — register, login, Google OAuth, provider management."""

from dataclasses import dataclass
from uuid import UUID, uuid4

from src.core.exceptions import (
    BadRequestException,
    ConflictException,
    NotFoundException,
    UnauthorizedException,
)
from src.core.security import generate_session_token, hash_password, verify_password_async
from src.infrastructure.external.google_oauth import verify_google_token
from src.infrastructure.persistence.postgres.models import Clinic, User, UserAuthProvider
from src.infrastructure.persistence.postgres.repos.auth_repo import AuthRepository
from src.infrastructure.persistence.redis.sessions import SessionManager


@dataclass
class AuthResult:
    token: str
    onboarding_pending: bool = False


class AuthService:
    def __init__(self, auth_repo: AuthRepository, session_manager: SessionManager):
        self.auth_repo = auth_repo
        self.session_manager = session_manager

    # --- Email / Password Auth ---

    async def register(self, data: dict) -> AuthResult:
        """Register a new user with email, password, profile, and clinic."""
        if await self.auth_repo.get_by_email(data["email"]):
            raise ConflictException("An account with this email already exists")

        user_id = uuid4()
        profile = data["profile"]
        clinic_data = data["clinic"]
        password_hash = hash_password(data["password"])

        user = User(
            id=user_id,
            email=data["email"],
            first_name=profile["first_name"],
            last_name=profile.get("last_name"),
            gender=profile.get("gender"),
            speciality=profile.get("speciality"),
            is_onboarded=True,
        )
        clinic = Clinic(
            user_id=user_id,
            name=clinic_data["name"],
            street=clinic_data.get("street"),
            city=clinic_data.get("city"),
            state=clinic_data.get("state"),
            pincode=clinic_data.get("pincode"),
            country=clinic_data["country"],
        )
        provider = UserAuthProvider(
            id=uuid4(),
            user_id=user_id,
            provider="email",
            email=data["email"],
            password_hash=password_hash,
            is_primary=True,
        )

        await self.auth_repo.create_user(user)
        await self.auth_repo.create_clinic(clinic)
        await self.auth_repo.create_provider(provider)

        token = generate_session_token()
        await self.session_manager.create_session(token, user_id, "doctor")
        return AuthResult(token=token)

    async def login(self, email: str, password: str) -> AuthResult:
        """Authenticate with email and password."""
        user = await self.auth_repo.get_by_email(email)
        if not user:
            raise UnauthorizedException("Invalid email or password")

        provider = await self.auth_repo.get_email_provider(email)
        if not provider or not provider.password_hash:
            raise UnauthorizedException("Invalid email or password")

        if not await verify_password_async(password, provider.password_hash):
            raise UnauthorizedException("Invalid email or password")

        await self.auth_repo.update_provider_last_used(provider.id)

        token = generate_session_token()
        await self.session_manager.create_session(token, user.id, "doctor")
        return AuthResult(token=token)

    # --- Google OAuth ---

    async def google_login(self, id_token_str: str) -> AuthResult:
        """Sign in or sign up with Google."""
        info = await verify_google_token(id_token_str)
        google_id = info.sub
        email = info.email

        existing = await self.auth_repo.get_provider("google", google_id)
        if existing:
            user = await self.auth_repo.get_user_by_id(existing.user_id)
            await self.auth_repo.update_provider_last_used(existing.id)
            token = generate_session_token()
            await self.session_manager.create_session(token, existing.user_id, "doctor")
            return AuthResult(token=token, onboarding_pending=not user.is_onboarded)

        email_provider = await self.auth_repo.get_email_provider(email)
        if email_provider:
            raise ConflictException(
                "An account with this email already uses email/password login. "
                "Sign in with your password, then link Google in your account settings."
            )

        user_id = uuid4()
        user = User(
            id=user_id,
            email=email,
            first_name=info.given_name,
            last_name=info.family_name,
        )
        provider = UserAuthProvider(
            id=uuid4(),
            user_id=user_id,
            provider="google",
            provider_user_id=google_id,
            email=email,
            is_primary=True,
        )

        await self.auth_repo.create_user(user)
        await self.auth_repo.create_provider(provider)

        token = generate_session_token()
        await self.session_manager.create_session(token, user_id, "doctor")
        return AuthResult(token=token, onboarding_pending=True)

    async def link_provider(self, user_id: UUID, provider: str, token: str) -> None:
        """Link an OAuth provider (google, apple, microsoft) to the current account."""
        if provider == "google":
            info = await verify_google_token(token)
        else:
            raise BadRequestException(f"Unsupported provider: {provider}")

        google_id = info.sub
        email = info.email

        existing = await self.auth_repo.get_provider(provider, google_id)
        if existing:
            raise ConflictException(f"{provider.title()} account is already linked")

        provider_row = UserAuthProvider(
            id=uuid4(),
            user_id=user_id,
            provider=provider,
            provider_user_id=google_id,
            email=email,
            is_primary=False,
        )
        await self.auth_repo.create_provider(provider_row)

    # --- Provider Management ---

    async def get_providers(self, user_id: UUID) -> list[UserAuthProvider]:
        """List all auth providers linked to the user's account."""
        return list(await self.auth_repo.get_user_providers(user_id))

    async def disconnect_provider(self, user_id: UUID, provider_id: UUID) -> None:
        """Disconnect an OAuth provider (e.g. Google)."""
        provider = await self.auth_repo.get_provider_by_id(provider_id)
        if not provider or provider.user_id != user_id:
            raise NotFoundException("Provider not found")

        if provider.provider == "email":
            raise BadRequestException("Cannot disconnect email/password login")

        count = len(await self.auth_repo.get_user_providers(user_id))
        if count <= 1:
            raise BadRequestException(
                "Cannot disconnect your only login method. Set a password first."
            )

        await self.auth_repo.delete_provider(provider_id)

    async def set_password(self, user_id: UUID, password: str) -> None:
        """Set or change password for a user."""
        user = await self.auth_repo.get_user_by_id(user_id)
        if not user:
            raise UnauthorizedException("User not found")

        password_hash = hash_password(password)

        existing = await self.auth_repo.get_email_provider(user.email)
        if existing:
            await self.auth_repo.update_provider_password(existing.id, password_hash)
            return

        provider = UserAuthProvider(
            id=uuid4(),
            user_id=user_id,
            provider="email",
            email=user.email,
            password_hash=password_hash,
            is_primary=False,
        )
        await self.auth_repo.create_provider(provider)

    # --- Onboarding ---

    async def onboarding(self, user_id: UUID, profile: dict, clinic: dict) -> None:
        """Complete onboarding after Google signup — save profile and create clinic."""
        user = await self.auth_repo.get_user_by_id(user_id)
        if not user:
            raise UnauthorizedException("User not found")

        await self.auth_repo.update_user(user, {**profile, "is_onboarded": True})
        await self.auth_repo.create_clinic(
            Clinic(
                user_id=user_id,
                name=clinic["name"],
                street=clinic.get("street"),
                city=clinic.get("city"),
                state=clinic.get("state"),
                pincode=clinic.get("pincode"),
                country=clinic["country"],
            )
        )

    # --- Session ---

    async def logout(self, session_token: str) -> None:
        """Revoke a session."""
        await self.session_manager.delete_session(session_token)
