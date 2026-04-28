This file is a merged representation of a subset of the codebase, containing specifically included files, combined into a single document by Repomix.

# File Summary

## Purpose
This file contains a packed representation of a subset of the repository's contents that is considered the most important context.
It is designed to be easily consumable by AI systems for analysis, code review,
or other automated processes.

## File Format
The content is organized as follows:
1. This summary section
2. Repository information
3. Directory structure
4. Repository files (if enabled)
5. Multiple file entries, each consisting of:
  a. A header with the file path (## File: path/to/file)
  b. The full contents of the file in a code block

## Usage Guidelines
- This file should be treated as read-only. Any changes should be made to the
  original repository files, not this packed version.
- When processing this file, use the file path to distinguish
  between different files in the repository.
- Be aware that this file may contain sensitive information. Handle it with
  the same level of security as you would the original repository.

## Notes
- Some files may have been excluded based on .gitignore rules and Repomix's configuration
- Binary files are not included in this packed representation. Please refer to the Repository Structure section for a complete list of file paths, including binary files
- Only files matching these patterns are included: src/core/**/*, src/dependencies/**/*, src/infrastructure/**/*
- Files matching patterns in .gitignore are excluded
- Files matching default ignore patterns are excluded
- Files are sorted by Git change count (files with more changes are at the bottom)

# Directory Structure
```
src/core/config.py
src/core/context.py
src/core/exceptions.py
src/core/lifecycle.py
src/core/logging.py
src/core/middleware.py
src/core/security.py
src/dependencies/ai.py
src/dependencies/auth.py
src/dependencies/db.py
src/dependencies/infra.py
src/dependencies/repositories.py
src/dependencies/services.py
src/infrastructure/__init__.py
src/infrastructure/external/brave.py
src/infrastructure/external/brevo.py
src/infrastructure/external/deepgram.py
src/infrastructure/external/google_files.py
src/infrastructure/external/google_oauth.py
src/infrastructure/external/razorpay.py
src/infrastructure/external/stripe.py
src/infrastructure/llm/__init__.py
src/infrastructure/llm/factory.py
src/infrastructure/llm/service.py
src/infrastructure/persistence/__init__.py
src/infrastructure/persistence/postgres/__init__.py
src/infrastructure/persistence/postgres/alembic/env.py
src/infrastructure/persistence/postgres/alembic/script.py.mako
src/infrastructure/persistence/postgres/alembic/versions/2026_03_26_1752-c5c4151db92f_initial_tables.py
src/infrastructure/persistence/postgres/alembic/versions/2026_04_02_0935-0dd637d7ae14_add_scribe_usage_table.py
src/infrastructure/persistence/postgres/alembic/versions/2026_04_02_2033-a2b2a94e2336_make_speaker_id_optional_in_transcript_.py
src/infrastructure/persistence/postgres/alembic/versions/2026_04_06_1417-ed54f2e84840_add_reports_and_templates_tables.py
src/infrastructure/persistence/postgres/alembic/versions/2026_04_06_1947-c19ecbad6d79_add_set_null_to_consultation_last_.py
src/infrastructure/persistence/postgres/alembic/versions/2026_04_10_1040-8d5b036266d4_add_attachments_table_for_file_uploads.py
src/infrastructure/persistence/postgres/alembic/versions/2026_04_10_1550-23d3d241c2d5_update_consultations_patient_id_foreign_.py
src/infrastructure/persistence/postgres/alembic/versions/2026_04_10_2100-a27175f0cd70_add_invoices_table.py
src/infrastructure/persistence/postgres/alembic/versions/2026_04_13_1451-d87af33a1d2f_update_invoices_table_for_modular_.py
src/infrastructure/persistence/postgres/alembic/versions/2026_04_17_1554-ad6d01f4d6e9_add_notification_tables.py
src/infrastructure/persistence/postgres/alembic/versions/2026_04_21_2049-8bb89d1019a9_add_consultation_insights.py
src/infrastructure/persistence/postgres/database.py
src/infrastructure/persistence/postgres/models.py
src/infrastructure/persistence/postgres/repos/ai_conversations_repo.py
src/infrastructure/persistence/postgres/repos/attachments_repo.py
src/infrastructure/persistence/postgres/repos/auth_repo.py
src/infrastructure/persistence/postgres/repos/billing_repo.py
src/infrastructure/persistence/postgres/repos/consultation_insights_repo.py
src/infrastructure/persistence/postgres/repos/consultations_repo.py
src/infrastructure/persistence/postgres/repos/email_logs_repo.py
src/infrastructure/persistence/postgres/repos/invoices_repo.py
src/infrastructure/persistence/postgres/repos/password_resets_repo.py
src/infrastructure/persistence/postgres/repos/patients_repo.py
src/infrastructure/persistence/postgres/repos/reports_repo.py
src/infrastructure/persistence/postgres/repos/scribe_usage_logs_repo.py
src/infrastructure/persistence/postgres/repos/templates_repo.py
src/infrastructure/persistence/postgres/repos/user_repo.py
src/infrastructure/persistence/redis/__init__.py
src/infrastructure/persistence/redis/client.py
src/infrastructure/persistence/redis/pubsub.py
src/infrastructure/persistence/redis/sessions.py
src/infrastructure/persistence/s3/client.py
```

# Files

## File: src/core/context.py
```python
from contextvars import ContextVar
from typing import Optional

# Context Variables
request_id_ctx: ContextVar[str] = ContextVar("request_id", default="")
user_id_ctx: ContextVar[Optional[str]] = ContextVar("user_id", default=None)


def get_trace_id() -> str:
    """Get the current request's Trace ID."""
    return request_id_ctx.get("system")


def get_user_id() -> Optional[str]:
    """Get the current authenticated User ID (if set)."""
    return user_id_ctx.get()


def set_trace_id(trace_id: str) -> None:
    """Set the trace ID for the current context."""
    request_id_ctx.set(trace_id)


def set_user_id(user_id: Optional[str]) -> None:
    """Set the user ID for the current context."""
    user_id_ctx.set(user_id)
```

## File: src/core/lifecycle.py
```python
from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.core.config import settings
from src.core.logging import get_logger
from src.infrastructure.persistence.postgres.database import check_db_connection, close_db_connections
from src.infrastructure.persistence.redis.client import init_redis, close_redis

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application Lifecycle Manager.

    Handles startup initialization and shutdown cleanup for critical infrastructure.
    """

    # Startup
    logger.info(f"{settings.PROJECT_NAME} starting up...")
    logger.info(f"Environment: {settings.ENVIRONMENT} | Debug: {settings.DEBUG}")

    # Initialize Redis (Critical: Sessions, Celery, Caching)
    try:
        await init_redis()
    except Exception as e:
        logger.critical(f"FATAL: Redis initialization failed: {e}")

    # Check Database Connection (Critical: Data Persistence)
    try:
        if await check_db_connection():
            logger.info("Database connection established")
        else:
            logger.critical("FATAL: Database connection failed. The application cannot persist data.")
    except Exception as e:
        logger.critical(f"FATAL: Database connection check failed: {e}")

    # Note: External services (Stripe, Deepgram, etc.) are initialized lazily
    # on first use to avoid blocking startup if they're temporarily unavailable.

    logger.info("Startup complete. API server ready.")

    yield

    # Shutdown
    logger.info("Shutting down...")

    # Close database connections
    try:
        await close_db_connections()
    except Exception as e:
        logger.error(f"Error closing database connections: {e}")

    # Close Redis connection
    try:
        await close_redis()
    except Exception as e:
        logger.error(f"Error closing Redis connection: {e}")

    logger.info(f"{settings.PROJECT_NAME} shutdown complete")
```

## File: src/infrastructure/external/brevo.py
```python
from typing import Optional

from brevo import AsyncBrevo
from brevo.transactional_emails import (
    SendTransacEmailRequestSender,
    SendTransacEmailRequestToItem,
)

from src.core.config import settings
from src.core.logging import get_logger

logger = get_logger(__name__)


class BrevoClient:
    """
    Async wrapper for Brevo (formerly SendinBlue) email API.
    Handles transactional emails with retries and error handling.
    """

    def __init__(self):
        self.client = AsyncBrevo(api_key=settings.BREVO_API_KEY)
        self.from_email = settings.EMAIL_FROM_ADDRESS
        self.from_name = settings.EMAIL_FROM_NAME

    async def send_email(
        self,
        to_email: str,
        to_name: Optional[str],
        subject: str,
        html_content: str,
        reply_to: Optional[str] = None,
    ) -> str:
        """
        Send a transactional email via Brevo.

        Args:
            to_email: Recipient email address
            to_name: Recipient name (optional)
            subject: Email subject line
            html_content: HTML email body
            reply_to: Reply-to address (optional)

        Returns:
            Brevo message ID for tracking

        Raises:
            Exception: If email sending fails
        """
        try:
            sender = SendTransacEmailRequestSender(
                name=self.from_name,
                email=self.from_email,
            )

            to = [SendTransacEmailRequestToItem(email=to_email, name=to_name or to_email)]

            result = await self.client.transactional_emails.send_transac_email(
                subject=subject,
                html_content=html_content,
                sender=sender,
                to=to,
                reply_to=reply_to,
                request_options={
                    "timeout_in_seconds": 10,
                    "max_retries": 2,
                },
            )

            logger.info(f"Email sent successfully to {to_email}. Message ID: {result.message_id}")
            return result.message_id

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            raise
```

## File: src/infrastructure/external/google_files.py
```python
"""Google Files API client for uploading files for Gemini consumption."""

import os
import asyncio
import tempfile
from typing import Optional
from google import genai

from src.core.config import settings
from src.core.logging import get_logger

logger = get_logger(__name__)


class GoogleFilesClient:
    """
    Client for Google Files API (for Gemini file uploads).
    Handles uploading files and retrieving URIs for Gemini LLM consumption.
    """

    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY

        if not self.api_key:
            logger.warning("GEMINI_API_KEY is missing. Google Files upload will fail.")
        else:
            # Initialize the new SDK client
            self.client = genai.Client(api_key=self.api_key)

    async def upload_file(
        self,
        file_bytes: bytes,
        file_name: str,
    ) -> Optional[str]:
        """
        Upload a file to Google Files API for Gemini consumption.

        Args:
            file_bytes: File content as bytes
            file_name: Original file name

        Returns:
            File URI that can be passed to Gemini, or None if upload fails
        """
        if not self.api_key:
            logger.error("Cannot upload to Google Files: GEMINI_API_KEY is missing")
            return None

        # Write bytes to a temporary file.
        _, ext = os.path.splitext(file_name)

        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as temp_file:
            temp_file.write(file_bytes)
            temp_path = temp_file.name

        try:
            # Use asyncio.to_thread because the SDK's upload method is synchronous
            uploaded_file = await asyncio.to_thread(
                self.client.files.upload,
                file=temp_path
            )

            logger.info(f"Successfully uploaded file '{file_name}' to Google Files: {uploaded_file.uri}")
            return uploaded_file.uri

        except Exception as e:
            logger.error(f"Unexpected error uploading to Google Files: {str(e)}")
            return None

        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
```

## File: src/infrastructure/external/google_oauth.py
```python
import httpx
from src.core.exceptions import UnauthorizedException

class GoogleClient:
    """Wrapper for Google Identity Services API."""
    
    def __init__(self):
        # Use the v3 userinfo endpoint instead of tokeninfo
        self.user_info_url = "https://www.googleapis.com/oauth2/v3/userinfo"

    async def verify_access_token(self, token: str) -> dict:
        """
        Verifies a Google Access Token and returns user identity.
        """
        async with httpx.AsyncClient() as client:
            # Pass the token securely as a Bearer header
            response = await client.get(
                self.user_info_url, 
                headers={"Authorization": f"Bearer {token}"}
            )
            
            if response.status_code != 200:
                raise UnauthorizedException("Invalid Google Token")
            
            data = response.json()
            
            return {
                "email": data.get("email"),
                "first_name": data.get("given_name", "Doctor"),
                "last_name": data.get("family_name", ""),
                "verified": data.get("email_verified") in [True, "true"]
            }
```

## File: src/infrastructure/llm/__init__.py
```python
from .factory import LLMFactory
from .service import LLMService

__all__ = ["LLMFactory", "LLMService"]
```

## File: src/infrastructure/llm/service.py
```python
from typing import Type, AsyncGenerator, List, Union, TypeVar, Optional
from pydantic import BaseModel
from langchain_core.messages import SystemMessage, HumanMessage, BaseMessage
from langchain_core.language_models import BaseChatModel
from langchain_core.runnables import Runnable
from src.utils.timer import measure_time
from src.core.logging import get_logger

logger = get_logger(__name__)

T = TypeVar("T", bound=BaseModel)

class LLMService:
    """
    Lean wrapper for LLM operations.
    Handles message preparation, timing, and resilient execution.
    """

    def __init__(
        self, 
        model: BaseChatModel,
        fallback_model: Optional[BaseChatModel] = None,
        max_retries: int = 3
    ):
        self.model = model
        self.fallback_model = fallback_model
        self.max_retries = max_retries

    def _prepare_messages(self, system: str, user: Union[str, List[BaseMessage]]) -> List[BaseMessage]:
        """Converts inputs into LangChain's required List[BaseMessage] format."""
        messages: List[BaseMessage] = [SystemMessage(content=system)]
        if isinstance(user, str):
            messages.append(HumanMessage(content=user))
        elif isinstance(user, list):
            messages.extend(user)
        return messages

    def _build_runnable(self, schema: Optional[Type[T]] = None) -> Runnable:
        """
        Internal helper to construct a resilient chain.
        Applies structured output, retries, and fallbacks in the correct order.
        """
        # 1. Apply schema if provided (must be done on raw model)
        primary = self.model.with_structured_output(schema) if schema else self.model
        
        # 2. Add native retry for transient errors
        runnable = primary.with_retry(stop_after_attempt=self.max_retries)

        # 3. Add fallback model if configured
        if self.fallback_model:
            fallback = self.fallback_model.with_structured_output(schema) if schema else self.fallback_model
            runnable = runnable.with_fallbacks([
                fallback.with_retry(stop_after_attempt=self.max_retries)
            ])
            
        return runnable

    @measure_time("LLM Generate Text")
    async def generate_text(self, system: str, user: Union[str, List[BaseMessage]]) -> str:
        """Standard text generation with resilience."""
        messages = self._prepare_messages(system, user)
        runnable = self._build_runnable()
        response = await runnable.ainvoke(messages)
        return response.content

    @measure_time("LLM Structured Output")
    async def generate_structured(
        self,
        system: str,
        user: Union[str, List[BaseMessage]],
        schema: Type[T]
    ) -> T:
        """Force Pydantic output with resilience."""
        messages = self._prepare_messages(system, user)
        runnable = self._build_runnable(schema=schema)
        return await runnable.ainvoke(messages)

    async def stream_text(
        self,
        system: str,
        user: Union[str, List[BaseMessage]]
    ) -> AsyncGenerator[str, None]:
        """
        Stream text chunks.
        Note: Retries are disabled for streams to avoid duplicate partial output.
        Fallbacks are still supported for connection failures.
        """
        messages = self._prepare_messages(system, user)
        
        runnable = self.model
        if self.fallback_model:
            runnable = runnable.with_fallbacks([self.fallback_model])
            
        async for chunk in runnable.astream(messages):
            if chunk.content:
                yield chunk.content
```

## File: src/infrastructure/persistence/postgres/alembic/versions/2026_03_26_1752-c5c4151db92f_initial_tables.py
```python
"""Initial tables

Revision ID: c5c4151db92f
Revises: None
Create Date: 2026-03-26 17:52:44.766867

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'c5c4151db92f'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create Root Tables (Users and Patients)
    op.create_table('users',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=True),
        sa.Column('auth_provider', sa.String(length=50), nullable=False),
        sa.Column('first_name', sa.String(length=100), nullable=False),
        sa.Column('last_name', sa.String(length=100), nullable=True),
        sa.Column('role', sa.String(length=50), nullable=False),
        sa.Column('provider_id', sa.String(length=100), nullable=True),
        sa.Column('gender', sa.String(length=20), nullable=True),
        sa.Column('date_of_birth', sa.Date(), nullable=True),
        sa.Column('registration_status', sa.String(length=50), nullable=False),
        sa.Column('has_seen_asset_prompt', sa.Boolean(), nullable=False),
        sa.Column('preferences', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.Column('signature_url', sa.String(length=500), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_deleted_at'), 'users', ['deleted_at'], unique=False)
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

    op.create_table('patients',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=False),
        sa.Column('identifier', sa.String(length=100), nullable=True),
        sa.Column('date_of_birth', sa.Date(), nullable=True),
        sa.Column('gender', sa.String(length=20), nullable=True),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_patients_user_id'), 'patients', ['user_id'], unique=False)

    # 2. Create Profile/Billing Tables
    op.create_table('clinics',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('clinic_name', sa.String(length=255), nullable=False),
        sa.Column('street_address', sa.String(length=255), nullable=True),
        sa.Column('city', sa.String(length=100), nullable=True),
        sa.Column('state', sa.String(length=100), nullable=True),
        sa.Column('pincode', sa.String(length=20), nullable=True),
        sa.Column('country', sa.String(length=2), nullable=False),
        sa.Column('logo_url', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )

    op.create_table('subscriptions',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('plan_type', sa.String(length=50), nullable=False),
        sa.Column('gateway', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('external_customer_id', sa.String(length=100), nullable=True),
        sa.Column('external_subscription_id', sa.String(length=100), nullable=True),
        sa.Column('pending_checkout_session_id', sa.String(length=255), nullable=True),
        sa.Column('current_period_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('current_period_end', sa.DateTime(timezone=True), nullable=False),
        sa.Column('card_brand', sa.String(length=50), nullable=True),
        sa.Column('card_last4', sa.String(length=4), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )

    # 3. Create Consultations (Without the transcript FK yet)
    op.create_table('consultations',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('patient_id', sa.Uuid(), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('clinical_summary_text', sa.Text(), nullable=True),
        sa.Column('is_title_edited', sa.Boolean(), nullable=False),
        sa.Column('doctor_speaker_id', sa.Integer(), nullable=True),
        sa.Column('last_summarized_transcript_id', sa.Uuid(), nullable=True),
        sa.Column('total_audio_seconds', sa.Integer(), nullable=False),
        sa.Column('current_session_started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_consultations_user_id'), 'consultations', ['user_id'], unique=False)

    # 4. Create Transcripts (Now safe because consultations exists)
    op.create_table('consultation_transcripts',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('consultation_id', sa.Uuid(), nullable=False),
        sa.Column('speaker_id', sa.Integer(), nullable=False),
        sa.Column('transcript', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['consultation_id'], ['consultations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_consultation_transcripts_consultation_id'), 'consultation_transcripts', ['consultation_id'], unique=False)

    # 5. Add the deferred Foreign Key to consultations
    op.create_foreign_key(
        'fk_consultations_last_transcript',
        'consultations', 'consultation_transcripts',
        ['last_summarized_transcript_id'], ['id']
    )

    # 6. Create AI Conversations
    op.create_table('ai_conversations',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('consultation_id', sa.Uuid(), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('is_title_generated', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['consultation_id'], ['consultations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('consultation_id')
    )
    op.create_index(op.f('ix_ai_conversations_user_id'), 'ai_conversations', ['user_id'], unique=False)

    op.create_table('ai_messages',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('conversation_id', sa.Uuid(), nullable=False),
        sa.Column('role', sa.String(length=50), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('artifacts', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('input_method', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['conversation_id'], ['ai_conversations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ai_messages_conversation_id'), 'ai_messages', ['conversation_id'], unique=False)


def downgrade() -> None:
    # 1. Drop AI related
    op.drop_index(op.f('ix_ai_messages_conversation_id'), table_name='ai_messages')
    op.drop_table('ai_messages')
    op.drop_index(op.f('ix_ai_conversations_user_id'), table_name='ai_conversations')
    op.drop_table('ai_conversations')

    # 2. Drop the circular FK first
    op.drop_constraint('fk_consultations_last_transcript', 'consultations', type_='foreignkey')

    # 3. Drop Transcripts and Consultations
    op.drop_index(op.f('ix_consultation_transcripts_consultation_id'), table_name='consultation_transcripts')
    op.drop_table('consultation_transcripts')
    op.drop_index(op.f('ix_consultations_user_id'), table_name='consultations')
    op.drop_table('consultations')

    # 4. Drop Billing/Patients
    op.drop_table('subscriptions')
    op.drop_index(op.f('ix_patients_user_id'), table_name='patients')
    op.drop_table('patients')
    op.drop_table('clinics')

    # 5. Drop Users (Root)
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_index(op.f('ix_users_deleted_at'), table_name='users')
    op.drop_table('users')
```

## File: src/infrastructure/persistence/postgres/alembic/versions/2026_04_02_0935-0dd637d7ae14_add_scribe_usage_table.py
```python
"""Add Scribe Usage table

Revision ID: 0dd637d7ae14
Revises: c5c4151db92f
Create Date: 2026-04-02 09:35:29.338098

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0dd637d7ae14'
down_revision: Union[str, None] = 'c5c4151db92f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('scribe_usage_logs',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('user_id', sa.Uuid(), nullable=False),
    sa.Column('consultation_id', sa.Uuid(), nullable=True),
    sa.Column('seconds_used', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['consultation_id'], ['consultations.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_scribe_usage_logs_user_id'), 'scribe_usage_logs', ['user_id'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_scribe_usage_logs_user_id'), table_name='scribe_usage_logs')
    op.drop_table('scribe_usage_logs')
    # ### end Alembic commands ###
```

## File: src/infrastructure/persistence/postgres/alembic/versions/2026_04_02_2033-a2b2a94e2336_make_speaker_id_optional_in_transcript_.py
```python
"""Make speaker id optional in transcript table

Revision ID: a2b2a94e2336
Revises: 0dd637d7ae14
Create Date: 2026-04-02 20:33:07.607249

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a2b2a94e2336'
down_revision: Union[str, None] = '0dd637d7ae14'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('consultation_transcripts', 'speaker_id',
               existing_type=sa.INTEGER(),
               nullable=True)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('consultation_transcripts', 'speaker_id',
               existing_type=sa.INTEGER(),
               nullable=False)
    # ### end Alembic commands ###
```

## File: src/infrastructure/persistence/postgres/alembic/versions/2026_04_06_1417-ed54f2e84840_add_reports_and_templates_tables.py
```python
"""Add reports and templates tables

Revision ID: ed54f2e84840
Revises: a2b2a94e2336
Create Date: 2026-04-06 14:17:30.307528

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ed54f2e84840'
down_revision: Union[str, None] = 'a2b2a94e2336'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('templates',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('user_id', sa.Uuid(), nullable=True),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('category', sa.String(length=100), nullable=True),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('content', sa.Text(), nullable=False),
    sa.Column('is_system', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_templates_user_id'), 'templates', ['user_id'], unique=False)
    op.create_table('reports',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('consultation_id', sa.Uuid(), nullable=False),
    sa.Column('template_id', sa.Uuid(), nullable=False),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('content', sa.Text(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['consultation_id'], ['consultations.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['template_id'], ['templates.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_reports_consultation_id'), 'reports', ['consultation_id'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_reports_consultation_id'), table_name='reports')
    op.drop_table('reports')
    op.drop_index(op.f('ix_templates_user_id'), table_name='templates')
    op.drop_table('templates')
    # ### end Alembic commands ###
```

## File: src/infrastructure/persistence/postgres/alembic/versions/2026_04_06_1947-c19ecbad6d79_add_set_null_to_consultation_last_.py
```python
"""Add SET NULL to consultation last_summarized_transcript_id FK

Revision ID: c19ecbad6d79
Revises: ed54f2e84840
Create Date: 2026-04-06 19:47:38.594172

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c19ecbad6d79'
down_revision: Union[str, None] = 'ed54f2e84840'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(op.f('fk_consultations_last_transcript'), 'consultations', type_='foreignkey')
    op.create_foreign_key(None, 'consultations', 'consultation_transcripts', ['last_summarized_transcript_id'], ['id'], ondelete='SET NULL')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'consultations', type_='foreignkey')
    op.create_foreign_key(op.f('fk_consultations_last_transcript'), 'consultations', 'consultation_transcripts', ['last_summarized_transcript_id'], ['id'])
    # ### end Alembic commands ###
```

## File: src/infrastructure/persistence/postgres/alembic/versions/2026_04_10_1040-8d5b036266d4_add_attachments_table_for_file_uploads.py
```python
"""Add attachments table for file uploads

Revision ID: 8d5b036266d4
Revises: c19ecbad6d79
Create Date: 2026-04-10 10:40:41.798531

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8d5b036266d4'
down_revision: Union[str, None] = 'c19ecbad6d79'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('attachments',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('user_id', sa.Uuid(), nullable=False),
    sa.Column('message_id', sa.Uuid(), nullable=True),
    sa.Column('file_name', sa.String(length=255), nullable=True),
    sa.Column('content_type', sa.String(length=100), nullable=True),
    sa.Column('s3_key', sa.String(length=500), nullable=False),
    sa.Column('google_uri', sa.String(length=500), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['message_id'], ['ai_messages.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_attachments_user_id'), 'attachments', ['user_id'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_attachments_user_id'), table_name='attachments')
    op.drop_table('attachments')
    # ### end Alembic commands ###
```

## File: src/infrastructure/persistence/postgres/alembic/versions/2026_04_10_1550-23d3d241c2d5_update_consultations_patient_id_foreign_.py
```python
"""update consultations patient_id foreign key to SET NULL on delete

Revision ID: 23d3d241c2d5
Revises: 8d5b036266d4
Create Date: 2026-04-10 15:50:01.081070

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '23d3d241c2d5'
down_revision: Union[str, None] = '8d5b036266d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(op.f('consultations_patient_id_fkey'), 'consultations', type_='foreignkey')
    op.create_foreign_key(None, 'consultations', 'patients', ['patient_id'], ['id'], ondelete='SET NULL')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'consultations', type_='foreignkey')
    op.create_foreign_key(op.f('consultations_patient_id_fkey'), 'consultations', 'patients', ['patient_id'], ['id'])
    # ### end Alembic commands ###
```

## File: src/infrastructure/persistence/postgres/alembic/versions/2026_04_10_2100-a27175f0cd70_add_invoices_table.py
```python
"""add invoices table

Revision ID: a27175f0cd70
Revises: 23d3d241c2d5
Create Date: 2026-04-10 21:00:06.634499

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a27175f0cd70'
down_revision: Union[str, None] = '23d3d241c2d5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('invoices',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('subscription_id', sa.Uuid(), nullable=False),
    sa.Column('user_id', sa.Uuid(), nullable=False),
    sa.Column('stripe_invoice_id', sa.String(length=100), nullable=False),
    sa.Column('stripe_subscription_id', sa.String(length=100), nullable=True),
    sa.Column('amount_paid', sa.Integer(), nullable=False),
    sa.Column('currency', sa.String(length=3), nullable=False),
    sa.Column('status', sa.String(length=50), nullable=False),
    sa.Column('invoice_pdf_url', sa.String(length=500), nullable=False),
    sa.Column('hosted_invoice_url', sa.String(length=500), nullable=False),
    sa.Column('period_start', sa.DateTime(timezone=True), nullable=False),
    sa.Column('period_end', sa.DateTime(timezone=True), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['subscription_id'], ['subscriptions.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_invoices_stripe_invoice_id'), 'invoices', ['stripe_invoice_id'], unique=True)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_invoices_stripe_invoice_id'), table_name='invoices')
    op.drop_table('invoices')
    # ### end Alembic commands ###
```

## File: src/infrastructure/persistence/postgres/alembic/versions/2026_04_13_1451-d87af33a1d2f_update_invoices_table_for_modular_.py
```python
"""update invoices table for modular providers

Revision ID: d87af33a1d2f
Revises: a27175f0cd70
Create Date: 2026-04-13 14:51:28.282504

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd87af33a1d2f'
down_revision: Union[str, None] = 'a27175f0cd70'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('invoices', sa.Column('gateway', sa.String(length=50), nullable=False))
    op.add_column('invoices', sa.Column('external_invoice_id', sa.String(length=100), nullable=True))
    op.add_column('invoices', sa.Column('external_subscription_id', sa.String(length=100), nullable=True))
    op.alter_column('invoices', 'invoice_pdf_url',
               existing_type=sa.VARCHAR(length=500),
               nullable=True)
    op.alter_column('invoices', 'hosted_invoice_url',
               existing_type=sa.VARCHAR(length=500),
               nullable=True)
    op.drop_index(op.f('ix_invoices_stripe_invoice_id'), table_name='invoices')
    op.drop_column('invoices', 'stripe_invoice_id')
    op.drop_column('invoices', 'stripe_subscription_id')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('invoices', sa.Column('stripe_subscription_id', sa.VARCHAR(length=100), autoincrement=False, nullable=True))
    op.add_column('invoices', sa.Column('stripe_invoice_id', sa.VARCHAR(length=100), autoincrement=False, nullable=False))
    op.create_index(op.f('ix_invoices_stripe_invoice_id'), 'invoices', ['stripe_invoice_id'], unique=True)
    op.alter_column('invoices', 'hosted_invoice_url',
               existing_type=sa.VARCHAR(length=500),
               nullable=False)
    op.alter_column('invoices', 'invoice_pdf_url',
               existing_type=sa.VARCHAR(length=500),
               nullable=False)
    op.drop_column('invoices', 'external_subscription_id')
    op.drop_column('invoices', 'external_invoice_id')
    op.drop_column('invoices', 'gateway')
    # ### end Alembic commands ###
```

## File: src/infrastructure/persistence/postgres/alembic/versions/2026_04_17_1554-ad6d01f4d6e9_add_notification_tables.py
```python
"""add notification tables

Revision ID: ad6d01f4d6e9
Revises: d87af33a1d2f
Create Date: 2026-04-17 15:54:17.517360

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'ad6d01f4d6e9'
down_revision: Union[str, None] = 'd87af33a1d2f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('email_logs',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('user_id', sa.Uuid(), nullable=True),
    sa.Column('email_template', sa.String(length=100), nullable=False),
    sa.Column('to_email', sa.String(length=255), nullable=False),
    sa.Column('status', sa.String(length=50), nullable=False),
    sa.Column('provider_message_id', sa.String(length=255), nullable=True),
    sa.Column('error_message', sa.Text(), nullable=True),
    sa.Column('template_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_email_logs_email_template'), 'email_logs', ['email_template'], unique=False)
    op.create_index(op.f('ix_email_logs_status'), 'email_logs', ['status'], unique=False)
    op.create_index(op.f('ix_email_logs_user_id'), 'email_logs', ['user_id'], unique=False)

    op.create_table('password_resets',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('user_id', sa.Uuid(), nullable=False),
    sa.Column('token', sa.Uuid(), nullable=False),
    sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('used_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_password_resets_expires_at'), 'password_resets', ['expires_at'], unique=False)
    op.create_index(op.f('ix_password_resets_token'), 'password_resets', ['token'], unique=True)
    op.create_index(op.f('ix_password_resets_user_id'), 'password_resets', ['user_id'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_password_resets_user_id'), table_name='password_resets')
    op.drop_index(op.f('ix_password_resets_token'), table_name='password_resets')
    op.drop_index(op.f('ix_password_resets_expires_at'), table_name='password_resets')
    op.drop_table('password_resets')
    
    op.drop_index(op.f('ix_email_logs_user_id'), table_name='email_logs')
    op.drop_index(op.f('ix_email_logs_status'), table_name='email_logs')
    op.drop_index(op.f('ix_email_logs_email_template'), table_name='email_logs')
    op.drop_table('email_logs')
    # ### end Alembic commands ###
```

## File: src/infrastructure/persistence/postgres/alembic/versions/2026_04_21_2049-8bb89d1019a9_add_consultation_insights.py
```python
"""add consultation insights

Revision ID: 8bb89d1019a9
Revises: ad6d01f4d6e9
Create Date: 2026-04-21 20:49:02.719420

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8bb89d1019a9'
down_revision: Union[str, None] = 'ad6d01f4d6e9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('consultation_insights',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('consultation_id', sa.Uuid(), nullable=False),
    sa.Column('category', sa.String(length=50), nullable=False),
    sa.Column('content', sa.Text(), nullable=False),
    sa.Column('is_dismissed', sa.Boolean(), nullable=False),
    sa.Column('is_user_added', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['consultation_id'], ['consultations.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_consultation_insights_consultation_id'), 'consultation_insights', ['consultation_id'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_consultation_insights_consultation_id'), table_name='consultation_insights')
    op.drop_table('consultation_insights')
    # ### end Alembic commands ###
```

## File: src/infrastructure/persistence/postgres/repos/attachments_repo.py
```python
"""Repository for file attachments."""

import uuid
from typing import List, Optional
from sqlalchemy import select

from src.infrastructure.persistence.postgres.models import Attachment


class AttachmentsRepository:
    """Repository for file attachments database operations."""

    def __init__(self, session):
        self.session = session

    # --- Read Operations ---

    async def get_attachment(
        self,
        attachment_id: uuid.UUID,
        user_id: uuid.UUID
    ) -> Optional[Attachment]:
        """Fetch a single attachment by ID, ensuring user ownership."""
        stmt = select(Attachment).where(
            Attachment.id == attachment_id,
            Attachment.user_id == user_id
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_attachments(
        self,
        attachment_ids: List[uuid.UUID],
        user_id: uuid.UUID
    ) -> List[Attachment]:
        """Fetch multiple attachments by IDs, ensuring user ownership."""
        if not attachment_ids:
            return []

        stmt = select(Attachment).where(
            Attachment.id.in_(attachment_ids),
            Attachment.user_id == user_id
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    # --- Write Operations ---

    async def create_attachment(
        self,
        user_id: uuid.UUID,
        file_name: str,
        content_type: str,
        s3_key: str,
        google_uri: Optional[str] = None
    ) -> Attachment:
        """Create a new attachment with S3 key and optional Google URI."""
        attachment = Attachment(
            user_id=user_id,
            file_name=file_name,
            content_type=content_type,
            s3_key=s3_key,
            google_uri=google_uri
        )
        self.session.add(attachment)
        await self.session.commit()
        return attachment

    async def link_to_message(
        self,
        attachment_id: uuid.UUID,
        message_id: uuid.UUID
    ) -> bool:
        """Link an attachment to a message."""
        stmt = select(Attachment).where(Attachment.id == attachment_id)
        result = await self.session.execute(stmt)
        attachment = result.scalar_one_or_none()

        if attachment:
            attachment.message_id = message_id
            await self.session.commit()
            return True

        return False

    async def update_google_uri(
        self,
        attachment_id: uuid.UUID,
        google_uri: str
    ) -> bool:
        """Update the Google URI for an attachment (for Gemini API)."""
        stmt = select(Attachment).where(Attachment.id == attachment_id)
        result = await self.session.execute(stmt)
        attachment = result.scalar_one_or_none()

        if attachment:
            attachment.google_uri = google_uri
            await self.session.commit()
            return True

        return False

    async def delete_attachment(
        self,
        attachment_id: uuid.UUID,
        user_id: uuid.UUID
    ) -> Optional[str]:
        """
        Delete an attachment and return its s3_key for S3 cleanup.

        Only allows deletion if attachment is not linked to a message (orphaned).
        Returns s3_key if deleted, None if not found or already linked.
        """
        stmt = select(Attachment).where(
            Attachment.id == attachment_id,
            Attachment.user_id == user_id
        )
        result = await self.session.execute(stmt)
        attachment = result.scalar_one_or_none()

        if not attachment:
            return None

        # Only allow deletion of orphaned attachments (not linked to messages)
        if attachment.message_id is not None:
            raise ValueError("Cannot delete attachment that is linked to a message")

        s3_key = attachment.s3_key
        await self.session.delete(attachment)
        await self.session.commit()
        return s3_key
```

## File: src/infrastructure/persistence/postgres/repos/consultation_insights_repo.py
```python
"""Repository for ConsultationInsight model."""

import uuid
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.persistence.postgres.models import ConsultationInsight


class ConsultationInsightsRepository:
    """Handles ConsultationInsight CRUD operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_insights_by_consultation(
        self,
        consultation_id: uuid.UUID,
        include_dismissed: bool = False
    ) -> list[ConsultationInsight]:
        """Get all insights for a consultation, optionally including dismissed."""
        query = select(ConsultationInsight).where(
            ConsultationInsight.consultation_id == consultation_id
        )

        if not include_dismissed:
            query = query.where(ConsultationInsight.is_dismissed == False)

        query = query.order_by(ConsultationInsight.created_at)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_insight_by_id(
        self,
        insight_id: uuid.UUID,
        consultation_id: uuid.UUID
    ) -> ConsultationInsight | None:
        """Get a specific insight by ID."""
        query = select(ConsultationInsight).where(
            and_(
                ConsultationInsight.id == insight_id,
                ConsultationInsight.consultation_id == consultation_id
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def create_insight(
        self,
        consultation_id: uuid.UUID,
        category: str,
        content: str,
        is_user_added: bool = False
    ) -> ConsultationInsight:
        """Create a new insight."""
        insight = ConsultationInsight(
            consultation_id=consultation_id,
            category=category,
            content=content,
            is_user_added=is_user_added,
            is_dismissed=False
        )
        self.session.add(insight)
        await self.session.flush()
        return insight

    async def dismiss_insight(
        self,
        insight_id: uuid.UUID,
        consultation_id: uuid.UUID
    ) -> bool:
        """Soft delete an insight by setting is_dismissed=True."""
        insight = await self.get_insight_by_id(insight_id, consultation_id)
        if not insight:
            return False

        insight.is_dismissed = True
        await self.session.flush()
        return True

    async def delete_insight(
        self,
        insight_id: uuid.UUID,
        consultation_id: uuid.UUID
    ) -> bool:
        """Permanently delete an insight."""
        insight = await self.get_insight_by_id(insight_id, consultation_id)
        if not insight:
            return False

        await self.session.delete(insight)
        await self.session.flush()
        return True

    async def upsert_insights(
        self,
        consultation_id: uuid.UUID,
        insights: list[dict]
    ) -> list[ConsultationInsight]:
        """
        Bulk upsert insights.
        Each insight dict should have: category, content, is_dismissed, is_user_added
        Returns created/updated insights.
        """
        result = []

        for insight_data in insights:
            # Check if similar insight exists (same category + content)
            existing = await self.session.execute(
                select(ConsultationInsight).where(
                    and_(
                        ConsultationInsight.consultation_id == consultation_id,
                        ConsultationInsight.category == insight_data["category"],
                        ConsultationInsight.content == insight_data["content"]
                    )
                )
            )
            existing_insight = existing.scalar_one_or_none()

            if existing_insight:
                # Update dismiss state if changed
                if existing_insight.is_dismissed != insight_data.get("is_dismissed", False):
                    existing_insight.is_dismissed = insight_data["is_dismissed", False]
                    await self.session.flush()
                result.append(existing_insight)
            else:
                # Create new insight
                new_insight = await self.create_insight(
                    consultation_id=consultation_id,
                    category=insight_data["category"],
                    content=insight_data["content"],
                    is_user_added=insight_data.get("is_user_added", False)
                )
                result.append(new_insight)

        return result

    async def get_insights_by_category(
        self,
        consultation_id: uuid.UUID,
        category: str
    ) -> list[ConsultationInsight]:
        """Get all insights for a specific category."""
        query = select(ConsultationInsight).where(
            and_(
                ConsultationInsight.consultation_id == consultation_id,
                ConsultationInsight.category == category
            )
        ).order_by(ConsultationInsight.created_at)

        result = await self.session.execute(query)
        return list(result.scalars().all())
```

## File: src/infrastructure/persistence/postgres/repos/email_logs_repo.py
```python
import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.persistence.postgres.models import EmailLog


class EmailLogsRepository:
    """Repository for email log operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_log(
        self,
        email_template: str,
        to_email: str,
        status: str,
        user_id: Optional[uuid.UUID] = None,
        provider_message_id: Optional[str] = None,
        error_message: Optional[str] = None,
        template_metadata: Optional[dict] = None,
    ) -> EmailLog:
        """
        Create a new email log entry.

        Args:
            email_template: Template identifier (e.g., 'password_reset')
            to_email: Recipient email address
            status: 'queued', 'sent', 'failed', 'bounced'
            user_id: User ID (optional)
            provider_message_id: Brevo message ID (optional)
            error_message: Error details if failed (optional)
            template_metadata: Template-specific data (optional)

        Returns:
            Created EmailLog instance
        """
        log = EmailLog(
            user_id=user_id,
            email_template=email_template,
            to_email=to_email,
            status=status,
            provider_message_id=provider_message_id,
            error_message=error_message,
            template_metadata=template_metadata,
        )
        self.session.add(log)
        await self.session.flush()
        return log

    async def update_log_status(
        self,
        log_id: uuid.UUID,
        status: str,
        provider_message_id: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> Optional[EmailLog]:
        """
        Update an email log's status after sending.

        Args:
            log_id: Email log ID
            status: New status ('sent', 'failed', 'bounced')
            provider_message_id: Brevo message ID (optional)
            error_message: Error details if failed (optional)

        Returns:
            Updated EmailLog or None if not found
        """
        stmt = select(EmailLog).where(EmailLog.id == log_id)
        result = await self.session.execute(stmt)
        log = result.scalar_one_or_none()

        if log:
            log.status = status
            if provider_message_id:
                log.provider_message_id = provider_message_id
            if error_message:
                log.error_message = error_message
            await self.session.flush()

        return log

    async def get_user_logs(
        self,
        user_id: uuid.UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> list[EmailLog]:
        """
        Get email logs for a specific user.

        Args:
            user_id: User ID
            limit: Max results
            offset: Pagination offset

        Returns:
            List of EmailLog instances
        """
        stmt = (
            select(EmailLog)
            .where(EmailLog.user_id == user_id)
            .order_by(EmailLog.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
```

## File: src/infrastructure/persistence/postgres/repos/password_resets_repo.py
```python
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.persistence.postgres.models import PasswordReset


class PasswordResetsRepository:
    """Repository for password reset token operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_reset_token(
        self,
        user_id: uuid.UUID,
        expires_hours: int = 1,
    ) -> PasswordReset:
        """
        Create a new password reset token.

        Args:
            user_id: User ID
            expires_hours: Token validity in hours (default: 1)

        Returns:
            Created PasswordReset instance
        """
        token = PasswordReset(
            user_id=user_id,
            token=uuid.uuid4(),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=expires_hours),
        )
        self.session.add(token)
        await self.session.flush()
        return token

    async def get_valid_token(
        self,
        token: uuid.UUID,
    ) -> Optional[PasswordReset]:
        """
        Get a valid, unused reset token.

        Args:
            token: Reset token UUID

        Returns:
            PasswordReset instance if valid, None otherwise
        """
        stmt = select(PasswordReset).where(
            and_(
                PasswordReset.token == token,
                PasswordReset.used_at.is_(None),
                PasswordReset.expires_at > datetime.now(timezone.utc),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def mark_token_used(
        self,
        token_id: uuid.UUID,
    ) -> Optional[PasswordReset]:
        """
        Mark a reset token as used.

        Args:
            token_id: Password reset ID

        Returns:
            Updated PasswordReset or None if not found
        """
        stmt = select(PasswordReset).where(PasswordReset.id == token_id)
        result = await self.session.execute(stmt)
        token = result.scalar_one_or_none()

        if token:
            token.used_at = datetime.now(timezone.utc)
            await self.session.flush()

        return token

    async def invalidate_user_tokens(
        self,
        user_id: uuid.UUID,
    ) -> int:
        """
        Invalidate all unused tokens for a user (e.g., when password is changed).

        Args:
            user_id: User ID

        Returns:
            Number of tokens invalidated
        """
        stmt = select(PasswordReset).where(
            and_(
                PasswordReset.user_id == user_id,
                PasswordReset.used_at.is_(None),
            )
        )
        result = await self.session.execute(stmt)
        tokens = list(result.scalars().all())

        now = datetime.now(timezone.utc)
        for token in tokens:
            token.used_at = now

        await self.session.flush()
        return len(tokens)
```

## File: src/infrastructure/persistence/postgres/repos/reports_repo.py
```python
import uuid
from typing import Optional, List
from sqlalchemy import select, delete

from src.infrastructure.persistence.postgres.models import Report, Template


class ReportsRepository:
    """Repository for report database operations."""

    def __init__(self, session):
        self.session = session

    # --- Read Operations ---

    async def get_by_id(self, report_id: uuid.UUID) -> Optional[Report]:
        """Fetches report by ID."""
        stmt = select(Report).where(Report.id == report_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id_and_user(
        self,
        report_id: uuid.UUID,
        user_id: uuid.UUID
    ) -> Optional[Report]:
        """Fetches report by ID, ensuring user ownership via consultation."""
        stmt = select(Report).join(
            Report.consultation
        ).where(
            Report.id == report_id,
            Report.consultation.has(user_id=user_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_consultation(
        self,
        consultation_id: uuid.UUID
    ) -> List[Report]:
        """Fetches all reports for a consultation."""
        stmt = select(
            Report.id,
            Report.title,
            Report.created_at,
            Template.name.label("template_name")
        ).join(
            Template, Report.template_id == Template.id
        ).where(
            Report.consultation_id == consultation_id
        ).order_by(Report.created_at.desc())

        result = await self.session.execute(stmt)
        return [
            {
                "id": row.id,
                "title": row.title,
                "template_name": row.template_name,
                "created_at": row.created_at
            }
            for row in result.all()
        ]

    async def find_duplicate_title(
        self,
        consultation_id: uuid.UUID,
        title: str
    ) -> Optional[Report]:
        """Checks if a report with the same title exists for the consultation."""
        stmt = select(Report).where(
            Report.consultation_id == consultation_id,
            Report.title == title
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    # --- Write Operations ---

    async def create(
        self,
        consultation_id: uuid.UUID,
        template_id: uuid.UUID,
        title: str,
        content: str
    ) -> Report:
        """Creates a new report."""
        report = Report(
            consultation_id=consultation_id,
            template_id=template_id,
            title=title,
            content=content
        )
        self.session.add(report)
        await self.session.commit()
        await self.session.refresh(report)
        return report

    async def update(
        self,
        report_id: uuid.UUID,
        data: dict
    ) -> bool:
        """Updates report fields."""
        stmt = select(Report).where(Report.id == report_id)
        result = await self.session.execute(stmt)
        report = result.scalar_one_or_none()

        if report:
            for key, value in data.items():
                if hasattr(report, key) and value is not None:
                    setattr(report, key, value)
            await self.session.commit()
            await self.session.refresh(report)
            return True

        return False

    async def delete(self, report_id: uuid.UUID) -> bool:
        """Deletes a report by ID."""
        stmt = delete(Report).where(Report.id == report_id)
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount > 0
```

## File: src/infrastructure/persistence/postgres/repos/scribe_usage_logs_repo.py
```python
import uuid
from datetime import datetime
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.persistence.postgres.models import ScribeUsageLog


class ScribeUsageLogsRepository:
    """Repository for scribe usage logs database operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_log(
        self,
        user_id: uuid.UUID,
        consultation_id: uuid.UUID,
        seconds_used: int
    ) -> ScribeUsageLog:
        """Creates a new usage log entry."""
        log = ScribeUsageLog(
            user_id=user_id,
            consultation_id=consultation_id,
            seconds_used=seconds_used
        )
        self.session.add(log)
        await self.session.commit()
        await self.session.refresh(log)
        return log

    async def get_usage_in_period(
        self,
        user_id: uuid.UUID,
        period_start: datetime,
        period_end: datetime
    ) -> int:
        """
        Returns total seconds used by user within a billing period.
        Sums logs where created_at falls within the period.
        """
        stmt = (
            select(func.sum(ScribeUsageLog.seconds_used))
            .where(
                ScribeUsageLog.user_id == user_id,
                ScribeUsageLog.created_at >= period_start,
                ScribeUsageLog.created_at <= period_end
            )
        )
        result = await self.session.execute(stmt)
        total_seconds = result.scalar()
        return total_seconds or 0
```

## File: src/infrastructure/persistence/postgres/repos/templates_repo.py
```python
import uuid
from typing import Optional, List
from sqlalchemy import select, delete

from src.infrastructure.persistence.postgres.models import Template


class TemplatesRepository:
    """Repository for template database operations."""

    def __init__(self, session):
        self.session = session

    # --- Read Operations ---

    async def get_by_id(self, template_id: uuid.UUID) -> Optional[Template]:
        """Fetches template by ID."""
        stmt = select(Template).where(Template.id == template_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id_and_user(
        self,
        template_id: uuid.UUID,
        user_id: uuid.UUID
    ) -> Optional[Template]:
        """Fetches template by ID, ensuring user ownership (or is system)."""
        stmt = select(Template).where(
            Template.id == template_id,
            (Template.user_id == user_id) | (Template.is_system == True)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def find_by_name_and_user(
        self,
        name: str,
        user_id: uuid.UUID
    ) -> Optional[Template]:
        """Checks if a template with the same name exists for the user."""
        stmt = select(Template).where(
            Template.name == name,
            Template.user_id == user_id
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_all(self, user_id: uuid.UUID, search: Optional[str] = None) -> List[Template]:
        """
        Returns all templates for user (system + user's own).
        System templates have user_id = NULL.

        Args:
            user_id: The user's ID
            search: Optional search term to filter by name or description
        """
        stmt = select(Template).where(
            (Template.user_id == user_id) | (Template.user_id == None)
        )

        # Add search filter if provided
        if search:
            stmt = stmt.where(
                (Template.name.ilike(f"%{search}%")) |
                (Template.description.ilike(f"%{search}%"))
            )

        stmt = stmt.order_by(Template.is_system.desc(), Template.name.asc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    # --- Write Operations ---

    async def create(
        self,
        user_id: uuid.UUID,
        name: str,
        content: str,
        category: Optional[str] = None,
        description: Optional[str] = None
    ) -> Template:
        """Creates a new user template."""
        template = Template(
            user_id=user_id,
            name=name,
            content=content,
            category=category,
            description=description,
            is_system=False
        )
        self.session.add(template)
        await self.session.commit()
        await self.session.refresh(template)
        return template

    async def update(
        self,
        template_id: uuid.UUID,
        data: dict
    ) -> bool:
        """Updates template fields (only for non-system templates)."""
        stmt = select(Template).where(
            Template.id == template_id,
            Template.is_system == False
        )
        result = await self.session.execute(stmt)
        template = result.scalar_one_or_none()

        if template:
            for key, value in data.items():
                if hasattr(template, key) and value is not None:
                    setattr(template, key, value)
            await self.session.commit()
            await self.session.refresh(template)
            return True

        return False

    async def delete(self, template_id: uuid.UUID) -> bool:
        """Deletes a template (only for non-system templates)."""
        stmt = delete(Template).where(
            Template.id == template_id,
            Template.is_system == False
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount > 0
```

## File: src/dependencies/db.py
```python
"""
Database dependencies for FastAPI routes.

Re-exports data persistence layer dependencies (Postgres, Redis).
"""

from typing import AsyncGenerator

import redis.asyncio as aioredis
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.persistence.postgres.database import async_session_maker
from src.infrastructure.persistence.redis.client import get_redis_client


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency for Postgres database session.

    Automatically handles commit/rollback and cleanup.

    Usage in routes:
        @app.get("/users")
        async def get_users(session: AsyncSession = Depends(get_db_session)):
            result = await session.execute(select(User))
            return result.scalars().all()
    """
    async with async_session_maker() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_redis() -> AsyncGenerator[aioredis.Redis, None]:
    """
    FastAPI dependency for Redis client.

    Usage in routes:
        @app.get("/cache")
        async def get_cache(redis: aioredis.Redis = Depends(get_redis)):
            value = await redis.get("key")
            return {"value": value}
    """
    redis_client = get_redis_client()
    yield redis_client
```

## File: src/infrastructure/external/brave.py
```python
"""Brave Search API client for medical web search."""

import httpx
from typing import List, Optional

from src.core.config import settings
from src.core.logging import get_logger
from src.schemas.features.copilot import BraveSearchResult

logger = get_logger(__name__)


class BraveSearchClient:
    """
    Client for Brave Search API.
    Handles site-restricted searches for medical information.
    """

    def __init__(self):
        self.api_key = settings.BRAVE_SEARCH_API_KEY
        self.base_url = "https://api.search.brave.com/res/v1/web/search"
        self.timeout = 10.0

        # Request configuration
        self.headers = {
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "X-Subscription-Token": self.api_key
        }

        # HTTP client with connection pooling
        self._client = httpx.AsyncClient(
            timeout=self.timeout,
            headers=self.headers,
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
        )

        if not self.api_key:
            logger.warning("Brave Search API key is missing. Search will fail.")

    async def close(self):
        """Cleanup HTTP client resources."""
        await self._client.aclose()

    async def search(
        self,
        query: str,
        count: int = 8,
        sites: Optional[List[str]] = None
    ) -> List[BraveSearchResult]:
        """
        Execute a web search, optionally restricted to specific domains.

        Args:
            query: Search query string
            count: Number of results to return (max 20)
            sites: Optional list of domains to restrict search to

        Returns:
            List of BraveSearchResult with full metadata
        """
        if not self.api_key:
            return []

        # Build query with site filters
        full_query = self._build_query(query, sites)

        params = {
            "q": full_query,
            "count": min(count, 20),
            "search_lang": "en",
            "text_decorations": False,
            "extra_snippets": True,
        }

        try:
            response = await self._client.get(self.base_url, params=params)
            response.raise_for_status()
            return self._parse_response(response.json())

        except httpx.HTTPError as e:
            logger.error(f"Brave API Error: {str(e)}")
            return []

    def _build_query(self, query: str, sites: Optional[List[str]]) -> str:
        """
        Appends site filters to the user query.
        Format: "query (site:a.com OR site:b.com)"
        """
        if not sites:
            return query

        # Clean and format site filters
        site_filters = " OR ".join([f"site:{site.strip()}" for site in sites if site.strip()])
        return f"{query} ({site_filters})"

    def _parse_response(self, data: dict) -> List[BraveSearchResult]:
        """
        Maps raw API JSON to BraveSearchResult Pydantic models.
        """
        raw_results = data.get("web", {}).get("results", [])
        parsed_results = []

        for item in raw_results:
            try:
                profile = item.get("profile", {})
                meta = item.get("meta_url", {})

                result = BraveSearchResult(
                    title=item.get("title", "Untitled"),
                    url=item.get("url", ""),
                    description=item.get("description", ""),
                    extra_snippets=item.get("extra_snippets", []),
                    profile_name=profile.get("name"),
                    profile_img=profile.get("img"),
                    hostname=meta.get("hostname")
                )
                parsed_results.append(result)

            except Exception as e:
                logger.warning(f"Failed to parse a search result item: {e}")
                continue

        return parsed_results
```

## File: src/infrastructure/external/deepgram.py
```python
from deepgram import DeepgramClient as DGClient
from deepgram.core.api_error import ApiError

from src.core.logging import get_logger
from src.core.config import settings
from src.core.exceptions import BadRequestException

logger = get_logger(__name__)


class DeepgramClient:
    """Deepgram Wrapper for speech-to-text. Handles temporary token generation."""

    def __init__(self):
        self.api_key = settings.DEEPGRAM_API_KEY
        self._client: DGClient | None = None

    @property
    def client(self) -> DGClient:
        if self._client is None:
            self._client = DGClient(api_key=self.api_key)
        return self._client

    async def generate_temporary_token(self) -> str:
        """Generates temporary access token for frontend WebSocket."""
        try:
            response = self.client.auth.v1.tokens.grant()
            token = response.access_token

            if not token:
                raise BadRequestException("Deepgram returned empty token")

            logger.debug("Successfully generated Deepgram temporary token")
            return token

        except ApiError as e:
            logger.error(f"Deepgram token generation failed: {str(e)}")
            raise BadRequestException(f"Failed to generate Deepgram token: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error generating Deepgram token: {str(e)}")
            raise BadRequestException("Failed to generate Deepgram token")
```

## File: src/infrastructure/llm/factory.py
```python
from typing import Optional
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
```

## File: src/infrastructure/persistence/postgres/alembic/env.py
```python
import asyncio
import os
import sys
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context

# Add the project root to the Python path
sys.path.insert(0, os.path.realpath(os.path.join(os.path.dirname(__file__), "../../../../../")))

# 1. Import your app code
from src.core.config import settings
from src.infrastructure.persistence.postgres.models import Base 


# Alembic Config object
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 2. Set the metadata so Alembic can "see" tables
target_metadata = Base.metadata

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = settings.DATABASE_URL
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()

async def run_async_migrations() -> None:
    """
    The main entry point for async migrations.
    """
    # Create a config dict and inject the DB URL from .env settings
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = settings.DATABASE_URL

    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()

def run_migrations_online() -> None:
    """Run migrations in 'online' mode (standard for us)."""
    asyncio.run(run_async_migrations())

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

## File: src/infrastructure/persistence/postgres/alembic/script.py.mako
```
"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision}
Create Date: ${create_date}

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

# revision identifiers, used by Alembic.
revision: str = ${repr(up_revision)}
down_revision: Union[str, None] = ${repr(down_revision)}
branch_labels: Union[str, Sequence[str], None] = ${repr(branch_labels)}
depends_on: Union[str, Sequence[str], None] = ${repr(depends_on)}


def upgrade() -> None:
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    ${downgrades if downgrades else "pass"}
```

## File: src/infrastructure/persistence/postgres/database.py
```python
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from src.core.config import settings
from src.core.logging import get_logger

logger = get_logger(__name__)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass


# Create async engine
engine: AsyncEngine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

# Create session factory
async_session_maker = async_sessionmaker(
    engine,
    expire_on_commit=False,
)


async def check_db_connection() -> bool:
    """
    Verify database connectivity.

    Returns True if connection is successful, False otherwise.
    """
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error(f"Database connection check failed: {e}")
        return False


async def close_db_connections() -> None:
    """Close all database connections."""
    await engine.dispose()
    logger.info("Database connections closed")
```

## File: src/infrastructure/persistence/postgres/repos/ai_conversations_repo.py
```python
"""Repository for AI conversations and messages."""

import uuid
from typing import List, Optional, Tuple
from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.infrastructure.persistence.postgres.models import AIConversation, AIMessage


class AIConversationsRepository:
    """Repository for AI conversations and messages database operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    # --- Read Operations: Conversations ---

    async def get_conversation(
        self,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID
    ) -> Optional[AIConversation]:
        """Fetch a single conversation by ID, ensuring user ownership."""
        stmt = select(AIConversation).where(
            AIConversation.id == conversation_id,
            AIConversation.user_id == user_id
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_conversations(
        self,
        user_id: uuid.UUID,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[AIConversation], int]:
        """
        List conversations for a user with pagination.
        Returns (conversations, total_count).
        """
        # Get total count
        count_stmt = select(func.count()).where(AIConversation.user_id == user_id)
        count_result = await self.session.execute(count_stmt)
        total = count_result.scalar()

        # Get paginated results
        stmt = (
            select(AIConversation)
            .where(AIConversation.user_id == user_id)
            .order_by(AIConversation.updated_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await self.session.execute(stmt)
        conversations = list(result.scalars().all())

        return conversations, total

    # --- Read Operations: Messages ---

    async def get_messages(
        self,
        conversation_id: uuid.UUID
    ) -> List[AIMessage]:
        """Fetch all messages for a conversation, ordered by creation time, with attachments."""
        stmt = (
            select(AIMessage)
            .where(AIMessage.conversation_id == conversation_id)
            .options(selectinload(AIMessage.attachments))
            .order_by(AIMessage.created_at.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    # --- Write Operations: Conversations ---

    async def create_conversation(
        self,
        user_id: uuid.UUID,
        title: str = "New Chat",
        consultation_id: Optional[uuid.UUID] = None
    ) -> AIConversation:
        """Create a new conversation."""
        conversation = AIConversation(
            user_id=user_id,
            title=title,
            consultation_id=consultation_id,
            is_title_generated=False
        )
        self.session.add(conversation)
        await self.session.commit()
        return conversation

    async def update_title(
        self,
        conversation_id: uuid.UUID,
        title: str
    ) -> bool:
        """Update conversation title and mark as generated."""
        stmt = select(AIConversation).where(AIConversation.id == conversation_id)
        result = await self.session.execute(stmt)
        conversation = result.scalar_one_or_none()

        if conversation:
            conversation.title = title
            conversation.is_title_generated = True
            await self.session.commit()
            return True

        return False

    # --- Write Operations: Messages ---

    async def add_message(
        self,
        conversation_id: uuid.UUID,
        role: str,
        content: str,
        input_method: str = "text",
        artifacts: Optional[dict] = None
    ) -> AIMessage:
        """Add a message to a conversation."""
        message = AIMessage(
            conversation_id=conversation_id,
            role=role,
            content=content,
            input_method=input_method,
            artifacts=artifacts
        )
        self.session.add(message)
        await self.session.commit()
        return message

    # --- Write Operations: Delete ---

    async def update_timestamp(
        self,
        conversation_id: uuid.UUID
    ) -> None:
        """Update conversation's updated_at timestamp to current time."""
        await self.session.execute(
            update(AIConversation)
            .where(AIConversation.id == conversation_id)
            .values(updated_at=func.now())
        )
        await self.session.commit()

    async def delete_conversation(
        self,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID
    ) -> bool:
        """
        Delete a conversation and all its messages (cascade).
        Returns True if deleted, False if not found.
        """
        stmt = select(AIConversation).where(
            AIConversation.id == conversation_id,
            AIConversation.user_id == user_id
        )
        result = await self.session.execute(stmt)
        conversation = result.scalar_one_or_none()

        if conversation:
            await self.session.delete(conversation)
            await self.session.commit()
            return True

        return False
```

## File: src/infrastructure/persistence/postgres/repos/invoices_repo.py
```python
"""Repository for billing invoices."""

import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy import select, desc

from src.infrastructure.persistence.postgres.models import Invoice


class InvoicesRepository:
    """Repository for invoice database operations."""

    def __init__(self, session):
        self.session = session

    # --- Read Operations ---

    async def get_invoice(
        self,
        invoice_id: uuid.UUID,
        user_id: uuid.UUID
    ) -> Optional[Invoice]:
        """Fetch a single invoice by ID, ensuring user ownership."""
        stmt = select(Invoice).where(
            Invoice.id == invoice_id,
            Invoice.user_id == user_id
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_invoice_by_external_id(
        self,
        external_invoice_id: str
    ) -> Optional[Invoice]:
        """Fetch an invoice by external invoice ID (Stripe/Razorpay)."""
        stmt = select(Invoice).where(
            Invoice.external_invoice_id == external_invoice_id
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_invoices(
        self,
        user_id: uuid.UUID,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[List[Invoice], int]:
        """
        List invoices for a user with pagination.

        Returns:
            (invoices, total_count)
        """
        # Get total count
        from sqlalchemy import func
        count_stmt = select(func.count()).where(Invoice.user_id == user_id)
        count_result = await self.session.execute(count_stmt)
        total = count_result.scalar()

        # Get paginated results
        stmt = (
            select(Invoice)
            .where(Invoice.user_id == user_id)
            .order_by(desc(Invoice.period_end))
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await self.session.execute(stmt)
        invoices = list(result.scalars().all())

        return invoices, total

    async def list_invoices_by_subscription(
        self,
        subscription_id: uuid.UUID,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[List[Invoice], int]:
        """
        List invoices for a specific subscription.

        Returns:
            (invoices, total_count)
        """
        from sqlalchemy import func

        # Get total count
        count_stmt = select(func.count()).where(Invoice.subscription_id == subscription_id)
        count_result = await self.session.execute(count_stmt)
        total = count_result.scalar()

        # Get paginated results
        stmt = (
            select(Invoice)
            .where(Invoice.subscription_id == subscription_id)
            .order_by(desc(Invoice.period_end))
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await self.session.execute(stmt)
        invoices = list(result.scalars().all())

        return invoices, total

    # --- Write Operations ---

    async def create_invoice(
        self,
        subscription_id: uuid.UUID,
        user_id: uuid.UUID,
        gateway: str,
        external_invoice_id: Optional[str],
        external_subscription_id: Optional[str],
        amount_paid: int,
        currency: str,
        status: str,
        invoice_pdf_url: Optional[str],
        hosted_invoice_url: Optional[str],
        period_start: datetime,
        period_end: datetime
    ) -> Invoice:
        """Create a new invoice record."""
        invoice = Invoice(
            subscription_id=subscription_id,
            user_id=user_id,
            gateway=gateway,
            external_invoice_id=external_invoice_id,
            external_subscription_id=external_subscription_id,
            amount_paid=amount_paid,
            currency=currency,
            status=status,
            invoice_pdf_url=invoice_pdf_url,
            hosted_invoice_url=hosted_invoice_url,
            period_start=period_start,
            period_end=period_end
        )
        self.session.add(invoice)
        await self.session.commit()
        return invoice

    async def update_invoice_status(
        self,
        invoice_id: uuid.UUID,
        status: str
    ) -> bool:
        """Update invoice status."""
        stmt = select(Invoice).where(Invoice.id == invoice_id)
        result = await self.session.execute(stmt)
        invoice = result.scalar_one_or_none()

        if invoice:
            invoice.status = status
            await self.session.commit()
            return True

        return False
```

## File: src/infrastructure/persistence/postgres/repos/patients_repo.py
```python
import uuid
from datetime import date
from typing import Optional, List
from sqlalchemy import select, delete, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.persistence.postgres.models import Patient


class PatientsRepository:
    """Repository for patient database operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    # --- Read Operations ---

    async def get_by_id(
        self,
        patient_id: uuid.UUID,
        user_id: uuid.UUID
    ) -> Optional[Patient]:
        """Fetches patient by ID, ensuring user ownership."""
        stmt = select(Patient).where(
            Patient.id == patient_id,
            Patient.user_id == user_id
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_user(
        self,
        user_id: uuid.UUID,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[List[Patient], int]:
        """
        Returns paginated list of patients for user.
        Supports optional search by full_name.
        Returns (items, total_count).
        """
        # Base filter
        filters = [Patient.user_id == user_id]
        if search:
            filters.append(Patient.full_name.ilike(f"%{search}%"))

        # Count total
        count_stmt = select(func.count(Patient.id)).where(*filters)
        count_result = await self.session.execute(count_stmt)
        total = count_result.scalar()

        # Fetch page
        offset = (page - 1) * page_size
        stmt = (
            select(Patient)
            .where(*filters)
            .order_by(Patient.created_at.desc())
            .limit(page_size)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        items = list(result.scalars().all())

        return items, total

    async def find_by_email_or_identifier(
        self,
        user_id: uuid.UUID,
        email: Optional[str] = None,
        identifier: Optional[str] = None
    ) -> Optional[Patient]:
        """Checks if a patient already exists with the same email or identifier."""
        if not email and not identifier:
            return None

        from sqlalchemy import or_
        stmt = select(Patient).where(
            Patient.user_id == user_id,
            or_(
                Patient.email == email if email else False,
                Patient.identifier == identifier if identifier else False
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    # --- Write Operations ---

    async def create(
        self,
        user_id: uuid.UUID,
        full_name: str,
        identifier: Optional[str] = None,
        date_of_birth: Optional[date] = None,
        gender: Optional[str] = None,
        email: Optional[str] = None
    ) -> Patient:
        """Creates a new patient."""
        patient = Patient(
            user_id=user_id,
            full_name=full_name,
            identifier=identifier,
            date_of_birth=date_of_birth,
            gender=gender,
            email=email
        )
        self.session.add(patient)
        await self.session.commit()
        await self.session.refresh(patient)
        return patient

    async def update(
        self,
        patient_id: uuid.UUID,
        data: dict
    ) -> bool:
        """
        Updates patient fields.
        Only updates fields that exist on the model and have non-None values.
        Supports: full_name, identifier, date_of_birth, gender, email.
        """
        stmt = select(Patient).where(Patient.id == patient_id)
        result = await self.session.execute(stmt)
        patient = result.scalar_one_or_none()

        if patient:
            for key, value in data.items():
                if hasattr(patient, key) and value is not None:
                    setattr(patient, key, value)
            await self.session.commit()
            await self.session.refresh(patient)
            return True

        return False

    async def delete(self, patient_id: uuid.UUID) -> bool:
        """Deletes a patient by ID."""
        stmt = delete(Patient).where(Patient.id == patient_id)
        await self.session.execute(stmt)
        await self.session.commit()
        return True
```

## File: src/core/logging.py
```python
import datetime as dt
import json
import logging
import sys
from typing import Any

from src.core.config import settings
from src.core.context import get_trace_id, get_user_id
from src.utils.common import serialize_for_json


# Standard logging attributes to exclude when extracting 'extra' data
STANDARD_KEYS = {
    "args",
    "asctime",
    "created",
    "exc_info",
    "exc_text",
    "filename",
    "funcName",
    "levelname",
    "levelno",
    "lineno",
    "module",
    "msecs",
    "message",
    "msg",
    "name",
    "pathname",
    "process",
    "processName",
    "relativeCreated",
    "stack_info",
    "thread",
    "threadName",
    "taskName",
}


class JSONFormatter(logging.Formatter):
    """
    Formats logs as a flat JSON structure for production observability.
    Automatically injects Trace ID and User ID from context.
    """

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "trace_id": get_trace_id(),
            "user_id": get_user_id(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Merge extra fields passed via extra={...}
        for key, value in record.__dict__.items():
            if key not in STANDARD_KEYS:
                log_data[key] = serialize_for_json(value)

        # Handle exceptions
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data, default=str)


class TextFormatter(logging.Formatter):
    """
    Formats logs as readable text for local development.
    Format: [TIME] LEVEL [TRACE_ID] [USER_ID] [MODULE:LINE] MESSAGE | EXTRA
    """

    def format(self, record: logging.LogRecord) -> str:
        timestamp = self.formatTime(record, "%H:%M:%S")
        trace_id = get_trace_id() or "system"
        user_id = get_user_id()

        # Build user_id part of log
        user_part = f"[{user_id}]" if user_id else "[--]"

        # Base log string
        log_msg = (
            f"[{timestamp}] {record.levelname:<8} "
            f"[{trace_id[:12]}] "
            f"{user_part} "
            f"[{record.module}:{record.lineno}] "
            f"{record.getMessage()}"
        )

        # Append extras
        extras = []
        for key, value in record.__dict__.items():
            if key not in STANDARD_KEYS:
                extras.append(f"{key}={value}")

        if extras:
            log_msg += f" | {' '.join(extras)}"

        if record.exc_info:
            log_msg += f"\n{self.formatException(record.exc_info)}"

        return log_msg


def setup_logging() -> None:
    """
    Configures the root logger based on environment settings.
    Should be called once at application startup.
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.WARNING)

    # Remove default handlers to avoid duplication
    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)

    # Select formatter based on config
    if settings.LOG_FORMAT.upper() == "JSON":
        handler.setFormatter(JSONFormatter())
    else:
        handler.setFormatter(TextFormatter())

    root_logger.addHandler(handler)

    # Enable logs for application code
    logging.getLogger("src").setLevel(settings.LOG_LEVEL)

    # Configure uvicorn logs
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

    # Silence noisy third-party loggers
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("langchain").setLevel(logging.WARNING)
    logging.getLogger("celery").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Factory to get a configured logger instance."""
    return logging.getLogger(name)
```

## File: src/core/middleware.py
```python
import time
import uuid
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from src.core.context import request_id_ctx
from src.core.logging import get_logger


logger = get_logger(__name__)


class RequestContextMiddleware(BaseHTTPMiddleware):
    """
    Handles Request Tracing, Context, and Timing.

    1. Generates a unique Trace ID for every request
    2. Sets the ContextVar for logging visibility
    3. Logs request duration and status (reads user_id from request.state)
    4. Injects X-Trace-ID and X-Process-Time headers for frontend

    Note: user_id is stored in request.state by auth deps because BaseHTTPMiddleware
    creates a new async context where ContextVars set in call_next() aren't visible.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.perf_counter()

        # 1. Generate Trace ID (32-char hex)
        trace_id = uuid.uuid4().hex

        # 2. Set Context (Returns a token to reset later)
        token = request_id_ctx.set(trace_id)

        try:
            # 3. Process Request
            response = await call_next(request)

            # 4. Calculate duration
            duration = (time.perf_counter() - start_time) * 1000

            # 5. Inject Headers for Frontend Debugging
            response.headers["X-Trace-ID"] = trace_id
            response.headers["X-Process-Time"] = f"{duration:.2f}"

            # 6. Log Success (includes user_id if authenticated)
            user_id = getattr(request.state, "user_id", None)
            logger.info(
                "Request finished",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration_ms": round(duration, 2),
                    "client": request.client.host if request.client else None,
                    "user_id": user_id,
                },
            )
            return response

        except Exception as e:
            duration = (time.perf_counter() - start_time) * 1000
            user_id = getattr(request.state, "user_id", None)
            logger.error(
                "Request failed",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "duration_ms": round(duration, 2),
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "user_id": user_id,
                },
                exc_info=True,
            )
            raise

        finally:
            # 7. Cleanup Context (ContextVars automatically reset between requests)
            request_id_ctx.reset(token)
```

## File: src/dependencies/ai.py
```python
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
```

## File: src/infrastructure/persistence/postgres/repos/consultations_repo.py
```python
import uuid
from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import select, update, func, delete
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.persistence.postgres.models import Consultation, ConsultationTranscript


class ConsultationsRepository:
    """Repository for consultation and transcript database operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    # --- Read Operations: Consultation ---

    async def get_by_id(self, consultation_id: uuid.UUID) -> Optional[Consultation]:
        """Fetches consultation by ID."""
        stmt = select(Consultation).where(Consultation.id == consultation_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id_and_user(
        self,
        consultation_id: uuid.UUID,
        user_id: uuid.UUID
    ) -> Optional[Consultation]:
        """Fetches consultation by ID, ensuring user ownership."""
        stmt = select(Consultation).options(
            selectinload(Consultation.patient)
        ).where(
            Consultation.id == consultation_id,
            Consultation.user_id == user_id
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_user(
        self,
        user_id: uuid.UUID,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[List[Consultation], int]:
        """
        Returns paginated list of consultations for user.
        Supports optional search by title.
        Returns (items, total_count).
        """
        # Base filter
        filters = [Consultation.user_id == user_id]
        if search:
            filters.append(Consultation.title.ilike(f"%{search}%"))

        # Count total
        count_stmt = select(func.count(Consultation.id)).where(*filters)
        count_result = await self.session.execute(count_stmt)
        total = count_result.scalar()

        # Fetch page with patient loaded
        offset = (page - 1) * page_size
        stmt = (
            select(Consultation)
            .options(selectinload(Consultation.patient))
            .where(*filters)
            .order_by(Consultation.updated_at.desc())
            .limit(page_size)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        items = list(result.scalars().all())

        return items, total

    async def list_by_patient(
        self,
        patient_id: uuid.UUID,
        user_id: uuid.UUID,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[List[Consultation], int]:
        """
        Returns paginated list of consultations for a specific patient.
        Ensures user ownership of both patient and consultations.
        Returns (items, total_count).
        """
        # Count total
        count_stmt = select(func.count(Consultation.id)).where(
            Consultation.user_id == user_id,
            Consultation.patient_id == patient_id
        )
        count_result = await self.session.execute(count_stmt)
        total = count_result.scalar()

        # Fetch page
        offset = (page - 1) * page_size
        stmt = (
            select(Consultation)
            .options(selectinload(Consultation.patient))
            .where(
                Consultation.user_id == user_id,
                Consultation.patient_id == patient_id
            )
            .order_by(Consultation.created_at.desc())
            .limit(page_size)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        items = list(result.scalars().all())

        return items, total

    # --- Read Operations: Transcript ---

    async def get_transcripts(
        self,
        consultation_id: uuid.UUID
    ) -> List[ConsultationTranscript]:
        """Fetches all transcripts for a consultation."""
        stmt = (
            select(ConsultationTranscript)
            .where(ConsultationTranscript.consultation_id == consultation_id)
            .order_by(ConsultationTranscript.created_at.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_transcripts_since(
        self,
        consultation_id: uuid.UUID,
        since_id: Optional[uuid.UUID]
    ) -> List[ConsultationTranscript]:
        """
        Fetches transcripts created after a specific transcript ID.
        If since_id is None, returns the most recent 20 transcripts.
        """
        if since_id is None:
            # First summary - get recent transcripts, ordered oldest to newest
            stmt = (
                select(ConsultationTranscript)
                .where(ConsultationTranscript.consultation_id == consultation_id)
                .order_by(ConsultationTranscript.created_at.desc())
                .limit(20)
            )
        else:
            # Incremental update - get transcripts after the last summarized one
            from sqlalchemy import select as sel
            last_transcript_stmt = sel(ConsultationTranscript.created_at).where(
                ConsultationTranscript.id == since_id
            )
            last_result = await self.session.execute(last_transcript_stmt)
            last_created_at = last_result.scalar_one_or_none()

            if last_created_at:
                stmt = (
                    select(ConsultationTranscript)
                    .where(
                        ConsultationTranscript.consultation_id == consultation_id,
                        ConsultationTranscript.created_at > last_created_at
                    )
                    .order_by(ConsultationTranscript.created_at.asc())
                )
            else:
                # Fallback: return all if since_id not found
                stmt = (
                    select(ConsultationTranscript)
                    .where(ConsultationTranscript.consultation_id == consultation_id)
                    .order_by(ConsultationTranscript.created_at.asc())
                )

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def has_new_transcripts(
        self,
        consultation_id: uuid.UUID,
        since_id: Optional[uuid.UUID]
    ) -> bool:
        """Checks if there are transcripts newer than the given ID."""
        if since_id is None:
            stmt = (
                select(func.count(ConsultationTranscript.id))
                .where(ConsultationTranscript.consultation_id == consultation_id)
            )
        else:
            last_transcript_stmt = select(ConsultationTranscript.created_at).where(
                ConsultationTranscript.id == since_id
            )
            last_result = await self.session.execute(last_transcript_stmt)
            last_created_at = last_result.scalar_one_or_none()

            if last_created_at:
                stmt = (
                    select(func.count(ConsultationTranscript.id))
                    .where(
                        ConsultationTranscript.consultation_id == consultation_id,
                        ConsultationTranscript.created_at >= last_created_at
                    )
                    .where(ConsultationTranscript.id != since_id)
                )
            else:
                # Fallback: if since_id not found, return False
                return False

        result = await self.session.execute(stmt)
        count = result.scalar()
        return count > 0

    # --- Write Operations: Consultation ---

    async def create(
        self,
        user_id: uuid.UUID,
        patient_id: Optional[uuid.UUID],
        title: str
    ) -> Consultation:
        """Creates a new consultation."""
        consultation = Consultation(
            user_id=user_id,
            patient_id=patient_id,
            title=title
        )
        self.session.add(consultation)
        await self.session.commit()
        await self.session.refresh(consultation)
        return consultation

    async def update(
        self,
        consultation_id: uuid.UUID,
        **fields
    ) -> bool:
        """
        Updates consultation fields.
        Supports: title, patient_id, clinical_summary_text, is_title_edited,
                  last_summarized_transcript_id, doctor_speaker_id.
        """
        stmt = (
            update(Consultation)
            .where(Consultation.id == consultation_id)
            .values(**fields)
        )
        await self.session.execute(stmt)
        await self.session.commit()
        return True

    async def delete(self, consultation_id: uuid.UUID) -> bool:
        """Deletes a consultation by ID."""
        stmt = delete(Consultation).where(Consultation.id == consultation_id)
        await self.session.execute(stmt)
        await self.session.commit()
        return True

    async def start_session(
        self,
        consultation_id: uuid.UUID
    ) -> bool:
        """Sets current_session_started_at to start billing timer."""
        stmt = (
            update(Consultation)
            .where(Consultation.id == consultation_id)
            .values(current_session_started_at=datetime.now(timezone.utc))
        )
        await self.session.execute(stmt)
        await self.session.commit()
        return True

    async def stop_session(
        self,
        consultation_id: uuid.UUID,
        duration_seconds: int
    ) -> bool:
        """
        Adds duration to total_audio_seconds and clears current_session_started_at.
        """
        stmt = (
            update(Consultation)
            .where(Consultation.id == consultation_id)
            .values(
                total_audio_seconds=Consultation.total_audio_seconds + duration_seconds,
                current_session_started_at=None
            )
        )
        await self.session.execute(stmt)
        await self.session.commit()
        return True

    # --- Write Operations: Transcript ---

    async def create_transcript(
        self,
        consultation_id: uuid.UUID,
        speaker_id: Optional[int],
        transcript: str
    ) -> ConsultationTranscript:
        """Creates a new transcript record."""
        record = ConsultationTranscript(
            consultation_id=consultation_id,
            speaker_id=speaker_id,
            transcript=transcript
        )
        self.session.add(record)
        await self.session.commit()
        await self.session.refresh(record)
        return record
```

## File: src/infrastructure/persistence/postgres/repos/user_repo.py
```python
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.infrastructure.persistence.postgres.models import User, Clinic


class UserRepository:
    """Repository for user and clinic database operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    # --- Read Operations ---

    async def get_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        """Fetches a user by ID (without relations)."""
        stmt = select(User).where(User.id == user_id, User.deleted_at == None)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_with_details(self, user_id: uuid.UUID) -> Optional[User]:
        """
        Master read for user profile.
        Includes clinic and subscription relationships.
        Used by GET /auth/me.
        """
        stmt = (
            select(User)
            .where(User.id == user_id, User.deleted_at == None)
            .options(
                selectinload(User.clinic),
                selectinload(User.subscription)
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    # --- Write Operations: Profile Updates ---

    async def update_profile(self, user_id: uuid.UUID, data: Dict[str, Any]) -> Optional[User]:
        """Updates user profile fields (name, dob, gender, provider_id)."""
        stmt = select(User).where(User.id == user_id, User.deleted_at == None)
        result = await self.session.execute(stmt)
        user = result.scalar_one_or_none()

        if user:
            for key, value in data.items():
                if hasattr(user, key) and value is not None:
                    setattr(user, key, value)
            await self.session.commit()
            await self.session.refresh(user)

        return user

    async def update_clinic(self, user_id: uuid.UUID, data: Dict[str, Any]) -> Optional[Clinic]:
        """Updates clinic fields (name, address, location)."""
        stmt = select(Clinic).where(Clinic.user_id == user_id)
        result = await self.session.execute(stmt)
        clinic = result.scalar_one_or_none()

        if clinic:
            for key, value in data.items():
                if hasattr(clinic, key) and value is not None:
                    setattr(clinic, key, value)
            await self.session.commit()
            await self.session.refresh(clinic)

        return clinic

    # --- Write Operations: Assets (Signatures, Logos) ---

    async def update_signature_url(self, user_id: uuid.UUID, url: str) -> bool:
        """Updates user signature URL after S3 upload."""
        stmt = update(User).where(User.id == user_id).values(signature_url=url)
        await self.session.execute(stmt)
        await self.session.commit()
        return True

    async def update_clinic_logo_url(self, user_id: uuid.UUID, url: str) -> bool:
        """Updates clinic logo URL after S3 upload."""
        stmt = update(Clinic).where(Clinic.user_id == user_id).values(logo_url=url)
        await self.session.execute(stmt)
        await self.session.commit()
        return True

    # --- Write Operations: Preferences ---

    async def update_preferences(self, user_id: uuid.UUID, updates: Dict[str, Any]) -> bool:
        """
        Merges data into JSONB preferences column.
        Used for UI state like dismissed_modals, theme, etc.
        """
        stmt = select(User).where(User.id == user_id)
        result = await self.session.execute(stmt)
        user = result.scalar_one_or_none()

        if user:
            current_prefs = dict(user.preferences or {})
            current_prefs.update(updates)
            user.preferences = current_prefs
            await self.session.commit()
            return True
        return False

    # --- Write Operations: Lifecycle ---

    async def soft_delete(self, user_id: uuid.UUID) -> bool:
        """
        Soft-deletes user by setting deleted_at timestamp.
        User cannot login after this.
        """
        stmt = (
            update(User)
            .where(User.id == user_id)
            .values(
                deleted_at=datetime.now(timezone.utc),
                registration_status="deleted"
            )
        )
        await self.session.execute(stmt)
        await self.session.commit()
        return True
```

## File: src/infrastructure/persistence/redis/client.py
```python
from typing import Optional

import redis.asyncio as aioredis

from src.core.config import settings
from src.core.logging import get_logger

logger = get_logger(__name__)

# Global Redis client instance
_redis_client: Optional[aioredis.Redis] = None


async def init_redis() -> None:
    """
    Initialize the Redis connection pool.

    Should be called during application startup.
    Verifies connection immediately.
    """
    global _redis_client

    if _redis_client is not None:
        return

    try:
        _redis_client = await aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            max_connections=50,
        )
        # Verify connection immediately on startup
        await _redis_client.ping()
        logger.info(f"Connected to Redis")
    except Exception as e:
        logger.error(f"Failed to initialize Redis: {e}")
        raise


def get_redis_client() -> aioredis.Redis:
    """
    Get the Redis client instance directly.

    Used for non-dependency access (Celery tasks, utility functions).

    Raises RuntimeError if Redis has not been initialized.
    """
    global _redis_client
    if _redis_client is None:
        raise RuntimeError("Redis not initialized. Call init_redis() first.")
    return _redis_client


async def check_redis_connection() -> bool:
    """
    Verify Redis connectivity.

    Returns True if connection is successful, False otherwise.
    """
    try:
        client = get_redis_client()
        await client.ping()
        return True
    except Exception as e:
        logger.error(f"Redis connection check failed: {e}")
        return False


async def close_redis() -> None:
    """Close the Redis connection pool."""
    global _redis_client
    if _redis_client is not None:
        await _redis_client.aclose()
        _redis_client = None
        logger.info("Redis connection closed")
```

## File: src/infrastructure/persistence/redis/pubsub.py
```python
import json
from datetime import datetime, timezone
from typing import AsyncGenerator, Any, Dict

from redis.asyncio import Redis
from src.core.logging import get_logger

logger = get_logger(__name__)

class PubSubManager:
    def __init__(self, redis_client: Redis):
        self.redis = redis_client
        self.channel_prefix = "ws:user:"

    async def publish(self, user_id: str, event_type: str, data: Dict[str, Any]) -> None:
        """
        Publishes a message to a specific user's channel.
        Any service (Billing, Scribe, etc.) can call this.
        """
        channel = f"{self.channel_prefix}{user_id}"
        message = {
            "event_type": event_type,
            "data": data,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        await self.redis.publish(channel, json.dumps(message))
        logger.debug(f"Published event '{event_type}' to user {user_id}")

    async def subscribe(self, user_id: str) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Subscribes to a user's channel and yields messages as they arrive.
        This will be used by the WebSocket handler.
        """
        channel_name = f"{self.channel_prefix}{user_id}"
        pubsub = self.redis.pubsub()
        await pubsub.subscribe(channel_name)
        
        logger.info(f"Subscribed to Redis channel: {channel_name}")

        try:
            async for message in pubsub.listen():
                if message["type"] == "message":
                    # Parse JSON to ensure it's valid before yielding
                    data = json.loads(message["data"])
                    # Ensure event_type exists for backward compatibility
                    if "event" in data and "event_type" not in data:
                        data["event_type"] = data["event"]
                        del data["event"]
                    yield data
        finally:
            try:
                await pubsub.unsubscribe(channel_name)
                await pubsub.close()
                logger.info(f"Unsubscribed from Redis channel: {channel_name}")
            except Exception as e:
                logger.debug(f"Error during pubsub cleanup (connection likely already closed): {e}")
```

## File: src/infrastructure/persistence/redis/sessions.py
```python
import json
import uuid
from typing import Optional, Dict, Any
from redis.asyncio import Redis

class SessionManager:
    def __init__(self, redis_client: Redis):
        self.redis = redis_client
        self.prefix = "session:"
        self.ttl = 86400  

    async def create_session(
        self, 
        token: str, 
        user_id: uuid.UUID, 
        role: str
    ) -> None:
        """Stores session data in Redis with a 24h expiry."""
        key = f"{self.prefix}{token}"
        data = {
            "user_id": str(user_id),
            "role": role
        }
        await self.redis.set(key, json.dumps(data), ex=self.ttl)

    async def get_session(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves session data and refreshes the TTL (Sliding Window).
        Returns None if session is expired or invalid.
        """
        key = f"{self.prefix}{token}"
        data = await self.redis.get(key)
        
        if not data:
            return None

        # Refresh the 24h timer every time the session is used
        await self.redis.expire(key, self.ttl)
        return json.loads(data)

    async def delete_session(self, token: str) -> None:
        """Removes the session from Redis (Logout)."""
        await self.redis.delete(f"{self.prefix}{token}")
```

## File: src/core/security.py
```python
import asyncio
import secrets
import bcrypt

from src.core.logging import get_logger

logger = get_logger(__name__)


# Password hashing

def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.
    Args:
        password: Plain text password
    Returns:
        Hashed password as a string
    """
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """
    Verify a plain password against a hashed password.

    Args:
        plain: Plain text password to verify
        hashed: Hashed password to compare against

    Returns:
        True if password matches, False otherwise
    """
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


async def verify_password_async(plain: str, hashed: str) -> bool:
    """
    Async wrapper for verify_password.

    Use this in async routes to avoid greenlet_spawn errors.

    Args:
        plain: Plain text password to verify
        hashed: Hashed password to compare against

    Returns:
        True if password matches, False otherwise
    """
    return await asyncio.to_thread(verify_password, plain, hashed)


# Session tokens (opaque tokens for Redis)

def generate_session_token() -> str:
    """
    Generate a cryptographically secure random session token.

    Returns a 32-byte hex string (64 characters) suitable for use as an opaque token.
    This token will be stored in Redis with the user_id as the value.

    Returns:
        Random session token
    """
    return secrets.token_hex(32)
```

## File: src/infrastructure/persistence/postgres/repos/auth_repo.py
```python
import uuid
from typing import Optional, Dict, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.infrastructure.persistence.postgres.models import User, Clinic, Subscription

class AuthRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    # --- Read Operations ---

    async def get_by_email(self, email: str) -> Optional[User]:
        """
        Fetches a user by email for login verification. Includes subscription.
        """
        stmt = (
            select(User)
            .where(User.email == email, User.deleted_at == None)
            .options(selectinload(User.subscription))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()


    # --- Transactional Write Operations ---

    async def create_standard_user(
        self, 
        user_data: Dict[str, Any], 
        clinic_data: Dict[str, Any], 
        sub_data: Dict[str, Any]
    ) -> User:
        """
        Atomic transaction to create a full account.
        Used for Email/Password registration.
        """
        # 1. Create User Instance
        new_user = User(**user_data)
        self.session.add(new_user)
        await self.session.flush() 

        # 2. Create Clinic
        new_clinic = Clinic(user_id=new_user.id, **clinic_data)
        self.session.add(new_clinic)

        # 3. Create Subscription
        new_sub = Subscription(user_id=new_user.id, **sub_data)
        self.session.add(new_sub)

        # Commit is handled by the caller (Service/Middleware) or here
        await self.session.commit()
        await self.session.refresh(new_user)
        return new_user

    async def create_partial_google_user(self, email: str, first_name: str, last_name: str) -> User:
        """
        Creates a shell user for Google signups who still need to finish onboarding.
        """
        new_user = User(
            email=email,
            first_name=first_name,
            last_name=last_name,
            auth_provider="google",
            registration_status="pending_details"
        )
        self.session.add(new_user)
        await self.session.commit()
        await self.session.refresh(new_user)
        return new_user

    async def complete_google_onboarding(
        self, 
        user_id: uuid.UUID, 
        user_update_data: Dict[str, Any],
        clinic_data: Dict[str, Any], 
        sub_data: Dict[str, Any]
    ) -> User:
        """
        Updates the partial Google user and creates their clinic/subscription.
        """
        # 1. Fetch and Update User
        stmt = select(User).where(User.id == user_id)
        result = await self.session.execute(stmt)
        user = result.scalar_one()

        for key, value in user_update_data.items():
            setattr(user, key, value)
        
        user.registration_status = "completed"

        # 2. Create Clinic
        new_clinic = Clinic(user_id=user.id, **clinic_data)
        self.session.add(new_clinic)

        # 3. Create Subscription
        new_sub = Subscription(user_id=user.id, **sub_data)
        self.session.add(new_sub)

        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def update_password(self, user_id: uuid.UUID, password_hash: str) -> bool:
        """
        Updates the password hash for a specific user.
        """
        stmt = select(User).where(User.id == user_id)
        result = await self.session.execute(stmt)
        user = result.scalar_one_or_none()

        if user:
            user.password_hash = password_hash
            await self.session.commit()
            return True
        return False
```

## File: src/infrastructure/persistence/postgres/repos/billing_repo.py
```python
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.persistence.postgres.models import Subscription


class BillingRepository:
    """Repository for subscription and billing database operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    # --- Read Operations ---

    async def get_by_user(self, user_id: uuid.UUID) -> Optional[Subscription]:
        """Fetches subscription record for a user."""
        stmt = select(Subscription).where(Subscription.user_id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_customer_id(self, customer_id: str, gateway: str) -> Optional[Subscription]:
        """Finds subscription by payment gateway customer ID."""
        stmt = select(Subscription).where(
            Subscription.external_customer_id == customer_id,
            Subscription.gateway == gateway
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    # --- Write Operations: Plan Changes ---

    async def activate_pro_plan(
        self,
        user_id: uuid.UUID,
        subscription_id: str,
        period_start: datetime,
        period_end: datetime,
        card_details: Optional[Dict[str, str]] = None,
        customer_id: Optional[str] = None
    ) -> bool:
        """
        Upgrades user to Copilot Pro after successful payment.
        Clears pending checkout session ID and stores customer_id from webhook.
        """
        stmt = (
            update(Subscription)
            .where(Subscription.user_id == user_id)
            .values(
                plan_type="copilot_pro",
                status="active",
                external_subscription_id=subscription_id,
                external_customer_id=customer_id,
                pending_checkout_session_id=None,
                current_period_start=period_start,
                current_period_end=period_end,
                card_brand=card_details.get("brand") if card_details else None,
                card_last4=card_details.get("last4") if card_details else None
            )
        )
        await self.session.execute(stmt)
        await self.session.commit()
        return True

    async def downgrade_to_free_tier(
        self,
        user_id: uuid.UUID,
        period_start: datetime,
        period_end: datetime
    ) -> bool:
        """
        Reverts user to free tier after subscription ends.
        Clears all payment gateway data.
        """
        stmt = (
            update(Subscription)
            .where(Subscription.user_id == user_id)
            .values(
                plan_type="free_tier",
                status="active",
                gateway="none",
                external_subscription_id=None,
                pending_checkout_session_id=None,
                card_brand=None,
                card_last4=None,
                current_period_start=period_start,
                current_period_end=period_end
            )
        )
        await self.session.execute(stmt)
        await self.session.commit()
        return True

    # --- Write Operations: Status Updates ---

    async def update_status(self, user_id: uuid.UUID, status: str) -> bool:
        """Updates subscription status (active, past_due, canceled)."""
        stmt = (
            update(Subscription)
            .where(Subscription.user_id == user_id)
            .values(status=status)
        )
        await self.session.execute(stmt)
        await self.session.commit()
        return True

    async def set_canceled_status(self, user_id: uuid.UUID) -> bool:
        """
        Marks subscription as canceled (manual cancellation).
        User retains access until period_end. Cron will downgrade later.
        """
        stmt = (
            update(Subscription)
            .where(Subscription.user_id == user_id)
            .values(status="canceled")
        )
        await self.session.execute(stmt)
        await self.session.commit()
        return True

    # --- Write Operations: Checkout ---

    async def set_pending_checkout(
        self,
        user_id: uuid.UUID,
        gateway: str,
        external_customer_id: str,
        pending_checkout_session_id: str
    ) -> bool:
        """Sets pending checkout details when user initiates Pro upgrade."""
        stmt = (
            update(Subscription)
            .where(Subscription.user_id == user_id)
            .values(
                gateway=gateway,
                external_customer_id=external_customer_id,
                pending_checkout_session_id=pending_checkout_session_id
            )
        )
        await self.session.execute(stmt)
        await self.session.commit()
        return True

    async def clear_pending_checkout(self, user_id: uuid.UUID) -> bool:
        """Clears pending checkout session ID when user abandons checkout."""
        stmt = (
            update(Subscription)
            .where(Subscription.user_id == user_id)
            .values(pending_checkout_session_id=None)
        )
        await self.session.execute(stmt)
        await self.session.commit()
        return True

    # --- Cron Operations ---

    async def renew_free_plans(self) -> int:
        """
        Cron job: Bulk renew free-tier and trial subscriptions expiring within 1 hour.

        Returns:
            Number of subscriptions renewed.

        Note:
            Pro users are NOT handled here - Stripe webhooks manage their renewal.
        """
        now = datetime.now(timezone.utc)
        expiry_threshold = now + timedelta(hours=1)

        stmt = (
            update(Subscription)
            .where(
                Subscription.plan_type.in_(["free_tier", "free_trial"]),
                Subscription.current_period_end <= expiry_threshold
            )
            .values(
                current_period_start=now,
                current_period_end=now + timedelta(days=30),
                plan_type="free_tier",
                status="active"
            )
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount
```

## File: src/infrastructure/persistence/s3/client.py
```python
import mimetypes
from typing import Optional, TYPE_CHECKING
import aioboto3
from botocore.config import Config
from src.core.config import settings

if TYPE_CHECKING:
    from aiobotocore.client import AioBaseClient
    S3ServiceClient = AioBaseClient

class S3Client:
    """
    S3-Compatible Storage Client (Optimized for Backblaze B2).
    Handles secure file uploads and time-limited URL generation.
    """

    def __init__(self):
        self.bucket_name: str = settings.S3_BUCKET_NAME
        self.session = aioboto3.Session()

        # Backblaze requires specific config for S3 compatibility
        self.client_config = Config(
            signature_version='s3v4',
            retries={'max_attempts': 3, 'mode': 'standard'}
        )

    def _get_client(self):
        """Internal helper to create the async client context."""
        return self.session.client(
            's3',
            endpoint_url=settings.S3_ENDPOINT_URL,
            aws_access_key_id=settings.S3_ACCESS_KEY_ID,
            aws_secret_access_key=settings.S3_SECRET_ACCESS_KEY,
            region_name=settings.S3_REGION,
            config=self.client_config
        )

    # --- Core Operations ---

    async def generate_presigned_url(self, object_key: Optional[str], expires_in: int = 3600) -> Optional[str]:
        """
        Generates a secure, temporary URL for a private file.
        Default expiry is 1 hour.
        """
        if not object_key:
            return None

        async with self._get_client() as s3:
            # Type hint the dynamic s3 client
            s3_client: "S3ServiceClient" = s3
            return await s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': object_key},
                ExpiresIn=expires_in
            )

    async def upload_file(self, content: bytes, object_key: str, content_type: Optional[str] = None) -> str:
        """
        Uploads binary data to the bucket and returns the object key.
        Guesses content_type from object_key if not provided.
        """
        if not content_type:
            content_type, _ = mimetypes.guess_type(object_key)
            content_type = content_type or 'application/octet-stream'

        async with self._get_client() as s3:
            s3_client: "S3ServiceClient" = s3
            await s3_client.put_object(
                Bucket=self.bucket_name,
                Key=object_key,
                Body=content,
                ContentType=content_type
            )
            return object_key

    async def delete_file(self, object_key: str):
        """Removes a file from the bucket."""
        async with self._get_client() as s3:
            s3_client: "S3ServiceClient" = s3
            await s3_client.delete_object(Bucket=self.bucket_name, Key=object_key)

    async def download_file(self, object_key: str) -> bytes:
        """Downloads a file from the bucket and returns its content as bytes."""
        async with self._get_client() as s3:
            s3_client: "S3ServiceClient" = s3
            response = await s3_client.get_object(Bucket=self.bucket_name, Key=object_key)
            return await response['Body'].read()
```

## File: src/core/config.py
```python
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Core Application
    PROJECT_NAME: str = "Medical Copilot Extension API"
    API_V1_PREFIX: str = "/api/v1"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    PORT: int = 8000
    HOST: str = "0.0.0.0"

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["*"]

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "JSON"

    # Database
    DATABASE_URL: str

    # Redis & Celery
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: Optional[str] = None
    CELERY_RESULT_BACKEND: Optional[str] = None

    # AI/LLM - Providers
    GROQ_API_KEY: str
    GEMINI_API_KEY: Optional[str] = None

    # Fast LLM (Routing, Extraction, Nudges)
    FAST_LLM_PROVIDER: str = "groq"
    FAST_LLM_MODEL: str = "openai/gpt-oss-20b"
    FAST_LLM_TEMP: float = 0.2
    FAST_LLM_FALLBACK_PROVIDER: str = "google"
    FAST_LLM_FALLBACK_MODEL: str = "gemini-3-flash-preview"

    # Tiny LLM (Quick operations, structured output)
    TINY_LLM_PROVIDER: str = "groq"
    TINY_LLM_MODEL: str = "llama-3.3-8b-instant"
    TINY_LLM_TEMP: float = 0.2
    TINY_LLM_FALLBACK_PROVIDER: str = "groq"
    TINY_LLM_FALLBACK_MODEL: str = "gemma2-9b-it"

    # Smart LLM (Clinical Reasoning, Synthesis)
    SMART_LLM_PROVIDER: str = "groq"
    SMART_LLM_MODEL: str = "openai/gpt-oss-120b"
    SMART_LLM_TEMP: float = 0.3
    SMART_LLM_FALLBACK_PROVIDER: str = "google"
    SMART_LLM_FALLBACK_MODEL: str = "gemini-3-flash-preview"

    # External APIs
    DEEPGRAM_API_KEY: str
    BRAVE_SEARCH_API_KEY: Optional[str] = None

    # S3 Storage
    S3_ENDPOINT_URL: str
    S3_BUCKET_NAME: str
    S3_ACCESS_KEY_ID: str
    S3_SECRET_ACCESS_KEY: str
    S3_REGION: str = "us-east-1"

    # Stripe
    STRIPE_SECRET_KEY: str
    STRIPE_WEBHOOK_SECRET: str
    STRIPE_PRO_PLAN_ID: str

    # Razorpay
    RAZORPAY_KEY_ID: str
    RAZORPAY_KEY_SECRET: str
    RAZORPAY_WEBHOOK_SECRET: str
    RAZORPAY_PRO_PLAN_ID: str

    # Payment (shared for Stripe & Razorpay)
    PAYMENT_SUCCESS_URL: str
    PAYMENT_CANCEL_URL: str
    
    # Limits
    FREE_TRIAL_DAYS: int = 7
    FREE_SCRIBE_LIMIT_MINUTES: int = 400
    TRIAL_SCRIBE_LIMIT_MINUTES: int = 800
    PRO_SCRIBE_LIMIT_MINUTES: int = 6000

    # Auth
    SESSION_EXPIRY_SECONDS: int = 86400

    # Email (Brevo)
    BREVO_API_KEY: str
    EMAIL_FROM_ADDRESS: str
    EMAIL_FROM_NAME: str
    FRONTEND_URL: str  # For password reset links, etc.

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
```

## File: src/core/exceptions.py
```python
from typing import Any, Dict, Optional

from fastapi import HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from src.core.logging import get_logger

logger = get_logger(__name__)


# --- Custom Exception Classes ---

class AppException(Exception):
    """Base exception for application-specific errors."""

    def __init__(
        self,
        message: str,
        code: str = "APP_ERROR",
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)


class NotFoundException(AppException):
    """Resource not found."""

    def __init__(self, message: str = "Resource not found", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
            details=details,
        )


class BadRequestException(AppException):
    """Bad request - invalid input or business logic violation."""

    def __init__(self, message: str = "Bad request", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="BAD_REQUEST",
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details,
        )


class UnauthorizedException(AppException):
    """Unauthorized - authentication required."""

    def __init__(self, message: str = "Unauthorized", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="UNAUTHORIZED",
            status_code=status.HTTP_401_UNAUTHORIZED,
            details=details,
        )


class ForbiddenException(AppException):
    """Forbidden - insufficient permissions."""

    def __init__(self, message: str = "Forbidden", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="FORBIDDEN",
            status_code=status.HTTP_403_FORBIDDEN,
            details=details,
        )


class ConflictException(AppException):
    """Conflict - resource already exists or state conflict."""

    def __init__(self, message: str = "Conflict", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="CONFLICT",
            status_code=status.HTTP_409_CONFLICT,
            details=details,
        )


class RateLimitException(AppException):
    """Rate limit exceeded."""

    def __init__(self, message: str = "Rate limit exceeded", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="RATE_LIMIT_EXCEEDED",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            details=details,
        )


class UsageLimitException(AppException):
    """Usage quota exceeded - user needs to upgrade plan."""

    def __init__(
        self,
        message: str = "Usage limit exceeded",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            code="USAGE_LIMIT_EXCEEDED",
            status_code=status.HTTP_403_FORBIDDEN,
            details=details,
        )


# --- Exception Handlers ---

async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    Handles FastAPI request validation errors.

    Logs detailed validation errors for debugging.
    Returns a clean 422 response to the client.
    """
    errors = exc.errors()

    logger.warning(
        f"Validation error: {request.method} {request.url.path}",
        extra={
            "validation_errors": errors,
            "error_count": len(errors),
            "body": exc.body if hasattr(exc, "body") else None,
        },
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "code": "VALIDATION_ERROR",
            "message": "Request validation failed",
            "errors": errors,
        },
    )


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """
    Handles application-specific exceptions.

    Returns a structured error response with error code and details.
    """
    logger.error(
        f"Application error: {request.method} {request.url.path}",
        extra={
            "error_code": exc.code,
            "error_message": exc.message,
            "error_details": exc.details,
        },
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": exc.code,
            "message": exc.message,
            "details": exc.details if exc.details else None,
        },
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Catches all unhandled exceptions.

    Logs the full exception traceback.
    Returns a generic 500 error response (doesn't expose internal details).
    """
    logger.error(
        f"Unhandled exception: {request.method} {request.url.path}",
        extra={
            "error_type": type(exc).__name__,
            "error_message": str(exc),
        },
        exc_info=True,
    )

    # Don't expose internal error details in production
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "code": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected error occurred. Please try again later.",
        },
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """
    Handles FastAPI HTTPExceptions.

    Provides consistent error response format.
    """
    logger.warning(
        f"HTTP exception: {request.method} {request.url.path}",
        extra={
            "status_code": exc.status_code,
            "detail": exc.detail,
        },
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": f"HTTP_{exc.status_code}",
            "message": exc.detail,
        },
    )


# --- Helper Functions ---

def setup_exception_handlers(app) -> None:
    """
    Register all exception handlers with the FastAPI app.

    Call this in main.py after creating the app instance.
    """
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
```

## File: src/infrastructure/external/razorpay.py
```python
import time
import razorpay
import uuid
from typing import Dict, Any, Optional, TYPE_CHECKING

from src.core.config import settings
from src.core.exceptions import BadRequestException
from src.core.logging import get_logger
from src.schemas.features.billing import RazorpayWebhookData

if TYPE_CHECKING:
    from razorpay.resources import Customer, Subscription
    from razorpay.utility import Utility

logger = get_logger(__name__)


class RazorpayClient:
    """
    Razorpay Wrapper for March 2026 API.
    Handles Subscriptions, Signature Verification, and event normalization.
    """

    def __init__(self):
        self.client = razorpay.Client(
            auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
        )
        # Type hints for dynamic attributes
        self.customer: "Customer" = self.client.customer
        self.subscription: "Subscription" = self.client.subscription
        self.utility: "Utility" = self.client.utility

    # --- SDK Methods ---

    async def create_subscription(self, user_id: str) -> Dict[str, str]:
        """
        Creates a subscription and returns the subscription_id.
        Razorpay creates customer automatically during checkout.
        """
        try:
            data = {
                "plan_id": settings.RAZORPAY_PRO_PLAN_ID,
                "total_count": 120,
                "quantity": 1,
                "customer_notify": 1,
                "notes": {"user_id": user_id}
            }
            subscription = self.subscription.create(data=data)

            return {
                "subscription_id": subscription['id']
            }
        except Exception as e:
            raise BadRequestException(message=f"Razorpay Subscription Error: {str(e)}")

    async def expire_checkout_session(self, subscription_id: str) -> bool:
        """Invalidates a pending subscription."""
        try:
            self.subscription.cancel(subscription_id)
            return True
        except Exception as e:
            logger.error(f"Failed to cancel Razorpay subscription {subscription_id}: {str(e)}")
            return False

    async def cancel_subscription(self, subscription_id: str) -> bool:
        """
        Cancels a subscription at the end of the current billing cycle.
        User retains access until period_end. Razorpay will send completion event then.
        """
        try:
            self.subscription.cancel(subscription_id, cancel_at_cycle_end=1)
            return True
        except Exception as e:
            logger.error(f"Failed to cancel Razorpay subscription {subscription_id}: {str(e)}")
            return False

    # --- Utility Methods ---

    def verify_webhook(self, payload: bytes, signature: str) -> bool:
        """Verifies the x-razorpay-signature."""
        try:
            return self.utility.verify_webhook_signature(
                signature,
                payload.decode('utf-8'),
                settings.RAZORPAY_WEBHOOK_SECRET
            )
        except Exception:
            raise BadRequestException("Invalid Razorpay Webhook Signature")

    def extract_user_id(self, subscription_entity: Dict[str, Any]) -> Optional[uuid.UUID]:
        """Robustly finds user_id in Razorpay notes."""
        user_id_str = subscription_entity.get("notes", {}).get("user_id")
        try:
            return uuid.UUID(user_id_str) if user_id_str else None
        except (ValueError, TypeError):
            return None

    def extract_card_details(self, payment_entity: Dict[str, Any]) -> Dict[str, str]:
        """Extracts brand and last4 from Razorpay payment entity."""
        card = payment_entity.get("card", {})
        if not card:
            return {"brand": "unknown", "last4": "xxxx"}

        return {
            "brand": card.get("network", "unknown"),
            "last4": card.get("last4", "xxxx"),
        }

    def parse_subscription_event(
        self,
        subscription_entity: Dict[str, Any],
        payment_entity: Dict[str, Any]
    ) -> Optional[RazorpayWebhookData]:
        """Normalizes a Razorpay subscription event."""
        user_id = self.extract_user_id(subscription_entity)
        if not user_id:
            return None

        return RazorpayWebhookData(
            user_id=user_id,
            customer_id=subscription_entity.get("customer_id"),
            subscription_id=subscription_entity.get("id"),
            period_start=subscription_entity.get("current_start"),
            period_end=subscription_entity.get("current_end"),
            card_details=self.extract_card_details(payment_entity)
        )
```

## File: src/infrastructure/external/stripe.py
```python
import stripe
import uuid
from typing import Optional, Dict, Any

from src.core.logging import get_logger
from src.core.config import settings
from src.core.exceptions import BadRequestException
from src.schemas.features.billing import StripeWebhookData

logger = get_logger(__name__)

# Initialize Stripe globally
stripe.api_key = settings.STRIPE_SECRET_KEY


class StripeClient:
    """
    Stripe Wrapper for March 2026 API.
    Handles Subscription Sessions, Metadata-driven verification, and event parsing.
    """

    # --- SDK Methods ---

    async def create_customer(self, email: str, name: str) -> str:
        """Creates a permanent customer object in Stripe."""
        customer = stripe.Customer.create(
            email=email,
            name=name,
            metadata={"source": "medical-copilot-ext"}
        )
        return customer.id

    async def create_subscription_session(
        self,
        customer_id: str,
        user_id: str,
    ) -> Dict[str, str]:
        """Creates a checkout session for the Copilot Pro plan."""
        try:
            session = stripe.checkout.Session.create(
                customer=customer_id,
                payment_method_types=['card'],
                line_items=[{
                    'price': settings.STRIPE_PRO_PLAN_ID,
                    'quantity': 1,
                }],
                mode='subscription',
                success_url=settings.PAYMENT_SUCCESS_URL,
                cancel_url=settings.PAYMENT_CANCEL_URL,
                subscription_data={
                    "metadata": {"user_id": user_id}
                },
                metadata={"user_id": user_id}
            )
            return {
                "checkout_url": session.url,
                "session_id": session.id
            }
        except stripe.error.StripeError as e:
            raise BadRequestException(message=f"Stripe Session Error: {str(e)}")

    async def get_card_details_from_invoice(self, invoice_id: str):
        try:
            payments = stripe.InvoicePayment.list(
                invoice=invoice_id,
                expand=["data.payment.payment_intent.payment_method"]
            )

            for p in payments.data:
                payment = p.payment

                if payment.type == "payment_intent":
                    pi = payment.payment_intent

                    if pi and pi.payment_method and pi.payment_method.card:
                        card = pi.payment_method.card
                        return {
                            "brand": card.brand,
                            "last4": card.last4
                        }

            invoice = stripe.Invoice.retrieve(
                invoice_id,
                expand=["default_payment_method"]
            )

            if invoice.default_payment_method and invoice.default_payment_method.card:
                card = invoice.default_payment_method.card
                return {
                    "brand": card.brand,
                    "last4": card.last4
                }

            return None

        except Exception as e:
            logger.error(f"Failed to get card details: {str(e)}")
            return None

    async def expire_checkout_session(self, session_id: str) -> bool:
        """Invalidates an active checkout session."""
        try:
            stripe.checkout.Session.expire(session_id)
            return True
        except Exception as e:
            logger.error(f"Failed to expire Stripe session {session_id}: {str(e)}")
            return False

    async def cancel_subscription(self, subscription_id: str) -> bool:
        """
        Cancels a subscription at the end of the current billing period.
        User retains access until period_end. Stripe will send deletion event then.
        """
        try:
            stripe.Subscription.modify(
                subscription_id,
                cancel_at_period_end=True
            )
            return True
        except Exception as e:
            logger.error(f"Failed to cancel Stripe subscription {subscription_id}: {str(e)}")
            return False

    # --- Utility Methods ---

    def verify_webhook(self, payload: bytes, sig_header: str) -> stripe.Event:
        """Validates that the event came from Stripe."""
        try:
            return stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
        except (ValueError, stripe.error.SignatureVerificationError):
            raise BadRequestException("Invalid Stripe Webhook Signature")

    def extract_user_id(self, data_object: Dict[str, Any]) -> Optional[uuid.UUID]:
        """Robustly finds user_id in Stripe metadata."""
        # 1. Try direct metadata
        user_id_str = data_object.get("metadata", {}).get("user_id")

        # 2. Try nested parent metadata (common in 2026 invoice events)
        if not user_id_str and "parent" in data_object:
            user_id_str = (
                data_object.get("parent", {})
                .get("subscription_details", {})
                .get("metadata", {})
                .get("user_id")
            )

        try:
            return uuid.UUID(user_id_str) if user_id_str else None
        except (ValueError, TypeError):
            return None

    async def parse_invoice_paid(self, data_object: Dict[str, Any]) -> Optional[StripeWebhookData]:
        """
        Normalizes a Stripe invoice.paid event.
        Returns both subscription data and invoice details.
        """
        user_id = self.extract_user_id(data_object)
        if not user_id:
            return None

        # Extract Subscription ID
        subscription_id = (
            data_object.get("parent", {})
            .get("subscription_details", {})
            .get("subscription")
        ) or data_object.get("subscription")

        # Get accurate period from line item
        lines = data_object.get("lines", {}).get("data", [])
        if lines:
            period = lines[0].get("period", {})
            period_start = period.get("start")
            period_end = period.get("end")
        else:
            period_start = data_object.get("period_start")
            period_end = data_object.get("period_end")

        card_details = await self.get_card_details_from_invoice(data_object.get("id"))

        return StripeWebhookData(
            # Subscription data
            user_id=user_id,
            customer_id=data_object.get("customer"),
            subscription_id=subscription_id,
            period_start=period_start,
            period_end=period_end,
            card_details=card_details,

            # Invoice data
            stripe_invoice_id=data_object.get("id"),
            amount_paid=data_object.get("amount_paid"),
            currency=data_object.get("currency"),
            status=data_object.get("status"),
            invoice_pdf_url=data_object.get("invoice_pdf"),
            hosted_invoice_url=data_object.get("hosted_invoice_url")
        )
```

## File: src/dependencies/auth.py
```python
import uuid
from typing import Annotated, Optional

from fastapi import Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from src.core.context import set_user_id
from src.core.exceptions import UnauthorizedException, ForbiddenException
from src.dependencies.infra import get_session_manager
from src.dependencies.repositories import get_user_repo
from src.infrastructure.persistence.postgres.repos.user_repo import UserRepository
from src.infrastructure.persistence.redis.sessions import SessionManager
from src.schemas.features.auth import CurrentUser

# Security scheme for FastAPI docs
security = HTTPBearer()


async def get_current_user(
    request: Request,
    token: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    session_manager: SessionManager = Depends(get_session_manager),
    user_repo: UserRepository = Depends(get_user_repo),
) -> CurrentUser:
    """
    Authenticate and return the current user.

    Flow:
    1. Extract Bearer token from Authorization header
    2. Look up session in Redis (refreshes TTL automatically)
    3. Fetch user from database and map to CurrentUser schema
    4. Set user_id in context for logging
    """
    token_value = token.credentials

    # 1. Look up session in Redis (SessionManager handles TTL refresh)
    session_data = await session_manager.get_session(token_value)
    if not session_data:
        raise UnauthorizedException(message="Invalid or expired session")

    # 2. Fetch user from database
    user_id = uuid.UUID(session_data["user_id"])
    user = await user_repo.get_with_details(user_id)

    # 3. Security Checks
    if not user:
        raise UnauthorizedException(message="User account no longer exists")

    if user.registration_status == "deleted":
        raise UnauthorizedException(message="Account has been deactivated")

    # 4. Set user_id in context for tracing/logging
    user_id_str = str(user.id)
    request.state.user_id = user_id_str
    set_user_id(user_id_str)

    # 5. Map to CurrentUser schema (clean API contract)
    return CurrentUser.model_validate(user)


async def get_current_doctor(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> CurrentUser:
    """
    Verify the current user is a doctor.
    """
    if current_user.role != "doctor":
        raise ForbiddenException(message="Access restricted to doctors")
    return current_user


async def get_current_admin(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> CurrentUser:
    """
    Verify the current user is an admin.
    """
    if current_user.role != "admin":
        raise ForbiddenException(message="Access restricted to administrators")
    return current_user


# --- Type Aliases for cleaner route signatures ---

CurrentUserDep = Annotated[CurrentUser, Depends(get_current_user)]
CurrentDoctorDep = Annotated[CurrentUser, Depends(get_current_doctor)]
CurrentAdminDep = Annotated[CurrentUser, Depends(get_current_admin)]


# --- WebSocket Authentication ---


async def get_ws_user_id(token: str, session_manager: SessionManager) -> Optional[str]:
    """
    Authenticates WebSocket connections via query token.
    Returns user_id or None if invalid.
    """
    session = await session_manager.get_session(token)
    if not session:
        return None
    return session.get("user_id")
```

## File: src/dependencies/infra.py
```python
"""
External infrastructure service dependencies for FastAPI routes.

Re-exports third-party service clients (Stripe, Razorpay, Google, S3).
"""

from typing import Annotated
from fastapi import Depends

from src.dependencies.db import get_redis
from src.infrastructure.external.google_oauth import GoogleClient
from src.infrastructure.external.google_files import GoogleFilesClient
from src.infrastructure.external.deepgram import DeepgramClient
from src.infrastructure.external.brave import BraveSearchClient
from src.infrastructure.external.stripe import StripeClient
from src.infrastructure.external.razorpay import RazorpayClient
from src.infrastructure.external.brevo import BrevoClient
from src.infrastructure.persistence.s3.client import S3Client
from src.infrastructure.persistence.redis.sessions import SessionManager
from src.infrastructure.persistence.redis.pubsub import PubSubManager


# --- Singleton Clients ---

_google_client: GoogleClient | None = None
_google_files_client: GoogleFilesClient | None = None
_deepgram_client: DeepgramClient | None = None
_brave_client: BraveSearchClient | None = None
_stripe_client: StripeClient | None = None
_razorpay_client: RazorpayClient | None = None
_brevo_client: BrevoClient | None = None
_s3_client: S3Client | None = None
_pubsub_manager: PubSubManager | None = None


def get_google_client() -> GoogleClient:
    """Provides Google OAuth client singleton."""
    global _google_client
    if _google_client is None:
        _google_client = GoogleClient()
    return _google_client


def get_google_files_client() -> GoogleFilesClient:
    """Provides Google Files client singleton."""
    global _google_files_client
    if _google_files_client is None:
        _google_files_client = GoogleFilesClient()
    return _google_files_client


def get_deepgram_client() -> DeepgramClient:
    """Provides Deepgram client singleton."""
    global _deepgram_client
    if _deepgram_client is None:
        _deepgram_client = DeepgramClient()
    return _deepgram_client


def get_stripe_client() -> StripeClient:
    """Provides Stripe client singleton."""
    global _stripe_client
    if _stripe_client is None:
        _stripe_client = StripeClient()
    return _stripe_client


def get_razorpay_client() -> RazorpayClient:
    """Provides Razorpay client singleton."""
    global _razorpay_client
    if _razorpay_client is None:
        _razorpay_client = RazorpayClient()
    return _razorpay_client


def get_brevo_client() -> BrevoClient:
    """Provides Brevo email client singleton."""
    global _brevo_client
    if _brevo_client is None:
        _brevo_client = BrevoClient()
    return _brevo_client


def get_s3_client() -> S3Client:
    """Provides S3 client singleton."""
    global _s3_client
    if _s3_client is None:
        _s3_client = S3Client()
    return _s3_client


def get_brave_client() -> BraveSearchClient:
    """Provides Brave Search client singleton."""
    global _brave_client
    if _brave_client is None:
        _brave_client = BraveSearchClient()
    return _brave_client


def get_session_manager(redis = Depends(get_redis)) -> SessionManager:
    """Provides Redis Session Manager."""
    return SessionManager(redis_client=redis)


def get_pubsub_manager(redis = Depends(get_redis)) -> PubSubManager:
    """Provides Redis PubSub Manager."""
    global _pubsub_manager
    if _pubsub_manager is None:
        _pubsub_manager = PubSubManager(redis_client=redis)
    return _pubsub_manager


# Type Aliases for cleaner route signatures
GoogleClientDep = Annotated[GoogleClient, Depends(get_google_client)]
GoogleFilesClientDep = Annotated[GoogleFilesClient, Depends(get_google_files_client)]
DeepgramClientDep = Annotated[DeepgramClient, Depends(get_deepgram_client)]
BraveClientDep = Annotated[BraveSearchClient, Depends(get_brave_client)]
StripeClientDep = Annotated[StripeClient, Depends(get_stripe_client)]
RazorpayClientDep = Annotated[RazorpayClient, Depends(get_razorpay_client)]
BrevoClientDep = Annotated[BrevoClient, Depends(get_brevo_client)]
S3ClientDep = Annotated[S3Client, Depends(get_s3_client)]
PubSubManagerDep = Annotated[PubSubManager, Depends(get_pubsub_manager)]
```

## File: src/dependencies/repositories.py
```python
from typing import Annotated
from fastapi import Depends

from src.dependencies.db import get_db_session
from src.infrastructure.persistence.postgres.repos.auth_repo import AuthRepository
from src.infrastructure.persistence.postgres.repos.user_repo import UserRepository
from src.infrastructure.persistence.postgres.repos.billing_repo import BillingRepository
from src.infrastructure.persistence.postgres.repos.consultations_repo import ConsultationsRepository
from src.infrastructure.persistence.postgres.repos.scribe_usage_logs_repo import ScribeUsageLogsRepository
from src.infrastructure.persistence.postgres.repos.patients_repo import PatientsRepository
from src.infrastructure.persistence.postgres.repos.templates_repo import TemplatesRepository
from src.infrastructure.persistence.postgres.repos.reports_repo import ReportsRepository
from src.infrastructure.persistence.postgres.repos.ai_conversations_repo import AIConversationsRepository
from src.infrastructure.persistence.postgres.repos.attachments_repo import AttachmentsRepository
from src.infrastructure.persistence.postgres.repos.invoices_repo import InvoicesRepository
from src.infrastructure.persistence.postgres.repos.email_logs_repo import EmailLogsRepository
from src.infrastructure.persistence.postgres.repos.password_resets_repo import PasswordResetsRepository
from src.infrastructure.persistence.postgres.repos.consultation_insights_repo import ConsultationInsightsRepository


# --- Repository Dependencies ---

async def get_auth_repo(session = Depends(get_db_session)) -> AuthRepository:
    """Provides AuthRepository with DB session."""
    return AuthRepository(session=session)


async def get_user_repo(session = Depends(get_db_session)) -> UserRepository:
    """Provides UserRepository with DB session."""
    return UserRepository(session=session)


async def get_billing_repo(session = Depends(get_db_session)) -> BillingRepository:
    """Provides BillingRepository with DB session."""
    return BillingRepository(session=session)


async def get_consultations_repo(session = Depends(get_db_session)) -> ConsultationsRepository:
    """Provides ConsultationsRepository with DB session."""
    return ConsultationsRepository(session=session)


async def get_scribe_usage_logs_repo(session = Depends(get_db_session)) -> ScribeUsageLogsRepository:
    """Provides ScribeUsageLogsRepository with DB session."""
    return ScribeUsageLogsRepository(session=session)


async def get_patients_repo(session = Depends(get_db_session)) -> PatientsRepository:
    """Provides PatientsRepository with DB session."""
    return PatientsRepository(session=session)


async def get_templates_repo(session = Depends(get_db_session)) -> TemplatesRepository:
    """Provides TemplatesRepository with DB session."""
    return TemplatesRepository(session=session)


async def get_reports_repo(session = Depends(get_db_session)) -> ReportsRepository:
    """Provides ReportsRepository with DB session."""
    return ReportsRepository(session=session)


async def get_ai_conversations_repo(session = Depends(get_db_session)) -> AIConversationsRepository:
    """Provides AIConversationsRepository with DB session."""
    return AIConversationsRepository(session=session)


async def get_attachments_repo(session = Depends(get_db_session)) -> AttachmentsRepository:
    """Provides AttachmentsRepository with DB session."""
    return AttachmentsRepository(session=session)


async def get_invoices_repo(session = Depends(get_db_session)) -> InvoicesRepository:
    """Provides InvoicesRepository with DB session."""
    return InvoicesRepository(session=session)


async def get_email_logs_repo(session = Depends(get_db_session)) -> EmailLogsRepository:
    """Provides EmailLogsRepository with DB session."""
    return EmailLogsRepository(session=session)


async def get_password_resets_repo(session = Depends(get_db_session)) -> PasswordResetsRepository:
    """Provides PasswordResetsRepository with DB session."""
    return PasswordResetsRepository(session=session)


async def get_consultation_insights_repo(session = Depends(get_db_session)) -> ConsultationInsightsRepository:
    """Provides ConsultationInsightsRepository with DB session."""
    return ConsultationInsightsRepository(session=session)


# Type Aliases for cleaner route signatures
AuthRepoDep = Annotated[AuthRepository, Depends(get_auth_repo)]
UserRepoDep = Annotated[UserRepository, Depends(get_user_repo)]
BillingRepoDep = Annotated[BillingRepository, Depends(get_billing_repo)]
ConsultationsRepoDep = Annotated[ConsultationsRepository, Depends(get_consultations_repo)]
ScribeUsageLogsRepoDep = Annotated[ScribeUsageLogsRepository, Depends(get_scribe_usage_logs_repo)]
PatientsRepoDep = Annotated[PatientsRepository, Depends(get_patients_repo)]
TemplatesRepoDep = Annotated[TemplatesRepository, Depends(get_templates_repo)]
ReportsRepoDep = Annotated[ReportsRepository, Depends(get_reports_repo)]
AIConversationsRepoDep = Annotated[AIConversationsRepository, Depends(get_ai_conversations_repo)]
AttachmentsRepoDep = Annotated[AttachmentsRepository, Depends(get_attachments_repo)]
InvoicesRepoDep = Annotated[InvoicesRepository, Depends(get_invoices_repo)]
EmailLogsRepoDep = Annotated[EmailLogsRepository, Depends(get_email_logs_repo)]
PasswordResetsRepoDep = Annotated[PasswordResetsRepository, Depends(get_password_resets_repo)]
ConsultationInsightsRepoDep = Annotated[ConsultationInsightsRepository, Depends(get_consultation_insights_repo)]
```

## File: src/infrastructure/persistence/postgres/models.py
```python
import uuid
from datetime import date, datetime
from typing import List, Optional
from sqlalchemy import String, Integer, Boolean, ForeignKey, Text, DateTime, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass

class TimestampMixin:
    """Provides created_at and updated_at columns to tables."""
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


# --- Core Identity & Billing ---

class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[Optional[str]] = mapped_column(String(255))
    auth_provider: Mapped[str] = mapped_column(String(50), default="local") # 'local' or 'google'

    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[Optional[str]] = mapped_column(String(100))
    role: Mapped[str] = mapped_column(String(50), default="doctor")
    provider_id: Mapped[Optional[str]] = mapped_column(String(100))
    gender: Mapped[Optional[str]] = mapped_column(String(20))
    date_of_birth: Mapped[Optional[date]] = mapped_column()

    registration_status: Mapped[str] = mapped_column(String(50), default="pending_details")
    has_seen_asset_prompt: Mapped[bool] = mapped_column(Boolean, default=False)
    preferences: Mapped[dict] = mapped_column(JSONB, server_default='{}')
    signature_url: Mapped[Optional[str]] = mapped_column(String(500))

    # Soft delete - if not null, user is deleted
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), index=True)

    # Relationships
    clinic: Mapped["Clinic"] = relationship(back_populates="user", uselist=False, cascade="all, delete-orphan")
    subscription: Mapped["Subscription"] = relationship(back_populates="user", uselist=False, cascade="all, delete-orphan")
    patients: Mapped[List["Patient"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    consultations: Mapped[List["Consultation"]] = relationship(back_populates="user")
    ai_conversations: Mapped[List["AIConversation"]] = relationship(back_populates="user")
    templates: Mapped[List["Template"]] = relationship(back_populates="user", cascade="all, delete-orphan")

class Clinic(Base, TimestampMixin):
    __tablename__ = "clinics"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), unique=True)
    
    clinic_name: Mapped[str] = mapped_column(String(255))
    street_address: Mapped[Optional[str]] = mapped_column(String(255))
    city: Mapped[Optional[str]] = mapped_column(String(100))
    state: Mapped[Optional[str]] = mapped_column(String(100))
    pincode: Mapped[Optional[str]] = mapped_column(String(20))
    country: Mapped[str] = mapped_column(String(2)) # Strictly 2-letter ISO code
    logo_url: Mapped[Optional[str]] = mapped_column(String(500))

    user: Mapped["User"] = relationship(back_populates="clinic")

class Subscription(Base, TimestampMixin):
    __tablename__ = "subscriptions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), unique=True)
    
    plan_type: Mapped[str] = mapped_column(String(50)) # 'free_trial', 'free_tier', 'copilot_pro'
    gateway: Mapped[str] = mapped_column(String(50))   # 'none', 'stripe', 'razorpay'
    status: Mapped[str] = mapped_column(String(50))    # 'trialing', 'active', 'past_due', 'canceled'
    
    external_customer_id: Mapped[Optional[str]] = mapped_column(String(100))
    external_subscription_id: Mapped[Optional[str]] = mapped_column(String(100))
    pending_checkout_session_id: Mapped[Optional[str]] = mapped_column(String(255))
    
    current_period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    current_period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    
    card_brand: Mapped[Optional[str]] = mapped_column(String(50))
    card_last4: Mapped[Optional[str]] = mapped_column(String(4))

    user: Mapped["User"] = relationship(back_populates="subscription")
    invoices: Mapped[List["Invoice"]] = relationship(back_populates="subscription", cascade="all, delete-orphan")


class Invoice(Base, TimestampMixin):
    __tablename__ = "invoices"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    subscription_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("subscriptions.id"))
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))

    # Gateway identifier
    gateway: Mapped[str] = mapped_column(String(50))  # stripe, razorpay

    # External IDs (gateway-specific, optional)
    external_invoice_id: Mapped[Optional[str]] = mapped_column(String(100))  # Stripe: in_xxx, Razorpay: inv_xxx
    external_subscription_id: Mapped[Optional[str]] = mapped_column(String(100))  # Stripe: sub_xxx, Razorpay: sub_xxx

    # Payment data
    amount_paid: Mapped[int] = mapped_column(Integer)  # In pence/cents
    currency: Mapped[str] = mapped_column(String(3))  # gbp, usd, inr, eur
    status: Mapped[str] = mapped_column(String(50))  # paid, open, void, uncollectible

    # Invoice URLs (optional, Stripe only for now)
    invoice_pdf_url: Mapped[Optional[str]] = mapped_column(String(500))  # Direct PDF download
    hosted_invoice_url: Mapped[Optional[str]] = mapped_column(String(500))  # Stripe hosted page

    # Billing period covered
    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    # Relationships
    subscription: Mapped["Subscription"] = relationship(back_populates="invoices")
    user: Mapped["User"] = relationship()
    

# --- Clinical Engine ---

class Patient(Base, TimestampMixin):
    __tablename__ = "patients"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    
    full_name: Mapped[str] = mapped_column(String(255))
    identifier: Mapped[Optional[str]] = mapped_column(String(100))
    date_of_birth: Mapped[Optional[date]] = mapped_column()
    gender: Mapped[Optional[str]] = mapped_column(String(20))
    email: Mapped[Optional[str]] = mapped_column(String(255))

    user: Mapped["User"] = relationship(back_populates="patients")
    consultations: Mapped[List["Consultation"]] = relationship(back_populates="patient")

class Consultation(Base, TimestampMixin):
    __tablename__ = "consultations"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    patient_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("patients.id", ondelete="SET NULL"))

    title: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(50), default="active") # active, paused, completed
    clinical_summary_text: Mapped[Optional[str]] = mapped_column(Text)
    is_title_edited: Mapped[bool] = mapped_column(Boolean, default=False)

    doctor_speaker_id: Mapped[Optional[int]] = mapped_column(Integer)
    last_summarized_transcript_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("consultation_transcripts.id", ondelete="SET NULL"))

    # Billing/Usage tracking
    total_audio_seconds: Mapped[int] = mapped_column(Integer, default=0)
    current_session_started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    user: Mapped["User"] = relationship(back_populates="consultations")
    patient: Mapped["Patient"] = relationship(back_populates="consultations")
    transcripts: Mapped[List["ConsultationTranscript"]] = relationship(back_populates="consultation", foreign_keys="[ConsultationTranscript.consultation_id]")
    insights: Mapped[List["ConsultationInsight"]] = relationship(back_populates="consultation", cascade="all, delete-orphan")
    ai_conversation: Mapped[Optional["AIConversation"]] = relationship(back_populates="consultation")
    reports: Mapped[List["Report"]] = relationship(back_populates="consultation", cascade="all, delete-orphan")

