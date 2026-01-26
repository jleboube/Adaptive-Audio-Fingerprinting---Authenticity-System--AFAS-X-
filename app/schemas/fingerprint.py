"""Pydantic schemas for fingerprinting endpoints."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class LayerResult(BaseModel):
    """Result from a single fingerprint layer."""

    layer_type: str = Field(..., description="Layer identifier (A-F)")
    layer_hash: str = Field(..., description="SHA-256 hash of layer data")
    confidence_score: float = Field(
        ..., ge=0.0, le=1.0, description="Confidence score for this layer"
    )
    parameters: dict = Field(default_factory=dict, description="Layer parameters used")


class FingerprintRequest(BaseModel):
    """Request body for fingerprinting audio."""

    audio_base64: str = Field(..., description="Base64-encoded audio data")
    file_name: str | None = Field(None, description="Original file name")
    creator_id: str | None = Field(None, description="Creator identifier")
    device_id: str | None = Field(None, description="Device identifier")
    metadata: dict | None = Field(None, description="Additional metadata")


class FingerprintResponse(BaseModel):
    """Response from fingerprinting operation."""

    record_id: UUID = Field(..., description="Audio record UUID")
    original_hash: str = Field(..., description="Hash of original audio")
    fingerprinted_hash: str = Field(..., description="Hash of fingerprinted audio")
    fingerprinted_audio_base64: str = Field(
        ..., description="Base64-encoded fingerprinted audio"
    )
    layers: list[LayerResult] = Field(..., description="Results from each layer")
    blockchain_hash: str = Field(..., description="Blockchain block hash")
    ethereum_tx_hash: str | None = Field(None, description="Ethereum transaction hash (if on-chain)")
    version: str = Field(..., description="Fingerprint algorithm version")
    created_at: datetime = Field(..., description="Timestamp of creation")

    class Config:
        from_attributes = True
