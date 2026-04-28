from fastapi import FastAPI

from src.api.health import router as health_router
from src.api.v1 import api_router
from src.core.config import settings
from src.core.lifecycle import lifespan

app = FastAPI(title=settings.PROJECT_NAME, version="1.0.0", lifespan=lifespan)

app.include_router(health_router)
app.include_router(api_router, prefix=settings.API_V1_PREFIX)
