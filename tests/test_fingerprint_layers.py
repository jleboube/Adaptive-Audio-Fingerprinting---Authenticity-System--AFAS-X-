"""Tests for fingerprint layers."""

import numpy as np
import pytest

from app.services.fingerprinting.layer_a import LayerA
from app.services.fingerprinting.layer_b import LayerB
from app.services.fingerprinting.layer_c import LayerC
from app.services.fingerprinting.layer_d import LayerD
from app.services.fingerprinting.layer_e import LayerE
from app.services.fingerprinting.layer_f import LayerF


class TestLayerA:
    """Tests for spectral fingerprinting layer."""

    def test_extract_produces_valid_output(self, sample_audio):
        """Test that extraction produces valid output."""
        layer = LayerA()
        output = layer.extract(sample_audio)

        assert output.layer_type == "A"
        assert len(output.layer_hash) == 64  # SHA-256
        assert 0 <= output.confidence_score <= 1
        assert "features" in output.parameters

    def test_extract_is_deterministic(self, sample_audio):
        """Test that extraction is deterministic."""
        layer = LayerA()
        output1 = layer.extract(sample_audio)
        output2 = layer.extract(sample_audio)

        assert output1.layer_hash == output2.layer_hash

    def test_embed_preserves_audio_length(self, sample_audio):
        """Test that embedding preserves audio length."""
        layer = LayerA()
        embedded = layer.embed(sample_audio, {"test": "data"})

        assert len(embedded) == len(sample_audio)

    def test_embed_is_subtle(self, sample_audio):
        """Test that embedding changes are subtle."""
        layer = LayerA()
        embedded = layer.embed(sample_audio, {"test": "data"})

        # Changes should be small
        diff = np.abs(embedded - sample_audio)
        assert np.max(diff) < 0.1


class TestLayerB:
    """Tests for temporal fingerprinting layer."""

    def test_extract_produces_valid_output(self, sample_audio):
        """Test that extraction produces valid output."""
        layer = LayerB()
        output = layer.extract(sample_audio)

        assert output.layer_type == "B"
        assert len(output.layer_hash) == 64
        assert 0 <= output.confidence_score <= 1

    def test_extract_detects_tempo_features(self, sample_audio):
        """Test that temporal features are detected."""
        layer = LayerB()
        output = layer.extract(sample_audio)

        assert "features" in output.parameters
        features = output.parameters["features"]
        assert "tempo" in features


class TestLayerC:
    """Tests for physiological fingerprinting layer."""

    def test_extract_produces_valid_output(self, sample_audio):
        """Test that extraction produces valid output."""
        layer = LayerC()
        output = layer.extract(sample_audio)

        assert output.layer_type == "C"
        assert len(output.layer_hash) == 64
        assert 0 <= output.confidence_score <= 1

    def test_extract_includes_pitch_features(self, sample_audio):
        """Test that pitch features are included."""
        layer = LayerC()
        output = layer.extract(sample_audio)

        assert "features" in output.parameters


class TestLayerD:
    """Tests for semantic fingerprinting layer."""

    def test_extract_produces_valid_output(self, sample_audio):
        """Test that extraction produces valid output."""
        layer = LayerD()
        output = layer.extract(sample_audio)

        assert output.layer_type == "D"
        assert len(output.layer_hash) == 64
        assert 0 <= output.confidence_score <= 1

    def test_extract_includes_mfcc_features(self, sample_audio):
        """Test that MFCC features are included."""
        layer = LayerD()
        output = layer.extract(sample_audio)

        features = output.parameters.get("features", {})
        assert "mfcc_mean" in features


class TestLayerE:
    """Tests for adversarial fingerprinting layer."""

    def test_extract_produces_valid_output(self, sample_audio):
        """Test that extraction produces valid output."""
        layer = LayerE()
        output = layer.extract(sample_audio)

        assert output.layer_type == "E"
        assert len(output.layer_hash) == 64
        assert 0 <= output.confidence_score <= 1

    def test_embed_adds_perturbations(self, sample_audio):
        """Test that embedding adds adversarial perturbations."""
        layer = LayerE()
        embedded = layer.embed(sample_audio, {"test": "data"})

        # Should be different but similar
        assert not np.array_equal(embedded, sample_audio)
        correlation = np.corrcoef(embedded.flatten(), sample_audio.flatten())[0, 1]
        assert correlation > 0.99  # Very similar


class TestLayerF:
    """Tests for meta fingerprinting layer."""

    def test_extract_produces_valid_output(self, sample_audio):
        """Test that extraction produces valid output."""
        layer = LayerF()
        output = layer.extract(sample_audio)

        assert output.layer_type == "F"
        assert len(output.layer_hash) == 64
        assert 0 <= output.confidence_score <= 1

    def test_extract_with_layer_outputs(self, sample_audio):
        """Test meta layer with other layer outputs."""
        # Create outputs from other layers
        layer_a = LayerA()
        layer_b = LayerB()
        output_a = layer_a.extract(sample_audio)
        output_b = layer_b.extract(sample_audio)

        layer_f = LayerF()
        output = layer_f.extract(sample_audio, [output_a, output_b])

        assert "layer_consistency" in output.parameters
        assert output.parameters["layer_consistency"]["layer_count"] == 2
