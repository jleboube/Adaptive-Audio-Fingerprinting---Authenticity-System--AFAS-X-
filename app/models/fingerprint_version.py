"""Fingerprint version model."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class FingerprintVersion(BaseModel):
    """Model for tracking fingerprint algorithm versions."""

    __tablename__ = "fingerprint_versions"

    version: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    algorithm_config: Mapped[dict] = mapped_column(JSONB, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    deprecated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
