"""Add authentication tables.

Revision ID: 001_add_auth_tables
Revises:
Create Date: 2024-11-11

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: str | None = "000"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add users, api_keys, refresh_tokens tables and user_id columns."""
    # Create users table
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), unique=True, nullable=False, index=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column(
            "seed_phrase_hash",
            sa.String(64),
            nullable=False,
            comment="SHA-256 hash of normalized seed phrase - NEVER store plaintext",
        ),
        sa.Column("display_name", sa.String(100), nullable=True),
        sa.Column("is_active", sa.Boolean(), default=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
    )

    # Create api_keys table
    op.create_table(
        "api_keys",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "key_prefix",
            sa.String(12),
            nullable=False,
            comment="Visible prefix like 'afas_xxxx' for identification",
        ),
        sa.Column(
            "key_hash",
            sa.String(64),
            unique=True,
            nullable=False,
            comment="SHA-256 hash of full API key",
        ),
        sa.Column(
            "name",
            sa.String(100),
            nullable=False,
            comment="User-provided name for the key",
        ),
        sa.Column(
            "scopes",
            postgresql.JSONB(),
            default=[],
            comment='Permission scopes e.g. ["fingerprint:create", "verify:read"]',
        ),
        sa.Column("is_active", sa.Boolean(), default=True),
        sa.Column(
            "expires_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="Optional expiration time",
        ),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
    )

    # Create refresh_tokens table
    op.create_table(
        "refresh_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "token_hash",
            sa.String(64),
            unique=True,
            nullable=False,
            comment="SHA-256 hash of the refresh token",
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_revoked", sa.Boolean(), default=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
    )

    # Add user_id column to audio_records
    op.add_column(
        "audio_records",
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
        ),
    )

    # Add user_id column to verification_logs
    op.add_column(
        "verification_logs",
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
        ),
    )


def downgrade() -> None:
    """Remove authentication tables and columns."""
    # Remove user_id columns
    op.drop_column("verification_logs", "user_id")
    op.drop_column("audio_records", "user_id")

    # Drop tables in correct order (dependencies first)
    op.drop_table("refresh_tokens")
    op.drop_table("api_keys")
    op.drop_table("users")
