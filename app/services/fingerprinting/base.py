"""Base class for fingerprint layers."""

from abc import ABC, abstractmethod
from dataclasses import dataclass

import numpy as np


@dataclass
class LayerOutput:
    """Output from a fingerprint layer."""

    layer_type: str
    layer_hash: str
    confidence_score: float
    parameters: dict
    embedded_audio: np.ndarray | None = None  # Audio with embedded fingerprint


class FingerprintLayer(ABC):
    """Abstract base class for fingerprint layers."""

    layer_type: str = ""

    def __init__(self, sample_rate: int = 22050, version: str = "1.0.0") -> None:
        self.sample_rate = sample_rate
        self.version = version

    @abstractmethod
    def extract(self, audio: np.ndarray) -> LayerOutput:
        """Extract fingerprint from audio.

        Args:
            audio: Audio samples as numpy array

        Returns:
            LayerOutput with hash and confidence score
        """
        pass

    @abstractmethod
    def embed(self, audio: np.ndarray, fingerprint_data: dict) -> np.ndarray:
        """Embed fingerprint into audio.

        Args:
            audio: Audio samples as numpy array
            fingerprint_data: Data to embed

        Returns:
            Modified audio with embedded fingerprint
        """
        pass

    @abstractmethod
    def verify(self, audio: np.ndarray, expected_hash: str) -> tuple[bool, float]:
        """Verify audio against expected fingerprint.

        Args:
            audio: Audio samples to verify
            expected_hash: Expected fingerprint hash

        Returns:
            Tuple of (matches, confidence)
        """
        pass
