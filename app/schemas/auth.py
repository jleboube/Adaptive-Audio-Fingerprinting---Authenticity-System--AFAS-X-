"""Pydantic schemas for authentication."""

import re
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator


# =============================================================================
# User Registration
# =============================================================================


class RegisterRequest(BaseModel):
    """Request schema for user registration."""

    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, max_length=128, description="Password")
    display_name: str | None = Field(None, max_length=100, description="Display name")

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Ensure password has uppercase, lowercase, and digit."""
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit")
        return v


class RegisterResponse(BaseModel):
    """Response schema for user registration."""

    user_id: UUID
    email: str
    display_name: str | None
    seed_phrase: str = Field(
        ...,
        description="24-word BIP-39 seed phrase - SAVE THIS! It will NEVER be shown again.",
    )
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                "email": "user@example.com",
                "display_name": "John Doe",
                "seed_phrase": "word1 word2 word3 ... word24",
                "access_token": "eyJ...",
                "refresh_token": "eyJ...",
                "token_type": "bearer",
            }
        }


# =============================================================================
# Login
# =============================================================================


class LoginRequest(BaseModel):
    """Request schema for login."""

    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="Password")


class LoginResponse(BaseModel):
    """Response schema for login."""

    user_id: UUID
    email: str
    display_name: str | None
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


# =============================================================================
# Token Refresh
# =============================================================================


class TokenRefreshRequest(BaseModel):
    """Request schema for token refresh."""

    refresh_token: str = Field(..., description="Refresh token")


class TokenRefreshResponse(BaseModel):
    """Response schema for token refresh."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


# =============================================================================
# User Info
# =============================================================================


class UserResponse(BaseModel):
    """Response schema for user info."""

    id: UUID
    email: str
    display_name: str | None
    avatar_url: str | None = None
    oauth_provider: str | None = None
    is_active: bool
    created_at: datetime


class UserUpdateRequest(BaseModel):
    """Request schema for updating user info."""

    display_name: str | None = Field(None, max_length=100)


# =============================================================================
# API Keys
# =============================================================================


class APIKeyCreateRequest(BaseModel):
    """Request schema for creating an API key."""

    name: str = Field(..., min_length=1, max_length=100, description="Name for the key")
    scopes: list[str] = Field(
        default=["fingerprint:create", "verify:read"],
        description="Permission scopes",
    )
    expires_in_days: int | None = Field(
        None,
        ge=1,
        le=365,
        description="Days until expiration (None = never expires)",
    )


class APIKeyCreateResponse(BaseModel):
    """Response schema for created API key - shows full key ONCE."""

    id: UUID
    name: str
    key: str = Field(..., description="Full API key - SAVE THIS! It will NEVER be shown again.")
    key_prefix: str
    scopes: list[str]
    expires_at: datetime | None
    created_at: datetime


class APIKeyListItem(BaseModel):
    """Schema for API key in list (no full key shown)."""

    id: UUID
    name: str
    key_prefix: str
    scopes: list[str]
    is_active: bool
    expires_at: datetime | None
    last_used_at: datetime | None
    created_at: datetime


class APIKeyListResponse(BaseModel):
    """Response schema for listing API keys."""

    keys: list[APIKeyListItem]
    total: int


# =============================================================================
# Seed Phrase Verification (Ownership Proof)
# =============================================================================


class VerifyOwnershipRequest(BaseModel):
    """Request schema for verifying fingerprint ownership via seed phrase."""

    seed_phrase: str = Field(..., description="24-word BIP-39 seed phrase")
    record_id: UUID = Field(..., description="Fingerprint record ID to verify ownership of")


class VerifyOwnershipResponse(BaseModel):
    """Response schema for ownership verification."""

    verified: bool
    message: str
    record_id: UUID | None = None
    owner_email: str | None = None
    created_at: datetime | None = None


# =============================================================================
# Google OAuth
# =============================================================================


class GoogleOAuthResponse(BaseModel):
    """Response schema for Google OAuth login/register."""

    user_id: UUID
    email: str
    display_name: str | None
    avatar_url: str | None
    is_new_user: bool
    seed_phrase: str | None = Field(
        None,
        description="Only returned for new users - SAVE THIS! It will NEVER be shown again.",
    )
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class GoogleAuthUrlResponse(BaseModel):
    """Response schema for Google OAuth authorization URL."""

    auth_url: str
