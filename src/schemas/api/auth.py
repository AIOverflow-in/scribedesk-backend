from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


# --- Reusable Sub-Schemas ---

class UserProfileData(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    gender: Optional[str] = Field(None, pattern="^(Male|Female|Other|Prefer not to say)$")
    speciality: Optional[str] = Field(None, max_length=100)


class ClinicData(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    street: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    pincode: Optional[str] = Field(None, max_length=20)
    country: str = Field(..., min_length=2, max_length=2, pattern="^[A-Z]{2}$")


# --- Request ---

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    profile: UserProfileData
    clinic: ClinicData


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class GoogleLoginRequest(BaseModel):
    idToken: str


class ConnectProviderRequest(BaseModel):
    provider: str = Field(..., pattern="^(google|apple|microsoft)$")
    token: str


class SetPasswordRequest(BaseModel):
    password: str = Field(..., min_length=8)
    confirm_password: str = Field(..., min_length=8)


class OnboardingRequest(BaseModel):
    profile: UserProfileData
    clinic: ClinicData


# --- Response ---

class AuthResponse(BaseModel):
    status: str = "success"
    session_token: Optional[str] = None
    onboarding_pending: bool = False


class ProviderResponse(BaseModel):
    id: UUID
    provider: str
    email: str
    is_primary: bool
    linked_at: datetime
    last_used_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ProvidersListResponse(BaseModel):
    status: str = "success"
    providers: list[ProviderResponse]
