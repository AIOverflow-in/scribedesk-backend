"""SQLAlchemy ORM models for ScribeDesk."""

import uuid
from datetime import date, datetime
from typing import Optional

from sqlalchemy import Boolean, Date, DateTime, Integer, String, Text, ForeignKey, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


# --- Core Identity & Billing ---

class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[Optional[str]] = mapped_column(String(255))
    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[Optional[str]] = mapped_column(String(100))
    signature_url: Mapped[Optional[str]] = mapped_column(String(500))
    dob: Mapped[Optional[date]] = mapped_column(Date)
    gender: Mapped[Optional[str]] = mapped_column(String(20))
    speciality: Mapped[Optional[str]] = mapped_column(String(100))

    clinic: Mapped[Optional["Clinic"]] = relationship(back_populates="user", uselist=False, cascade="all, delete-orphan")
    patients: Mapped[list["Patient"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    sessions: Mapped[list["Session"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    templates: Mapped[list["Template"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class Clinic(Base):
    __tablename__ = "clinics"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    name: Mapped[str] = mapped_column(String(255))
    street: Mapped[Optional[str]] = mapped_column(String(255))
    city: Mapped[Optional[str]] = mapped_column(String(100))
    state: Mapped[Optional[str]] = mapped_column(String(100))
    pincode: Mapped[Optional[str]] = mapped_column(String(20))
    country: Mapped[Optional[str]] = mapped_column(String(2))
    logo_url: Mapped[Optional[str]] = mapped_column(String(500))

    user: Mapped["User"] = relationship(back_populates="clinic")


class Patient(TimestampMixin, Base):
    __tablename__ = "patients"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[Optional[str]] = mapped_column(String(100))
    email: Mapped[Optional[str]] = mapped_column(String(255))
    identifier: Mapped[Optional[str]] = mapped_column(String(100))
    date_of_birth: Mapped[Optional[date]] = mapped_column(Date)
    gender: Mapped[Optional[str]] = mapped_column(String(20))
    blood_group: Mapped[Optional[str]] = mapped_column(String(10))

    user: Mapped["User"] = relationship(back_populates="patients")
    sessions: Mapped[list["Session"]] = relationship(back_populates="patient")


class Session(TimestampMixin, Base):
    __tablename__ = "sessions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    patient_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("patients.id", ondelete="SET NULL"))
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="active")
    total_audio_seconds: Mapped[int] = mapped_column(Integer, default=0)
    current_segment_start: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    clinical_summary: Mapped[Optional[str]] = mapped_column(Text)
    last_summarized_transcript_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("session_timeline.id", ondelete="SET NULL"), nullable=True)

    user: Mapped["User"] = relationship(back_populates="sessions")
    patient: Mapped[Optional["Patient"]] = relationship(back_populates="sessions")
    timeline: Mapped[list["SessionTimeline"]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
        passive_deletes=True,
        foreign_keys="SessionTimeline.session_id",
    )
    reports: Mapped[list["Report"]] = relationship(back_populates="session", cascade="all, delete-orphan", passive_deletes=True)


class SessionTimeline(Base):
    __tablename__ = "session_timeline"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sessions.id", ondelete="CASCADE"))
    type: Mapped[str] = mapped_column(String(20))
    event_type: Mapped[Optional[str]] = mapped_column(String(20))
    content: Mapped[Optional[str]] = mapped_column(Text)
    speaker_id: Mapped[Optional[int]] = mapped_column(Integer)
    relative_seconds: Mapped[Optional[int]] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    session: Mapped["Session"] = relationship(back_populates="timeline", foreign_keys=[session_id])


# --- Reports & Templates ---

class Template(TimestampMixin, Base):
    __tablename__ = "templates"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255))
    root_type: Mapped[str] = mapped_column(String(50))
    sub_type: Mapped[Optional[str]] = mapped_column(String(50))
    content: Mapped[str] = mapped_column(Text)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))

    user: Mapped[Optional["User"]] = relationship(back_populates="templates")


class Report(TimestampMixin, Base):
    __tablename__ = "reports"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sessions.id", ondelete="CASCADE"))
    template_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("templates.id", ondelete="RESTRICT"))
    title: Mapped[str] = mapped_column(String(255))
    content: Mapped[str] = mapped_column(Text)
    report_metadata: Mapped[Optional[dict]] = mapped_column("report_metadata", JSONB)
    is_signed: Mapped[bool] = mapped_column(Boolean, default=False)
    signed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    content_hash: Mapped[Optional[str]] = mapped_column(String(64))

    session: Mapped["Session"] = relationship(back_populates="reports")
    template: Mapped["Template"] = relationship()
