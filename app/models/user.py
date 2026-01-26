"""User model for authentication."""

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.api_key import APIKey
    from app.models.audio_record import AudioRecord
    from app.models.refresh_token import RefreshToken
    from app.models.verification_log import VerificationLog


class User(BaseModel):
    """Model for user accounts."""

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )
    password_hash: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Null for OAuth-only users",
    )
    seed_phrase_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="SHA-256 hash of normalized seed phrase - NEVER store plaintext",
    )
    display_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # OAuth provider info
    oauth_provider: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        comment="OAuth provider: 'google', 'github', etc. Null for email/password users",
    )
    oauth_provider_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        index=True,
        comment="User ID from OAuth provider",
    )
    avatar_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="Profile picture URL from OAuth provider",
    )

    # Relationships
    api_keys: Mapped[list["APIKey"]] = relationship(
        "APIKey",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(
        "RefreshToken",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    audio_records: Mapped[list["AudioRecord"]] = relationship(
        "AudioRecord",
        back_populates="user",
    )
    verification_logs: Mapped[list["VerificationLog"]] = relationship(
        "VerificationLog",
        back_populates="user",
    )
