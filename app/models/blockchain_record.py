"""Blockchain record model."""

from datetime import datetime

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class BlockchainRecord(BaseModel):
    """Model for blockchain blocks."""

    __tablename__ = "blockchain_records"

    block_index: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    block_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    previous_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    data: Mapped[dict] = mapped_column(JSONB, nullable=False)
    nonce: Mapped[int] = mapped_column(Integer, nullable=False)
    signature: Mapped[str | None] = mapped_column(String(128), nullable=True)
