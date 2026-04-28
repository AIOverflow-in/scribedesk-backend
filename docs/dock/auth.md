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
- Only files matching these patterns are included: src/infrastructure/persistence/postgres/repos/auth_repo.py, src/modules/auth/service.py, src/schemas/**/*, src/api/v1/auth.py, src/main.py
- Files matching patterns in .gitignore are excluded
- Files matching default ignore patterns are excluded
- Files are sorted by Git change count (files with more changes are at the bottom)

# Directory Structure
```
src/api/v1/auth.py
src/infrastructure/persistence/postgres/repos/auth_repo.py
src/main.py
src/modules/auth/service.py
src/schemas/api/__init__.py
src/schemas/api/auth.py
src/schemas/api/billing.py
src/schemas/api/chat.py
src/schemas/api/common.py
src/schemas/api/consultations.py
src/schemas/api/patients.py
src/schemas/api/reports.py
src/schemas/api/templates.py
src/schemas/api/thinking_board.py
src/schemas/api/user.py
src/schemas/api/websockets.py
src/schemas/db/__init__.py
src/schemas/db/auth.py
src/schemas/db/clinical.py
src/schemas/db/copilot.py
src/schemas/db/notification.py
src/schemas/db/thinking_board.py
src/schemas/features/auth.py
src/schemas/features/billing.py
src/schemas/features/copilot.py
src/schemas/features/notification.py
src/schemas/features/thinking_board.py
```

# Files

## File: src/schemas/api/__init__.py
```python
# --- Auth ---
from .auth import (
    UserProfileData,
    ClinicData,
    StandardRegisterRequest,
    GoogleOnboardingRequest,
    LoginRequest,
    GoogleVerifyRequest,
    AuthResponse,
)


__all__ = [
    # Auth
    "UserProfileData",
    "ClinicData",
    "StandardRegisterRequest",
    "GoogleOnboardingRequest",
    "LoginRequest",
    "GoogleVerifyRequest",
    "AuthResponse",
]
```

## File: src/schemas/api/chat.py
```python
"""Request and response schemas for chat API."""

from datetime import datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field


# --- Request Schemas ---

class ChatRequest(BaseModel):
    """Payload for POST /chat - Send a message to the AI."""
    message: str = Field(..., min_length=1, description="User message text")
    conversation_id: Optional[UUID] = Field(None, description="Existing conversation ID, or null for new chat")
    attachment_ids: List[UUID] = Field(default_factory=list, description="File attachment IDs to include")


class UploadRequest(BaseModel):
    """Payload for POST /upload - Upload a file attachment."""
    file_name: str = Field(..., description="Original file name")
    content_type: str = Field(..., description="MIME type of the file")


# --- Response Schemas ---

class MessageAttachment(BaseModel):
    """Attachment info in a conversation message."""
    id: UUID
    file_name: Optional[str] = None
    content_type: Optional[str] = None
    url: str


class ChatMessageResponse(BaseModel):
    """A single message in the conversation."""
    id: UUID
    role: str
    content: str
    created_at: datetime
    attachments: List[MessageAttachment] = []
    artifacts: Optional[dict] = None  # Citations, widgets, etc.


class ChatConversationResponse(BaseModel):
    """Response with conversation details and messages."""
    id: UUID
    title: str
    is_title_generated: bool
    created_at: datetime
    updated_at: datetime
    messages: List[ChatMessageResponse]


class ChatConversationItemResponse(BaseModel):
    """Single conversation in a list (without messages)."""
    id: UUID
    title: str
    is_title_generated: bool
    created_at: datetime
    updated_at: datetime


class ChatConversationListResponse(BaseModel):
    """Paginated list of conversations."""
    items: List[ChatConversationItemResponse]
    total: int
    page: int
    page_size: int


class UploadResponse(BaseModel):
    """Response from POST /upload with attachment metadata."""
    attachment_id: UUID
    url: str


# --- Stream Schemas ---

class StreamChunk(BaseModel):
    """A single chunk in the SSE stream."""
    type: str  # "content", "tool_call", "metadata", "status", "done", "error"
    content: Optional[str] = None  # Text content for "content" type
    tool_name: Optional[str] = None  # Tool name for "tool_call" type
    status_message: Optional[str] = None  # Status message for UI
    metadata_type: Optional[str] = None  # For "metadata" type (e.g., "citations")
    data: Optional[dict] = None  # Additional data (citations, tool results, etc.)
    error: Optional[str] = None  # Error message if type="error"
```

## File: src/schemas/api/common.py
```python
from pydantic import BaseModel


class StatusResponse(BaseModel):
    """Generic status response for simple operations."""
    status: str
```

## File: src/schemas/api/reports.py
```python
from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field


# --- Request Schemas ---

class CreateReportRequest(BaseModel):
    """Payload for POST /api/reports - Generate a report."""
    template_id: UUID
    consultation_id: UUID


class UpdateReportRequest(BaseModel):
    """Payload for PATCH /api/reports/{id} - Update report title/content."""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    content: Optional[str] = None


# --- Response Schemas ---

class ReportResponse(BaseModel):
    """A single report with full content."""
    id: UUID
    consultation_id: UUID
    template_id: UUID
    title: str
    content: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ReportMetadata(BaseModel):
    """Report metadata (without full content) for lists."""
    id: UUID
    title: str
    template_name: str
    created_at: datetime
```

