"""Provenance endpoint for retrieving blockchain records."""

import structlog
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.audio_record import AudioRecord
from app.models.fingerprint_layer import FingerprintLayer
from app.schemas.provenance import (
    AudioInfo,
    BlockInfo,
    LayerInfo,
    ProvenanceResponse,
)
from app.services.blockchain import BlockchainService

logger = structlog.get_logger()
router = APIRouter()


@router.get("/{audio_hash}", response_model=ProvenanceResponse)
async def get_provenance(
    audio_hash: str,
    db: AsyncSession = Depends(get_db),
) -> ProvenanceResponse:
    """Get provenance information for an audio file.

    This endpoint retrieves:
    1. Audio record metadata
    2. All fingerprint layer information
    3. Blockchain record and chain validation

    Args:
        audio_hash: SHA-256 hash of original or fingerprinted audio

    Returns:
        ProvenanceResponse with complete provenance information
    """
    logger.info("Provenance lookup", hash=audio_hash[:16])

    # Find audio record by hash
    result = await db.execute(
        select(AudioRecord).where(
            (AudioRecord.original_hash == audio_hash)
            | (AudioRecord.fingerprinted_hash == audio_hash)
        )
    )
    record = result.scalar_one_or_none()

    if not record:
        return ProvenanceResponse(
            found=False,
            audio_info=None,
            layers=None,
            blockchain=None,
            chain_valid=None,
            chain_length=None,
        )

    # Get fingerprint layers
    layers_result = await db.execute(
        select(FingerprintLayer).where(FingerprintLayer.audio_record_id == record.id)
    )
    layers = layers_result.scalars().all()

    # Get blockchain record
    blockchain_service = BlockchainService(db)
    block = await blockchain_service.find_block_by_audio_hash(record.original_hash)

    block_info = None
    chain_valid = None
    chain_length = None

    if block:
        block_info = BlockInfo(
            block_index=block.block_index,
            block_hash=block.block_hash,
            previous_hash=block.previous_hash,
            timestamp=block.timestamp,
            nonce=block.nonce,
            signature=block.signature,
        )

        # Verify chain integrity
        is_valid, errors = await blockchain_service.verify_chain(
            up_to_index=block.block_index
        )
        chain_valid = is_valid

        # Get chain length
        chain = await blockchain_service.get_chain_to_genesis(block.block_hash)
        chain_length = len(chain)

        if not is_valid:
            logger.warning(
                "Chain validation failed",
                block_index=block.block_index,
                errors=errors,
            )

    logger.info(
        "Provenance lookup complete",
        record_id=str(record.id),
        has_blockchain=block is not None,
        chain_valid=chain_valid,
    )

    return ProvenanceResponse(
        found=True,
        audio_info=AudioInfo(
            record_id=record.id,
            original_hash=record.original_hash,
            fingerprinted_hash=record.fingerprinted_hash,
            creator_id=record.creator_id,
            device_id=record.device_id,
            file_name=record.file_name,
            duration_seconds=record.duration_seconds,
            created_at=record.created_at,
        ),
        layers=[
            LayerInfo(
                layer_type=layer.layer_type,
                layer_hash=layer.layer_hash,
                confidence_score=layer.confidence_score,
                version=layer.version,
            )
            for layer in layers
        ],
        blockchain=block_info,
        chain_valid=chain_valid,
        chain_length=chain_length,
    )
