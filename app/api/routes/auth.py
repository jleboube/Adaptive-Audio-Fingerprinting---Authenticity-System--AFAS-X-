"""Authentication routes for AFAS-X."""

from datetime import datetime, timedelta, timezone
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_current_user
from app.core.database import get_db
from app.core.security import (
    create_access_token,
    create_refresh_token,
    generate_api_key,
    generate_seed_phrase,
    hash_password,
    hash_seed_phrase,
    verify_password,
    verify_seed_phrase,
    verify_token,
)
from app.models.api_key import APIKey
from app.models.audio_record import AudioRecord
from app.models.refresh_token import RefreshToken
from app.models.user import User
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

logger = structlog.get_logger()
router = APIRouter()


# =============================================================================
# Registration
# =============================================================================


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: RegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> RegisterResponse:
    """Register a new user account.

    Returns a 24-word seed phrase that will NEVER be shown again.
    The user MUST save this phrase - it's the only way to prove fingerprint ownership.
    """
    logger.info("Registration attempt", email=request.email)

    # Check if email already exists
    result = await db.execute(select(User).where(func.lower(User.email) == func.lower(request.email)))
    if result.scalar_one_or_none():
        logger.warning("Registration failed: email exists", email=request.email)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    # Generate seed phrase
    seed_phrase = generate_seed_phrase()
    seed_hash = hash_seed_phrase(seed_phrase)

    # Create user
    user = User(
        email=request.email.lower(),
        password_hash=hash_password(request.password),
        seed_phrase_hash=seed_hash,
        display_name=request.display_name,
        is_active=True,
    )
    db.add(user)
    await db.flush()

    # Create tokens
    access_token = create_access_token(str(user.id), user.email)
    refresh_token, refresh_expires = create_refresh_token(str(user.id))

    # Store refresh token hash
    refresh_record = RefreshToken(
        user_id=user.id,
        token_hash=hash_seed_phrase(refresh_token),  # Reuse hash function
        expires_at=refresh_expires,
    )
    db.add(refresh_record)

    await db.commit()

    logger.info("User registered successfully", user_id=str(user.id), email=user.email)

    return RegisterResponse(
        user_id=user.id,
        email=user.email,
        display_name=user.display_name,
        seed_phrase=seed_phrase,  # ONLY time this is returned
        access_token=access_token,
        refresh_token=refresh_token,
    )


# =============================================================================
# Login
# =============================================================================


@router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> LoginResponse:
    """Login with email and password."""
    logger.info("Login attempt", email=request.email)

    # Find user
    result = await db.execute(select(User).where(func.lower(User.email) == func.lower(request.email)))
    user = result.scalar_one_or_none()

    if user is None or not verify_password(request.password, user.password_hash):
        logger.warning("Login failed: invalid credentials", email=request.email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.is_active:
        logger.warning("Login failed: inactive account", email=request.email)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )

    # Create tokens
    access_token = create_access_token(str(user.id), user.email)
    refresh_token, refresh_expires = create_refresh_token(str(user.id))

    # Store refresh token hash
    refresh_record = RefreshToken(
        user_id=user.id,
        token_hash=hash_seed_phrase(refresh_token),
        expires_at=refresh_expires,
    )
    db.add(refresh_record)
    await db.commit()

    logger.info("User logged in", user_id=str(user.id))

    return LoginResponse(
        user_id=user.id,
        email=user.email,
        display_name=user.display_name,
        access_token=access_token,
        refresh_token=refresh_token,
    )


# =============================================================================
# Token Refresh
# =============================================================================


@router.post("/refresh", response_model=TokenRefreshResponse)
async def refresh_tokens(
    request: TokenRefreshRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenRefreshResponse:
    """Refresh access token using refresh token."""
    payload = verify_token(request.refresh_token, token_type="refresh")
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    # Check if token is revoked
    token_hash = hash_seed_phrase(request.refresh_token)
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.is_revoked == False,  # noqa: E712
        )
    )
    refresh_record = result.scalar_one_or_none()

    if refresh_record is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token revoked or not found",
        )

    # Get user
    result = await db.execute(select(User).where(User.id == UUID(user_id)))
    user = result.scalar_one_or_none()

    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or deactivated",
        )

    # Revoke old refresh token
    refresh_record.is_revoked = True

    # Create new tokens (token rotation)
    access_token = create_access_token(str(user.id), user.email)
    new_refresh_token, refresh_expires = create_refresh_token(str(user.id))

    # Store new refresh token
    new_refresh_record = RefreshToken(
        user_id=user.id,
        token_hash=hash_seed_phrase(new_refresh_token),
        expires_at=refresh_expires,
    )
    db.add(new_refresh_record)
    await db.commit()

    logger.info("Tokens refreshed", user_id=str(user.id))

    return TokenRefreshResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
    )


