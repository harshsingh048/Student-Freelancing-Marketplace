"""
models/user.py
──────────────
User model covering all three roles: student, client, admin.
Student-specific fields (skills, bio, portfolio, rating) are
stored here for simplicity; a separate StudentProfile table
could be used in a larger system.
"""

import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    Boolean, DateTime, Enum, Float, Integer,
    String, Text, func, JSON
)
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.config.database import Base
import enum


class UserRole(str, enum.Enum):
    STUDENT = "student"
    CLIENT  = "client"
    ADMIN   = "admin"


class User(Base):
    __tablename__ = "users"

    # ── Primary key ──────────────────────────────────────────────────────────
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # ── Auth fields ──────────────────────────────────────────────────────────
    email: Mapped[str]           = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)

    # ── Role & status ────────────────────────────────────────────────────────
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="userrole"), default=UserRole.CLIENT, nullable=False
    )
    is_active: Mapped[bool]   = mapped_column(Boolean, default=True)
    is_banned: Mapped[bool]   = mapped_column(Boolean, default=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)

    # ── Common profile ───────────────────────────────────────────────────────
    full_name: Mapped[str]              = mapped_column(String(150), nullable=False)
    avatar_url: Mapped[Optional[str]]   = mapped_column(String(500))
    phone: Mapped[Optional[str]]        = mapped_column(String(20))

    # ── Student-only profile ─────────────────────────────────────────────────
    bio: Mapped[Optional[str]]          = mapped_column(Text)
    skills: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String), default=list)
    portfolio_links: Mapped[Optional[dict]] = mapped_column(JSON, default=list)
    # e.g. [{"title": "My App", "url": "https://...", "image_url": "..."}]

    # ── Rating (auto-updated by review controller) ────────────────────────────
    average_rating: Mapped[float] = mapped_column(Float, default=0.0)
    total_reviews: Mapped[int]    = mapped_column(Integer, default=0)

    # ── Timestamps ───────────────────────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # ── Relationships ────────────────────────────────────────────────────────
    # Student → Gigs they created
    gigs: Mapped[List["Gig"]] = relationship(        # noqa: F821
        "Gig", back_populates="student", cascade="all, delete-orphan"
    )
    # Client → Orders they placed
    orders_as_client: Mapped[List["Order"]] = relationship(  # noqa: F821
        "Order", back_populates="client", foreign_keys="Order.client_id",
        cascade="all, delete-orphan"
    )
    # Student → Orders assigned to them
    orders_as_student: Mapped[List["Order"]] = relationship(  # noqa: F821
        "Order", back_populates="student", foreign_keys="Order.student_id"
    )
    # Client → Reviews they wrote
    reviews_given: Mapped[List["Review"]] = relationship(    # noqa: F821
        "Review", back_populates="client", foreign_keys="Review.client_id"
    )
    # Student → Reviews they received
    reviews_received: Mapped[List["Review"]] = relationship( # noqa: F821
        "Review", back_populates="student", foreign_keys="Review.student_id"
    )
    # Messages (both sides)
    sent_messages: Mapped[List["Message"]] = relationship(   # noqa: F821
        "Message", back_populates="sender", foreign_keys="Message.sender_id"
    )
    received_messages: Mapped[List["Message"]] = relationship( # noqa: F821
        "Message", back_populates="receiver", foreign_keys="Message.receiver_id"
    )

    def __repr__(self) -> str:
        return f"<User {self.email} [{self.role}]>"
