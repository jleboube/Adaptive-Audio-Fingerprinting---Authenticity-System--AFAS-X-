"""Verification service for audio authenticity checking."""

import base64
import io
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum

import librosa
import numpy as np
import soundfile as sf
import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.audio_record import AudioRecord
from app.models.fingerprint_layer import FingerprintLayer
from app.services.blockchain import BlockchainService
from app.services.fingerprinting.layer_a import LayerA
from app.services.fingerprinting.layer_b import LayerB
from app.services.fingerprinting.layer_c import LayerC
from app.services.fingerprinting.layer_d import LayerD
from app.services.fingerprinting.layer_e import LayerE
from app.services.fingerprinting.layer_f import LayerF

logger = structlog.get_logger()
settings = get_settings()


class VerificationResult(str, Enum):
    """Possible verification outcomes."""

    AUTHENTIC = "AUTHENTIC"
    MODIFIED = "MODIFIED"
    UNKNOWN = "UNKNOWN"
    FAILED = "FAILED"


@dataclass
class LayerVerificationResult:
    """Result from verifying a single layer."""

    layer_type: str
    matches: bool
    confidence: float
    details: str | None = None


@dataclass
class VerificationOutput:
    """Complete verification output."""

    result: VerificationResult
    confidence_score: float
    record_id: str | None
    original_hash: str | None
    layer_results: list[LayerVerificationResult]
    blockchain_verified: bool
    provenance_chain: list[str] | None
    verified_at: datetime


