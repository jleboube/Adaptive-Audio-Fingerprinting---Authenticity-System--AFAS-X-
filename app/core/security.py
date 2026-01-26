"""Security utilities including Ed25519 signing, JWT, and BIP-39."""

import base64
import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
from mnemonic import Mnemonic

from app.core.config import get_settings

settings = get_settings()


class Ed25519Signer:
    """Ed25519 digital signature handler."""

    def __init__(self, private_key_b64: str | None = None) -> None:
        """Initialize with existing key or generate new one."""
        if private_key_b64:
            key_bytes = base64.b64decode(private_key_b64)
            self._private_key = Ed25519PrivateKey.from_private_bytes(key_bytes)
        else:
            self._private_key = Ed25519PrivateKey.generate()

        self._public_key = self._private_key.public_key()

    @property
    def private_key_b64(self) -> str:
        """Export private key as base64."""
        key_bytes = self._private_key.private_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PrivateFormat.Raw,
            encryption_algorithm=serialization.NoEncryption(),
        )
        return base64.b64encode(key_bytes).decode()

    @property
    def public_key_b64(self) -> str:
        """Export public key as base64."""
        key_bytes = self._public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
        return base64.b64encode(key_bytes).decode()

    def sign(self, data: bytes) -> str:
        """Sign data and return base64-encoded signature."""
        signature = self._private_key.sign(data)
        return base64.b64encode(signature).decode()

    def verify(self, data: bytes, signature_b64: str) -> bool:
        """Verify signature against data."""
        try:
            signature = base64.b64decode(signature_b64)
            self._public_key.verify(signature, data)
            return True
        except Exception:
            return False

    @classmethod
    def verify_with_public_key(
        cls, data: bytes, signature_b64: str, public_key_b64: str
    ) -> bool:
        """Verify signature using provided public key."""
        try:
            signature = base64.b64decode(signature_b64)
            public_key_bytes = base64.b64decode(public_key_b64)
            public_key = Ed25519PublicKey.from_public_bytes(public_key_bytes)
            public_key.verify(signature, data)
            return True
        except Exception:
            return False


def compute_sha256(data: bytes) -> str:
    """Compute SHA-256 hash of data."""
    return hashlib.sha256(data).hexdigest()


def compute_audio_hash(audio_data: bytes, metadata: dict | None = None) -> str:
    """Compute hash of audio data with optional metadata."""
    hasher = hashlib.sha256()
    hasher.update(audio_data)
    if metadata:
        # Sort keys for deterministic hashing
        for key in sorted(metadata.keys()):
            hasher.update(f"{key}:{metadata[key]}".encode())
    return hasher.hexdigest()


def generate_nonce() -> int:
    """Generate a random nonce for blockchain proof-of-work."""
    return secrets.randbelow(2**32)


def get_timestamp_iso() -> str:
    """Get current timestamp in ISO format."""
    return datetime.now(timezone.utc).isoformat()


# Global signer instance
_signer: Ed25519Signer | None = None


def get_signer() -> Ed25519Signer:
    """Get or create the global Ed25519 signer."""
    global _signer
    if _signer is None:
        _signer = Ed25519Signer(settings.ed25519_private_key)
    return _signer


# =============================================================================
# Password Hashing
# =============================================================================


def hash_password(password: str) -> str:
    """Hash a password using bcrypt with work factor 12."""
    password_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against its hash."""
    try:
        password_bytes = password.encode("utf-8")
        hash_bytes = password_hash.encode("utf-8")
        return bcrypt.checkpw(password_bytes, hash_bytes)
    except Exception:
        return False


# =============================================================================
# JWT Token Management
# =============================================================================


def create_access_token(
    user_id: str,
    email: str,
    expires_delta: timedelta | None = None,
) -> str:
    """Create a JWT access token."""
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.access_token_expire_minutes)

    expire = datetime.now(timezone.utc) + expires_delta
    payload = {
        "sub": user_id,
        "email": email,
        "type": "access",
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def create_refresh_token(user_id: str) -> tuple[str, datetime]:
    """Create a refresh token and return (token, expiry)."""
    expires = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)
    payload = {
        "sub": user_id,
        "type": "refresh",
        "exp": expires,
        "iat": datetime.now(timezone.utc),
        "jti": str(uuid.uuid4()),  # Unique token ID
    }
    token = jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    return token, expires


def verify_token(token: str, token_type: str = "access") -> dict | None:
    """Verify and decode a JWT token. Returns payload or None if invalid."""
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
        if payload.get("type") != token_type:
            return None
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


# =============================================================================
# BIP-39 Seed Phrase Generation
# =============================================================================


def generate_seed_phrase() -> str:
    """Generate a 24-word BIP-39 mnemonic seed phrase."""
    mnemo = Mnemonic("english")
    # 256 bits of entropy = 24 words
    return mnemo.generate(strength=256)


def hash_seed_phrase(seed_phrase: str) -> str:
    """Hash a seed phrase for storage. Normalizes by lowercasing and stripping."""
    normalized = " ".join(seed_phrase.lower().split())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def verify_seed_phrase(seed_phrase: str, stored_hash: str) -> bool:
    """Verify a seed phrase against its stored hash."""
    computed_hash = hash_seed_phrase(seed_phrase)
    return secrets.compare_digest(computed_hash, stored_hash)


def is_valid_seed_phrase(seed_phrase: str) -> bool:
    """Check if a seed phrase is a valid BIP-39 mnemonic."""
    mnemo = Mnemonic("english")
    return mnemo.check(seed_phrase)


# =============================================================================
# API Key Management
# =============================================================================


def generate_api_key() -> tuple[str, str, str]:
    """Generate an API key. Returns (full_key, prefix, hash)."""
    # Generate 32 random bytes, hex encode to 64 chars
    random_part = secrets.token_hex(32)
    full_key = f"afas_{random_part}"
    prefix = f"afas_{random_part[:8]}"
    key_hash = hashlib.sha256(full_key.encode("utf-8")).hexdigest()
    return full_key, prefix, key_hash


def hash_api_key(api_key: str) -> str:
    """Hash an API key for storage."""
    return hashlib.sha256(api_key.encode("utf-8")).hexdigest()


def verify_api_key(api_key: str, stored_hash: str) -> bool:
    """Verify an API key against its stored hash."""
    computed_hash = hash_api_key(api_key)
    return secrets.compare_digest(computed_hash, stored_hash)