class ConsultationTranscript(Base, TimestampMixin):
    __tablename__ = "consultation_transcripts"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    consultation_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("consultations.id", ondelete="CASCADE"), index=True)
    speaker_id: Mapped[Optional[int]] = mapped_column(Integer) # e.g. 0 or 1 from Deepgram
    transcript: Mapped[str] = mapped_column(Text)

    consultation: Mapped["Consultation"] = relationship(back_populates="transcripts", foreign_keys=[consultation_id])


class ConsultationInsight(Base, TimestampMixin):
    """
    AI-generated or user-added insights for clinical decision support.
    Organized into fixed categories: safety, diagnosis, treatment, investigations, medicolegal, questions.
    """
    __tablename__ = "consultation_insights"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    consultation_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("consultations.id", ondelete="CASCADE"), index=True)

    category: Mapped[str] = mapped_column(String(50))  # safety, diagnosis, treatment, investigations, medicolegal, questions
    content: Mapped[str] = mapped_column(Text)         # The insight content (bullet points)
    is_dismissed: Mapped[bool] = mapped_column(Boolean, default=False)
    is_user_added: Mapped[bool] = mapped_column(Boolean, default=False)

    consultation: Mapped["Consultation"] = relationship(back_populates="insights")


class ScribeUsageLog(Base, TimestampMixin):
    """
    Usage ledger for scribe billing.
    One row per pause event - tracks exact seconds used with timestamp.
    Immutable - never deleted, even if consultation is deleted.
    """
    __tablename__ = "scribe_usage_logs"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    consultation_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("consultations.id", ondelete="SET NULL"))
    seconds_used: Mapped[int] = mapped_column(Integer)