class VerificationService:
    """Service for verifying audio authenticity."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.sample_rate = settings.default_sample_rate

        # Initialize layers for verification
        self.layers = {
            "A": LayerA(sample_rate=self.sample_rate),
            "B": LayerB(sample_rate=self.sample_rate),
            "C": LayerC(sample_rate=self.sample_rate),
            "D": LayerD(sample_rate=self.sample_rate),
            "E": LayerE(sample_rate=self.sample_rate),
            "F": LayerF(sample_rate=self.sample_rate),
        }

    def _load_audio(self, audio_bytes: bytes) -> np.ndarray:
        """Load audio from bytes."""
        try:
            audio_io = io.BytesIO(audio_bytes)
            audio, sr = sf.read(audio_io)

            if len(audio.shape) > 1:
                audio = np.mean(audio, axis=1)

            if sr != self.sample_rate:
                audio = librosa.resample(audio, orig_sr=sr, target_sr=self.sample_rate)

            return audio.astype(np.float32)
        except Exception:
            audio_io = io.BytesIO(audio_bytes)
            audio, _ = librosa.load(audio_io, sr=self.sample_rate, mono=True)
            return audio.astype(np.float32)

    def _compute_audio_hash(self, audio: np.ndarray) -> str:
        """Compute hash of audio samples."""
        import hashlib

        quantized = (audio * 32767).astype(np.int16)
        return hashlib.sha256(quantized.tobytes()).hexdigest()

    async def _find_record_by_hash(
        self, audio_hash: str
    ) -> tuple[AudioRecord | None, list[FingerprintLayer]]:
        """Find audio record by original or fingerprinted hash."""
        logger.debug("Searching for audio record", search_hash=audio_hash)

        # Try original hash first
        result = await self.db.execute(
            select(AudioRecord).where(AudioRecord.original_hash == audio_hash)
        )
        record = result.scalar_one_or_none()

        if not record:
            # Try fingerprinted hash
            result = await self.db.execute(
                select(AudioRecord).where(AudioRecord.fingerprinted_hash == audio_hash)
            )
            record = result.scalar_one_or_none()

        if record:
            logger.warning(
                "VERIFICATION DEBUG: Found matching record",
                record_id=str(record.id),
                original_hash=record.original_hash,
                fingerprinted_hash=record.fingerprinted_hash,
            )
        else:
            logger.warning("VERIFICATION DEBUG: No record found for hash", search_hash=audio_hash)

        if record:
            # Get fingerprint layers
            layers_result = await self.db.execute(
                select(FingerprintLayer).where(
                    FingerprintLayer.audio_record_id == record.id
                )
            )
            layers = list(layers_result.scalars().all())
            return record, layers

        return None, []

    async def verify(
        self,
        audio_base64: str,
        expected_hash: str | None = None,
    ) -> VerificationOutput:
        """Verify audio authenticity.

        Args:
            audio_base64: Base64-encoded audio to verify
            expected_hash: Optional expected original hash

        Returns:
            VerificationOutput with results
        """
        logger.info("Starting verification")
        verified_at = datetime.now(timezone.utc)

        try:
            # Decode and load audio
            audio_bytes = base64.b64decode(audio_base64)
            audio = self._load_audio(audio_bytes)
            submitted_hash = self._compute_audio_hash(audio)

            logger.warning(
                "VERIFICATION DEBUG: Audio loaded",
                submitted_hash=submitted_hash,
                audio_length=len(audio),
            )

            # Find matching record
            search_hash = expected_hash or submitted_hash
            record, stored_layers = await self._find_record_by_hash(search_hash)

            if not record:
                # Try with submitted hash if expected_hash didn't match
                if expected_hash and expected_hash != submitted_hash:
                    record, stored_layers = await self._find_record_by_hash(submitted_hash)

            if not record:
                logger.warning(
                    "VERIFICATION DEBUG: No matching record found",
                    submitted_hash=submitted_hash,
                    search_hash=search_hash,
                )
                return VerificationOutput(
                    result=VerificationResult.UNKNOWN,
                    confidence_score=0.0,
                    record_id=None,
                    original_hash=None,
                    layer_results=[],
                    blockchain_verified=False,
                    provenance_chain=None,
                    verified_at=verified_at,
                )

            # Build expected layer hashes map
            expected_layer_hashes = {
                layer.layer_type: layer.layer_hash for layer in stored_layers
            }

            # First, extract current fingerprints from layers A-E
            # We need these to properly verify Layer F
            current_layer_outputs = []
            layer_results = []

            for layer_type in ["A", "B", "C", "D", "E"]:
                layer = self.layers[layer_type]
                expected_hash = expected_layer_hashes.get(layer_type)

                if not expected_hash:
                    layer_results.append(
                        LayerVerificationResult(
                            layer_type=layer_type,
                            matches=False,
                            confidence=0.0,
                            details="Expected hash not found",
                        )
                    )
                    continue

                try:
                    # Extract current fingerprint
                    current_output = layer.extract(audio)
                    current_layer_outputs.append(current_output)

                    # Compare hashes directly for exact match
                    matches = current_output.layer_hash == expected_hash
                    confidence = 1.0 if matches else 0.0

                    layer_results.append(
                        LayerVerificationResult(
                            layer_type=layer_type,
                            matches=matches,
                            confidence=confidence,
                            details=None,
                        )
                    )
                except Exception as e:
                    logger.warning(f"Layer {layer_type} verification error", error=str(e))
                    layer_results.append(
                        LayerVerificationResult(
                            layer_type=layer_type,
                            matches=False,
                            confidence=0.0,
                            details=f"Error: {str(e)}",
                        )
                    )

            # Now verify Layer F with the current layer outputs
            layer_f = self.layers["F"]
            expected_f_hash = expected_layer_hashes.get("F")

            if expected_f_hash:
                try:
                    # Extract Layer F with the current layer outputs
                    current_f_output = layer_f.extract(audio, current_layer_outputs)

                    # Compare hashes directly
                    f_matches = current_f_output.layer_hash == expected_f_hash
                    f_confidence = 1.0 if f_matches else 0.0

                    layer_results.append(
                        LayerVerificationResult(
                            layer_type="F",
                            matches=f_matches,
                            confidence=f_confidence,
                            details=None,
                        )
                    )
                except Exception as e:
                    logger.warning("Layer F verification error", error=str(e))
                    layer_results.append(
                        LayerVerificationResult(
                            layer_type="F",
                            matches=False,
                            confidence=0.0,
                            details=f"Error: {str(e)}",
                        )
                    )
            else:
                layer_results.append(
                    LayerVerificationResult(
                        layer_type="F",
                        matches=False,
                        confidence=0.0,
                        details="Expected hash not found",
                    )
                )

            # Calculate overall result
            matching_layers = sum(1 for lr in layer_results if lr.matches)
            total_layers = len(layer_results)
            match_ratio = matching_layers / total_layers if total_layers > 0 else 0

            # Confidence is 100% if all layers match, otherwise based on match ratio
            if matching_layers == total_layers:
                confidence_score = 1.0  # 100% match
            else:
                confidence_score = match_ratio

            # Verify blockchain
            blockchain_service = BlockchainService(self.db)
            block = await blockchain_service.find_block_by_audio_hash(record.original_hash)
            blockchain_verified = block is not None

            provenance_chain = None
            if block:
                provenance_chain = await blockchain_service.get_chain_to_genesis(
                    block.block_hash
                )

            # Determine final result
            if matching_layers == total_layers and blockchain_verified:
                result = VerificationResult.AUTHENTIC
            elif match_ratio > 0.8 and blockchain_verified:
                result = VerificationResult.AUTHENTIC
            elif match_ratio > 0.5:
                result = VerificationResult.MODIFIED
            elif match_ratio > 0:
                result = VerificationResult.MODIFIED
            else:
                result = VerificationResult.FAILED

            logger.info(
                "Verification complete",
                result=result.value,
                confidence=confidence_score,
                matching_layers=matching_layers,
                blockchain_verified=blockchain_verified,
            )

            return VerificationOutput(
                result=result,
                confidence_score=confidence_score,
                record_id=str(record.id),
                original_hash=record.original_hash,
                layer_results=layer_results,
                blockchain_verified=blockchain_verified,
                provenance_chain=provenance_chain,
                verified_at=verified_at,
            )

        except Exception as e:
            logger.error("Verification failed", error=str(e))
            return VerificationOutput(
                result=VerificationResult.FAILED,
                confidence_score=0.0,
                record_id=None,
                original_hash=None,
                layer_results=[],
                blockchain_verified=False,
                provenance_chain=None,
                verified_at=verified_at,
            )
