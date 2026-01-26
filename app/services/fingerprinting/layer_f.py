"""Layer F: Meta fingerprinting with cross-layer consistency checks."""

import hashlib
import json

import numpy as np

from app.services.fingerprinting.base import FingerprintLayer, LayerOutput


class LayerF(FingerprintLayer):
    """Meta fingerprint layer for cross-layer consistency validation.

    This layer:
    - Combines hashes from all other layers
    - Verifies cross-layer consistency
    - Detects selective modifications
    - Provides overall integrity score
    """

    layer_type = "F"

    def __init__(
        self,
        sample_rate: int = 22050,
        version: str = "1.0.0",
        hash_algorithm: str = "sha256",
    ) -> None:
        super().__init__(sample_rate, version)
        self.hash_algorithm = hash_algorithm

    def _compute_audio_statistics(self, audio: np.ndarray) -> dict:
        """Compute basic audio statistics for integrity checking."""
        return {
            "length": len(audio),
            "mean": float(np.mean(audio)),
            "std": float(np.std(audio)),
            "min": float(np.min(audio)),
            "max": float(np.max(audio)),
            "rms": float(np.sqrt(np.mean(audio ** 2))),
            "zero_crossings": int(np.sum(np.diff(np.sign(audio)) != 0)),
            "checksum": hashlib.md5(audio.tobytes()).hexdigest()[:16],
        }

    def _compute_layer_consistency(self, layer_outputs: list[LayerOutput]) -> dict:
        """Analyze consistency across layer outputs."""
        if not layer_outputs:
            return {
                "layer_count": 0,
                "avg_confidence": 0.0,
                "confidence_variance": 0.0,
                "all_valid": False,
            }

        confidences = [lo.confidence_score for lo in layer_outputs]

        return {
            "layer_count": len(layer_outputs),
            "avg_confidence": float(np.mean(confidences)),
            "confidence_variance": float(np.var(confidences)),
            "min_confidence": float(np.min(confidences)),
            "max_confidence": float(np.max(confidences)),
            "all_valid": all(c > 0.3 for c in confidences),
        }

    def extract(
        self,
        audio: np.ndarray,
        layer_outputs: list[LayerOutput] | None = None,
    ) -> LayerOutput:
        """Extract meta fingerprint from audio and other layers.

        Args:
            audio: Audio samples
            layer_outputs: Optional list of outputs from layers A-E
        """
        audio_stats = self._compute_audio_statistics(audio)

        # Combine layer hashes if available
        if layer_outputs:
            layer_hashes = {lo.layer_type: lo.layer_hash for lo in layer_outputs}
            layer_consistency = self._compute_layer_consistency(layer_outputs)
        else:
            layer_hashes = {}
            layer_consistency = self._compute_layer_consistency([])

        # Create meta hash
        meta_data = {
            "audio_stats": audio_stats,
            "layer_hashes": layer_hashes,
            "layer_consistency": layer_consistency,
            "version": self.version,
        }

        # Serialize deterministically
        meta_string = json.dumps(meta_data, sort_keys=True, separators=(",", ":"))
        layer_hash = hashlib.sha256(meta_string.encode()).hexdigest()

        # Meta confidence based on layer consistency
        if layer_outputs:
            base_confidence = layer_consistency["avg_confidence"]
            consistency_bonus = 1.0 - layer_consistency["confidence_variance"]
            confidence = 0.7 * base_confidence + 0.3 * consistency_bonus
        else:
            # Without other layers, confidence based on audio quality
            confidence = min(1.0, audio_stats["rms"] * 5)

        return LayerOutput(
            layer_type=self.layer_type,
            layer_hash=layer_hash,
            confidence_score=max(0.1, min(1.0, confidence)),
            parameters={
                "hash_algorithm": self.hash_algorithm,
                "audio_stats": audio_stats,
                "layer_hashes": layer_hashes,
                "layer_consistency": layer_consistency,
            },
        )

    def embed(self, audio: np.ndarray, fingerprint_data: dict) -> np.ndarray:
        """Meta layer doesn't embed - it validates.

        Returns audio unchanged. The meta layer's value is in verification.
        """
        # No modification - meta layer is for validation only
        return audio

    def verify(
        self,
        audio: np.ndarray,
        expected_hash: str,
        current_layer_outputs: list[LayerOutput] | None = None,
        expected_layer_hashes: dict | None = None,
    ) -> tuple[bool, float]:
        """Verify meta fingerprint and cross-layer consistency.

        Args:
            audio: Audio to verify
            expected_hash: Expected meta layer hash
            current_layer_outputs: Current layer outputs for comparison
            expected_layer_hashes: Expected hashes for each layer
        """
        current = self.extract(audio, current_layer_outputs)

        # Check meta hash
        meta_match = current.layer_hash == expected_hash

        # Check individual layer consistency if expected hashes provided
        if expected_layer_hashes and current_layer_outputs:
            matching_layers = 0
            for lo in current_layer_outputs:
                expected = expected_layer_hashes.get(lo.layer_type)
                if expected and lo.layer_hash == expected:
                    matching_layers += 1

            layer_match_ratio = matching_layers / len(current_layer_outputs)
        else:
            layer_match_ratio = 1.0 if meta_match else 0.0

        # Combined confidence
        if meta_match and layer_match_ratio > 0.8:
            return True, current.confidence_score

        # Partial match indicates modification
        if layer_match_ratio > 0.5:
            return False, layer_match_ratio * 0.5

        return False, 0.1

    def compute_integrity_score(
        self,
        current_layer_outputs: list[LayerOutput],
        expected_layer_outputs: list[LayerOutput],
    ) -> dict:
        """Compute detailed integrity score between current and expected layers.

        Returns detailed breakdown of matches and mismatches.
        """
        results = {
            "overall_match": True,
            "layer_results": {},
            "integrity_score": 0.0,
        }

        expected_map = {lo.layer_type: lo for lo in expected_layer_outputs}

        matching_layers = 0
        total_confidence = 0.0

        for current_lo in current_layer_outputs:
            expected_lo = expected_map.get(current_lo.layer_type)

            if expected_lo:
                matches = current_lo.layer_hash == expected_lo.layer_hash
                results["layer_results"][current_lo.layer_type] = {
                    "matches": matches,
                    "current_hash": current_lo.layer_hash[:16] + "...",
                    "expected_hash": expected_lo.layer_hash[:16] + "...",
                    "current_confidence": current_lo.confidence_score,
                    "expected_confidence": expected_lo.confidence_score,
                }

                if matches:
                    matching_layers += 1
                else:
                    results["overall_match"] = False

                total_confidence += current_lo.confidence_score
            else:
                results["layer_results"][current_lo.layer_type] = {
                    "matches": False,
                    "error": "Expected layer not found",
                }
                results["overall_match"] = False

        # Compute integrity score
        if current_layer_outputs:
            match_ratio = matching_layers / len(current_layer_outputs)
            avg_confidence = total_confidence / len(current_layer_outputs)
            results["integrity_score"] = 0.6 * match_ratio + 0.4 * avg_confidence
        else:
            results["integrity_score"] = 0.0

        return results
