"""
models/message.py
─────────────────
Simple direct-message model for the built-in chat feature.
Threads are implicit: group by (min(sender_id, receiver_id), max(sender_id, receiver_id)).
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Text, func, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.config.database import Base


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # ── Participants ──────────────────────────────────────────────────────────
    sender_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    receiver_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True
    )

    # ── Content ───────────────────────────────────────────────────────────────
    content: Mapped[str]               = mapped_column(Text, nullable=False)
    attachment_url: Mapped[Optional[str]] = mapped_column(String(500))  # optional file

    # ── Status ────────────────────────────────────────────────────────────────
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)

    # ── Timestamps ────────────────────────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # ── Relationships ──────────────────────────────────────────────────────────
    sender:   Mapped["User"] = relationship("User", back_populates="sent_messages",     # noqa: F821
                                             foreign_keys=[sender_id])
    receiver: Mapped["User"] = relationship("User", back_populates="received_messages", # noqa: F821
                                             foreign_keys=[receiver_id])

    def __repr__(self) -> str:
        return f"<Message {self.id} from {self.sender_id}>"
