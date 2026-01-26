-- Initialize AFAS-X database schema

-- Audio records table
CREATE TABLE IF NOT EXISTS audio_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    original_hash VARCHAR(64) NOT NULL UNIQUE,
    fingerprinted_hash VARCHAR(64),
    creator_id VARCHAR(255),
    device_id VARCHAR(255),
    file_name VARCHAR(255),
    duration_seconds FLOAT,
    sample_rate INTEGER,
    channels INTEGER,
    file_size_bytes BIGINT,
    mime_type VARCHAR(50),
    extra_metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Fingerprint layers table
CREATE TABLE IF NOT EXISTS fingerprint_layers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    audio_record_id UUID NOT NULL REFERENCES audio_records(id) ON DELETE CASCADE,
    layer_type VARCHAR(1) NOT NULL CHECK (layer_type IN ('A', 'B', 'C', 'D', 'E', 'F')),
    layer_hash VARCHAR(64) NOT NULL,
    confidence_score FLOAT CHECK (confidence_score >= 0 AND confidence_score <= 1),
    parameters JSONB DEFAULT '{}',
    version VARCHAR(20) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(audio_record_id, layer_type, version)
);

-- Blockchain records table
CREATE TABLE IF NOT EXISTS blockchain_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    block_index INTEGER NOT NULL UNIQUE,
    block_hash VARCHAR(64) NOT NULL UNIQUE,
    previous_hash VARCHAR(64) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    data JSONB NOT NULL,
    nonce INTEGER NOT NULL,
    signature VARCHAR(128),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Verification logs table
CREATE TABLE IF NOT EXISTS verification_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    audio_record_id UUID REFERENCES audio_records(id) ON DELETE SET NULL,
    submitted_hash VARCHAR(64) NOT NULL,
    verification_result VARCHAR(20) NOT NULL CHECK (verification_result IN ('AUTHENTIC', 'MODIFIED', 'UNKNOWN', 'FAILED')),
    confidence_score FLOAT CHECK (confidence_score >= 0 AND confidence_score <= 1),
    layer_results JSONB DEFAULT '{}',
    blockchain_verified BOOLEAN DEFAULT FALSE,
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Fingerprint versions table
CREATE TABLE IF NOT EXISTS fingerprint_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    version VARCHAR(20) NOT NULL UNIQUE,
    algorithm_config JSONB NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    deprecated_at TIMESTAMP WITH TIME ZONE
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_audio_records_original_hash ON audio_records(original_hash);
CREATE INDEX IF NOT EXISTS idx_audio_records_fingerprinted_hash ON audio_records(fingerprinted_hash);
CREATE INDEX IF NOT EXISTS idx_audio_records_created_at ON audio_records(created_at);
CREATE INDEX IF NOT EXISTS idx_fingerprint_layers_audio_record_id ON fingerprint_layers(audio_record_id);
CREATE INDEX IF NOT EXISTS idx_fingerprint_layers_layer_hash ON fingerprint_layers(layer_hash);
CREATE INDEX IF NOT EXISTS idx_blockchain_records_block_index ON blockchain_records(block_index);
CREATE INDEX IF NOT EXISTS idx_blockchain_records_block_hash ON blockchain_records(block_hash);
CREATE INDEX IF NOT EXISTS idx_verification_logs_audio_record_id ON verification_logs(audio_record_id);
CREATE INDEX IF NOT EXISTS idx_verification_logs_created_at ON verification_logs(created_at);

-- Insert genesis block for blockchain
INSERT INTO blockchain_records (block_index, block_hash, previous_hash, timestamp, data, nonce, signature)
VALUES (
    0,
    'genesis_afas_x_block_0000000000000000000000000000000000',
    '0000000000000000000000000000000000000000000000000000000000000000',
    NOW(),
    '{"type": "genesis", "message": "AFAS-X Genesis Block", "version": "1.0.0"}',
    0,
    NULL
) ON CONFLICT (block_index) DO NOTHING;

-- Insert default fingerprint version
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
) ON CONFLICT (version) DO NOTHING;