# =============================================================================
# Logout
# =============================================================================


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    request: TokenRefreshRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Logout by revoking refresh token."""
    token_hash = hash_seed_phrase(request.refresh_token)
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.user_id == current_user.id,
        )
    )
    refresh_record = result.scalar_one_or_none()

    if refresh_record:
        refresh_record.is_revoked = True
        await db.commit()
        logger.info("User logged out", user_id=str(current_user.id))


# =============================================================================
# Current User
# =============================================================================


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """Get current user info."""
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        display_name=current_user.display_name,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
    )


@router.patch("/me", response_model=UserResponse)
async def update_me(
    request: UserUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """Update current user info."""
    if request.display_name is not None:
        current_user.display_name = request.display_name

    await db.commit()
    await db.refresh(current_user)

    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        display_name=current_user.display_name,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
    )


# =============================================================================
# API Keys
# =============================================================================


@router.get("/api-keys", response_model=APIKeyListResponse)
async def list_api_keys(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIKeyListResponse:
    """List all API keys for the current user."""
    result = await db.execute(
        select(APIKey)
        .where(APIKey.user_id == current_user.id)
        .order_by(APIKey.created_at.desc())
    )
    keys = result.scalars().all()

    return APIKeyListResponse(
        keys=[
            APIKeyListItem(
                id=key.id,
                name=key.name,
                key_prefix=key.key_prefix,
                scopes=key.scopes,
                is_active=key.is_active,
                expires_at=key.expires_at,
                last_used_at=key.last_used_at,
                created_at=key.created_at,
            )
            for key in keys
        ],
        total=len(keys),
    )


@router.post("/api-keys", response_model=APIKeyCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    request: APIKeyCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIKeyCreateResponse:
    """Create a new API key.

    Returns the full API key ONCE. Save it securely - it cannot be retrieved again.
    """
    full_key, prefix, key_hash = generate_api_key()

    expires_at = None
    if request.expires_in_days:
        expires_at = datetime.now(timezone.utc) + timedelta(days=request.expires_in_days)

    api_key = APIKey(
        user_id=current_user.id,
        key_prefix=prefix,
        key_hash=key_hash,
        name=request.name,
        scopes=request.scopes,
        expires_at=expires_at,
    )
    db.add(api_key)
    await db.commit()
    await db.refresh(api_key)

    logger.info(
        "API key created",
        user_id=str(current_user.id),
        key_prefix=prefix,
        scopes=request.scopes,
    )

    return APIKeyCreateResponse(
        id=api_key.id,
        name=api_key.name,
        key=full_key,  # ONLY time this is returned
        key_prefix=api_key.key_prefix,
        scopes=api_key.scopes,
        expires_at=api_key.expires_at,
        created_at=api_key.created_at,
    )


@router.delete("/api-keys/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_api_key(
    key_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Revoke (deactivate) an API key."""
    result = await db.execute(
        select(APIKey).where(
            APIKey.id == key_id,
            APIKey.user_id == current_user.id,
        )
    )
    api_key = result.scalar_one_or_none()

    if api_key is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found",
        )

    api_key.is_active = False
    await db.commit()

    logger.info("API key revoked", user_id=str(current_user.id), key_id=str(key_id))


# =============================================================================
# Seed Phrase Ownership Verification
# =============================================================================


@router.post("/verify-ownership", response_model=VerifyOwnershipResponse)
async def verify_ownership(
    request: VerifyOwnershipRequest,
    db: AsyncSession = Depends(get_db),
) -> VerifyOwnershipResponse:
    """Verify fingerprint ownership using seed phrase.

    This endpoint allows proving ownership of a fingerprint using the original
    seed phrase generated at registration. This is useful for legal disputes
    or claiming ownership of a voice fingerprint.

    NOTE: No authentication required - seed phrase IS the proof.
    """
    logger.info("Ownership verification attempt", record_id=str(request.record_id))

    # Find the audio record
    result = await db.execute(select(AudioRecord).where(AudioRecord.id == request.record_id))
    audio_record = result.scalar_one_or_none()

    if audio_record is None:
        return VerifyOwnershipResponse(
            verified=False,
            message="Fingerprint record not found",
        )

    if audio_record.user_id is None:
        return VerifyOwnershipResponse(
            verified=False,
            message="This fingerprint is not linked to any user account",
            record_id=audio_record.id,
        )

    # Get the user who owns this record
    result = await db.execute(select(User).where(User.id == audio_record.user_id))
    owner = result.scalar_one_or_none()

    if owner is None:
        return VerifyOwnershipResponse(
            verified=False,
            message="Owner account not found",
            record_id=audio_record.id,
        )

    # Verify the seed phrase
    if verify_seed_phrase(request.seed_phrase, owner.seed_phrase_hash):
        logger.info(
            "Ownership verified successfully",
            record_id=str(audio_record.id),
            owner_id=str(owner.id),
        )
        return VerifyOwnershipResponse(
            verified=True,
            message="Ownership verified. The seed phrase matches the owner of this fingerprint.",
            record_id=audio_record.id,
            owner_email=owner.email,
            created_at=audio_record.created_at,
        )
    else:
        logger.warning(
            "Ownership verification failed: seed phrase mismatch",
            record_id=str(audio_record.id),
        )
        return VerifyOwnershipResponse(
            verified=False,
            message="Seed phrase does not match the owner of this fingerprint",
            record_id=audio_record.id,
        )
