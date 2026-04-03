"""
models/order.py
───────────────
Order placed by a Client for a Student's Gig.
Includes escrow-style payment status tracking.
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Enum, ForeignKey, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.config.database import Base
import enum


class OrderStatus(str, enum.Enum):
    PENDING     = "pending"       # order created, awaiting payment
    IN_PROGRESS = "in_progress"   # payment done, student working
    DELIVERED   = "delivered"     # student marked as delivered
    COMPLETED   = "completed"     # client approved delivery
    CANCELLED   = "cancelled"     # cancelled by either party
    DISPUTED    = "disputed"      # under dispute resolution


class PaymentStatus(str, enum.Enum):
    UNPAID    = "unpaid"          # no payment yet
    HELD      = "held"            # escrowed (paid but not released)
    RELEASED  = "released"        # payment sent to student
    REFUNDED  = "refunded"        # payment returned to client


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # ── Foreign keys ─────────────────────────────────────────────────────────
    gig_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("gigs.id", ondelete="SET NULL"), nullable=True
    )
    client_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # ── Pricing snapshot (captured at time of order) ─────────────────────────
    amount: Mapped[float]          = mapped_column(Numeric(10, 2), nullable=False)
    platform_fee: Mapped[float]    = mapped_column(Numeric(10, 2), default=0.0)
    student_earnings: Mapped[float]= mapped_column(Numeric(10, 2), default=0.0)

    # ── Status ───────────────────────────────────────────────────────────────
    status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus, name="orderstatus"), default=OrderStatus.PENDING
    )
    payment_status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus, name="paymentstatus"), default=PaymentStatus.UNPAID
    )

    # ── Mock payment fields (Razorpay simulation) ─────────────────────────────
    razorpay_order_id: Mapped[Optional[str]]   = mapped_column(String(100))
    razorpay_payment_id: Mapped[Optional[str]] = mapped_column(String(100))
    razorpay_signature: Mapped[Optional[str]]  = mapped_column(String(255))

    # ── Delivery ─────────────────────────────────────────────────────────────
    requirements: Mapped[Optional[str]]     = mapped_column(Text)   # client's brief
    delivery_note: Mapped[Optional[str]]    = mapped_column(Text)   # student's delivery message
    expected_delivery: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # ── Timestamps ───────────────────────────────────────────────────────────
    created_at: Mapped[datetime]  = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime]  = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # ── Relationships ─────────────────────────────────────────────────────────
    gig:     Mapped["Gig"]    = relationship("Gig", back_populates="orders")                # noqa: F821
    client:  Mapped["User"]   = relationship("User", back_populates="orders_as_client",     # noqa: F821
                                              foreign_keys=[client_id])
    student: Mapped["User"]   = relationship("User", back_populates="orders_as_student",    # noqa: F821
                                              foreign_keys=[student_id])
    review:  Mapped[Optional["Review"]] = relationship("Review", back_populates="order",    # noqa: F821
                                                         uselist=False)

    def __repr__(self) -> str:
        return f"<Order {self.id} [{self.status}]>"