class AIConversation(Base, TimestampMixin):
    __tablename__ = "ai_conversations"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    consultation_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("consultations.id", ondelete="CASCADE"), unique=True)
    
    title: Mapped[str] = mapped_column(String(255), default="New Chat")
    is_title_generated: Mapped[bool] = mapped_column(Boolean, default=False)

    user: Mapped["User"] = relationship(back_populates="ai_conversations")
    consultation: Mapped["Consultation"] = relationship(back_populates="ai_conversation")
    messages: Mapped[List["AIMessage"]] = relationship(back_populates="conversation", cascade="all, delete-orphan")

class AIMessage(Base, TimestampMixin):
    __tablename__ = "ai_messages"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    conversation_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("ai_conversations.id", ondelete="CASCADE"), index=True)

    role: Mapped[str] = mapped_column(String(50))                         # user, assistant, tool
    content: Mapped[str] = mapped_column(Text)
    artifacts: Mapped[Optional[dict]] = mapped_column(JSONB)              # Citations, UI widgets
    input_method: Mapped[str] = mapped_column(String(50), default="text") # text, voice

    conversation: Mapped["AIConversation"] = relationship(back_populates="messages")
    attachments: Mapped[List["Attachment"]] = relationship(back_populates="message", cascade="all, delete-orphan")


