"""Custom blockchain implementation for audio provenance tracking."""

import hashlib
import json
from datetime import datetime, timezone

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_signer, get_timestamp_iso
from app.models.blockchain_record import BlockchainRecord

logger = structlog.get_logger()

DIFFICULTY = 2  # Number of leading zeros required in hash


class Block:
    """Represents a single block in the chain."""

    def __init__(
        self,
        index: int,
        timestamp: str,
        data: dict,
        previous_hash: str,
        nonce: int = 0,
        signature: str | None = None,
    ) -> None:
        self.index = index
        self.timestamp = timestamp
        self.data = data
        self.previous_hash = previous_hash
        self.nonce = nonce
        self.signature = signature
        self.hash = self.calculate_hash()

    def calculate_hash(self) -> str:
        """Calculate SHA-256 hash of block contents."""
        block_string = json.dumps(
            {
                "index": self.index,
                "timestamp": self.timestamp,
                "data": self.data,
                "previous_hash": self.previous_hash,
                "nonce": self.nonce,
            },
            sort_keys=True,
        )
        return hashlib.sha256(block_string.encode()).hexdigest()

    def mine(self, difficulty: int = DIFFICULTY) -> None:
        """Mine the block by finding a valid nonce."""
        target = "0" * difficulty
        while not self.hash.startswith(target):
            self.nonce += 1
            self.hash = self.calculate_hash()

    def sign(self, signer) -> None:
        """Sign the block hash with Ed25519."""
        self.signature = signer.sign(self.hash.encode())

    def to_dict(self) -> dict:
        """Convert block to dictionary."""
        return {
            "index": self.index,
            "timestamp": self.timestamp,
            "data": self.data,
            "previous_hash": self.previous_hash,
            "nonce": self.nonce,
            "hash": self.hash,
            "signature": self.signature,
        }


class BlockchainService:
    """Service for managing the blockchain."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.signer = get_signer()

    async def get_latest_block(self) -> BlockchainRecord | None:
        """Get the most recent block in the chain."""
        result = await self.db.execute(
            select(BlockchainRecord).order_by(BlockchainRecord.block_index.desc()).limit(1)
        )
        return result.scalar_one_or_none()

    async def get_block_by_hash(self, block_hash: str) -> BlockchainRecord | None:
        """Get a block by its hash."""
        result = await self.db.execute(
            select(BlockchainRecord).where(BlockchainRecord.block_hash == block_hash)
        )
        return result.scalar_one_or_none()

    async def get_block_by_index(self, index: int) -> BlockchainRecord | None:
        """Get a block by its index."""
        result = await self.db.execute(
            select(BlockchainRecord).where(BlockchainRecord.block_index == index)
        )
        return result.scalar_one_or_none()

    async def add_block(self, data: dict) -> Block:
        """Add a new block to the chain."""
        latest = await self.get_latest_block()

        if latest is None:
            # This shouldn't happen if init.sql ran, but handle it
            logger.warning("No genesis block found, creating one")
            genesis = await self._create_genesis_block()
            latest = genesis

        new_block = Block(
            index=latest.block_index + 1,
            timestamp=get_timestamp_iso(),
            data=data,
            previous_hash=latest.block_hash,
        )

        # Mine the block
        new_block.mine()

        # Sign the block
        new_block.sign(self.signer)

        # Save to database
        record = BlockchainRecord(
            block_index=new_block.index,
            block_hash=new_block.hash,
            previous_hash=new_block.previous_hash,
            timestamp=datetime.fromisoformat(new_block.timestamp),
            data=new_block.data,
            nonce=new_block.nonce,
            signature=new_block.signature,
        )
        self.db.add(record)
        await self.db.flush()

        logger.info(
            "Block added to chain",
            block_index=new_block.index,
            block_hash=new_block.hash,
        )

        return new_block

    async def _create_genesis_block(self) -> BlockchainRecord:
        """Create the genesis block."""
        genesis = Block(
            index=0,
            timestamp=get_timestamp_iso(),
            data={"type": "genesis", "message": "AFAS-X Genesis Block", "version": "1.0.0"},
            previous_hash="0" * 64,
        )
        genesis.hash = "genesis_afas_x_block_0000000000000000000000000000000000"

        record = BlockchainRecord(
            block_index=genesis.index,
            block_hash=genesis.hash,
            previous_hash=genesis.previous_hash,
            timestamp=datetime.fromisoformat(genesis.timestamp),
            data=genesis.data,
            nonce=genesis.nonce,
            signature=None,
        )
        self.db.add(record)
        await self.db.flush()

        return record

    async def verify_chain(self, up_to_index: int | None = None) -> tuple[bool, list[str]]:
        """Verify the integrity of the blockchain."""
        errors = []

        # Get all blocks in order
        query = select(BlockchainRecord).order_by(BlockchainRecord.block_index)
        if up_to_index is not None:
            query = query.where(BlockchainRecord.block_index <= up_to_index)

        result = await self.db.execute(query)
        blocks = result.scalars().all()

        if not blocks:
            return False, ["No blocks found in chain"]

        previous_block = None
        for block in blocks:
            # Skip genesis block hash verification (special case)
            if block.block_index == 0:
                previous_block = block
                continue

            # Verify previous hash link
            if previous_block and block.previous_hash != previous_block.block_hash:
                errors.append(
                    f"Block {block.block_index}: previous_hash mismatch"
                )

            # Verify block hash
            reconstructed = Block(
                index=block.block_index,
                timestamp=block.timestamp.isoformat(),
                data=block.data,
                previous_hash=block.previous_hash,
                nonce=block.nonce,
            )
            if reconstructed.hash != block.block_hash:
                errors.append(
                    f"Block {block.block_index}: hash verification failed"
                )

            # Verify signature if present
            if block.signature:
                if not self.signer.verify(
                    block.block_hash.encode(), block.signature
                ):
                    errors.append(
                        f"Block {block.block_index}: signature verification failed"
                    )

            previous_block = block

        return len(errors) == 0, errors

    async def get_chain_to_genesis(self, block_hash: str) -> list[str]:
        """Get the chain of block hashes from a block back to genesis."""
        chain = []
        current_hash = block_hash

        while current_hash:
            block = await self.get_block_by_hash(current_hash)
            if block is None:
                break

            chain.append(block.block_hash)

            if block.block_index == 0:
                break

            current_hash = block.previous_hash

        return chain

    async def find_block_by_audio_hash(self, audio_hash: str) -> BlockchainRecord | None:
        """Find the block containing a specific audio hash."""
        # Search through blocks for one containing this audio hash
        # Use first() instead of scalar_one_or_none() in case of duplicates
        result = await self.db.execute(
            select(BlockchainRecord)
            .where(BlockchainRecord.data["original_hash"].astext == audio_hash)
            .order_by(BlockchainRecord.block_index.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()