## File: src/schemas/api/templates.py
```python
from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field


# --- Request Schemas ---

class CreateTemplateRequest(BaseModel):
    """Payload for POST /api/templates - Create a custom template."""
    name: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., min_length=1)
    category: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None


class UpdateTemplateRequest(BaseModel):
    """Payload for PATCH /api/templates/{id} - Update a template."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    content: Optional[str] = None
    category: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None


# --- Response Schemas ---

class TemplateResponse(BaseModel):
    """A single template returned in API responses."""
    id: UUID
    name: str
    category: Optional[str] = None
    description: Optional[str] = None
    content: str
    is_system: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
```

## File: src/schemas/api/thinking_board.py
```python
"""API schemas for Thinking Board endpoints."""

import uuid
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class InsightCategory(str, Enum):
    """Fixed categories for clinical insights."""
    SAFETY = "safety"
    DIAGNOSIS = "diagnosis"
    TREATMENT = "treatment"
    INVESTIGATIONS = "investigations"
    MEDICOLEGAL = "medicolegal"
    QUESTIONS = "questions"


class InsightResponse(BaseModel):
    """Single insight in the thinking board."""
    id: uuid.UUID
    category: InsightCategory
    content: str
    is_user_added: bool
    created_at: str

    class Config:
        from_attributes = True


class ThinkingBoardResponse(BaseModel):
    """Complete thinking board with all categories."""
    safety: List[InsightResponse] = []
    diagnosis: List[InsightResponse] = []
    treatment: List[InsightResponse] = []
    investigations: List[InsightResponse] = []
    medicolegal: List[InsightResponse] = []
    questions: List[InsightResponse] = []


class AddInsightRequest(BaseModel):
    """Request to add a user-created insight."""
    category: InsightCategory
    content: str = Field(..., min_length=1, max_length=1000)


class AddInsightResponse(BaseModel):
    """Response after adding an insight."""
    id: uuid.UUID
    category: InsightCategory
    content: str
    is_user_added: bool
    created_at: str
```

## File: src/schemas/db/__init__.py
```python
# --- Auth ---
from .auth import UserDb, ClinicDb, SubscriptionDb

# --- Clinical ---
from .clinical import PatientDb, ConsultationDb, ConsultationTranscriptDb

# --- Copilot ---
from .copilot import AIConversationDb, AIMessageDb


__all__ = [
    # Auth
    "UserDb",
    "ClinicDb",
    "SubscriptionDb",
    # Clinical
    "PatientDb",
    "ConsultationDb",
    "ConsultationTranscriptDb",
    # Copilot
    "AIConversationDb",
    "AIMessageDb",
]
```

## File: src/schemas/db/auth.py
```python
from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


# --- User ---

class UserDb(BaseModel):
    """Pydantic representation of the User model."""
    id: UUID
    email: EmailStr
    first_name: str
    last_name: Optional[str]
    role: str
    provider_id: Optional[str]
    gender: Optional[str]
    date_of_birth: Optional[date]
    registration_status: str
    has_seen_asset_prompt: bool
    preferences: dict
    signature_url: Optional[str]
    auth_provider: str
    deleted_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# --- Clinic ---

class ClinicDb(BaseModel):
    """Pydantic representation of the Clinic model."""
    id: UUID
    user_id: UUID
    clinic_name: str
    street_address: Optional[str]
    city: Optional[str]
    state: Optional[str]
    pincode: Optional[str]
    country: str
    logo_url: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# --- Subscription ---

class SubscriptionDb(BaseModel):
    """Pydantic representation of the Subscription model."""
    id: UUID
    user_id: UUID
    plan_type: str
    gateway: str
    status: str
    external_customer_id: Optional[str]
    external_subscription_id: Optional[str]
    pending_checkout_session_id: Optional[str]
    current_period_start: datetime
    current_period_end: datetime
    card_brand: Optional[str]
    card_last4: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
```

## File: src/schemas/db/clinical.py
```python
from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr


# --- Patient ---

class PatientDb(BaseModel):
    """Pydantic representation of the Patient model."""
    id: UUID
    user_id: UUID
    full_name: str
    identifier: Optional[str]
    date_of_birth: Optional[date]
    gender: Optional[str]
    email: Optional[EmailStr]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# --- Consultation ---

class ConsultationDb(BaseModel):
    """Pydantic representation of the Consultation model."""
    id: UUID
    user_id: UUID
    patient_id: Optional[UUID]
    title: str
    status: str
    clinical_summary_text: Optional[str]
    is_title_edited: bool
    doctor_speaker_id: Optional[int]
    last_summarized_transcript_id: Optional[UUID]
    total_audio_seconds: int
    current_session_started_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# --- ConsultationTranscript ---

class ConsultationTranscriptDb(BaseModel):
    """Pydantic representation of the ConsultationTranscript model."""
    id: UUID
    consultation_id: UUID
    speaker_id: int
    transcript: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
```

