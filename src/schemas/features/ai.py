"""Schemas for LLM-powered features."""

from typing import List, Optional
from enum import Enum
from pydantic import BaseModel, Field

class BraveSearchResult(BaseModel):
    """Search result from Brave API."""
    title: str
    url: str
    description: str
    extra_snippets: List[str] = Field(default_factory=list)
    profile_name: Optional[str] = None
    profile_img: Optional[str] = None
    hostname: Optional[str] = None