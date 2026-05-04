from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from src.api.health import router as health_router
from src.api.v1 import api_router
from src.core.config import settings
from src.core.exceptions import setup_exception_handlers
from src.core.lifecycle import lifespan

from langsmith.middleware import TracingMiddleware
from src.core.middleware import RequestContextMiddleware

load_dotenv()

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Clinical Tool",
    version="1.0.0",
    lifespan=lifespan,
)

setup_exception_handlers(app)

app.add_middleware(TracingMiddleware)
app.add_middleware(RequestContextMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(api_router, prefix=settings.API_V1_PREFIX)