## File: src/schemas/db/notification.py
```python
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class PasswordResetDb(BaseModel):
    """Pydantic representation of the PasswordReset model."""
    id: UUID
    user_id: UUID
    token: UUID
    expires_at: datetime
    used_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class EmailLogDb(BaseModel):
    """Pydantic representation of the EmailLog model."""
    id: UUID
    user_id: Optional[UUID]
    email_template: str
    to_email: str
    status: str
    provider_message_id: Optional[str]
    error_message: Optional[str]
    template_metadata: Optional[dict]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
```

## File: src/schemas/db/thinking_board.py
```python
"""Database schemas for ConsultationInsight model."""

import uuid
from datetime import datetime
from pydantic import BaseModel


class ConsultationInsightDb(BaseModel):
    """ConsultationInsight model as returned from DB."""
    id: uuid.UUID
    consultation_id: uuid.UUID
    category: str
    content: str
    is_dismissed: bool
    is_user_added: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
```

## File: src/schemas/features/auth.py
```python
from typing import Optional
from uuid import UUID
from pydantic import BaseModel


class CurrentUser(BaseModel):
    """Minimal user context for authenticated requests."""
    id: UUID
    email: str
    first_name: str
    last_name: Optional[str] = None
    role: str
    registration_status: str

    class Config:
        from_attributes = True
```

## File: src/schemas/features/notification.py
```python
import uuid
from enum import Enum
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


# --- Enums ---


class EmailStatus(str, Enum):
    """Status of an email in the sending pipeline"""
    QUEUED = "queued"       # Added to Celery queue
    SENT = "sent"           # Successfully sent to provider
    FAILED = "failed"       # Failed to send (will retry)
    BOUNCED = "bounced"     # Provider returned hard bounce
    DELIVERED = "delivered" # Confirmed delivered (if provider supports)


class EmailTemplate(str, Enum):
    """Email template identifiers"""
    # Auth emails
    WELCOME_FREE = "welcome_free"
    WELCOME_PRO = "welcome_pro"
    PASSWORD_RESET = "password_reset"
    PASSWORD_CHANGED = "password_changed"

    # Billing emails
    PLAN_ACTIVATED = "plan_activated"
    PAYMENT_FAILED = "payment_failed"
    SUBSCRIPTION_CANCELLED = "subscription_cancelled"
    INVOICE_READY = "invoice_ready"


# --- Password Reset ---


class PasswordResetRequest(BaseModel):
    """Request to initiate password reset"""
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Confirm password reset with token and new password"""
    token: uuid.UUID
    new_password: str = Field(..., min_length=8, max_length=100)


class PasswordResetResponse(BaseModel):
    """Response after initiating password reset"""
    message: str
    # For security, we don't reveal if email exists


# --- Email Logs ---


class EmailLogResponse(BaseModel):
    """Email log entry (for admin/debugging)"""
    id: uuid.UUID
    user_id: Optional[uuid.UUID] = None
    email_template: str
    to_email: str
    status: str
    provider_message_id: Optional[str] = None
    error_message: Optional[str] = None
    template_metadata: Optional[dict] = None
    created_at: str

    class Config:
        from_attributes = True


class EmailLogListResponse(BaseModel):
    """Paginated list of email logs for a user"""
    logs: list[EmailLogResponse]
    total: int
    page: int
    page_size: int


# --- Internal Email Sending DTO ---


class EmailData(BaseModel):
    """Data required to send an email (used internally by NotificationService)"""
    to_email: str
    to_name: Optional[str] = None
    template_name: EmailTemplate
    subject: str
    template_data: dict
    user_id: Optional[uuid.UUID] = None
    template_metadata: Optional[dict] = None
```

## File: src/schemas/features/thinking_board.py
```python
"""Internal schemas for LLM structured output - Thinking Board."""

from typing import List, Dict
from pydantic import BaseModel


class ThinkingBoardGenerateResponse(BaseModel):
    """
    Structured response from LLM for thinking board generation.
    AI returns insights organized by category.
    """
    safety: List[str] = []
    diagnosis: List[str] = []
    treatment: List[str] = []
    investigations: List[str] = []
    medicolegal: List[str] = []
    questions: List[str] = []
```

## File: src/schemas/api/billing.py
```python
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime


class UpgradeResponse(BaseModel):
    """Response for upgrade checkout creation."""
    checkout_url: Optional[str] = None


class Invoice(BaseModel):
    """Invoice schema - used for both list items and detail response."""
    id: str
    gateway: str
    amount_paid: float
    currency: str
    status: str
    invoice_pdf_url: Optional[str] = None
    hosted_invoice_url: Optional[str] = None
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    created_at: Optional[datetime] = None


class InvoiceListResponse(BaseModel):
    """Response for invoice list with pagination."""
    items: List[Invoice]
    total: int
    page: int
    page_size: int
```

