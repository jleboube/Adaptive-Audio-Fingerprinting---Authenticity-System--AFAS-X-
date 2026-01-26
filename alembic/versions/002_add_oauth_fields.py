"""Add OAuth fields to users table.

Revision ID: 002
Revises: 001
Create Date: 2024-01-26

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "002"
down_revision: str | None = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add OAuth fields to users table."""
    # Add oauth_provider column
    op.add_column(
        "users",
        sa.Column(
            "oauth_provider",
            sa.String(20),
            nullable=True,
            comment="OAuth provider: 'google', 'github', etc. Null for email/password users",
        ),
    )

    # Add oauth_provider_id column
    op.add_column(
        "users",
        sa.Column(
            "oauth_provider_id",
            sa.String(255),
            nullable=True,
            comment="User ID from OAuth provider",
        ),
    )

    # Add avatar_url column
    op.add_column(
        "users",
        sa.Column(
            "avatar_url",
            sa.String(500),
            nullable=True,
            comment="Profile picture URL from OAuth provider",
        ),
    )

    # Create index on oauth_provider_id for faster lookups
    op.create_index(
        "ix_users_oauth_provider_id",
        "users",
        ["oauth_provider_id"],
    )

    # Make password_hash nullable for OAuth-only users
    op.alter_column(
        "users",
        "password_hash",
        existing_type=sa.String(255),
        nullable=True,
        comment="Null for OAuth-only users",
    )


def downgrade() -> None:
    """Remove OAuth fields from users table."""
    # Drop index
    op.drop_index("ix_users_oauth_provider_id", table_name="users")

    # Drop columns
    op.drop_column("users", "avatar_url")
    op.drop_column("users", "oauth_provider_id")
    op.drop_column("users", "oauth_provider")

    # Make password_hash non-nullable again
    op.alter_column(
        "users",
        "password_hash",
        existing_type=sa.String(255),
        nullable=False,
    )
