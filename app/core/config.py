"""Application configuration using Pydantic settings."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Database
    database_url: str = "postgresql+asyncpg://afas:afas_secret@db:5432/afas"

    # Redis
    redis_url: str = "redis://redis:6379/0"

    # Security
    secret_key: str = "change-me-in-production"
    ed25519_private_key: str | None = None

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 44638
    debug: bool = False

    # Celery
    celery_broker_url: str = "redis://redis:6379/0"
    celery_result_backend: str = "redis://redis:6379/0"

    # Fingerprinting
    fingerprint_version: str = "1.0.0"

    # Audio processing defaults
    default_sample_rate: int = 22050
    default_fft_size: int = 2048
    default_hop_length: int = 512

    # Ethereum/Blockchain
    alchemy_rpc_url: str | None = None  # e.g., https://eth-sepolia.g.alchemy.com/v2/YOUR_API_KEY
    ethereum_private_key: str | None = None  # Wallet private key (hex)
    ethereum_network: str = "sepolia"  # Network name for logging

    # JWT Authentication
    jwt_secret_key: str | None = None  # Falls back to secret_key if not set
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 30

    # Google OAuth
    google_client_id: str | None = None
    google_client_secret: str | None = None
    google_redirect_uri: str = "https://afasx.my-ai.tech/auth/google/callback"
    frontend_url: str = "https://afasx.my-ai.tech"

    @property
    def jwt_secret(self) -> str:
        """Get JWT secret key, falling back to main secret key."""
        return self.jwt_secret_key or self.secret_key

    @property
    def google_oauth_enabled(self) -> bool:
        """Check if Google OAuth is configured."""
        return bool(self.google_client_id and self.google_client_secret)


@lru_cache
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()