## File: src/schemas/api/consultations.py
```python
from datetime import datetime
from typing import Optional, List
from uuid import UUID
from enum import Enum
from pydantic import BaseModel, Field

from src.schemas.api.reports import ReportMetadata
from src.schemas.features.copilot import SuggestionItem


# --- Request Schemas ---

class CreateConsultationRequest(BaseModel):
    """Payload for POST /api/consultations - Create a new consultation."""
    patient_id: Optional[UUID] = None


class UpdateConsultationRequest(BaseModel):
    """Payload for PATCH /api/consultations/{id} - Update consultation details."""
    title: Optional[str] = Field(None, min_length=3, max_length=255)
    patient_id: Optional[UUID] = None


class CreateTranscriptRequest(BaseModel):
    """Payload for POST /api/consultations/{id}/transcripts - Save a transcript chunk."""
    transcript: str = Field(..., min_length=1)
    speaker_id: Optional[int] = Field(None, ge=0, le=1)


class SuggestionsRequest(BaseModel):
    """Payload for POST /api/consultations/{id}/suggestions - Get AI nudges."""
    current: List[SuggestionItem] = Field(default_factory=list, description="Current suggestions with their states")


class PauseConsultationRequest(BaseModel):
    """Payload for POST /api/consultations/{id}/pause - Stop billing and optionally generate summary."""
    generate_summary: bool = Field(default=True, description="Whether to trigger background summary generation")


# --- Response Schemas ---

class TranscriptResponse(BaseModel):
    """A single transcript chunk returned in consultation details."""
    id: UUID
    speaker_id: Optional[int] = None
    transcript: str
    created_at: datetime

    class Config:
        from_attributes = True


class ConsultationResponse(BaseModel):
    """Minimal consultation response for frontend."""
    id: UUID
    title: str
    patient_id: Optional[UUID] = None
    patient_name: Optional[str] = None 
    clinical_summary_text: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ConsultationWithDetailsResponse(ConsultationResponse):
    """Extended consultation details with transcripts and reports."""
    transcripts: List[TranscriptResponse] = []
    reports: List[ReportMetadata] = []


class ConsultationWithTokenResponse(ConsultationResponse):
    """Response for POST /api/consultations - Includes Deepgram token."""
    token: str


class SuggestionsResponse(BaseModel):
    """Response for POST /api/consultations/{id}/suggestions."""
    suggestions: List[SuggestionItem]


class DeepgramTokenResponse(BaseModel):
    """Response for GET /api/consultations/{id}/deepgram-token."""
    token: str


# --- List Response ---

class ConsultationListResponse(BaseModel):
    """Paginated list of consultations."""
    items: List[ConsultationResponse]
    total: int
    page: int
    page_size: int
```

## File: src/schemas/api/patients.py
```python
from datetime import date, datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict

from src.schemas.api.common import StatusResponse


# --- Request Schemas ---

class CreatePatientRequest(BaseModel):
    """Payload for POST /api/patients - Create a new patient."""
    full_name: str = Field(..., min_length=1, max_length=255)
    identifier: str = Field(..., min_length=1, max_length=100)
    date_of_birth: Optional[date] = None
    gender: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=255)


class UpdatePatientRequest(BaseModel):
    """Payload for PATCH /api/patients/{id} - Update patient details. Identifier cannot be changed."""
    full_name: Optional[str] = Field(None, min_length=1, max_length=255)
    date_of_birth: Optional[date] = None
    gender: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=255)


# --- Response Schemas ---

class PatientResponse(BaseModel):
    """A single patient returned in API responses."""
    id: UUID
    full_name: str
    identifier: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    email: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PatientListResponse(BaseModel):
    """Paginated list of patients."""
    items: List[PatientResponse]
    total: int
    page: int
    page_size: int
```

## File: src/schemas/api/user.py
```python
from typing import Any, Optional, Dict
from datetime import date
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, computed_field


# --- Response Schemas ---

class ClinicInfo(BaseModel):
    """Clinic information for user profile."""
    clinic_name: str
    street_address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    country: str
    logo_url: Optional[str] = None


class SubscriptionInfo(BaseModel):
    """Subscription information for user profile."""
    plan_type: str
    status: str
    current_period_start: Optional[date] = None
    current_period_end: Optional[date] = None
    card_brand: Optional[str] = None
    card_last4: Optional[str] = None


class UserProfileResponse(BaseModel):
    """Full user profile returned by GET /auth/me."""
    id: UUID
    email: EmailStr
    first_name: str
    last_name: Optional[str] = None
    gender: Optional[str] = None
    age: Optional[int] = None
    provider_id: Optional[str] = None
    role: str
    registration_status: str
    has_seen_asset_prompt: bool = False
    preferences: Optional[Dict[str, Any]] = None
    signature_url: Optional[str] = None

    clinic: Optional[ClinicInfo] = None
    subscription: Optional[SubscriptionInfo] = None


# --- Request Schemas ---

class ProfileUpdateRequest(BaseModel):
    """Payload for PATCH /users/me/profile - Updates personal details."""
    first_name: Optional[str] = Field(None, min_length=3, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    gender: Optional[str] = Field(None, pattern="^(Male|Female|Other|Prefer not to say)$")
    date_of_birth: Optional[date] = None
    provider_id: Optional[str] = Field(None, description="Medical License Number")


class ClinicUpdateRequest(BaseModel):
    """Payload for PATCH /users/me/clinic - Updates clinic details."""
    clinic_name: Optional[str] = Field(None, min_length=2, max_length=255)
    street_address: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    pincode: Optional[str] = Field(None, max_length=20)

class FileUploadResponse(BaseModel):
    """Response for file upload endpoints (signature, clinic logo)."""
    status: str = "success"
    url: str


class PreferencesUpdateRequest(BaseModel):
    """Payload for PATCH /users/me/preferences - Updates UI state."""
    # Common UI preferences
    theme: Optional[str] = Field(None, pattern="^(light|dark|system)$")
    dismissed_modals: Optional[list[str]] = None
    has_seen_asset_prompt: Optional[bool] = None

    # Allow any additional preferences via extra field
    model_config = {"extra": "allow"}
```

