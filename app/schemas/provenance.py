"""Pydantic schemas for provenance endpoints."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class BlockInfo(BaseModel):
    """Information about a blockchain block."""

    block_index: int = Field(..., description="Block index in chain")
    block_hash: str = Field(..., description="SHA-256 hash of block")
    previous_hash: str = Field(..., description="Hash of previous block")
    timestamp: datetime = Field(..., description="Block creation timestamp")
    nonce: int = Field(..., description="Proof-of-work nonce")
    signature: str | None = Field(None, description="Ed25519 signature")


class AudioInfo(BaseModel):
    """Information about the audio record."""

    record_id: UUID = Field(..., description="Audio record UUID")
    original_hash: str = Field(..., description="Original audio hash")
    fingerprinted_hash: str | None = Field(None, description="Fingerprinted audio hash")
    creator_id: str | None = Field(None, description="Creator identifier")
    device_id: str | None = Field(None, description="Device identifier")
    file_name: str | None = Field(None, description="Original file name")
    duration_seconds: float | None = Field(None, description="Audio duration")
    created_at: datetime = Field(..., description="Record creation timestamp")


class LayerInfo(BaseModel):
    """Information about a fingerprint layer."""

    layer_type: str = Field(..., description="Layer identifier (A-F)")
    layer_hash: str = Field(..., description="Layer hash")
    confidence_score: float | None = Field(None, description="Layer confidence")
    version: str = Field(..., description="Algorithm version")


class ProvenanceResponse(BaseModel):
    """Response from provenance lookup."""

    found: bool = Field(..., description="Whether record was found")
    audio_info: AudioInfo | None = Field(None, description="Audio record information")
    layers: list[LayerInfo] | None = Field(None, description="Fingerprint layers")
    blockchain: BlockInfo | None = Field(None, description="Blockchain block info")
    chain_valid: bool | None = Field(None, description="Whether chain is valid")
    chain_length: int | None = Field(None, description="Length of chain to genesis")

    class Config:
        from_attributes = True
