from functools import lru_cache
from fastapi import Depends
from src.core.config import settings
from src.infrastructure.llm import LLMFactory, LLMService

@lru_cache()
def get_fast_llm_service() -> LLMService:
    """Dependency for the fast, lightweight model (e.g. Groq)."""
    model = LLMFactory.create(
        provider=settings.FAST_LLM_PROVIDER,
        model=settings.FAST_LLM_MODEL,
        temperature=settings.FAST_LLM_TEMP
    )

    fallback = None
    if settings.FAST_LLM_FALLBACK_PROVIDER and settings.FAST_LLM_FALLBACK_MODEL:
        fallback = LLMFactory.create(
            provider=settings.FAST_LLM_FALLBACK_PROVIDER,
            model=settings.FAST_LLM_FALLBACK_MODEL,
            temperature=settings.FAST_LLM_TEMP
        )

    return LLMService(model=model, fallback_model=fallback)

@lru_cache()
def get_tiny_llm_service() -> LLMService:
    """Dependency for the tiny, ultra-fast model (e.g. Llama 3.3 8B Instant)."""
    model = LLMFactory.create(
        provider=settings.TINY_LLM_PROVIDER,
        model=settings.TINY_LLM_MODEL,
        temperature=settings.TINY_LLM_TEMP
    )

    fallback = None
    if settings.TINY_LLM_FALLBACK_PROVIDER and settings.TINY_LLM_FALLBACK_MODEL:
        fallback = LLMFactory.create(
            provider=settings.TINY_LLM_FALLBACK_PROVIDER,
            model=settings.TINY_LLM_FALLBACK_MODEL,
            temperature=settings.TINY_LLM_TEMP
        )

    return LLMService(model=model, fallback_model=fallback)

@lru_cache()
def get_smart_llm_service() -> LLMService:
    """Dependency for the smarter, reasoning model (e.g. Gemini 3.0)."""
    model = LLMFactory.create(
        provider=settings.SMART_LLM_PROVIDER,
        model=settings.SMART_LLM_MODEL,
        temperature=settings.SMART_LLM_TEMP
    )
    
    fallback = None
    if settings.SMART_LLM_FALLBACK_PROVIDER and settings.SMART_LLM_FALLBACK_MODEL:
        fallback = LLMFactory.create(
            provider=settings.SMART_LLM_FALLBACK_PROVIDER,
            model=settings.SMART_LLM_FALLBACK_MODEL,
            temperature=settings.SMART_LLM_TEMP
        )
        
    return LLMService(model=model, fallback_model=fallback)