## File: src/schemas/db/copilot.py
```python
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


# --- AIConversation ---

class AIConversationDb(BaseModel):
    """Pydantic representation of the AIConversation model."""
    id: UUID
    user_id: UUID
    consultation_id: Optional[UUID]
    title: str
    is_title_generated: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# --- AIMessage ---

class AIMessageDb(BaseModel):
    """Pydantic representation of the AIMessage model."""
    id: UUID
    conversation_id: UUID
    role: str
    content: str
    artifacts: Optional[dict]
    input_method: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# --- Attachment ---

class AttachmentDb(BaseModel):
    """Pydantic representation of the Attachment model."""
    id: UUID
    user_id: UUID
    message_id: Optional[UUID]
    file_name: Optional[str]
    content_type: Optional[str]
    s3_key: str
    google_uri: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
```

## File: src/schemas/features/billing.py
```python
import uuid
from typing import Optional, Dict
from pydantic import BaseModel


class RazorpayWebhookData(BaseModel):
    """
    Normalized payment event data from Razorpay.
    Used by BillingService to update user subscriptions from Razorpay webhooks.
    """
    user_id: uuid.UUID
    customer_id: str
    subscription_id: str
    period_start: int
    period_end: int
    card_details: Optional[Dict[str, str]] = None


class StripeWebhookData(BaseModel):
    """
    Normalized payment event data from Stripe.
    Used by BillingService to update user subscriptions AND store invoices.
    """
    # Subscription data
    user_id: uuid.UUID
    customer_id: str
    subscription_id: str
    period_start: int
    period_end: int
    card_details: Optional[Dict[str, str]] = None

    # Invoice data (Stripe provides rich invoice details)
    stripe_invoice_id: str
    amount_paid: int
    currency: str
    status: str
    invoice_pdf_url: str
    hosted_invoice_url: str
```

## File: src/schemas/api/websockets.py
```python
from typing import Literal, Dict, Any, Optional
from pydantic import BaseModel


class WebSocketEvent(BaseModel):
    """
    Standard WebSocket event message sent to frontend.

    Event format:
    {
      "event_type": "payment_success" | "payment_failed" | ...,
      "data": {...},
      "timestamp": "2024-03-27T10:00:00Z"
    }
    """
    event_type: Literal[
        "payment_success",
        "payment_failed",
        "subscription_cancelled",
        "subscription_downgraded",
        "chat_title_generated",
        "consultation_title_generated",
        "summary_updated",
    ]
    data: Dict[str, Any]
    timestamp: Optional[str] = None


# --- Event Data Schemas (Frontend Reference) ---

class PaymentSuccessData(BaseModel):
    """Data for payment_success event."""
    plan: str
    message: str


class PaymentFailedData(BaseModel):
    """Data for payment_failed event."""
    reason: str
    message: str


class SubscriptionCancelledData(BaseModel):
    """Data for subscription_cancelled event."""
    plan: str
    message: str


class SubscriptionDowngradedData(BaseModel):
    """Data for subscription_downgraded event."""
    plan: str
    message: str


class ChatTitleGeneratedData(BaseModel):
    """Data for chat_title_generated event."""
    conv_id: str
    title: str


class ConsultationTitleGeneratedData(BaseModel):
    """Data for consultation_title_generated event."""
    consultation_id: str
    title: str


class SummaryUpdatedData(BaseModel):
    """Data for summary_updated event."""
    consultation_id: str
    reason: Literal["new_transcript", "manual_edit", "auto_refresh"]
    message: Optional[str] = None
```

