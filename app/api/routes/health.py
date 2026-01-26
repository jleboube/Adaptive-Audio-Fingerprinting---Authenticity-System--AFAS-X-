"""Health check and stats endpoints."""

from datetime import datetime, timezone
from typing import Any

import structlog
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.audio_record import AudioRecord
from app.models.blockchain_record import BlockchainRecord
from app.services.ethereum_blockchain import EthereumBlockchainService

logger = structlog.get_logger()
router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    timestamp: str
    services: dict[str, str]


class StatsResponse(BaseModel):
    """System stats response."""

    api_status: str
    database_status: str
    redis_status: str
    blockchain_status: str
    blockchain_blocks: int
    blockchain_synced: bool
    ethereum_connected: bool
    ethereum_network: str | None
    ethereum_wallet: str | None
    ethereum_balance: float | None
    total_fingerprints: int
    total_verifications: int
    active_layers: int
    timestamp: str


@router.get("/health", response_model=HealthResponse)
async def health_check(db: AsyncSession = Depends(get_db)) -> HealthResponse:
    """Check health of all services."""
    services = {}

    # Check database
    try:
        await db.execute(text("SELECT 1"))
        services["database"] = "up"
    except Exception as e:
        logger.error("Database health check failed", error=str(e))
        services["database"] = "down"

    # Check Redis (via Celery if configured)
    try:
        from app.workers.celery_app import celery_app

        celery_app.control.ping(timeout=1)
        services["redis"] = "up"
    except Exception:
        services["redis"] = "unknown"

    # Overall status
    status = "healthy" if services.get("database") == "up" else "unhealthy"

    return HealthResponse(
        status=status,
        timestamp=datetime.now(timezone.utc).isoformat(),
        services=services,
    )


@router.get("/stats", response_model=StatsResponse)
async def get_stats(db: AsyncSession = Depends(get_db)) -> StatsResponse:
    """Get system statistics for dashboard."""
    # Check database
    db_status = "up"
    try:
        await db.execute(text("SELECT 1"))
    except Exception:
        db_status = "down"

    # Check Redis
    redis_status = "up"
    try:
        from app.workers.celery_app import celery_app
        celery_app.control.ping(timeout=1)
    except Exception:
        redis_status = "unknown"

    # Get blockchain stats
    blockchain_blocks = 0
    blockchain_synced = False
    try:
        result = await db.execute(select(func.count()).select_from(BlockchainRecord))
        blockchain_blocks = result.scalar() or 0
        blockchain_synced = blockchain_blocks > 0
    except Exception as e:
        logger.error("Blockchain stats failed", error=str(e))

    # Get Ethereum stats
    ethereum_connected = False
    ethereum_network = None
    ethereum_wallet = None
    ethereum_balance = None
    try:
        eth_service = EthereumBlockchainService(db)
        ethereum_connected = eth_service.is_connected
        if ethereum_connected:
            chain_info = await eth_service.get_chain_info()
            ethereum_network = "sepolia" if chain_info.get("chain_id") == 11155111 else f"chain_{chain_info.get('chain_id')}"
            ethereum_wallet = eth_service.wallet_address
            ethereum_balance = await eth_service.get_balance()
    except Exception as e:
        logger.error("Ethereum stats failed", error=str(e))

    # Get fingerprint count
    total_fingerprints = 0
    try:
        result = await db.execute(select(func.count()).select_from(AudioRecord))
        total_fingerprints = result.scalar() or 0
    except Exception as e:
        logger.error("Fingerprint count failed", error=str(e))

    # For now, we don't track verifications separately
    total_verifications = 0

    return StatsResponse(
        api_status="online",
        database_status=db_status,
        redis_status=redis_status,
        blockchain_status="synced" if blockchain_synced else "offline",
        blockchain_blocks=blockchain_blocks,
        blockchain_synced=blockchain_synced,
        ethereum_connected=ethereum_connected,
        ethereum_network=ethereum_network,
        ethereum_wallet=ethereum_wallet,
        ethereum_balance=ethereum_balance,
        total_fingerprints=total_fingerprints,
        total_verifications=total_verifications,
        active_layers=6,  # We always have 6 layers (A-F)
        timestamp=datetime.now(timezone.utc).isoformat(),
    )
