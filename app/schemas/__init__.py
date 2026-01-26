"""Pydantic schemas for AFAS-X."""

from app.schemas.auth import (
    APIKeyCreateRequest,
    APIKeyCreateResponse,
    APIKeyListItem,
    APIKeyListResponse,
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    RegisterResponse,
    TokenRefreshRequest,
    TokenRefreshResponse,
    UserResponse,
    UserUpdateRequest,
    VerifyOwnershipRequest,
    VerifyOwnershipResponse,
)
from app.schemas.fingerprint import (
    FingerprintRequest,
    FingerprintResponse,
    LayerResult,
)
from app.schemas.provenance import ProvenanceResponse
from app.schemas.verify import VerifyRequest, VerifyResponse

__all__ = [
    # Auth
    "APIKeyCreateRequest",
    "APIKeyCreateResponse",
    "APIKeyListItem",
    "APIKeyListResponse",
    "LoginRequest",
    "LoginResponse",
    "RegisterRequest",
    "RegisterResponse",
    "TokenRefreshRequest",
    "TokenRefreshResponse",
    "UserResponse",
    "UserUpdateRequest",
    "VerifyOwnershipRequest",
    "VerifyOwnershipResponse",
    # Fingerprint
    "FingerprintRequest",
    "FingerprintResponse",
    "LayerResult",
    # Verify
    "VerifyRequest",
    "VerifyResponse",
    # Provenance
    "ProvenanceResponse",
]