## File: src/schemas/features/copilot.py
```python
"""Schemas for LLM-powered features."""

from typing import List, Optional
from enum import Enum
from pydantic import BaseModel, Field


class SuggestionCategory(str, Enum):
    """Categories for consultation suggestions."""
    MEDICAL = "medical"
    LEGAL = "legal"
    ADMINISTRATIVE = "administrative"


class SuggestionState(str, Enum):
    """State of a suggestion."""
    ACTIVE = "active"
    DISMISSED = "dismissed"


# --- Consultation Schemas ---

class ConsultationTitleResponse(BaseModel):
    """Response for consultation title generation."""
    title: str = Field(..., description="3-word consultation title")


class SuggestionItem(BaseModel):
    """Individual suggestion with category and state."""
    question: str = Field(..., description="The suggested question")
    category: SuggestionCategory = Field(..., description="Category: medical, legal, or administrative")
    state: SuggestionState = Field(default=SuggestionState.ACTIVE, description="State: active or dismissed")


class ConsultationSuggestionsResponse(BaseModel):
    """Response for AI suggestion generation."""
    suggestions: List[SuggestionItem] = Field(..., min_length=2, max_length=4, description="2-4 categorized suggestions")


# --- Chat Schemas ---

class BraveSearchResult(BaseModel):
    """Search result from Brave API."""
    title: str
    url: str
    description: str
    extra_snippets: List[str] = Field(default_factory=list)
    profile_name: Optional[str] = None
    profile_img: Optional[str] = None
    hostname: Optional[str] = None


class ChatTitleResponse(BaseModel):
    """Response for chat title generation."""
    title: str = Field(..., description="3-5 word chat title")
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

## File: src/schemas/api/auth.py
```python
from typing import Optional
from datetime import date
from pydantic import BaseModel, EmailStr, Field


# --- Reusable Sub-Schemas ---

