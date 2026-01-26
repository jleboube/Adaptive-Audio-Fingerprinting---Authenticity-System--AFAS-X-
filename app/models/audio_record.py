"""Audio record model."""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.fingerprint_layer import FingerprintLayer
    from app.models.user import User
    from app.models.verification_log import VerificationLog


class AudioRecord(BaseModel):
    """Model for storing audio file metadata and hashes."""

    __tablename__ = "audio_records"

    # User relationship - links fingerprint to owner
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    original_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    fingerprinted_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    creator_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    device_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    file_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    sample_rate: Mapped[int | None] = mapped_column(Integer, nullable=True)
    channels: Mapped[int | None] = mapped_column(Integer, nullable=True)
    file_size_bytes: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    mime_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    extra_metadata: Mapped[dict] = mapped_column(JSONB, default=dict)

    # Relationships
    user: Mapped["User | None"] = relationship("User", back_populates="audio_records")
    fingerprint_layers: Mapped[list["FingerprintLayer"]] = relationship(
        "FingerprintLayer",
        back_populates="audio_record",
        cascade="all, delete-orphan",
    )
    verification_logs: Mapped[list["VerificationLog"]] = relationship(
        "VerificationLog",
        back_populates="audio_record",
    )
