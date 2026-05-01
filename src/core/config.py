from typing import List, Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Medical Copilot Extension API"
    API_V1_PREFIX: str = "/api/v1"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    PORT: int = 8000
    HOST: str = "0.0.0.0"

    BACKEND_CORS_ORIGINS: List[str] = ["*"]

    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "JSON"

    DATABASE_URL: str

    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: Optional[str] = None
    CELERY_RESULT_BACKEND: Optional[str] = None

    SESSION_EXPIRY_SECONDS: int = 86400

    GROQ_API_KEY: str
    GEMINI_API_KEY: Optional[str] = None

    FAST_LLM_PROVIDER: str = "groq"
    FAST_LLM_MODEL: str = "openai/gpt-oss-20b"
    FAST_LLM_TEMP: float = 0.2
    FAST_LLM_FALLBACK_PROVIDER: str = "google"
    FAST_LLM_FALLBACK_MODEL: str = "gemini-3-flash-preview"

    TINY_LLM_PROVIDER: str = "groq"
    TINY_LLM_MODEL: str = "llama-3.3-8b-instant"
    TINY_LLM_TEMP: float = 0.2
    TINY_LLM_FALLBACK_PROVIDER: str = "groq"
    TINY_LLM_FALLBACK_MODEL: str = "gemma2-9b-it"

    SMART_LLM_PROVIDER: str = "groq"
    SMART_LLM_MODEL: str = "openai/gpt-oss-120b"
    SMART_LLM_TEMP: float = 0.3
    SMART_LLM_FALLBACK_PROVIDER: str = "google"
    SMART_LLM_FALLBACK_MODEL: str = "gemini-3-flash-preview"

    DEEPGRAM_API_KEY: str
    DEEPGRAM_MODEL: str = "nova-3-medical"
    DEEPGRAM_CHUNK_SIZE: int = 5
    BRAVE_SEARCH_API_KEY: Optional[str] = None

    S3_ENDPOINT_URL: str
    S3_BUCKET_NAME: str
    S3_ACCESS_KEY_ID: str
    S3_SECRET_ACCESS_KEY: str
    S3_REGION: str = "us-east-1"

    STRIPE_SECRET_KEY: str
    STRIPE_WEBHOOK_SECRET: str
    STRIPE_PRO_PLAN_ID: str

    FREE_TRIAL_DAYS: int = 7
    FREE_SCRIBE_LIMIT_MINUTES: int = 400
    TRIAL_SCRIBE_LIMIT_MINUTES: int = 800
    PRO_SCRIBE_LIMIT_MINUTES: int = 6000

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    def model_post_init(self, __context):
        if not self.CELERY_BROKER_URL:
            self.CELERY_BROKER_URL = self.REDIS_URL
        if not self.CELERY_RESULT_BACKEND:
            self.CELERY_RESULT_BACKEND = self.REDIS_URL


settings = Settings()
