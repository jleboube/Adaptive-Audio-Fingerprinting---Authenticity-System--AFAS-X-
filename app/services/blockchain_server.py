"""Blockchain ledger server for AFAS-X.

This is a simple Flask server that provides blockchain services
for the AFAS-X system. It runs as a separate service for decoupling
and can be scaled independently.
"""

import asyncio
import sys
from datetime import datetime, timezone

import structlog
from flask import Flask, jsonify, request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.models.blockchain_record import BlockchainRecord
from app.services.blockchain import BlockchainService

# Configure logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
)

logger = structlog.get_logger()
settings = get_settings()

app = Flask(__name__)

# Database setup
engine = create_async_engine(settings.database_url)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


def run_async(coro):
    """Run async coroutine in sync context."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "service": "afas-ledger",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })


@app.route("/chain/status", methods=["GET"])
def chain_status():
    """Get blockchain status."""
    async def _get_status():
        async with async_session() as session:
            service = BlockchainService(session)
            latest = await service.get_latest_block()
            is_valid, errors = await service.verify_chain()

            return {
                "chain_length": latest.block_index + 1 if latest else 0,
                "latest_hash": latest.block_hash if latest else None,
                "is_valid": is_valid,
                "errors": errors if not is_valid else [],
            }

    try:
        status = run_async(_get_status())
        return jsonify(status)
    except Exception as e:
        logger.error("Chain status failed", error=str(e))
        return jsonify({"error": str(e)}), 500


@app.route("/chain/verify", methods=["POST"])
def verify_chain():
    """Verify blockchain integrity."""
    data = request.get_json() or {}
    up_to_index = data.get("up_to_index")

    async def _verify():
        async with async_session() as session:
            service = BlockchainService(session)
            is_valid, errors = await service.verify_chain(up_to_index)
            return is_valid, errors

    try:
        is_valid, errors = run_async(_verify())
        return jsonify({
            "is_valid": is_valid,
            "errors": errors,
        })
    except Exception as e:
        logger.error("Chain verification failed", error=str(e))
        return jsonify({"error": str(e)}), 500


@app.route("/block/<block_hash>", methods=["GET"])
def get_block(block_hash: str):
    """Get a specific block by hash."""
    async def _get_block():
        async with async_session() as session:
            service = BlockchainService(session)
            block = await service.get_block_by_hash(block_hash)
            if block:
                return {
                    "found": True,
                    "block": {
                        "index": block.block_index,
                        "hash": block.block_hash,
                        "previous_hash": block.previous_hash,
                        "timestamp": block.timestamp.isoformat(),
                        "data": block.data,
                        "nonce": block.nonce,
                        "signature": block.signature,
                    },
                }
            return {"found": False}

    try:
        result = run_async(_get_block())
        return jsonify(result)
    except Exception as e:
        logger.error("Get block failed", error=str(e))
        return jsonify({"error": str(e)}), 500


@app.route("/provenance/<audio_hash>", methods=["GET"])
def get_provenance(audio_hash: str):
    """Get provenance chain for an audio hash."""
    async def _get_provenance():
        async with async_session() as session:
            service = BlockchainService(session)
            block = await service.find_block_by_audio_hash(audio_hash)

            if not block:
                return {"found": False, "chain": []}

            chain = await service.get_chain_to_genesis(block.block_hash)
            return {
                "found": True,
                "block_hash": block.block_hash,
                "chain_length": len(chain),
                "chain": chain,
            }

    try:
        result = run_async(_get_provenance())
        return jsonify(result)
    except Exception as e:
        logger.error("Get provenance failed", error=str(e))
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    logger.info("Starting AFAS-X Ledger Server", port=5001)
    app.run(host="0.0.0.0", port=5001, debug=settings.debug)
