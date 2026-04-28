from typing import Generic, List, TypeVar

from pydantic import BaseModel

DataT = TypeVar("DataT")


class StatusResponse(BaseModel):
    status: str


class PaginatedResponse(BaseModel, Generic[DataT]):
    items: List[DataT]
    total: int
    page: int
    page_size: int
