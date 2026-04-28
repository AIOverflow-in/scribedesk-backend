from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr


class UserDb(BaseModel):
    id: UUID
    email: EmailStr
    first_name: str
    last_name: Optional[str] = None
    signature_url: Optional[str] = None
    dob: Optional[date] = None
    gender: Optional[str] = None
    speciality: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ClinicDb(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    street: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    country: Optional[str] = None
    address: Optional[str] = None
    logo_url: Optional[str] = None

    class Config:
        from_attributes = True