class Attachment(Base, TimestampMixin):
    __tablename__ = "attachments"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    message_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("ai_messages.id", ondelete="SET NULL"))

    file_name: Mapped[Optional[str]] = mapped_column(String(255))
    content_type: Mapped[Optional[str]] = mapped_column(String(100))
    s3_key: Mapped[str] = mapped_column(String(500))                      # Permanent S3 storage
    google_uri: Mapped[Optional[str]] = mapped_column(String(500))         # Gemini API URI (expires in 48hrs)

    user: Mapped["User"] = relationship()
    message: Mapped["AIMessage"] = relationship(back_populates="attachments")


class Template(Base, TimestampMixin):
    __tablename__ = "templates"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id"), index=True)  # NULL for system templates

    name: Mapped[str] = mapped_column(String(255))
    category: Mapped[Optional[str]] = mapped_column(String(100))  # clinical, administrative, letters
    description: Mapped[Optional[str]] = mapped_column(Text)
    content: Mapped[str] = mapped_column(Text)  # Template with [] placeholders
    is_system: Mapped[bool] = mapped_column(Boolean, default=False)

    user: Mapped["User"] = relationship(back_populates="templates")


class Report(Base, TimestampMixin):
    __tablename__ = "reports"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    consultation_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("consultations.id", ondelete="CASCADE"), index=True)
    template_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("templates.id"))

    title: Mapped[str] = mapped_column(String(255))
    content: Mapped[str] = mapped_column(Text)

    consultation: Mapped["Consultation"] = relationship(back_populates="reports")
    template: Mapped["Template"] = relationship()


