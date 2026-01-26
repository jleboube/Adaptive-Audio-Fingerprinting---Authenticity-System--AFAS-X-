"""Layer A: Spectral fingerprinting with psychoacoustic masking."""

import hashlib

import librosa
import numpy as np
from scipy import signal

from app.services.fingerprinting.base import FingerprintLayer, LayerOutput


class LayerA(FingerprintLayer):
    """Spectral fingerprint layer using frequency perturbations.

    This layer analyzes spectral characteristics and embeds imperceptible
    perturbations in frequency bands, leveraging psychoacoustic masking
    to hide modifications.
    """

    layer_type = "A"

    def __init__(
        self,
        sample_rate: int = 22050,
        version: str = "1.0.0",
        n_fft: int = 2048,
        hop_length: int = 512,
        n_mels: int = 128,
    ) -> None:
        super().__init__(sample_rate, version)
        self.n_fft = n_fft
        self.hop_length = hop_length
        self.n_mels = n_mels

    def _compute_mel_spectrogram(self, audio: np.ndarray) -> np.ndarray:
        """Compute mel spectrogram of audio."""
        return librosa.feature.melspectrogram(
            y=audio,
            sr=self.sample_rate,
            n_fft=self.n_fft,
            hop_length=self.hop_length,
            n_mels=self.n_mels,
        )

    def _compute_spectral_features(self, audio: np.ndarray) -> dict:
        """Extract key spectral features for fingerprinting."""
        # Mel spectrogram
        mel_spec = self._compute_mel_spectrogram(audio)

        # Spectral centroid
        centroid = librosa.feature.spectral_centroid(
            y=audio, sr=self.sample_rate, n_fft=self.n_fft, hop_length=self.hop_length
        )

        # Spectral bandwidth
        bandwidth = librosa.feature.spectral_bandwidth(
            y=audio, sr=self.sample_rate, n_fft=self.n_fft, hop_length=self.hop_length
        )

        # Spectral rolloff
        rolloff = librosa.feature.spectral_rolloff(
            y=audio, sr=self.sample_rate, n_fft=self.n_fft, hop_length=self.hop_length
        )

        # Spectral contrast
        contrast = librosa.feature.spectral_contrast(
            y=audio, sr=self.sample_rate, n_fft=self.n_fft, hop_length=self.hop_length
        )

        return {
            "mel_mean": float(np.mean(mel_spec)),
            "mel_std": float(np.std(mel_spec)),
            "centroid_mean": float(np.mean(centroid)),
            "centroid_std": float(np.std(centroid)),
            "bandwidth_mean": float(np.mean(bandwidth)),
            "rolloff_mean": float(np.mean(rolloff)),
            "contrast_mean": float(np.mean(contrast)),
        }

    def _compute_psychoacoustic_mask(self, audio: np.ndarray) -> np.ndarray:
        """Compute psychoacoustic masking threshold.

        Uses a simplified model of the auditory system to determine
        where modifications can be hidden.
        """
        # Compute STFT
        stft = librosa.stft(audio, n_fft=self.n_fft, hop_length=self.hop_length)
        magnitude = np.abs(stft)

        # Compute power spectral density
        psd = magnitude ** 2

        # Apply frequency masking (simplified model)
        # Frequencies near loud components are masked
        mask = np.zeros_like(psd)
        for i in range(psd.shape[1]):
            frame_psd = psd[:, i]
            # Find peaks
            peaks, _ = signal.find_peaks(frame_psd, height=np.mean(frame_psd))
            for peak in peaks:
                # Create masking spread around peaks
                spread = 50  # bins
                start = max(0, peak - spread)
                end = min(len(frame_psd), peak + spread)
                # Masking threshold decreases with distance from peak
                for j in range(start, end):
                    distance = abs(j - peak)
                    mask[j, i] = max(
                        mask[j, i],
                        frame_psd[peak] * np.exp(-distance / 20),
                    )

        return mask

    def extract(self, audio: np.ndarray) -> LayerOutput:
        """Extract spectral fingerprint from audio."""
        features = self._compute_spectral_features(audio)

        # Create deterministic hash from features
        feature_string = "|".join(f"{k}:{v:.6f}" for k, v in sorted(features.items()))
        layer_hash = hashlib.sha256(feature_string.encode()).hexdigest()

        # Confidence based on signal quality
        rms = np.sqrt(np.mean(audio ** 2))
        silence_ratio = np.sum(np.abs(audio) < 0.001) / len(audio)
        confidence = min(1.0, max(0.0, 1.0 - silence_ratio) * min(1.0, rms * 10))

        return LayerOutput(
            layer_type=self.layer_type,
            layer_hash=layer_hash,
            confidence_score=confidence,
            parameters={
                "n_fft": self.n_fft,
                "hop_length": self.hop_length,
                "n_mels": self.n_mels,
                "features": features,
            },
        )

    def embed(self, audio: np.ndarray, fingerprint_data: dict) -> np.ndarray:
        """Embed spectral fingerprint using psychoacoustic masking."""
        # Compute masking threshold
        mask = self._compute_psychoacoustic_mask(audio)

        # Convert fingerprint data to bit sequence
        data_bytes = hashlib.sha256(str(fingerprint_data).encode()).digest()
        bits = np.unpackbits(np.frombuffer(data_bytes, dtype=np.uint8))

        # Embed bits in masked regions
        stft = librosa.stft(audio, n_fft=self.n_fft, hop_length=self.hop_length)
        magnitude = np.abs(stft)
        phase = np.angle(stft)

        # Find frames with sufficient masking for embedding
        mask_threshold = np.percentile(mask, 90)
        embeddable_positions = np.where(mask > mask_threshold)

        # Embed bits by subtly modifying magnitude
        bit_idx = 0
        for i in range(min(len(bits), len(embeddable_positions[0]))):
            freq_idx = embeddable_positions[0][i]
            time_idx = embeddable_positions[1][i]

            # Subtle magnitude modification based on bit
            if bits[bit_idx % len(bits)]:
                magnitude[freq_idx, time_idx] *= 1.001  # Very subtle increase
            else:
                magnitude[freq_idx, time_idx] *= 0.999  # Very subtle decrease

            bit_idx += 1

        # Reconstruct audio
        modified_stft = magnitude * np.exp(1j * phase)
        modified_audio = librosa.istft(
            modified_stft, hop_length=self.hop_length, length=len(audio)
        )

        return modified_audio.astype(audio.dtype)

    def verify(self, audio: np.ndarray, expected_hash: str) -> tuple[bool, float]:
        """Verify spectral fingerprint against expected hash."""
        current = self.extract(audio)

        # Direct hash comparison
        if current.layer_hash == expected_hash:
            return True, current.confidence_score

        # Feature-based similarity for modified audio
        # Extract original features from hash context (if available)
        # For now, return based on hash mismatch
        return False, current.confidence_score * 0.5
