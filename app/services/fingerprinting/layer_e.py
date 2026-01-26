"""Layer E: Adversarial fingerprinting with anti-cloning perturbations."""

import hashlib

import numpy as np
from scipy import signal

from app.services.fingerprinting.base import FingerprintLayer, LayerOutput


class LayerE(FingerprintLayer):
    """Adversarial fingerprint layer for anti-cloning protection.

    This layer adds subtle perturbations designed to:
    - Interfere with voice cloning systems
    - Create detectable artifacts if cloning is attempted
    - Maintain imperceptibility to human listeners

    Note: Full adversarial perturbation effectiveness requires training
    against specific voice cloning models. This is a placeholder/MVP
    implementation using general perturbation strategies.
    """

    layer_type = "E"

    def __init__(
        self,
        sample_rate: int = 22050,
        version: str = "1.0.0",
        perturbation_strength: float = 0.01,
        n_frequency_bands: int = 32,
    ) -> None:
        super().__init__(sample_rate, version)
        self.perturbation_strength = perturbation_strength
        self.n_frequency_bands = n_frequency_bands

    def _generate_adversarial_noise(
        self, audio: np.ndarray, seed: int
    ) -> np.ndarray:
        """Generate adversarial noise pattern.

        Uses a deterministic pattern based on seed for reproducibility.
        """
        rng = np.random.RandomState(seed)

        # Generate noise in frequency domain for better control
        n_samples = len(audio)
        noise_fft = np.zeros(n_samples, dtype=complex)

        # Add noise in specific frequency bands
        freqs = np.fft.fftfreq(n_samples, 1 / self.sample_rate)

        for band in range(self.n_frequency_bands):
            # Target specific frequency ranges
            low_freq = 100 + band * (8000 / self.n_frequency_bands)
            high_freq = low_freq + (8000 / self.n_frequency_bands)

            band_mask = (np.abs(freqs) >= low_freq) & (np.abs(freqs) < high_freq)

            # Add phase-randomized noise in band
            band_indices = np.where(band_mask)[0]
            phases = rng.uniform(-np.pi, np.pi, len(band_indices))
            magnitudes = rng.uniform(0, 1, len(band_indices)) * self.perturbation_strength

            noise_fft[band_indices] = magnitudes * np.exp(1j * phases)

        # Convert to time domain
        noise = np.real(np.fft.ifft(noise_fft))

        return noise.astype(np.float32)

    def _compute_perturbation_signature(self, audio: np.ndarray) -> dict:
        """Compute signature of adversarial perturbations in audio."""
        # Analyze high-frequency energy distribution
        stft = np.fft.rfft(audio)
        freqs = np.fft.rfftfreq(len(audio), 1 / self.sample_rate)

        # Band energies
        band_energies = []
        for band in range(self.n_frequency_bands):
            low_freq = 100 + band * (8000 / self.n_frequency_bands)
            high_freq = low_freq + (8000 / self.n_frequency_bands)

            band_mask = (freqs >= low_freq) & (freqs < high_freq)
            band_energy = np.sum(np.abs(stft[band_mask]) ** 2)
            band_energies.append(float(band_energy))

        # Normalize
        total_energy = sum(band_energies) + 1e-10
        normalized_energies = [e / total_energy for e in band_energies]

        # Phase coherence in high frequencies
        high_freq_mask = freqs > 4000
        if np.any(high_freq_mask):
            high_freq_phases = np.angle(stft[high_freq_mask])
            phase_variance = float(np.var(np.diff(high_freq_phases)))
        else:
            phase_variance = 0.0

        return {
            "band_energy_distribution": normalized_energies,
            "high_freq_phase_variance": phase_variance,
            "total_high_freq_energy": float(np.sum(band_energies[16:])),
        }

    def _generate_perturbation_seed(self, audio: np.ndarray) -> int:
        """Generate deterministic seed from audio content."""
        # Use audio statistics as seed
        audio_hash = hashlib.md5(audio.tobytes()).hexdigest()
        return int(audio_hash[:8], 16)

    def extract(self, audio: np.ndarray) -> LayerOutput:
        """Extract adversarial fingerprint from audio."""
        signature = self._compute_perturbation_signature(audio)

        # Create hash from signature
        feature_values = []
        for e in signature["band_energy_distribution"]:
            feature_values.append(f"{e:.8f}")
        feature_values.append(f"{signature['high_freq_phase_variance']:.8f}")
        feature_values.append(f"{signature['total_high_freq_energy']:.8f}")

        feature_string = "|".join(feature_values)
        layer_hash = hashlib.sha256(feature_string.encode()).hexdigest()

        # Confidence based on perturbation detectability
        energy_variance = np.var(signature["band_energy_distribution"])
        confidence = min(1.0, 0.5 + energy_variance * 10)

        return LayerOutput(
            layer_type=self.layer_type,
            layer_hash=layer_hash,
            confidence_score=confidence,
            parameters={
                "perturbation_strength": self.perturbation_strength,
                "n_frequency_bands": self.n_frequency_bands,
                "signature": signature,
            },
        )

    def embed(self, audio: np.ndarray, fingerprint_data: dict) -> np.ndarray:
        """Embed adversarial perturbations into audio.

        These perturbations are designed to:
        1. Be imperceptible to humans
        2. Disrupt voice cloning systems
        3. Create detectable artifacts if cloning is attempted
        """
        # Generate deterministic seed from fingerprint data
        data_str = str(sorted(fingerprint_data.items()))
        seed = int(hashlib.md5(data_str.encode()).hexdigest()[:8], 16)

        # Generate adversarial noise
        noise = self._generate_adversarial_noise(audio, seed)

        # Apply envelope matching (noise follows audio energy)
        envelope = np.abs(signal.hilbert(audio))
        envelope_smoothed = signal.savgol_filter(envelope, min(51, len(envelope) // 10 * 2 + 1), 3)
        envelope_normalized = envelope_smoothed / (np.max(envelope_smoothed) + 1e-10)

        # Shape noise by envelope
        shaped_noise = noise * envelope_normalized

        # Add phase-based watermark in specific bands
        stft = np.fft.rfft(audio)
        freqs = np.fft.rfftfreq(len(audio), 1 / self.sample_rate)

        # Target ultrasonic-adjacent frequencies (less perceptible)
        target_freqs = (freqs > 12000) & (freqs < 16000)
        data_hash = hashlib.sha256(data_str.encode()).digest()
        bits = np.unpackbits(np.frombuffer(data_hash, dtype=np.uint8))

        target_indices = np.where(target_freqs)[0]
        for i, idx in enumerate(target_indices[:len(bits)]):
            # Encode bit as subtle phase shift
            current_phase = np.angle(stft[idx])
            shift = 0.1 if bits[i % len(bits)] else -0.1
            stft[idx] = np.abs(stft[idx]) * np.exp(1j * (current_phase + shift))

        # Reconstruct with phase modifications
        phase_modified = np.fft.irfft(stft, n=len(audio))

        # Combine original with shaped noise and phase modifications
        modified_audio = audio + shaped_noise * 0.5 + (phase_modified - audio) * 0.5

        # Ensure same length
        modified_audio = modified_audio[:len(audio)]

        return modified_audio.astype(audio.dtype)

    def verify(self, audio: np.ndarray, expected_hash: str) -> tuple[bool, float]:
        """Verify adversarial fingerprint.

        Checks for presence of embedded perturbation patterns.
        """
        current = self.extract(audio)

        if current.layer_hash == expected_hash:
            return True, current.confidence_score

        # Check for cloning artifacts
        signature = current.parameters.get("signature", {})
        energy_dist = signature.get("band_energy_distribution", [])

        if energy_dist:
            # Cloned audio often has smoother frequency distribution
            energy_variance = np.var(energy_dist)
            # Lower variance might indicate cloning (perturbations removed)
            clone_suspicion = 1.0 - min(1.0, energy_variance * 20)

            if clone_suspicion > 0.7:
                return False, 0.3  # Suspected clone

        return False, current.confidence_score * 0.5
