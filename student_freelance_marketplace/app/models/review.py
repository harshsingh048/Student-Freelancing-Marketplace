"""
models/review.py
────────────────
Review left by a Client after an order is completed.
Rating (1–5) auto-updates the student's average_rating.
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.config.database import Base


class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # ── Foreign keys ─────────────────────────────────────────────────────────
    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False, unique=True          # one review per order
    )
    client_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    gig_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("gigs.id", ondelete="SET NULL"), nullable=True
    )

    # ── Review content ───────────────────────────────────────────────────────
    rating: Mapped[int]              = mapped_column(Integer, nullable=False)
    comment: Mapped[Optional[str]]   = mapped_column(Text)

    # ── DB-level constraint: rating must be 1-5 ───────────────────────────────
    __table_args__ = (
        CheckConstraint("rating >= 1 AND rating <= 5", name="rating_range"),
    )

    # ── Timestamps ───────────────────────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # ── Relationships ─────────────────────────────────────────────────────────
    order:   Mapped["Order"] = relationship("Order", back_populates="review")   # noqa: F821
    client:  Mapped["User"]  = relationship("User", back_populates="reviews_given",    # noqa: F821
                                             foreign_keys=[client_id])
    student: Mapped["User"]  = relationship("User", back_populates="reviews_received", # noqa: F821
                                             foreign_keys=[student_id])
    gig:     Mapped[Optional["Gig"]] = relationship("Gig", back_populates="reviews")   # noqa: F821

    def __repr__(self) -> str:
        return f"<Review {self.rating}★ on order {self.order_id}>"
