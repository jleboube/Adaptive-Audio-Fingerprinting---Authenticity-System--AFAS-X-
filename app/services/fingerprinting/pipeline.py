"""Pipeline orchestrator for multi-layer fingerprinting."""

import base64
import io
import tempfile
from dataclasses import dataclass

import librosa
import numpy as np
import soundfile as sf
import structlog
from pydub import AudioSegment

from app.core.config import get_settings
from app.services.fingerprinting.base import LayerOutput
from app.services.fingerprinting.layer_a import LayerA
from app.services.fingerprinting.layer_b import LayerB
from app.services.fingerprinting.layer_c import LayerC
from app.services.fingerprinting.layer_d import LayerD
from app.services.fingerprinting.layer_e import LayerE
from app.services.fingerprinting.layer_f import LayerF

logger = structlog.get_logger()
settings = get_settings()


@dataclass
class PipelineResult:
    """Result from fingerprinting pipeline."""

    original_audio: np.ndarray
    fingerprinted_audio: np.ndarray
    layer_outputs: list[LayerOutput]
    sample_rate: int
    duration_seconds: float
    original_hash: str
    fingerprinted_hash: str


class FingerprintPipeline:
    """Orchestrates multi-layer audio fingerprinting."""

    def __init__(
        self,
        sample_rate: int | None = None,
        version: str | None = None,
    ) -> None:
        self.sample_rate = sample_rate or settings.default_sample_rate
        self.version = version or settings.fingerprint_version

        # Initialize all layers
        self.layers = {
            "A": LayerA(sample_rate=self.sample_rate, version=self.version),
            "B": LayerB(sample_rate=self.sample_rate, version=self.version),
            "C": LayerC(sample_rate=self.sample_rate, version=self.version),
            "D": LayerD(sample_rate=self.sample_rate, version=self.version),
            "E": LayerE(sample_rate=self.sample_rate, version=self.version),
            "F": LayerF(sample_rate=self.sample_rate, version=self.version),
        }

    def _load_audio(self, audio_bytes: bytes) -> tuple[np.ndarray, int]:
        """Load audio from bytes, converting to standard format.

        Supports WAV, MP3, FLAC, OGG, M4A, AAC, and other formats via pydub/ffmpeg.
        """
        # Try to load with soundfile first (fastest for WAV/FLAC)
        try:
            audio_io = io.BytesIO(audio_bytes)
            audio, sr = sf.read(audio_io)

            # Convert to mono if stereo
            if len(audio.shape) > 1:
                audio = np.mean(audio, axis=1)

            # Resample if needed
            if sr != self.sample_rate:
                audio = librosa.resample(audio, orig_sr=sr, target_sr=self.sample_rate)
                sr = self.sample_rate

            return audio.astype(np.float32), sr
        except Exception as e:
            logger.warning("soundfile failed, trying pydub/ffmpeg", error=str(e))

        # Try pydub with ffmpeg for M4A, AAC, MP3, and other formats
        # Use a temp file because pydub/ffmpeg works better with files than BytesIO
        try:
            with tempfile.NamedTemporaryFile(suffix='.audio', delete=False) as tmp_file:
                tmp_file.write(audio_bytes)
                tmp_path = tmp_file.name

            try:
                # pydub will use ffmpeg to decode any supported format
                audio_segment = AudioSegment.from_file(tmp_path)

                # Convert to mono
                audio_segment = audio_segment.set_channels(1)

                # Get sample rate and resample if needed
                sr = audio_segment.frame_rate
                if sr != self.sample_rate:
                    audio_segment = audio_segment.set_frame_rate(self.sample_rate)
                    sr = self.sample_rate

                # Convert to numpy array (normalize to -1.0 to 1.0)
                samples = np.array(audio_segment.get_array_of_samples())
                audio = samples.astype(np.float32) / (2 ** (audio_segment.sample_width * 8 - 1))

                logger.info("Audio loaded via pydub/ffmpeg",
                           channels=audio_segment.channels,
                           sample_rate=sr,
                           duration=len(audio_segment) / 1000)

                return audio, sr
            finally:
                # Clean up temp file
                import os
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
        except Exception as e:
            logger.warning("pydub failed, trying librosa", error=str(e))

        # Final fallback to librosa
        try:
            audio_io = io.BytesIO(audio_bytes)
            audio, sr = librosa.load(audio_io, sr=self.sample_rate, mono=True)
            return audio.astype(np.float32), sr
        except Exception as e:
            logger.error("All audio loading methods failed", error=str(e))
            raise ValueError(f"Failed to load audio: {str(e)}")

    def _export_audio(self, audio: np.ndarray, format: str = "wav") -> bytes:
        """Export audio to bytes in specified format."""
        audio_io = io.BytesIO()
        sf.write(audio_io, audio, self.sample_rate, format=format)
        audio_io.seek(0)
        return audio_io.read()

    def _compute_audio_hash(self, audio: np.ndarray) -> str:
        """Compute hash of audio samples."""
        import hashlib

        # Quantize to reduce floating-point variance
        quantized = (audio * 32767).astype(np.int16)
        return hashlib.sha256(quantized.tobytes()).hexdigest()

    def process(self, audio_bytes: bytes) -> PipelineResult:
        """Process audio through all fingerprinting layers.

        Args:
            audio_bytes: Raw audio file bytes

        Returns:
            PipelineResult with all layer outputs and fingerprinted audio
        """
        logger.info("Starting fingerprint pipeline")

        # Load and normalize audio
        audio, sr = self._load_audio(audio_bytes)
        original_hash = self._compute_audio_hash(audio)
        duration = len(audio) / sr

        logger.info(
            "Audio loaded",
            duration_seconds=duration,
            sample_rate=sr,
            samples=len(audio),
        )

        # Process through extraction layers (A-E)
        layer_outputs = []
        current_audio = audio.copy()

        for layer_name in ["A", "B", "C", "D", "E"]:
            layer = self.layers[layer_name]
            try:
                output = layer.extract(current_audio)
                layer_outputs.append(output)
                logger.info(
                    f"Layer {layer_name} extracted",
                    hash=output.layer_hash[:16],
                    confidence=output.confidence_score,
                )
            except Exception as e:
                logger.error(f"Layer {layer_name} extraction failed", error=str(e))
                # Create fallback output
                import hashlib
                fallback_hash = hashlib.sha256(f"{layer_name}:error".encode()).hexdigest()
                layer_outputs.append(
                    LayerOutput(
                        layer_type=layer_name,
                        layer_hash=fallback_hash,
                        confidence_score=0.0,
                        parameters={"error": str(e)},
                    )
                )

        # Meta layer (F) - processes all other layer outputs
        layer_f = self.layers["F"]
        meta_output = layer_f.extract(current_audio, layer_outputs)
        layer_outputs.append(meta_output)
        logger.info(
            "Layer F (meta) extracted",
            hash=meta_output.layer_hash[:16],
            confidence=meta_output.confidence_score,
        )

        # Embed fingerprints into audio
        fingerprinted_audio = audio.copy()
        fingerprint_data = {
            "original_hash": original_hash,
            "layer_hashes": {lo.layer_type: lo.layer_hash for lo in layer_outputs},
            "version": self.version,
        }

        for layer_name in ["A", "B", "C", "D", "E"]:
            layer = self.layers[layer_name]
            try:
                fingerprinted_audio = layer.embed(fingerprinted_audio, fingerprint_data)
                logger.debug(f"Layer {layer_name} embedded")
            except Exception as e:
                logger.warning(f"Layer {layer_name} embedding failed", error=str(e))

        # Export and re-import to get the exact samples that will be in the WAV file
        # This ensures the hash matches what verification will compute
        exported_bytes = self._export_audio(fingerprinted_audio)
        reimported_audio = self._load_audio(exported_bytes)[0]
        fingerprinted_hash = self._compute_audio_hash(reimported_audio)

        # Re-extract fingerprints from the FINAL audio (after export/reimport)
        # This ensures verification will find matching hashes
        final_layer_outputs = []
        for layer_name in ["A", "B", "C", "D", "E"]:
            layer = self.layers[layer_name]
            try:
                output = layer.extract(reimported_audio)
                final_layer_outputs.append(output)
                logger.debug(
                    f"Layer {layer_name} re-extracted from fingerprinted audio",
                    hash=output.layer_hash[:16],
                )
            except Exception as e:
                logger.warning(f"Layer {layer_name} re-extraction failed", error=str(e))
                # Use original extraction as fallback
                original_output = next(
                    (lo for lo in layer_outputs if lo.layer_type == layer_name), None
                )
                if original_output:
                    final_layer_outputs.append(original_output)

        # Re-extract meta layer (F) with new layer outputs
        layer_f = self.layers["F"]
        final_meta_output = layer_f.extract(reimported_audio, final_layer_outputs)
        final_layer_outputs.append(final_meta_output)

        logger.info(
            "Pipeline complete",
            original_hash=original_hash[:16],
            fingerprinted_hash=fingerprinted_hash[:16],
        )

        return PipelineResult(
            original_audio=audio,
            fingerprinted_audio=reimported_audio,  # Use the reimported audio
            layer_outputs=final_layer_outputs,  # Use hashes from fingerprinted audio
            sample_rate=sr,
            duration_seconds=duration,
            original_hash=original_hash,
            fingerprinted_hash=fingerprinted_hash,
        )

    def process_base64(self, audio_base64: str) -> tuple[PipelineResult, str]:
        """Process base64-encoded audio.

        Returns:
            Tuple of (PipelineResult, fingerprinted_audio_base64)
        """
        # Fix base64 padding if needed
        # Browser FileReader sometimes produces base64 without proper padding
        padding_needed = len(audio_base64) % 4
        if padding_needed:
            audio_base64 += "=" * (4 - padding_needed)

        audio_bytes = base64.b64decode(audio_base64)
        result = self.process(audio_bytes)

        # Export fingerprinted audio to base64
        fingerprinted_bytes = self._export_audio(result.fingerprinted_audio)
        fingerprinted_base64 = base64.b64encode(fingerprinted_bytes).decode()

        return result, fingerprinted_base64