# --- Notifications & Security ---


class PasswordReset(Base, TimestampMixin):
    __tablename__ = "password_resets"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token: Mapped[uuid.UUID] = mapped_column(unique=True, default=uuid.uuid4, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship()


class EmailLog(Base, TimestampMixin):
    """
    Audit trail for all transactional emails sent.
    Provides debugging, compliance, and analytics capabilities.
    """
    __tablename__ = "email_logs"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    email_template: Mapped[str] = mapped_column(String(100), nullable=False, index=True)  # e.g., 'password_reset', 'welcome'
    to_email: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # 'queued', 'sent', 'failed', 'bounced'
    provider_message_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # Brevo message ID
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Error details if failed
    template_metadata: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)  # Template-specific data

    # Relationships
    user: Mapped["User"] = relationship()
```

## File: src/dependencies/services.py
```python
from typing import Annotated
from fastapi import Depends

from src.dependencies.db import get_redis
from src.dependencies.repositories import (
    AttachmentsRepoDep,
    AuthRepoDep,
    UserRepoDep,
    BillingRepoDep,
    ConsultationsRepoDep,
    ConsultationInsightsRepoDep,
    ScribeUsageLogsRepoDep,
    PatientsRepoDep,
    TemplatesRepoDep,
    ReportsRepoDep,
    AIConversationsRepoDep,
    InvoicesRepoDep,
    EmailLogsRepoDep,
    PasswordResetsRepoDep,
)
from src.dependencies.infra import (
    get_google_files_client,
    get_session_manager,
    get_google_client,
    get_deepgram_client,
    get_stripe_client,
    get_razorpay_client,
    get_s3_client,
    get_pubsub_manager,
    get_brevo_client,
)
from src.dependencies.ai import get_fast_llm_service, get_tiny_llm_service
from src.modules.auth.service import AuthService
from src.modules.users.service import UserService
from src.modules.billing.service import BillingService
from src.modules.billing.invoices import InvoiceService
from src.modules.billing.manager import BillingManager
from src.modules.notifications.service import NotificationService
from src.modules.consultations.service import ConsultationsService
from src.modules.consultations.thinking_board import ThinkingBoardService
from src.modules.patients.service import PatientsService
from src.modules.templates.service import TemplatesService
from src.modules.reports.service import ReportsService
from src.modules.attachments.service import AttachmentsService
from src.modules.copilot.service import ChatService
from src.modules.emails.service import EmailService


