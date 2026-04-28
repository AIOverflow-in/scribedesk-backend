from langchain_core.language_models import BaseChatModel
from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI
from src.core.config import settings

class LLMFactory:
    """Factory for creating raw LangChain Chat Model instances."""

    @staticmethod
    def create(
        provider: str,
        model: str,
        temperature: float,
        reasoning_effort: str = "low"
    ) -> BaseChatModel:
        """Create a raw LLM instance based on provider and model."""
        if provider == "groq":
            return LLMFactory._create_groq(model, temperature, reasoning_effort)
        elif provider == "google":
            return LLMFactory._create_google(model, temperature, reasoning_effort)

        raise ValueError(f"Unsupported LLM provider: {provider}")

    @staticmethod
    def _create_groq(model: str, temperature: float, effort: str) -> ChatGroq:
        """Create Groq chat model. Supports reasoning_effort for R1 models."""
        if not settings.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY is missing")

        return ChatGroq(
            model=model,
            temperature=temperature,
            api_key=settings.GROQ_API_KEY,
            reasoning_effort=effort
        )

    @staticmethod
    def _create_google(model: str, temperature: float, effort: str = "low") -> ChatGoogleGenerativeAI:
        if not settings.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is missing")

        return ChatGoogleGenerativeAI(
            model=model,
            temperature=temperature,
            google_api_key=settings.GEMINI_API_KEY,
        )