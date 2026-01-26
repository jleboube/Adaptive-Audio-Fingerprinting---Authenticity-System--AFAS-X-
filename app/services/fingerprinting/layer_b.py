"""Layer B: Temporal fingerprinting with phase and timing analysis."""

import hashlib

import librosa
import numpy as np

from app.services.fingerprinting.base import FingerprintLayer, LayerOutput


class LayerB(FingerprintLayer):
    """Temporal fingerprint layer using phase and micro-timing.

    This layer analyzes temporal characteristics including phase coherence,
    onset patterns, and micro-timing irregularities that are unique to
    each audio recording.
    """

    layer_type = "B"

    def __init__(
        self,
        sample_rate: int = 22050,
        version: str = "1.0.0",
        frame_length: int = 2048,
        hop_length: int = 512,
    ) -> None:
        super().__init__(sample_rate, version)
        self.frame_length = frame_length
        self.hop_length = hop_length

    def _compute_onset_features(self, audio: np.ndarray) -> dict:
        """Extract onset-related temporal features."""
        # Onset strength envelope
        onset_env = librosa.onset.onset_strength(
            y=audio,
            sr=self.sample_rate,
            hop_length=self.hop_length,
        )

        # Onset detection
        onsets = librosa.onset.onset_detect(
            onset_envelope=onset_env,
            sr=self.sample_rate,
            hop_length=self.hop_length,
        )

        # Compute inter-onset intervals
        if len(onsets) > 1:
            ioi = np.diff(onsets) * self.hop_length / self.sample_rate
            ioi_mean = float(np.mean(ioi))
            ioi_std = float(np.std(ioi))
        else:
            ioi_mean = 0.0
            ioi_std = 0.0

        return {
            "onset_count": len(onsets),
            "onset_strength_mean": float(np.mean(onset_env)),
            "onset_strength_std": float(np.std(onset_env)),
            "ioi_mean": ioi_mean,
            "ioi_std": ioi_std,
        }

    def _compute_phase_features(self, audio: np.ndarray) -> dict:
        """Extract phase-related features."""
        # Compute STFT
        stft = librosa.stft(
            audio, n_fft=self.frame_length, hop_length=self.hop_length
        )
        phase = np.angle(stft)

        # Phase derivative (instantaneous frequency deviation)
        phase_diff = np.diff(phase, axis=1)

        # Unwrap phase for continuity analysis
        unwrapped = np.unwrap(phase, axis=1)

        # Phase coherence across frequency bands
        phase_coherence = np.mean(np.abs(np.diff(phase, axis=0)))

        return {
            "phase_diff_mean": float(np.mean(np.abs(phase_diff))),
            "phase_diff_std": float(np.std(phase_diff)),
            "phase_coherence": float(phase_coherence),
            "unwrapped_range": float(np.ptp(unwrapped)),
        }

    def _compute_tempo_features(self, audio: np.ndarray) -> dict:
        """Extract tempo and rhythm features."""
        # Tempo estimation
        tempo, beat_frames = librosa.beat.beat_track(
            y=audio, sr=self.sample_rate, hop_length=self.hop_length
        )

        # Tempogram for tempo stability
        tempogram = librosa.feature.tempogram(
            y=audio, sr=self.sample_rate, hop_length=self.hop_length
        )

        # Convert tempo to scalar if it's an array
        tempo_value = float(tempo) if np.isscalar(tempo) else float(tempo[0])

        return {
            "tempo": tempo_value,
            "beat_count": len(beat_frames),
            "tempo_stability": float(np.std(np.mean(tempogram, axis=0))),
        }

    def _compute_zero_crossing_features(self, audio: np.ndarray) -> dict:
        """Extract zero-crossing related features."""
        zc = librosa.feature.zero_crossing_rate(
            audio, frame_length=self.frame_length, hop_length=self.hop_length
        )

        return {
            "zc_mean": float(np.mean(zc)),
            "zc_std": float(np.std(zc)),
        }

    def extract(self, audio: np.ndarray) -> LayerOutput:
        """Extract temporal fingerprint from audio."""
        # Gather all temporal features
        onset_features = self._compute_onset_features(audio)
        phase_features = self._compute_phase_features(audio)
        tempo_features = self._compute_tempo_features(audio)
        zc_features = self._compute_zero_crossing_features(audio)

        all_features = {
            **onset_features,
            **phase_features,
            **tempo_features,
            **zc_features,
        }

        # Create deterministic hash
        feature_string = "|".join(f"{k}:{v:.6f}" for k, v in sorted(all_features.items()))
        layer_hash = hashlib.sha256(feature_string.encode()).hexdigest()

        # Confidence based on signal characteristics
        has_onsets = onset_features["onset_count"] > 0
        has_tempo = tempo_features["tempo"] > 0
        phase_quality = 1.0 - min(1.0, phase_features["phase_diff_std"] / 3.0)

        confidence = (
            0.4 * float(has_onsets)
            + 0.3 * float(has_tempo)
            + 0.3 * phase_quality
        )

        return LayerOutput(
            layer_type=self.layer_type,
            layer_hash=layer_hash,
            confidence_score=confidence,
            parameters={
                "frame_length": self.frame_length,
                "hop_length": self.hop_length,
                "features": all_features,
            },
        )

    def embed(self, audio: np.ndarray, fingerprint_data: dict) -> np.ndarray:
        """Embed temporal fingerprint using micro-timing shifts."""
        # Convert fingerprint to bits
        data_bytes = hashlib.sha256(str(fingerprint_data).encode()).digest()
        bits = np.unpackbits(np.frombuffer(data_bytes, dtype=np.uint8))

        # Apply subtle phase shifts based on fingerprint bits
        stft = librosa.stft(
            audio, n_fft=self.frame_length, hop_length=self.hop_length
        )
        magnitude = np.abs(stft)
        phase = np.angle(stft)

        # Embed by modifying phase in low-energy regions
        energy = np.sum(magnitude ** 2, axis=0)
        low_energy_mask = energy < np.percentile(energy, 30)

        bit_idx = 0
        for frame_idx in np.where(low_energy_mask)[0]:
            if bit_idx >= len(bits):
                break
            # Very subtle phase shift
            shift = 0.001 if bits[bit_idx] else -0.001
            phase[:, frame_idx] += shift
            bit_idx += 1

        # Reconstruct
        modified_stft = magnitude * np.exp(1j * phase)
        modified_audio = librosa.istft(
            modified_stft, hop_length=self.hop_length, length=len(audio)
        )

        return modified_audio.astype(audio.dtype)

    def verify(self, audio: np.ndarray, expected_hash: str) -> tuple[bool, float]:
        """Verify temporal fingerprint."""
        current = self.extract(audio)

        if current.layer_hash == expected_hash:
            return True, current.confidence_score

        return False, current.confidence_score * 0.5