# --- Service Dependencies ---

async def get_email_service(
    email_logs_repo: EmailLogsRepoDep,
) -> EmailService:
    """
    Provides EmailService for transactional emails.
    """
    return EmailService(
        email_logs_repo=email_logs_repo,
    )


async def get_notification_service(
    pubsub_manager = Depends(get_pubsub_manager),
) -> NotificationService:
    """
    Provides NotificationService for real-time events.
    """
    return NotificationService(pubsub_manager=pubsub_manager)


async def get_user_service(
    user_repo: UserRepoDep,
    s3_client = Depends(get_s3_client),
    redis = Depends(get_redis),
) -> UserService:
    """
    Provides UserService with all dependencies.
    """
    return UserService(
        user_repo=user_repo,
        s3_client=s3_client,
        redis_client=redis,
    )

async def get_invoice_service(
    invoices_repo: InvoicesRepoDep,
    billing_repo: BillingRepoDep,
) -> InvoiceService:
    """
    Provides InvoiceService for billing.
    """
    return InvoiceService(
        invoices_repo=invoices_repo,
        billing_repo=billing_repo,
    )

async def get_billing_manager(
    billing_repo: BillingRepoDep,
    user_repo: UserRepoDep,
    pubsub_manager = Depends(get_pubsub_manager),
    email_service: EmailService = Depends(get_email_service),
) -> BillingManager:
    """
    Provides BillingManager for state transitions.
    """
    return BillingManager(
        billing_repo=billing_repo,
        user_repo=user_repo,
        pubsub_manager=pubsub_manager,
        email_service=email_service,
    )

