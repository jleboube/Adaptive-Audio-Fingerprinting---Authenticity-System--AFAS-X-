"""Verify endpoint for checking audio authenticity."""

from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_authenticated_user_optional
from app.core.database import get_db
from app.models.user import User
from app.models.verification_log import VerificationLog
from app.schemas.verify import (
    LayerVerificationResult,
    VerificationResult,
    VerifyRequest,
    VerifyResponse,
)
from app.services.verification import VerificationService

logger = structlog.get_logger()
router = APIRouter()


@router.post("", response_model=VerifyResponse)
async def verify_audio(
    request: VerifyRequest,
    http_request: Request,
    current_user: User | None = Depends(get_authenticated_user_optional),
    db: AsyncSession = Depends(get_db),
) -> VerifyResponse:
    """Verify audio authenticity against stored fingerprints.

    **Authentication Optional**: If provided (JWT or API key), the verification
    will be logged with the user's ID for audit purposes.

    This endpoint:
    1. Extracts fingerprints from the submitted audio
    2. Compares against stored fingerprint records
    3. Verifies blockchain provenance
    4. Returns detailed verification results
    5. Logs verification with user_id if authenticated

    Args:
        request: VerifyRequest with base64 audio
        http_request: HTTP request for logging metadata
        current_user: Optional authenticated user

    Returns:
        VerifyResponse with verification results
    """
    logger.info(
        "Verification request received",
        user_id=str(current_user.id) if current_user else None,
    )

    try:
        # Run verification
        service = VerificationService(db)
        result = await service.verify(
            audio_base64=request.audio_base64,
            expected_hash=request.original_hash,
        )

        # Log verification attempt (with user_id if authenticated)
        log_entry = VerificationLog(
            audio_record_id=UUID(result.record_id) if result.record_id else None,
            user_id=current_user.id if current_user else None,
            submitted_hash=result.original_hash or "unknown",
            verification_result=result.result.value,
            confidence_score=result.confidence_score,
            layer_results={
                lr.layer_type: {
                    "matches": lr.matches,
                    "confidence": lr.confidence,
                    "details": lr.details,
                }
                for lr in result.layer_results
            },
            blockchain_verified=result.blockchain_verified,
            ip_address=http_request.client.host if http_request.client else None,
            user_agent=http_request.headers.get("user-agent"),
        )
        db.add(log_entry)
        await db.commit()

        logger.info(
            "Verification complete",
            result=result.result.value,
            confidence=result.confidence_score,
            blockchain_verified=result.blockchain_verified,
        )

        return VerifyResponse(
            result=VerificationResult(result.result.value),
            confidence_score=result.confidence_score,
            record_id=UUID(result.record_id) if result.record_id else None,
            original_hash=result.original_hash,
            layer_results=[
                LayerVerificationResult(
                    layer_type=lr.layer_type,
                    matches=lr.matches,
                    confidence=lr.confidence,
                    details=lr.details,
                )
                for lr in result.layer_results
            ],
            blockchain_verified=result.blockchain_verified,
            provenance_chain=result.provenance_chain,
            verified_at=result.verified_at,
        )

    except Exception as e:
        logger.error("Verification failed", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Verification failed: {str(e)}",
        )
