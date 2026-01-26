"""Layer D: Semantic fingerprinting with prosody and emphasis analysis."""

import hashlib

import librosa
import numpy as np

from app.services.fingerprinting.base import FingerprintLayer, LayerOutput


class LayerD(FingerprintLayer):
    """Semantic fingerprint layer for prosodic features.

    This layer analyzes semantic-level audio characteristics:
    - Emphasis patterns (stressed syllables)
    - Pause structure and timing
    - Intonation contours
    - Speaking rate variations
    - Energy dynamics
    """

    layer_type = "D"

    def __init__(
        self,
        sample_rate: int = 22050,
        version: str = "1.0.0",
        n_mfcc: int = 13,
        hop_length: int = 512,
    ) -> None:
        super().__init__(sample_rate, version)
        self.n_mfcc = n_mfcc
        self.hop_length = hop_length

    def _compute_mfcc_features(self, audio: np.ndarray) -> dict:
        """Compute MFCC-based features for semantic analysis."""
        mfccs = librosa.feature.mfcc(
            y=audio,
            sr=self.sample_rate,
            n_mfcc=self.n_mfcc,
            hop_length=self.hop_length,
        )

        # Delta MFCCs (rate of change)
        delta_mfccs = librosa.feature.delta(mfccs)

        # Delta-delta MFCCs (acceleration)
        delta2_mfccs = librosa.feature.delta(mfccs, order=2)

        return {
            "mfcc_mean": [float(x) for x in np.mean(mfccs, axis=1)],
            "mfcc_std": [float(x) for x in np.std(mfccs, axis=1)],
            "delta_mfcc_mean": [float(x) for x in np.mean(delta_mfccs, axis=1)],
            "delta2_mfcc_mean": [float(x) for x in np.mean(delta2_mfccs, axis=1)],
        }

    def _compute_emphasis_features(self, audio: np.ndarray) -> dict:
        """Detect emphasis patterns in speech."""
        # RMS energy over time
        rms = librosa.feature.rms(y=audio, hop_length=self.hop_length)[0]

        # Find emphasis peaks (high energy moments)
        energy_threshold = np.percentile(rms, 75)
        emphasis_frames = rms > energy_threshold

        # Compute emphasis statistics
        emphasis_runs = np.diff(np.concatenate([[0], emphasis_frames.astype(int), [0]]))
        emphasis_starts = np.where(emphasis_runs == 1)[0]
        emphasis_ends = np.where(emphasis_runs == -1)[0]

        if len(emphasis_starts) > 0 and len(emphasis_ends) > 0:
            emphasis_durations = emphasis_ends - emphasis_starts
            emphasis_intervals = np.diff(emphasis_starts) if len(emphasis_starts) > 1 else [0]
        else:
            emphasis_durations = [0]
            emphasis_intervals = [0]

        return {
            "emphasis_count": len(emphasis_starts),
            "emphasis_duration_mean": float(np.mean(emphasis_durations)),
            "emphasis_interval_mean": float(np.mean(emphasis_intervals)),
            "energy_range": float(np.ptp(rms)),
            "energy_mean": float(np.mean(rms)),
        }

    def _compute_pause_features(self, audio: np.ndarray) -> dict:
        """Analyze pause structure and silence patterns."""
        # RMS energy
        rms = librosa.feature.rms(y=audio, hop_length=self.hop_length)[0]

        # Detect silence/pause regions
        silence_threshold = np.percentile(rms, 10)
        is_silence = rms < silence_threshold

        # Find pause segments
        silence_runs = np.diff(np.concatenate([[0], is_silence.astype(int), [0]]))
        silence_starts = np.where(silence_runs == 1)[0]
        silence_ends = np.where(silence_runs == -1)[0]

        if len(silence_starts) > 0 and len(silence_ends) > 0:
            pause_durations = (silence_ends - silence_starts) * self.hop_length / self.sample_rate
            pause_durations = pause_durations[pause_durations > 0.1]  # Filter very short pauses
        else:
            pause_durations = np.array([0])

        return {
            "pause_count": len(pause_durations),
            "pause_duration_mean": float(np.mean(pause_durations)) if len(pause_durations) > 0 else 0.0,
            "pause_duration_std": float(np.std(pause_durations)) if len(pause_durations) > 1 else 0.0,
            "silence_ratio": float(np.mean(is_silence)),
        }

    def _compute_intonation_features(self, audio: np.ndarray) -> dict:
        """Analyze intonation contours."""
        # Pitch tracking
        f0, voiced_flag, _ = librosa.pyin(
            audio,
            fmin=75,
            fmax=600,
            sr=self.sample_rate,
            hop_length=self.hop_length,
        )

        # Filter to voiced frames
        f0_voiced = f0[~np.isnan(f0)]

        if len(f0_voiced) < 10:
            return {
                "intonation_slope": 0.0,
                "intonation_range": 0.0,
                "pitch_contour_complexity": 0.0,
            }

        # Compute intonation slope (overall pitch trend)
        x = np.arange(len(f0_voiced))
        slope = np.polyfit(x, f0_voiced, 1)[0]

        # Pitch range in semitones
        pitch_range = 12 * np.log2(np.max(f0_voiced) / np.min(f0_voiced)) if np.min(f0_voiced) > 0 else 0

        # Contour complexity (number of direction changes)
        pitch_diff = np.diff(f0_voiced)
        direction_changes = np.sum(np.diff(np.sign(pitch_diff)) != 0)
        complexity = direction_changes / len(f0_voiced)

        return {
            "intonation_slope": float(slope),
            "intonation_range": float(pitch_range),
            "pitch_contour_complexity": float(complexity),
        }

    def _compute_speaking_rate(self, audio: np.ndarray) -> dict:
        """Estimate speaking rate from onset patterns."""
        # Onset detection
        onset_env = librosa.onset.onset_strength(
            y=audio, sr=self.sample_rate, hop_length=self.hop_length
        )
        onsets = librosa.onset.onset_detect(
            onset_envelope=onset_env,
            sr=self.sample_rate,
            hop_length=self.hop_length,
        )

        # Duration in seconds
        duration = len(audio) / self.sample_rate

        # Syllable rate estimation (onsets per second)
        syllable_rate = len(onsets) / duration if duration > 0 else 0

        # Rate variability
        if len(onsets) > 1:
            onset_times = onsets * self.hop_length / self.sample_rate
            intervals = np.diff(onset_times)
            rate_variability = float(np.std(intervals) / np.mean(intervals)) if np.mean(intervals) > 0 else 0
        else:
            rate_variability = 0.0

        return {
            "syllable_rate": float(syllable_rate),
            "rate_variability": rate_variability,
            "duration_seconds": float(duration),
        }

    def extract(self, audio: np.ndarray) -> LayerOutput:
        """Extract semantic fingerprint from audio."""
        mfcc_features = self._compute_mfcc_features(audio)
        emphasis_features = self._compute_emphasis_features(audio)
        pause_features = self._compute_pause_features(audio)
        intonation_features = self._compute_intonation_features(audio)
        rate_features = self._compute_speaking_rate(audio)

        # Flatten MFCC lists for hashing
        flat_features = {
            **{f"mfcc_mean_{i}": v for i, v in enumerate(mfcc_features["mfcc_mean"])},
            **{f"mfcc_std_{i}": v for i, v in enumerate(mfcc_features["mfcc_std"])},
            **emphasis_features,
            **pause_features,
            **intonation_features,
            **rate_features,
        }

        # Create hash
        feature_string = "|".join(f"{k}:{v:.6f}" for k, v in sorted(flat_features.items()))
        layer_hash = hashlib.sha256(feature_string.encode()).hexdigest()

        # Confidence based on speech quality indicators
        has_emphasis = emphasis_features["emphasis_count"] > 0
        has_pauses = pause_features["pause_count"] > 0
        has_intonation = intonation_features["intonation_range"] > 0

        confidence = (
            0.3 * float(has_emphasis)
            + 0.3 * float(has_pauses)
            + 0.4 * float(has_intonation)
        )

        return LayerOutput(
            layer_type=self.layer_type,
            layer_hash=layer_hash,
            confidence_score=max(0.1, confidence),  # Minimum confidence
            parameters={
                "n_mfcc": self.n_mfcc,
                "hop_length": self.hop_length,
                "features": {
                    **flat_features,
                    "mfcc_mean": mfcc_features["mfcc_mean"],
                    "mfcc_std": mfcc_features["mfcc_std"],
                },
            },
        )

    def embed(self, audio: np.ndarray, fingerprint_data: dict) -> np.ndarray:
        """Embed semantic fingerprint using subtle energy modulation."""
        data_bytes = hashlib.sha256(str(fingerprint_data).encode()).digest()
        bits = np.unpackbits(np.frombuffer(data_bytes, dtype=np.uint8))

        # Modulate energy in pause regions
        rms = librosa.feature.rms(y=audio, hop_length=self.hop_length)[0]
        silence_threshold = np.percentile(rms, 20)
        is_low_energy = rms < silence_threshold

        modified_audio = audio.copy()
        frame_length = self.hop_length

        bit_idx = 0
        for frame_idx in range(len(is_low_energy)):
            if is_low_energy[frame_idx] and bit_idx < len(bits):
                start = frame_idx * frame_length
                end = min((frame_idx + 1) * frame_length, len(audio))

                # Very subtle gain adjustment
                gain = 1.001 if bits[bit_idx] else 0.999
                modified_audio[start:end] *= gain
                bit_idx += 1

        return modified_audio.astype(audio.dtype)

    def verify(self, audio: np.ndarray, expected_hash: str) -> tuple[bool, float]:
        """Verify semantic fingerprint."""
        current = self.extract(audio)

        if current.layer_hash == expected_hash:
            return True, current.confidence_score

        return False, current.confidence_score * 0.5
