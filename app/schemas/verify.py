"""Pydantic schemas for verification endpoints."""

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field


class VerificationResult(str, Enum):
    """Possible verification outcomes."""

    AUTHENTIC = "AUTHENTIC"
    MODIFIED = "MODIFIED"
    UNKNOWN = "UNKNOWN"
    FAILED = "FAILED"


class LayerVerificationResult(BaseModel):
    """Verification result for a single layer."""

    layer_type: str = Field(..., description="Layer identifier (A-F)")
    matches: bool = Field(..., description="Whether layer matches stored fingerprint")
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Confidence of match/mismatch"
    )
    details: str | None = Field(None, description="Additional verification details")


class VerifyRequest(BaseModel):
    """Request body for verifying audio."""

    audio_base64: str = Field(..., description="Base64-encoded audio to verify")
    original_hash: str | None = Field(
        None, description="Expected original hash (optional)"
    )


class VerifyResponse(BaseModel):
    """Response from verification operation."""

    result: VerificationResult = Field(..., description="Overall verification result")
    confidence_score: float = Field(
        ..., ge=0.0, le=1.0, description="Overall confidence score"
    )
    record_id: UUID | None = Field(None, description="Matched audio record ID")
    original_hash: str | None = Field(None, description="Original audio hash")
    layer_results: list[LayerVerificationResult] = Field(
        ..., description="Per-layer verification results"
    )
    blockchain_verified: bool = Field(
        ..., description="Whether blockchain record was verified"
    )
    provenance_chain: list[str] | None = Field(
        None, description="Chain of block hashes"
    )
    verified_at: datetime = Field(..., description="Verification timestamp")

    class Config:
        from_attributes = True
