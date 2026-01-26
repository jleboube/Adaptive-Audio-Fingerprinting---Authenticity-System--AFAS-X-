"""Fingerprint layer model."""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Float, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.audio_record import AudioRecord


class FingerprintLayer(BaseModel):
    """Model for storing individual fingerprint layer data."""

    __tablename__ = "fingerprint_layers"
    __table_args__ = (
        UniqueConstraint(
            "audio_record_id", "layer_type", "version", name="uq_layer_version"
        ),
    )

    audio_record_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("audio_records.id", ondelete="CASCADE"),
        nullable=False,
    )
    layer_type: Mapped[str] = mapped_column(String(1), nullable=False)
    layer_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    parameters: Mapped[dict] = mapped_column(JSONB, default=dict)
    version: Mapped[str] = mapped_column(String(20), nullable=False)

    # Relationships
    audio_record: Mapped["AudioRecord"] = relationship(
        "AudioRecord",
        back_populates="fingerprint_layers",
    )
