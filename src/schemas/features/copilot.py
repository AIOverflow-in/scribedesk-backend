from datetime import date
from typing import Optional

from pydantic import BaseModel


class ChatTitleResponse(BaseModel):
    title: str


class PatientInfo(BaseModel):
    first_name: str
    last_name: Optional[str] = None
    date_of_birth: Optional[str] = None
    gender: Optional[str] = None
    blood_group: Optional[str] = None

    class Config:
        from_attributes = True


class SessionInfo(BaseModel):
    title: str
    status: str
    clinical_summary: Optional[str] = None
