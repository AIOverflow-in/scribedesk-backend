from contextlib import asynccontextmanager
from fastapi import FastAPI
from src.core.config import settings
from src.core.lifecycle import lifespan

app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION, lifespan=lifespan)
