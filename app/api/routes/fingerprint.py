"""Fingerprint endpoint for embedding audio fingerprints."""

from datetime import datetime, timezone
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_authenticated_user
from app.core.config import get_settings
from app.core.database import get_db
from app.models.audio_record import AudioRecord
from app.models.fingerprint_layer import FingerprintLayer
from app.models.user import User
from app.schemas.fingerprint import (
    FingerprintRequest,
    FingerprintResponse,
    LayerResult,
)
from app.services.blockchain import BlockchainService
from app.services.ethereum_blockchain import EthereumBlockchainService
from app.services.fingerprinting.pipeline import FingerprintPipeline

logger = structlog.get_logger()
router = APIRouter()
settings = get_settings()


@router.post("", response_model=FingerprintResponse)
async def create_fingerprint(
    request: FingerprintRequest,
    current_user: User = Depends(get_authenticated_user),
    db: AsyncSession = Depends(get_db),
) -> FingerprintResponse:
    """Embed fingerprints into audio and create blockchain record.

    **Authentication Required**: JWT token (Authorization: Bearer) or API key (X-API-Key header)

    This endpoint:
    1. Processes audio through all 6 fingerprint layers
    2. Embeds imperceptible fingerprints into the audio
    3. Creates a blockchain record for provenance
    4. Links the fingerprint to the authenticated user
    5. Returns the fingerprinted audio

    Args:
        request: FingerprintRequest with base64 audio and metadata
        current_user: Authenticated user (from JWT or API key)

    Returns:
        FingerprintResponse with fingerprinted audio and layer details
    """
    logger.info(
        "Fingerprint request received",
        file_name=request.file_name,
        creator_id=request.creator_id,
        user_id=str(current_user.id),
    )

    try:
        # Process audio through pipeline
        pipeline = FingerprintPipeline()
        result, fingerprinted_base64 = pipeline.process_base64(request.audio_base64)

        # Create database record - link to authenticated user
        audio_record = AudioRecord(
            user_id=current_user.id,  # Link fingerprint to user
            original_hash=result.original_hash,
            fingerprinted_hash=result.fingerprinted_hash,
            creator_id=request.creator_id or current_user.email,
            device_id=request.device_id,
            file_name=request.file_name,
            duration_seconds=result.duration_seconds,
            sample_rate=result.sample_rate,
            channels=1,  # Pipeline converts to mono
            extra_metadata=request.metadata or {},
        )
        db.add(audio_record)
        await db.flush()

        # Create fingerprint layer records
        layer_results = []
        for layer_output in result.layer_outputs:
            layer_record = FingerprintLayer(
                audio_record_id=audio_record.id,
                layer_type=layer_output.layer_type,
                layer_hash=layer_output.layer_hash,
                confidence_score=layer_output.confidence_score,
                parameters=layer_output.parameters,
                version=settings.fingerprint_version,
            )
            db.add(layer_record)

            layer_results.append(
                LayerResult(
                    layer_type=layer_output.layer_type,
                    layer_hash=layer_output.layer_hash,
                    confidence_score=layer_output.confidence_score,
                    parameters=layer_output.parameters,
                )
            )

        # Create local blockchain record
        blockchain_service = BlockchainService(db)
        block = await blockchain_service.add_block(
            {
                "type": "fingerprint",
                "original_hash": result.original_hash,
                "fingerprinted_hash": result.fingerprinted_hash,
                "audio_record_id": str(audio_record.id),
                "layer_hashes": {
                    lo.layer_type: lo.layer_hash for lo in result.layer_outputs
                },
                "version": settings.fingerprint_version,
                "creator_id": request.creator_id,
                "device_id": request.device_id,
            }
        )

        # Also register on Ethereum if configured
        eth_service = EthereumBlockchainService(db)
        eth_result = await eth_service.register_audio_on_chain(
            audio_hash=result.original_hash,
            fingerprint_hash=result.fingerprinted_hash,
            layer_hashes={lo.layer_type: lo.layer_hash for lo in result.layer_outputs},
            record_id=str(audio_record.id),
        )

        await db.commit()

        logger.info(
            "Fingerprint created successfully",
            record_id=str(audio_record.id),
            block_hash=block.hash[:16],
            ethereum_tx=eth_result.get("tx_hash"),
        )

        return FingerprintResponse(
            record_id=audio_record.id,
            original_hash=result.original_hash,
            fingerprinted_hash=result.fingerprinted_hash,
            fingerprinted_audio_base64=fingerprinted_base64,
            layers=layer_results,
            blockchain_hash=block.hash,
            ethereum_tx_hash=eth_result.get("tx_hash"),
            version=settings.fingerprint_version,
            created_at=datetime.now(timezone.utc),
        )

    except IntegrityError as e:
        await db.rollback()
        # Check if it's a duplicate audio hash
        if "audio_records_original_hash_key" in str(e) or "original_hash" in str(e):
            logger.warning(
                "Duplicate fingerprint attempt",
                original_hash=result.original_hash if 'result' in dir() else "unknown",
                user_id=str(current_user.id),
            )
            # Find the existing record
            existing = await db.execute(
                select(AudioRecord).where(
                    AudioRecord.original_hash == result.original_hash
                )
            )
            existing_record = existing.scalar_one_or_none()

            detail = "This audio file has already been fingerprinted."
            if existing_record:
                detail += f" Record ID: {existing_record.id}"
                if existing_record.user_id == current_user.id:
                    detail += " (owned by you)"
                else:
                    detail += " (owned by another user)"

            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=detail,
            )
        else:
            logger.error("Database integrity error", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database error occurred",
            )
    except Exception as e:
        logger.error("Fingerprint creation failed", error=str(e))
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create fingerprint: {str(e)}",
        )
