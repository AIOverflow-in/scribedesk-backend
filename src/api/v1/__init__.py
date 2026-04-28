from fastapi import APIRouter

from src.api.v1.auth import router as auth_router
from src.api.v1.patients import router as patients_router
from src.api.v1.templates import router as templates_router

api_router = APIRouter()
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(patients_router, prefix="", tags=["patients"])
api_router.include_router(templates_router, prefix="", tags=["templates"])
