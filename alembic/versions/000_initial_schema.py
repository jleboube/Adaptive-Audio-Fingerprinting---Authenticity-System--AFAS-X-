"""Initial database schema.

Revision ID: 000
Revises:
Create Date: 2024-01-01

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "000"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create initial AFAS-X database schema."""
    # Create audio_records table
    op.create_table(
        "audio_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("original_hash", sa.String(64), unique=True, nullable=False),
        sa.Column("fingerprinted_hash", sa.String(64), nullable=True),
        sa.Column("creator_id", sa.String(255), nullable=True),
        sa.Column("device_id", sa.String(255), nullable=True),
        sa.Column("file_name", sa.String(255), nullable=True),
        sa.Column("duration_seconds", sa.Float(), nullable=True),
        sa.Column("sample_rate", sa.Integer(), nullable=True),
        sa.Column("channels", sa.Integer(), nullable=True),
        sa.Column("file_size_bytes", sa.BigInteger(), nullable=True),
        sa.Column("mime_type", sa.String(50), nullable=True),
        sa.Column("extra_metadata", postgresql.JSONB(), server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index("idx_audio_records_original_hash", "audio_records", ["original_hash"])
    op.create_index("idx_audio_records_fingerprinted_hash", "audio_records", ["fingerprinted_hash"])
    op.create_index("idx_audio_records_created_at", "audio_records", ["created_at"])

    # Create fingerprint_layers table
    op.create_table(
        "fingerprint_layers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column(
            "audio_record_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("audio_records.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("layer_type", sa.String(1), nullable=False),
        sa.Column("layer_hash", sa.String(64), nullable=False),
        sa.Column("confidence_score", sa.Float(), nullable=True),
        sa.Column("parameters", postgresql.JSONB(), server_default="{}"),
        sa.Column("version", sa.String(20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint("layer_type IN ('A', 'B', 'C', 'D', 'E', 'F')", name="check_layer_type"),
        sa.CheckConstraint("confidence_score >= 0 AND confidence_score <= 1", name="check_confidence_score"),
        sa.UniqueConstraint("audio_record_id", "layer_type", "version", name="uq_layer_record_type_version"),
    )
    op.create_index("idx_fingerprint_layers_audio_record_id", "fingerprint_layers", ["audio_record_id"])
    op.create_index("idx_fingerprint_layers_layer_hash", "fingerprint_layers", ["layer_hash"])

    # Create blockchain_records table
    op.create_table(
        "blockchain_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("block_index", sa.Integer(), unique=True, nullable=False),
        sa.Column("block_hash", sa.String(64), unique=True, nullable=False),
        sa.Column("previous_hash", sa.String(64), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("data", postgresql.JSONB(), nullable=False),
        sa.Column("nonce", sa.Integer(), nullable=False),
        sa.Column("signature", sa.String(128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_blockchain_records_block_index", "blockchain_records", ["block_index"])
    op.create_index("idx_blockchain_records_block_hash", "blockchain_records", ["block_hash"])

    # Create verification_logs table
    op.create_table(
        "verification_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column(
            "audio_record_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("audio_records.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("submitted_hash", sa.String(64), nullable=False),
        sa.Column("verification_result", sa.String(20), nullable=False),
        sa.Column("confidence_score", sa.Float(), nullable=True),
        sa.Column("layer_results", postgresql.JSONB(), server_default="{}"),
        sa.Column("blockchain_verified", sa.Boolean(), server_default="false"),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint(
            "verification_result IN ('AUTHENTIC', 'MODIFIED', 'UNKNOWN', 'FAILED')",
            name="check_verification_result",
        ),
        sa.CheckConstraint("confidence_score >= 0 AND confidence_score <= 1", name="check_verification_confidence"),
    )
    op.create_index("idx_verification_logs_audio_record_id", "verification_logs", ["audio_record_id"])
    op.create_index("idx_verification_logs_created_at", "verification_logs", ["created_at"])

    # Create fingerprint_versions table
    op.create_table(
        "fingerprint_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("version", sa.String(20), unique=True, nullable=False),
        sa.Column("algorithm_config", postgresql.JSONB(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("deprecated_at", sa.DateTime(timezone=True), nullable=True),
    )

    # Insert genesis block
    op.execute("""
        INSERT INTO blockchain_records (block_index, block_hash, previous_hash, timestamp, data, nonce, signature)
        VALUES (
            0,
            'genesis_afas_x_block_0000000000000000000000000000000000',
            '0000000000000000000000000000000000000000000000000000000000000000',
            NOW(),
            '{"type": "genesis", "message": "AFAS-X Genesis Block", "version": "1.0.0"}',
            0,
            NULL
        ) ON CONFLICT (block_index) DO NOTHING
    """)

    # Insert default fingerprint version
    op.execute("""
        INSERT INTO fingerprint_versions (version, algorithm_config, is_active)
        VALUES (
            '1.0.0',
            '{
                "layer_a": {"type": "spectral", "fft_size": 2048, "hop_length": 512},
                "layer_b": {"type": "temporal", "frame_length": 2048},
                "layer_c": {"type": "physiological", "pitch_floor": 75, "pitch_ceiling": 600},
                "layer_d": {"type": "semantic", "n_mfcc": 13},
                "layer_e": {"type": "adversarial", "perturbation_strength": 0.01},
                "layer_f": {"type": "meta", "hash_algorithm": "sha256"}
            }',
            TRUE
        ) ON CONFLICT (version) DO NOTHING
    """)


def downgrade() -> None:
    """Drop all tables."""
    op.drop_table("fingerprint_versions")
    op.drop_table("verification_logs")
    op.drop_table("blockchain_records")
    op.drop_table("fingerprint_layers")
    op.drop_table("audio_records")
