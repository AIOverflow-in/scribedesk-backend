from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


# --- Response ---

class ClinicInfo(BaseModel):
    name: str
    street: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    country: Optional[str] = None
    logo_url: Optional[str] = None


class UserProfileResponse(BaseModel):
    id: UUID
    email: str
    first_name: str
    last_name: Optional[str] = None
    dob: Optional[date] = None
    gender: Optional[str] = None
    speciality: Optional[str] = None
    signature_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    clinic: Optional[ClinicInfo] = None

    class Config:
        from_attributes = True


# --- Request ---

class ProfileUpdateRequest(BaseModel):
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    dob: Optional[date] = None
    gender: Optional[str] = Field(None, pattern="^(Male|Female|Other|Prefer not to say)$")
    speciality: Optional[str] = Field(None, max_length=100)


class ClinicUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    street: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    pincode: Optional[str] = Field(None, max_length=20)
    country: Optional[str] = Field(None, min_length=2, max_length=2, pattern="^[A-Z]{2}$")
