"""
models/gig.py
─────────────
A Gig is a service offered by a Student.
"""

import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text, func, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.config.database import Base
import enum


class GigCategory(str, enum.Enum):
    WEB_DEVELOPMENT    = "web_development"
    MOBILE_APP         = "mobile_app"
    GRAPHIC_DESIGN     = "graphic_design"
    CONTENT_WRITING    = "content_writing"
    DATA_SCIENCE       = "data_science"
    VIDEO_EDITING      = "video_editing"
    DIGITAL_MARKETING  = "digital_marketing"
    TUTORING           = "tutoring"
    OTHER              = "other"


class Gig(Base):
    __tablename__ = "gigs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # ── FK to the student who created this gig ───────────────────────────────
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # ── Core fields ──────────────────────────────────────────────────────────
    title: Mapped[str]         = mapped_column(String(200), nullable=False)
    description: Mapped[str]   = mapped_column(Text, nullable=False)
    category: Mapped[GigCategory] = mapped_column(
        Enum(GigCategory, name="gigcategory"), nullable=False
    )
    price: Mapped[float]       = mapped_column(Numeric(10, 2), nullable=False)
    delivery_days: Mapped[int] = mapped_column(Integer, nullable=False)   # delivery time in days
    revision_count: Mapped[int]= mapped_column(Integer, default=1)

    # ── Media & status ───────────────────────────────────────────────────────
    thumbnail_url: Mapped[Optional[str]] = mapped_column(String(500))
    is_active: Mapped[bool]              = mapped_column(Boolean, default=True)

    # ── Timestamps ───────────────────────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # ── Relationships ────────────────────────────────────────────────────────
    student: Mapped["User"]           = relationship("User", back_populates="gigs")           # noqa: F821
    orders:  Mapped[List["Order"]]    = relationship("Order", back_populates="gig")            # noqa: F821
    reviews: Mapped[List["Review"]]   = relationship("Review", back_populates="gig")           # noqa: F821

    def __repr__(self) -> str:
        return f"<Gig '{self.title}' by {self.student_id}>"