async def get_billing_service(
    billing_repo: BillingRepoDep,
    user_repo: UserRepoDep,
    stripe_client = Depends(get_stripe_client),
    razorpay_client = Depends(get_razorpay_client),
    manager: BillingManager = Depends(get_billing_manager),
    invoice_service: InvoiceService = Depends(get_invoice_service),
) -> BillingService:
    """
    Provides BillingService with all dependencies.
    """
    return BillingService(
        billing_repo=billing_repo,
        user_repo=user_repo,
        stripe_client=stripe_client,
        razorpay_client=razorpay_client,
        manager=manager,
        invoice_service=invoice_service,
    )


async def get_auth_service(
    auth_repo: AuthRepoDep,
    user_repo: UserRepoDep,
    password_resets_repo: PasswordResetsRepoDep,
    session_manager = Depends(get_session_manager),
    google_client = Depends(get_google_client),
    stripe_client = Depends(get_stripe_client),
    razorpay_client = Depends(get_razorpay_client),
    billing_service: BillingService = Depends(get_billing_service),
    email_service = Depends(get_email_service),
) -> AuthService:
    """
    Provides AuthService with all dependencies.
    """
    return AuthService(
        auth_repo=auth_repo,
        user_repo=user_repo,
        password_resets_repo=password_resets_repo,
        session_manager=session_manager,
        google_client=google_client,
        stripe_client=stripe_client,
        razorpay_client=razorpay_client,
        billing_service=billing_service,
        email_service=email_service,
    )


