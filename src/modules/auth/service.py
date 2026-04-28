from uuid import uuid4

from src.core.exceptions import ConflictException, UnauthorizedException
from src.core.security import generate_session_token, hash_password, verify_password_async
from src.infrastructure.persistence.postgres.models import Clinic, User
from src.infrastructure.persistence.postgres.repos.auth_repo import AuthRepository
from src.infrastructure.persistence.redis.sessions import SessionManager


class AuthService:
    def __init__(self, auth_repo: AuthRepository, session_manager: SessionManager):
        self.auth_repo = auth_repo
        self.session_manager = session_manager

    async def register(self, data: dict) -> str:
        """Register a new user with profile and clinic data."""
        if await self.auth_repo.get_by_email(data["email"]):
            raise ConflictException("An account with this email already exists")

        user_id = uuid4()
        profile = data["profile"]
        clinic_data = data["clinic"]

        user = User(
            id=user_id,
            email=data["email"],
            password_hash=hash_password(data["password"]),
            first_name=profile["first_name"],
            last_name=profile.get("last_name"),
            dob=profile.get("dob"),
            gender=profile.get("gender"),
            speciality=profile.get("speciality"),
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

        await self.auth_repo.create_user(user, clinic)

        token = generate_session_token()
        await self.session_manager.create_session(token, user_id, "doctor")
        return token

    async def login(self, email: str, password: str) -> str:
        """Authenticate with email and password."""
        user = await self.auth_repo.get_by_email(email)
        if not user or not user.password_hash:
            raise UnauthorizedException("Invalid email or password")

        if not await verify_password_async(password, user.password_hash):
            raise UnauthorizedException("Invalid email or password")

        token = generate_session_token()
        await self.session_manager.create_session(token, user.id, "doctor")
        return token

    async def logout(self, session_token: str) -> None:
        """Revoke a session."""
        await self.session_manager.delete_session(session_token)