class UserProfileData(BaseModel):
    """Shared personal details for both standard and Google registration."""
    first_name: str = Field(..., min_length=3, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    gender: Optional[str] = Field(None, pattern="^(Male|Female|Other|Prefer not to say)$")
    date_of_birth: Optional[date] = None
    provider_id: Optional[str] = Field(None, description="Medical License Number")


class ClinicData(BaseModel):
    """Shared clinic details for all registrations."""
    clinic_name: str = Field(..., min_length=2, max_length=255)
    street_address: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    pincode: Optional[str] = Field(None, max_length=20)
    country: str = Field(..., min_length=2, max_length=2, pattern="^[A-Z]{2}$")


# --- Request Schemas ---

class StandardRegisterRequest(BaseModel):
    """Payload for POST /api/auth/register"""
    email: EmailStr
    password: str = Field(..., min_length=8)
    profile: UserProfileData
    clinic: ClinicData
    plan_type: str = Field(..., pattern="^(free_trial|copilot_pro)$")


class GoogleOnboardingRequest(BaseModel):
    """Payload for PATCH /api/auth/onboarding"""
    profile: UserProfileData
    clinic: ClinicData
    plan_type: str = Field(..., pattern="^(free_trial|copilot_pro)$")


class LoginRequest(BaseModel):
    """Payload for POST /api/auth/login"""
    email: EmailStr
    password: str


class GoogleVerifyRequest(BaseModel):
    """Payload for POST /api/auth/google/verify"""
    token: str = Field(..., description="The access token from Chrome Identity API")


# --- Response Schemas ---

class AuthResponse(BaseModel):
    """Standard 200 OK response for ALL auth routes."""
    status: str = "success"
    session_token: Optional[str] = None
    checkout_url: Optional[str] = None
```

## File: src/api/v1/auth.py
```python
from fastapi import APIRouter, Depends, Response, Header
from fastapi.security import HTTPAuthorizationCredentials

from src.api.v1.helpers import handle_auth_result
from src.core.exceptions import UnauthorizedException
from src.dependencies.auth import CurrentUserDep, security
from src.dependencies.services import AuthServiceDep, UserServiceDep
from src.schemas.api.auth import (
    LoginRequest,
    StandardRegisterRequest,
    GoogleVerifyRequest,
    GoogleOnboardingRequest,
    AuthResponse
)

from src.schemas.api.common import StatusResponse
from src.schemas.api.user import UserProfileResponse

from src.schemas.features.notification import (
    PasswordResetRequest,
    PasswordResetConfirm,
    PasswordResetResponse
)


router = APIRouter()

# --- Routes ---

@router.post("/password/reset", response_model=PasswordResetResponse)
async def request_password_reset(
    request: PasswordResetRequest,
    auth_service: AuthServiceDep,
):
    """Initiates password reset flow."""
    await auth_service.request_password_reset(request.email)
    return {"message": "If an account with that email exists, a reset link has been sent."}


@router.post("/password/reset/confirm", response_model=StatusResponse)
async def reset_password(
    request: PasswordResetConfirm,
    auth_service: AuthServiceDep,
):
    """Validates token and updates password."""
    await auth_service.reset_password(request.token, request.new_password)
    return {"status": "success"}


@router.post("/login", response_model=AuthResponse)
async def login(
    request: LoginRequest,
    response: Response,
    auth_service: AuthServiceDep,
    x_client_type: str = Header(default="web", alias="X-Client-Type")
):
    """Standard credentials login."""
    token = await auth_service.login(request.email, request.password)
    if not token:
        raise UnauthorizedException("Invalid email or password")

    return handle_auth_result(response, token, x_client_type)


@router.post("/register", response_model=AuthResponse)
async def register(
    request: StandardRegisterRequest,
    response: Response,
    auth_service: AuthServiceDep,
    x_client_type: str = Header(default="web", alias="X-Client-Type")
):
    """Standard 3-step registration form."""
    token, checkout_url = await auth_service.register_standard(request.model_dump())

    return handle_auth_result(response, token, x_client_type, checkout_url)


@router.post("/google/verify", response_model=AuthResponse)
async def google_verify(
    request: GoogleVerifyRequest,
    response: Response,
    auth_service: AuthServiceDep,
    x_client_type: str = Header(default="web", alias="X-Client-Type")
):
    """Verifies Chrome Extension Google token and initializes session."""
    token = await auth_service.authenticate_with_google(request.token)

    return handle_auth_result(response, token, x_client_type)


@router.patch("/onboarding", response_model=AuthResponse)
async def google_onboarding(
    request: GoogleOnboardingRequest,
    auth_service: AuthServiceDep,
    current_user: CurrentUserDep,
):
    """Completes the profile for partial Google accounts."""
    checkout_url = await auth_service.complete_google_onboarding(
        user_id=current_user.id,
        data=request.model_dump()
    )
    return AuthResponse(checkout_url=checkout_url)


@router.get("/me", response_model=UserProfileResponse)
async def get_me(
    user_service: UserServiceDep,
    current_user: CurrentUserDep,
):
    """Returns the full profile and clinic data for the dashboard."""
    profile = await user_service.get_my_profile(current_user.id)
    if not profile:
        raise UnauthorizedException("User not found")
    return profile


@router.post("/logout", response_model=StatusResponse)
async def logout(
    response: Response,
    auth_service: AuthServiceDep,
    token: HTTPAuthorizationCredentials = Depends(security),
):
    """Revokes the current session."""
    await auth_service.logout(token.credentials)
    response.delete_cookie("session_id")
    return {"status": "success"}
```

## File: src/main.py
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.v1 import api_router
from src.api.health import router as health_router
from src.core.config import settings
from src.core.exceptions import setup_exception_handlers
from src.core.lifecycle import lifespan
from src.core.logging import setup_logging, get_logger
from src.core.middleware import RequestContextMiddleware

# Setup logging first
setup_logging()
logger = get_logger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Medical Copilot Extension API",
    version="1.0.0",
    lifespan=lifespan,
)

# Register exception handlers
setup_exception_handlers(app)

# Register middleware
app.add_middleware(RequestContextMiddleware)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(health_router)
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/")
def read_root():
    return {"message": "Welcome to Medroid API", "version": "1.0.0"}
```

## File: src/modules/auth/service.py
```python
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple, Dict, Any, TYPE_CHECKING

from src.core.logging import get_logger
from src.core.exceptions import ConflictException, UnauthorizedException, BadRequestException
from src.core.security import generate_session_token, hash_password, verify_password_async
from src.infrastructure.persistence.postgres.repos.auth_repo import AuthRepository
from src.infrastructure.persistence.postgres.repos.user_repo import UserRepository
from src.infrastructure.persistence.redis.sessions import SessionManager
from src.infrastructure.external.google_oauth import GoogleClient
from src.infrastructure.external.stripe import StripeClient
from src.infrastructure.external.razorpay import RazorpayClient

if TYPE_CHECKING:
    from src.modules.billing.service import BillingService
    from src.modules.emails.service import EmailService


from src.infrastructure.persistence.postgres.repos.password_resets_repo import PasswordResetsRepository

logger = get_logger(__name__)

class AuthService:
    def __init__(
        self,
        auth_repo: AuthRepository,
        user_repo: UserRepository,
        password_resets_repo: PasswordResetsRepository,
        session_manager: SessionManager,
        google_client: GoogleClient,
        stripe_client: StripeClient,
        razorpay_client: RazorpayClient,
        billing_service: "BillingService" = None,
        email_service: "EmailService" = None,
    ):
        self.auth_repo = auth_repo
        self.user_repo = user_repo
        self.password_resets_repo = password_resets_repo
        self.session_manager = session_manager
        self.google_client = google_client
        self.stripe_client = stripe_client
        self.razorpay_client = razorpay_client
        self.billing_service = billing_service
        self.email_service = email_service

    # --- Login ---

    async def login(self, email: str, password: str) -> str:
        """
        Standard email/password login logic.
        """
        user = await self.auth_repo.get_by_email(email)
        
        if not user:
            raise UnauthorizedException("Invalid email or password")
            
        # Check if they should be using Google instead
        if user.auth_provider == "google":
            raise BadRequestException("Please use 'Login with Google' for this account.")

        # Verify Password
        if not await verify_password_async(password, user.password_hash):
            raise UnauthorizedException("Invalid email or password")

        # Success: Generate session
        token = generate_session_token()
        await self.session_manager.create_session(
            token, user.id, user.role
        )
        return token

    # --- Google Flows ---

    async def authenticate_with_google(self, google_token: str) -> str:
        """
        Handles both login and initial registration for Google users.
        """
        # 1. Verify with Google
        google_user = await self.google_client.verify_access_token(google_token)
        
        # 2. Check DB
        user = await self.auth_repo.get_by_email(google_user["email"])
        
        if not user:
            user = await self.auth_repo.create_partial_google_user(
                email=google_user["email"],
                first_name=google_user["first_name"],
                last_name=google_user["last_name"]
            )
        
        # 3. Create Session
        token = generate_session_token()
        await self.session_manager.create_session(token, user.id, user.role)
        
        return token

    # --- Registration & Onboarding ---

    async def register_standard(self, data: Dict[str, Any]) -> Tuple[str, Optional[str]]:
        """
        Handles the full 3-step registration form.
        """
        # 1. Check duplicate
        if await self.auth_repo.get_by_email(data['email']):
            raise ConflictException("An account with this email already exists")

        # 2. Prepare Data
        password_hash = hash_password(data['password'])

        user_id = uuid.uuid4()
        user_payload = {
            "id": user_id,
            "email": data['email'],
            "password_hash": password_hash,
            **data['profile'],
            "registration_status": "completed"
        }

        # 3. Handle Payment Routing (delegated to BillingService)
        checkout_url, sub_payload = await self.billing_service.prepare_subscription_payload(
            user_id=user_id,
            email=data['email'],
            name=data['profile']['first_name'],
            country=data['clinic']['country'],
            plan_type=data['plan_type']
        )

        # 4. Atomic Transaction
        await self.auth_repo.create_standard_user(user_payload, data['clinic'], sub_payload)

        # 5. Create Session
        token = generate_session_token()
        await self.session_manager.create_session(token, user_id, "doctor")

        # 6. Send welcome email for free trial users
        if self.email_service and data['plan_type'] == 'free_trial':
            trial_end_date = (datetime.now(timezone.utc) + timedelta(days=14)).strftime("%B %d, %Y")
            await self.email_service.send_welcome_free_email(
                to_email=data['email'],
                to_name=data['profile']['first_name'],
                user_id=user_id,
                trial_end_date=trial_end_date,
            )

        return token, checkout_url

    # --- Google Onboarding ---

    async def complete_google_onboarding(
        self,
        user_id: uuid.UUID,
        data: Dict[str, Any]
    ) -> Optional[str]:
        """
        Finalizes a Google signup by adding clinic/profile details.
        """
        # 1. Fetch the partial user to get their email (needed for Stripe/Razorpay)
        user = await self.user_repo.get_with_details(user_id)
        if not user:
            raise UnauthorizedException("Session invalid or user not found")

        # 2. Handle Payment Routing (delegated to BillingService)
        checkout_url, sub_payload = await self.billing_service.prepare_subscription_payload(
            user_id=user_id,
            email=user.email,
            name=data['profile']['first_name'],
            country=data['clinic']['country'],
            plan_type=data['plan_type']
        )

        # 3. Update DB (Atomic Transaction)
        await self.auth_repo.complete_google_onboarding(
            user_id=user_id,
            user_update_data=data['profile'],
            clinic_data=data['clinic'],
            sub_data=sub_payload
        )

        return checkout_url

    async def logout(self, session_token: str):
        """
        Instantly revokes the user's access globally.
        """
        await self.session_manager.delete_session(session_token)

    # --- Password Reset ---

    async def request_password_reset(self, email: str):
        """
        Initiates the password reset flow.
        """
        from src.core.config import settings
        from src.core.logging import get_logger

        user = await self.auth_repo.get_by_email(email)

        # Security: We don't reveal if the user exists or not
        if not user or user.auth_provider == "google":
            logger.info(f"Password reset requested for non-existent or google user: {email}")
            return

        # 1. Create Token
        reset_entry = await self.password_resets_repo.create_reset_token(user.id)

        # 2. Send Email
        if self.email_service:
            # Construct link
            reset_link = f"{settings.FRONTEND_URL}/reset-password?token={reset_entry.token}&email={email}"

            await self.email_service.send_password_reset_email(
                to_email=user.email,
                to_name=user.first_name,
                user_id=user.id,
                reset_link=reset_link
            )

        logger.info(f"Password reset link sent to {email}")

    async def reset_password(self, token_uuid: uuid.UUID, new_password: str):
        """
        Validates the token and updates the user's password.
        """
        # 1. Verify Token
        reset_entry = await self.password_resets_repo.get_valid_token(token_uuid)
        if not reset_entry:
            raise BadRequestException("Invalid or expired reset token")

        # 2. Update Password
        password_hash = hash_password(new_password)
        await self.auth_repo.update_password(reset_entry.user_id, password_hash)

        # 3. Invalidate current Token
        await self.password_resets_repo.mark_token_used(reset_entry.id)

        # 4. Invalidate all other active reset tokens for this user
        await self.password_resets_repo.invalidate_user_tokens(reset_entry.user_id)

        logger.info(f"Password successfully reset for user {reset_entry.user_id}")
```