async def get_thinking_board_service(
    consultations_repo: ConsultationsRepoDep,
    insights_repo: ConsultationInsightsRepoDep,
    tiny_llm_service = Depends(get_tiny_llm_service),
) -> ThinkingBoardService:
    """
    Provides ThinkingBoardService with all dependencies.
    Uses tiny LLM for faster structured output generation.
    """
    return ThinkingBoardService(
        consultations_repo=consultations_repo,
        insights_repo=insights_repo,
        llm_service=tiny_llm_service,
    )


async def get_consultations_service(
    consultations_repo: ConsultationsRepoDep,
    billing_repo: BillingRepoDep,
    usage_logs_repo: ScribeUsageLogsRepoDep,
    reports_repo: ReportsRepoDep,
    deepgram_client = Depends(get_deepgram_client),
    pubsub_manager = Depends(get_pubsub_manager),
    fast_llm_service = Depends(get_fast_llm_service),
) -> ConsultationsService:
    """
    Provides ConsultationsService with all dependencies.
    """
    return ConsultationsService(
        consultations_repo=consultations_repo,
        billing_repo=billing_repo,
        usage_logs_repo=usage_logs_repo,
        reports_repo=reports_repo,
        deepgram_client=deepgram_client,
        pubsub_manager=pubsub_manager,
        fast_llm_service=fast_llm_service,
    )


async def get_patients_service(
    patients_repo: PatientsRepoDep,
) -> PatientsService:
    """
    Provides PatientsService with all dependencies.
    """
    return PatientsService(patients_repo=patients_repo)


async def get_templates_service(
    templates_repo: TemplatesRepoDep,
) -> TemplatesService:
    """
    Provides TemplatesService with all dependencies.
    """
    return TemplatesService(templates_repo=templates_repo)


async def get_reports_service(
    reports_repo: ReportsRepoDep,
    templates_repo: TemplatesRepoDep,
    consultations_repo: ConsultationsRepoDep,
    patients_repo: PatientsRepoDep,
    user_repo: UserRepoDep,
    fast_llm_service = Depends(get_fast_llm_service),
) -> ReportsService:
    """
    Provides ReportsService with all dependencies.
    """
    return ReportsService(
        reports_repo=reports_repo,
        templates_repo=templates_repo,
        consultations_repo=consultations_repo,
        patients_repo=patients_repo,
        user_repo=user_repo,
        llm_service=fast_llm_service,
    )


async def get_attachments_service(
    attachments_repo: AttachmentsRepoDep,
    s3_client = Depends(get_s3_client),
    google_files_client = Depends(get_google_files_client),
) -> AttachmentsService:
    """
    Provides AttachmentsService with all dependencies.
    """
    return AttachmentsService(
        attachments_repo=attachments_repo,
        s3_client=s3_client,
        google_files_client=google_files_client,
    )


async def get_chat_service(
    ai_conversations_repo: AIConversationsRepoDep,
    attachments_repo: AttachmentsRepoDep,
    pubsub_manager = Depends(get_pubsub_manager),
    s3_client = Depends(get_s3_client),
    attachments_service: AttachmentsService = Depends(get_attachments_service),
) -> ChatService:
    """
    Provides ChatService with all dependencies.
    """
    return ChatService(
        ai_conversations_repo=ai_conversations_repo,
        attachments_repo=attachments_repo,
        pubsub_manager=pubsub_manager,
        s3_client=s3_client,
        attachments_service=attachments_service,
    )


# Type Aliases for cleaner route signatures
AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
UserServiceDep = Annotated[UserService, Depends(get_user_service)]
BillingServiceDep = Annotated[BillingService, Depends(get_billing_service)]
InvoiceServiceDep = Annotated[InvoiceService, Depends(get_invoice_service)]
NotificationServiceDep = Annotated[NotificationService, Depends(get_notification_service)]
EmailServiceDep = Annotated[EmailService, Depends(get_email_service)]
ConsultationsServiceDep = Annotated[ConsultationsService, Depends(get_consultations_service)]
ThinkingBoardServiceDep = Annotated[ThinkingBoardService, Depends(get_thinking_board_service)]
PatientsServiceDep = Annotated[PatientsService, Depends(get_patients_service)]
TemplatesServiceDep = Annotated[TemplatesService, Depends(get_templates_service)]
ReportsServiceDep = Annotated[ReportsService, Depends(get_reports_service)]
AttachmentsServiceDep = Annotated[AttachmentsService, Depends(get_attachments_service)]
ChatServiceDep = Annotated[ChatService, Depends(get_chat_service)]
```
