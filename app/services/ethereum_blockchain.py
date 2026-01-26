"""Ethereum blockchain integration for audio provenance tracking.

Uses Ethereum Sepolia testnet with Alchemy as the RPC provider.
Stores audio fingerprint hashes as transaction data on-chain.
"""

import hashlib
import json
from datetime import datetime, timezone
from typing import Any

import structlog
from eth_account import Account
from eth_account.messages import encode_defunct
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from web3 import Web3
from web3.exceptions import TransactionNotFound

from app.core.config import get_settings
from app.models.blockchain_record import BlockchainRecord

logger = structlog.get_logger()


class EthereumBlockchainService:
    """Service for interacting with Ethereum blockchain for provenance tracking."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.settings = get_settings()
        self.w3: Web3 | None = None
        self.account: Account | None = None
        self._initialize()

    def _initialize(self) -> None:
        """Initialize Web3 connection and account."""
        try:
            # Connect to Ethereum via Alchemy
            alchemy_url = self.settings.alchemy_rpc_url
            if not alchemy_url:
                logger.warning("No Alchemy RPC URL configured, using local blockchain only")
                return

            self.w3 = Web3(Web3.HTTPProvider(alchemy_url))

            if not self.w3.is_connected():
                logger.error("Failed to connect to Ethereum network")
                self.w3 = None
                return

            # Load or create account
            private_key = self.settings.ethereum_private_key
            if private_key:
                self.account = Account.from_key(private_key)
                logger.info(
                    "Ethereum wallet loaded",
                    address=self.account.address,
                    network="sepolia",
                )
            else:
                logger.warning("No Ethereum private key configured")

        except Exception as e:
            logger.error("Failed to initialize Ethereum connection", error=str(e))
            self.w3 = None

    @property
    def is_connected(self) -> bool:
        """Check if connected to Ethereum network."""
        return self.w3 is not None and self.w3.is_connected()

    @property
    def wallet_address(self) -> str | None:
        """Get the wallet address."""
        return self.account.address if self.account else None

    async def get_balance(self) -> float:
        """Get the ETH balance of the wallet."""
        if not self.w3 or not self.account:
            return 0.0
        try:
            balance_wei = self.w3.eth.get_balance(self.account.address)
            return self.w3.from_wei(balance_wei, "ether")
        except Exception as e:
            logger.error("Failed to get balance", error=str(e))
            return 0.0

    async def get_chain_info(self) -> dict[str, Any]:
        """Get current chain information."""
        if not self.w3:
            return {"connected": False}

        try:
            return {
                "connected": True,
                "chain_id": self.w3.eth.chain_id,
                "block_number": self.w3.eth.block_number,
                "gas_price_gwei": self.w3.from_wei(self.w3.eth.gas_price, "gwei"),
                "wallet_address": self.wallet_address,
            }
        except Exception as e:
            logger.error("Failed to get chain info", error=str(e))
            return {"connected": False, "error": str(e)}

    def _create_provenance_data(self, audio_data: dict) -> bytes:
        """Create provenance data to store on-chain."""
        # Create a compact representation of the audio fingerprint
        provenance = {
            "type": "AFAS-X-PROVENANCE",
            "version": "1.0",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "audio_hash": audio_data.get("original_hash"),
            "fingerprint_hash": audio_data.get("fingerprint_hash"),
            "layers": audio_data.get("layer_hashes", {}),
        }
        return json.dumps(provenance, sort_keys=True).encode()

    async def register_audio_on_chain(
        self,
        audio_hash: str,
        fingerprint_hash: str,
        layer_hashes: dict[str, str],
        record_id: str,
    ) -> dict[str, Any]:
        """Register audio fingerprint on Ethereum blockchain."""

        # Always save to local database first
        local_record = await self._save_local_record(
            audio_hash=audio_hash,
            fingerprint_hash=fingerprint_hash,
            layer_hashes=layer_hashes,
            record_id=record_id,
            tx_hash=None,
        )

        # If Ethereum is not configured, return local-only result
        if not self.w3 or not self.account:
            logger.info("Ethereum not configured, using local blockchain only")
            return {
                "success": True,
                "local_only": True,
                "block_hash": local_record.block_hash,
                "block_index": local_record.block_index,
                "tx_hash": None,
                "message": "Registered on local blockchain (Ethereum not configured)",
            }

        try:
            # Create provenance data
            provenance_data = self._create_provenance_data({
                "original_hash": audio_hash,
                "fingerprint_hash": fingerprint_hash,
                "layer_hashes": layer_hashes,
                "record_id": record_id,
            })

            # Build transaction (self-transfer with data)
            nonce = self.w3.eth.get_transaction_count(self.account.address)

            tx = {
                "nonce": nonce,
                "to": self.account.address,  # Self-transfer to store data
                "value": 0,
                "gas": 100000,
                "gasPrice": self.w3.eth.gas_price,
                "data": provenance_data,
                "chainId": self.w3.eth.chain_id,
            }

            # Sign and send transaction
            signed_tx = self.w3.eth.account.sign_transaction(tx, self.account.key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            tx_hash_hex = tx_hash.hex()

            logger.info(
                "Audio registered on Ethereum",
                tx_hash=tx_hash_hex,
                audio_hash=audio_hash[:16] + "...",
            )

            # Update local record with transaction hash
            local_record.data["ethereum_tx_hash"] = tx_hash_hex
            await self.db.flush()

            return {
                "success": True,
                "local_only": False,
                "block_hash": local_record.block_hash,
                "block_index": local_record.block_index,
                "tx_hash": tx_hash_hex,
                "message": "Registered on Ethereum Sepolia testnet",
            }

        except Exception as e:
            logger.error("Failed to register on Ethereum", error=str(e))
            return {
                "success": True,
                "local_only": True,
                "block_hash": local_record.block_hash,
                "block_index": local_record.block_index,
                "tx_hash": None,
                "error": str(e),
                "message": "Registered on local blockchain (Ethereum transaction failed)",
            }

    async def verify_on_chain(self, tx_hash: str) -> dict[str, Any]:
        """Verify a transaction exists on-chain."""
        if not self.w3:
            return {"verified": False, "error": "Ethereum not configured"}

        try:
            tx = self.w3.eth.get_transaction(tx_hash)
            receipt = self.w3.eth.get_transaction_receipt(tx_hash)

            # Decode the provenance data
            provenance_data = None
            if tx.get("input"):
                try:
                    provenance_data = json.loads(bytes.fromhex(tx["input"][2:]).decode())
                except Exception:
                    pass

            return {
                "verified": True,
                "block_number": receipt["blockNumber"],
                "block_hash": receipt["blockHash"].hex(),
                "status": "success" if receipt["status"] == 1 else "failed",
                "provenance_data": provenance_data,
            }

        except TransactionNotFound:
            return {"verified": False, "error": "Transaction not found"}
        except Exception as e:
            return {"verified": False, "error": str(e)}

    async def _save_local_record(
        self,
        audio_hash: str,
        fingerprint_hash: str,
        layer_hashes: dict[str, str],
        record_id: str,
        tx_hash: str | None,
    ) -> BlockchainRecord:
        """Save record to local blockchain database."""
        # Get latest block
        result = await self.db.execute(
            select(BlockchainRecord).order_by(BlockchainRecord.block_index.desc()).limit(1)
        )
        latest = result.scalar_one_or_none()

        if latest is None:
            # Create genesis block
            genesis = BlockchainRecord(
                block_index=0,
                block_hash="genesis_afas_x_ethereum_0000000000000000000000000000000000",
                previous_hash="0" * 64,
                timestamp=datetime.now(timezone.utc),
                data={"type": "genesis", "message": "AFAS-X Ethereum Integration Genesis"},
                nonce=0,
                signature=None,
            )
            self.db.add(genesis)
            await self.db.flush()
            latest = genesis

        # Create block data
        data = {
            "type": "audio_provenance",
            "original_hash": audio_hash,
            "fingerprint_hash": fingerprint_hash,
            "layer_hashes": layer_hashes,
            "record_id": record_id,
            "ethereum_tx_hash": tx_hash,
            "registered_at": datetime.now(timezone.utc).isoformat(),
        }

        # Calculate block hash
        block_string = json.dumps({
            "index": latest.block_index + 1,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": data,
            "previous_hash": latest.block_hash,
            "nonce": 0,
        }, sort_keys=True)
        block_hash = hashlib.sha256(block_string.encode()).hexdigest()

        # Create new block
        new_block = BlockchainRecord(
            block_index=latest.block_index + 1,
            block_hash=block_hash,
            previous_hash=latest.block_hash,
            timestamp=datetime.now(timezone.utc),
            data=data,
            nonce=0,
            signature=None,
        )
        self.db.add(new_block)
        await self.db.flush()

        return new_block

    async def get_provenance_by_audio_hash(self, audio_hash: str) -> dict[str, Any] | None:
        """Get provenance record for an audio hash."""
        result = await self.db.execute(
            select(BlockchainRecord).where(
                BlockchainRecord.data["original_hash"].astext == audio_hash
            )
        )
        record = result.scalar_one_or_none()

        if not record:
            return None

        response = {
            "found": True,
            "block_index": record.block_index,
            "block_hash": record.block_hash,
            "registered_at": record.data.get("registered_at"),
            "fingerprint_hash": record.data.get("fingerprint_hash"),
            "layer_hashes": record.data.get("layer_hashes", {}),
        }

        # Check Ethereum if tx_hash exists
        tx_hash = record.data.get("ethereum_tx_hash")
        if tx_hash and self.w3:
            eth_result = await self.verify_on_chain(tx_hash)
            response["ethereum"] = eth_result

        return response


def generate_ethereum_wallet() -> dict[str, str]:
    """Generate a new Ethereum wallet (for initial setup)."""
    account = Account.create()
    return {
        "address": account.address,
        "private_key": account.key.hex(),
    }
