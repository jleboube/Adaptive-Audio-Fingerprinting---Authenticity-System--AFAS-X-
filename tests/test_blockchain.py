"""Tests for blockchain service."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.blockchain import Block, BlockchainService


class TestBlock:
    """Tests for Block class."""

    def test_block_hash_is_deterministic(self):
        """Test that block hash is deterministic."""
        block1 = Block(
            index=1,
            timestamp="2024-01-01T00:00:00Z",
            data={"test": "data"},
            previous_hash="0" * 64,
        )
        block2 = Block(
            index=1,
            timestamp="2024-01-01T00:00:00Z",
            data={"test": "data"},
            previous_hash="0" * 64,
        )

        assert block1.hash == block2.hash

    def test_block_hash_changes_with_nonce(self):
        """Test that hash changes with different nonce."""
        block1 = Block(
            index=1,
            timestamp="2024-01-01T00:00:00Z",
            data={"test": "data"},
            previous_hash="0" * 64,
            nonce=0,
        )
        block2 = Block(
            index=1,
            timestamp="2024-01-01T00:00:00Z",
            data={"test": "data"},
            previous_hash="0" * 64,
            nonce=1,
        )

        assert block1.hash != block2.hash

    def test_block_mining(self):
        """Test block mining produces valid hash."""
        block = Block(
            index=1,
            timestamp="2024-01-01T00:00:00Z",
            data={"test": "data"},
            previous_hash="0" * 64,
        )
        block.mine(difficulty=2)

        # Hash should start with '00'
        assert block.hash.startswith("00")

    def test_block_to_dict(self):
        """Test block serialization."""
        block = Block(
            index=1,
            timestamp="2024-01-01T00:00:00Z",
            data={"test": "data"},
            previous_hash="0" * 64,
        )
        d = block.to_dict()

        assert d["index"] == 1
        assert d["timestamp"] == "2024-01-01T00:00:00Z"
        assert d["data"] == {"test": "data"}
        assert d["previous_hash"] == "0" * 64
        assert "hash" in d


@pytest.mark.asyncio
class TestBlockchainService:
    """Tests for BlockchainService."""

    async def test_add_block(self, db_session: AsyncSession):
        """Test adding a block to the chain."""
        # First create genesis block
        from app.models.blockchain_record import BlockchainRecord
        from datetime import datetime, timezone

        genesis = BlockchainRecord(
            block_index=0,
            block_hash="genesis_test_" + "0" * 52,
            previous_hash="0" * 64,
            timestamp=datetime.now(timezone.utc),
            data={"type": "genesis"},
            nonce=0,
        )
        db_session.add(genesis)
        await db_session.flush()

        service = BlockchainService(db_session)
        block = await service.add_block({"type": "test", "value": 123})

        assert block.index == 1
        assert block.previous_hash == genesis.block_hash
        assert block.data == {"type": "test", "value": 123}

    async def test_get_latest_block(self, db_session: AsyncSession):
        """Test getting the latest block."""
        from app.models.blockchain_record import BlockchainRecord
        from datetime import datetime, timezone

        # Add genesis block
        genesis = BlockchainRecord(
            block_index=0,
            block_hash="genesis_latest_" + "0" * 51,
            previous_hash="0" * 64,
            timestamp=datetime.now(timezone.utc),
            data={"type": "genesis"},
            nonce=0,
        )
        db_session.add(genesis)
        await db_session.flush()

        service = BlockchainService(db_session)
        latest = await service.get_latest_block()

        assert latest is not None
        assert latest.block_index == 0
