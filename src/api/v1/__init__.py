from fastapi import APIRouter

from src.api.v1.auth import router as auth_router
from src.api.v1.patients import router as patients_router
from src.api.v1.reports import router as reports_router
from src.api.v1.sessions import router as sessions_router
from src.api.v1.templates import router as templates_router
from src.api.v1.users import router as users_router
from src.api.v1.websockets import router as ws_router

api_router = APIRouter()
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(patients_router, prefix="", tags=["patients"])
api_router.include_router(reports_router, prefix="", tags=["reports"])
api_router.include_router(sessions_router, prefix="", tags=["sessions"])
api_router.include_router(templates_router, prefix="", tags=["templates"])
api_router.include_router(users_router, prefix="/users", tags=["users"])
api_router.include_router(ws_router, prefix="", tags=["websocket"])
