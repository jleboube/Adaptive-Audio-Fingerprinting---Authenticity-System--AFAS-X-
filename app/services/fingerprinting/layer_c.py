"""Layer C: Physiological fingerprinting with voice characteristics analysis."""

import hashlib

import librosa
import numpy as np

from app.services.fingerprinting.base import FingerprintLayer, LayerOutput

# Try to import parselmouth, fall back to librosa-only if not available
try:
    import parselmouth
    from parselmouth.praat import call

    HAS_PARSELMOUTH = True
except ImportError:
    HAS_PARSELMOUTH = False


class LayerC(FingerprintLayer):
    """Physiological fingerprint layer for voice characteristics.

    This layer analyzes physiological markers in voice recordings including:
    - Jitter (pitch variation)
    - Shimmer (amplitude variation)
    - Harmonic-to-noise ratio
    - Breath noise patterns
    - Formant frequencies
    """

    layer_type = "C"

    def __init__(
        self,
        sample_rate: int = 22050,
        version: str = "1.0.0",
        pitch_floor: float = 75.0,
        pitch_ceiling: float = 600.0,
    ) -> None:
        super().__init__(sample_rate, version)
        self.pitch_floor = pitch_floor
        self.pitch_ceiling = pitch_ceiling

    def _compute_pitch_features_praat(self, audio: np.ndarray) -> dict:
        """Compute pitch features using Praat/Parselmouth."""
        # Create Praat Sound object
        snd = parselmouth.Sound(audio, sampling_frequency=self.sample_rate)

        # Extract pitch
        pitch = call(snd, "To Pitch", 0.0, self.pitch_floor, self.pitch_ceiling)

        # Get pitch values
        pitch_values = pitch.selected_array["frequency"]
        pitch_values = pitch_values[pitch_values > 0]  # Remove unvoiced

        if len(pitch_values) == 0:
            return {
                "pitch_mean": 0.0,
                "pitch_std": 0.0,
                "pitch_range": 0.0,
                "voiced_ratio": 0.0,
            }

        return {
            "pitch_mean": float(np.mean(pitch_values)),
            "pitch_std": float(np.std(pitch_values)),
            "pitch_range": float(np.ptp(pitch_values)),
            "voiced_ratio": float(len(pitch_values) / len(pitch.selected_array["frequency"])),
        }

    def _compute_pitch_features_librosa(self, audio: np.ndarray) -> dict:
        """Compute pitch features using librosa (fallback)."""
        # Use librosa's pyin for pitch tracking
        f0, voiced_flag, voiced_probs = librosa.pyin(
            audio,
            fmin=self.pitch_floor,
            fmax=self.pitch_ceiling,
            sr=self.sample_rate,
        )

        # Filter to voiced frames
        f0_voiced = f0[~np.isnan(f0)]

        if len(f0_voiced) == 0:
            return {
                "pitch_mean": 0.0,
                "pitch_std": 0.0,
                "pitch_range": 0.0,
                "voiced_ratio": 0.0,
            }

        return {
            "pitch_mean": float(np.mean(f0_voiced)),
            "pitch_std": float(np.std(f0_voiced)),
            "pitch_range": float(np.ptp(f0_voiced)),
            "voiced_ratio": float(np.sum(~np.isnan(f0)) / len(f0)),
        }

    def _compute_jitter_shimmer_praat(self, audio: np.ndarray) -> dict:
        """Compute jitter and shimmer using Praat."""
        snd = parselmouth.Sound(audio, sampling_frequency=self.sample_rate)

        # Create PointProcess for voice analysis
        point_process = call(
            snd, "To PointProcess (periodic, cc)",
            self.pitch_floor, self.pitch_ceiling
        )

        # Jitter (local) - cycle-to-cycle variation in pitch period
        try:
            jitter = call(
                point_process, "Get jitter (local)",
                0.0, 0.0, 0.0001, 0.02, 1.3
            )
        except Exception:
            jitter = 0.0

        # Shimmer (local) - cycle-to-cycle variation in amplitude
        try:
            shimmer = call(
                [snd, point_process], "Get shimmer (local)",
                0.0, 0.0, 0.0001, 0.02, 1.3, 1.6
            )
        except Exception:
            shimmer = 0.0

        return {
            "jitter": float(jitter) if not np.isnan(jitter) else 0.0,
            "shimmer": float(shimmer) if not np.isnan(shimmer) else 0.0,
        }

    def _compute_jitter_shimmer_librosa(self, audio: np.ndarray) -> dict:
        """Estimate jitter and shimmer using librosa (fallback)."""
        # Get pitch track
        f0, _, _ = librosa.pyin(
            audio,
            fmin=self.pitch_floor,
            fmax=self.pitch_ceiling,
            sr=self.sample_rate,
        )

        # Filter voiced frames
        f0_voiced = f0[~np.isnan(f0)]

        if len(f0_voiced) < 3:
            return {"jitter": 0.0, "shimmer": 0.0}

        # Jitter approximation: relative variation in period
        periods = 1.0 / f0_voiced
        period_diffs = np.abs(np.diff(periods))
        jitter = float(np.mean(period_diffs) / np.mean(periods)) if np.mean(periods) > 0 else 0.0

        # Shimmer approximation: relative variation in amplitude
        frames = librosa.util.frame(audio, frame_length=2048, hop_length=512)
        amplitudes = np.max(np.abs(frames), axis=0)
        if len(amplitudes) > 1:
            amp_diffs = np.abs(np.diff(amplitudes))
            shimmer = float(np.mean(amp_diffs) / np.mean(amplitudes)) if np.mean(amplitudes) > 0 else 0.0
        else:
            shimmer = 0.0

        return {"jitter": jitter, "shimmer": shimmer}

    def _compute_hnr_praat(self, audio: np.ndarray) -> float:
        """Compute Harmonics-to-Noise Ratio using Praat."""
        snd = parselmouth.Sound(audio, sampling_frequency=self.sample_rate)

        try:
            harmonicity = call(
                snd, "To Harmonicity (cc)",
                0.01, self.pitch_floor, 0.1, 1.0
            )
            hnr = call(harmonicity, "Get mean", 0.0, 0.0)
            return float(hnr) if not np.isnan(hnr) else 0.0
        except Exception:
            return 0.0

    def _compute_hnr_librosa(self, audio: np.ndarray) -> float:
        """Estimate HNR using librosa (fallback)."""
        # Compute harmonic and percussive components
        harmonic, percussive = librosa.effects.hpss(audio)

        # HNR approximation
        harmonic_energy = np.sum(harmonic ** 2)
        noise_energy = np.sum(percussive ** 2)

        if noise_energy > 0:
            hnr = 10 * np.log10(harmonic_energy / noise_energy)
            return float(min(40, max(-10, hnr)))  # Clamp to reasonable range
        return 0.0

    def _compute_formants_librosa(self, audio: np.ndarray) -> dict:
        """Estimate formants using LPC analysis."""
        # Number of formants to estimate
        n_formants = 4

        # LPC analysis
        lpc_order = 2 * n_formants + 2
        lpc_coeffs = librosa.lpc(audio, order=lpc_order)

        # Find roots of LPC polynomial
        roots = np.roots(lpc_coeffs)

        # Convert to frequencies
        angles = np.angle(roots)
        freqs = angles * self.sample_rate / (2 * np.pi)

        # Filter positive frequencies and sort
        freqs = freqs[freqs > 0]
        freqs = np.sort(freqs)

        # Get first n_formants
        formants = freqs[:n_formants] if len(freqs) >= n_formants else np.zeros(n_formants)

        return {
            f"formant_{i+1}": float(formants[i]) if i < len(formants) else 0.0
            for i in range(n_formants)
        }

    def _compute_breath_noise(self, audio: np.ndarray) -> dict:
        """Detect breath noise patterns in speech."""
        # Compute spectral flux
        stft = librosa.stft(audio)
        spectral_flux = np.sqrt(np.mean(np.diff(np.abs(stft), axis=1) ** 2, axis=0))

        # High-frequency energy (breath noise is typically high-freq)
        high_freq_start = int(4000 * len(stft) / (self.sample_rate / 2))
        high_freq_energy = np.mean(np.abs(stft[high_freq_start:, :]) ** 2, axis=0)

        # Detect breath segments (high HF energy, high flux)
        breath_threshold = np.percentile(high_freq_energy, 80)
        breath_segments = high_freq_energy > breath_threshold

        return {
            "breath_ratio": float(np.mean(breath_segments)),
            "spectral_flux_mean": float(np.mean(spectral_flux)),
            "high_freq_energy_mean": float(np.mean(high_freq_energy)),
        }

    def extract(self, audio: np.ndarray) -> LayerOutput:
        """Extract physiological fingerprint from audio."""
        # Use Praat if available, otherwise fall back to librosa
        if HAS_PARSELMOUTH:
            pitch_features = self._compute_pitch_features_praat(audio)
            jitter_shimmer = self._compute_jitter_shimmer_praat(audio)
            hnr = self._compute_hnr_praat(audio)
        else:
            pitch_features = self._compute_pitch_features_librosa(audio)
            jitter_shimmer = self._compute_jitter_shimmer_librosa(audio)
            hnr = self._compute_hnr_librosa(audio)

        formant_features = self._compute_formants_librosa(audio)
        breath_features = self._compute_breath_noise(audio)

        all_features = {
            **pitch_features,
            **jitter_shimmer,
            "hnr": hnr,
            **formant_features,
            **breath_features,
            "has_parselmouth": HAS_PARSELMOUTH,
        }

        # Create hash
        feature_string = "|".join(
            f"{k}:{v:.6f}" if isinstance(v, float) else f"{k}:{v}"
            for k, v in sorted(all_features.items())
        )
        layer_hash = hashlib.sha256(feature_string.encode()).hexdigest()

        # Confidence based on voice detection quality
        voiced_ratio = pitch_features.get("voiced_ratio", 0.0)
        has_formants = any(v > 0 for k, v in formant_features.items())

        confidence = (
            0.5 * voiced_ratio
            + 0.3 * float(has_formants)
            + 0.2 * min(1.0, hnr / 20) if hnr > 0 else 0.0
        )

        return LayerOutput(
            layer_type=self.layer_type,
            layer_hash=layer_hash,
            confidence_score=max(0.0, min(1.0, confidence)),
            parameters={
                "pitch_floor": self.pitch_floor,
                "pitch_ceiling": self.pitch_ceiling,
                "has_parselmouth": HAS_PARSELMOUTH,
                "features": all_features,
            },
        )

    def embed(self, audio: np.ndarray, fingerprint_data: dict) -> np.ndarray:
        """Embed physiological fingerprint (minimal modification for voice).

        Voice characteristics are inherent - we only add subtle markers
        that don't affect perceived voice quality.
        """
        # Very subtle high-frequency watermark
        data_bytes = hashlib.sha256(str(fingerprint_data).encode()).digest()
        bits = np.unpackbits(np.frombuffer(data_bytes, dtype=np.uint8))

        # Generate near-ultrasonic marker
        t = np.arange(len(audio)) / self.sample_rate
        marker_freq = 18000  # Near ultrasonic
        marker = np.zeros_like(audio)

        # Encode bits as frequency shifts
        samples_per_bit = len(audio) // len(bits)
        for i, bit in enumerate(bits):
            start = i * samples_per_bit
            end = min((i + 1) * samples_per_bit, len(audio))
            freq = marker_freq + (100 if bit else -100)
            marker[start:end] = 0.0001 * np.sin(2 * np.pi * freq * t[start:end])

        return (audio + marker).astype(audio.dtype)

    def verify(self, audio: np.ndarray, expected_hash: str) -> tuple[bool, float]:
        """Verify physiological fingerprint."""
        current = self.extract(audio)

        if current.layer_hash == expected_hash:
            return True, current.confidence_score

        return False, current.confidence_score * 0.5
