from datetime import date
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


# --- Reusable Sub-Schemas ---

class UserProfileData(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    dob: Optional[date] = None
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


# --- Response ---

class AuthResponse(BaseModel):
    status: str = "success"
    session_token: Optional[str] = None
