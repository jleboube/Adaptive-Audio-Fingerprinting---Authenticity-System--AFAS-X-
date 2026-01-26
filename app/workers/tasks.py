"""Celery tasks for background processing."""

import asyncio
from datetime import datetime, timedelta, timezone

import structlog
from celery import shared_task
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.core.config import get_settings
from app.models.verification_log import VerificationLog
from app.services.blockchain import BlockchainService
from app.services.fingerprinting.pipeline import FingerprintPipeline

logger = structlog.get_logger()
settings = get_settings()


def get_async_session() -> async_sessionmaker[AsyncSession]:
    """Create async session for Celery tasks."""
    engine = create_async_engine(settings.database_url)
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


def run_async(coro):
    """Run async function in sync context."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@shared_task(name="app.workers.tasks.process_fingerprint")
def process_fingerprint_task(audio_base64: str, metadata: dict) -> dict:
    """Background task for processing large audio files.

    Args:
        audio_base64: Base64-encoded audio
        metadata: Additional metadata

    Returns:
        dict with processing results
    """
    logger.info("Processing fingerprint in background", metadata=metadata)

    try:
        pipeline = FingerprintPipeline()
        result, fingerprinted_base64 = pipeline.process_base64(audio_base64)

        return {
            "status": "success",
            "original_hash": result.original_hash,
            "fingerprinted_hash": result.fingerprinted_hash,
            "duration_seconds": result.duration_seconds,
            "layer_count": len(result.layer_outputs),
            "fingerprinted_audio_base64": fingerprinted_base64,
        }

    except Exception as e:
        logger.error("Background fingerprint processing failed", error=str(e))
        return {
            "status": "error",
            "error": str(e),
        }


@shared_task(name="app.workers.tasks.cleanup_old_logs")
def cleanup_old_logs(days: int = 90) -> dict:
    """Clean up old verification logs.

    Args:
        days: Delete logs older than this many days

    Returns:
        dict with cleanup results
    """
    logger.info("Starting verification log cleanup", days=days)

    async def _cleanup():
        async_session = get_async_session()
        async with async_session() as session:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

            result = await session.execute(
                delete(VerificationLog).where(
                    VerificationLog.created_at < cutoff_date
                )
            )
            deleted_count = result.rowcount
            await session.commit()

            return deleted_count

    try:
        deleted = run_async(_cleanup())
        logger.info("Verification log cleanup complete", deleted_count=deleted)
        return {"status": "success", "deleted_count": deleted}
    except Exception as e:
        logger.error("Cleanup failed", error=str(e))
        return {"status": "error", "error": str(e)}


@shared_task(name="app.workers.tasks.verify_blockchain")
def verify_blockchain() -> dict:
    """Verify blockchain integrity.

    Returns:
        dict with verification results
    """
    logger.info("Starting blockchain integrity verification")

    async def _verify():
        async_session = get_async_session()
        async with async_session() as session:
            blockchain_service = BlockchainService(session)
            is_valid, errors = await blockchain_service.verify_chain()

            latest = await blockchain_service.get_latest_block()
            chain_length = latest.block_index + 1 if latest else 0

            return is_valid, errors, chain_length

    try:
        is_valid, errors, chain_length = run_async(_verify())

        if not is_valid:
            logger.error(
                "Blockchain integrity check failed",
                errors=errors,
                chain_length=chain_length,
            )
        else:
            logger.info(
                "Blockchain integrity verified",
                chain_length=chain_length,
            )

        return {
            "status": "success" if is_valid else "warning",
            "is_valid": is_valid,
            "errors": errors,
            "chain_length": chain_length,
        }

    except Exception as e:
        logger.error("Blockchain verification failed", error=str(e))
        return {"status": "error", "error": str(e)}


@shared_task(name="app.workers.tasks.batch_fingerprint")
def batch_fingerprint_task(audio_items: list[dict]) -> dict:
    """Process multiple audio files in batch.

    Args:
        audio_items: List of dicts with 'audio_base64' and 'metadata'

    Returns:
        dict with batch processing results
    """
    logger.info("Starting batch fingerprint processing", count=len(audio_items))

    results = []
    for i, item in enumerate(audio_items):
        try:
            result = process_fingerprint_task(
                item.get("audio_base64", ""),
                item.get("metadata", {}),
            )
            results.append({"index": i, **result})
        except Exception as e:
            results.append({"index": i, "status": "error", "error": str(e)})

    success_count = sum(1 for r in results if r.get("status") == "success")

    logger.info(
        "Batch processing complete",
        total=len(audio_items),
        success=success_count,
        failed=len(audio_items) - success_count,
    )

    return {
        "status": "complete",
        "total": len(audio_items),
        "success": success_count,
        "results": results,
    }
