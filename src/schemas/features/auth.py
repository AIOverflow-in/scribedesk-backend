"""Auth-related schemas for internal use (not API-facing)."""

from typing import Optional

from pydantic import BaseModel


class GoogleUserInfo(BaseModel):
    sub: str = ""
    email: str = ""
    given_name: str = ""
    family_name: str = ""
    name: Optional[str] = None
    picture: Optional[str] = None
    email_verified: bool = False
