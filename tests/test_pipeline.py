"""Tests for the fingerprinting pipeline."""

import base64
import io

import numpy as np
import pytest
import soundfile as sf

from app.services.fingerprinting.pipeline import FingerprintPipeline


class TestFingerprintPipeline:
    """Tests for the fingerprint pipeline."""

    def test_process_produces_valid_result(self, sample_audio):
        """Test that processing produces valid results."""
        # Convert sample audio to bytes
        buffer = io.BytesIO()
        sf.write(buffer, sample_audio, 22050, format="WAV")
        audio_bytes = buffer.getvalue()

        pipeline = FingerprintPipeline()
        result = pipeline.process(audio_bytes)

        assert result.original_hash is not None
        assert result.fingerprinted_hash is not None
        assert len(result.layer_outputs) == 6  # All 6 layers
        assert result.duration_seconds > 0

    def test_process_base64(self, sample_audio_base64):
        """Test processing base64-encoded audio."""
        pipeline = FingerprintPipeline()
        result, fingerprinted_b64 = pipeline.process_base64(sample_audio_base64)

        assert result is not None
        assert fingerprinted_b64 is not None
        assert len(fingerprinted_b64) > 0

        # Verify we can decode the result
        decoded = base64.b64decode(fingerprinted_b64)
        assert len(decoded) > 0

    def test_all_layers_produce_output(self, sample_audio_base64):
        """Test that all layers produce valid output."""
        pipeline = FingerprintPipeline()
        result, _ = pipeline.process_base64(sample_audio_base64)

        layer_types = {lo.layer_type for lo in result.layer_outputs}
        expected = {"A", "B", "C", "D", "E", "F"}

        assert layer_types == expected

    def test_fingerprinted_audio_is_different(self, sample_audio_base64):
        """Test that fingerprinted audio differs from original."""
        pipeline = FingerprintPipeline()
        result, _ = pipeline.process_base64(sample_audio_base64)

        # Hashes should be different
        assert result.original_hash != result.fingerprinted_hash

    def test_fingerprinted_audio_is_similar(self, sample_audio_base64):
        """Test that fingerprinted audio is perceptually similar."""
        pipeline = FingerprintPipeline()
        result, _ = pipeline.process_base64(sample_audio_base64)

        # Audio should be highly correlated
        correlation = np.corrcoef(
            result.original_audio.flatten(),
            result.fingerprinted_audio.flatten(),
        )[0, 1]

        assert correlation > 0.95  # Very similar

    def test_deterministic_processing(self, sample_audio_base64):
        """Test that processing is deterministic."""
        pipeline = FingerprintPipeline()

        result1, _ = pipeline.process_base64(sample_audio_base64)
        result2, _ = pipeline.process_base64(sample_audio_base64)

        # Same input should produce same hashes
        assert result1.original_hash == result2.original_hash

        # Layer hashes should match
        for lo1, lo2 in zip(result1.layer_outputs, result2.layer_outputs):
            assert lo1.layer_hash == lo2.layer_hash
