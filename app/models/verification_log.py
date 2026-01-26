"""Verification log model."""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.audio_record import AudioRecord
    from app.models.user import User


class VerificationLog(BaseModel):
    """Model for tracking verification attempts."""

    __tablename__ = "verification_logs"

    audio_record_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("audio_records.id", ondelete="SET NULL"),
        nullable=True,
    )
    # User who performed verification (if authenticated)
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    submitted_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    verification_result: Mapped[str] = mapped_column(String(20), nullable=False)
    confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    layer_results: Mapped[dict] = mapped_column(JSONB, default=dict)
    blockchain_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    audio_record: Mapped["AudioRecord | None"] = relationship(
        "AudioRecord",
        back_populates="verification_logs",
    )
    user: Mapped["User | None"] = relationship("User", back_populates="verification_logs")
