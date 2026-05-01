from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


# --- Request ---

class CreatePatientRequest(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    identifier: Optional[str] = Field(None, max_length=100)
    date_of_birth: Optional[date] = None
    gender: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=255)
    blood_group: Optional[str] = Field(None, max_length=10)


class UpdatePatientRequest(BaseModel):
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    identifier: Optional[str] = Field(None, max_length=100)
    date_of_birth: Optional[date] = None
    gender: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=255)
    blood_group: Optional[str] = Field(None, max_length=10)


# --- Response ---

class PatientResponse(BaseModel):
    id: UUID
    first_name: str
    last_name: Optional[str] = None
    identifier: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    email: Optional[str] = None
    blood_group: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
