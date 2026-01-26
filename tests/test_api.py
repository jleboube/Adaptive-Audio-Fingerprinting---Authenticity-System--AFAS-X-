"""Tests for API endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestHealthEndpoint:
    """Tests for health check endpoint."""

    async def test_health_returns_ok(self, client: AsyncClient):
        """Test health endpoint returns success."""
        response = await client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "timestamp" in data
        assert "services" in data


@pytest.mark.asyncio
class TestRootEndpoint:
    """Tests for root endpoint."""

    async def test_root_returns_info(self, client: AsyncClient):
        """Test root endpoint returns app info."""
        response = await client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "AFAS-X"
        assert "version" in data
        assert "docs" in data


@pytest.mark.asyncio
class TestFingerprintEndpoint:
    """Tests for fingerprint endpoint."""

    async def test_fingerprint_creates_record(
        self, client: AsyncClient, sample_audio_base64
    ):
        """Test fingerprint endpoint creates record."""
        response = await client.post(
            "/fingerprint",
            json={
                "audio_base64": sample_audio_base64,
                "file_name": "test.wav",
                "creator_id": "test_user",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "record_id" in data
        assert "original_hash" in data
        assert "fingerprinted_hash" in data
        assert "fingerprinted_audio_base64" in data
        assert "layers" in data
        assert len(data["layers"]) == 6
        assert "blockchain_hash" in data

    async def test_fingerprint_invalid_audio(self, client: AsyncClient):
        """Test fingerprint endpoint rejects invalid audio."""
        response = await client.post(
            "/fingerprint",
            json={
                "audio_base64": "not_valid_base64!!!",
            },
        )

        assert response.status_code == 500  # Server error on invalid input


@pytest.mark.asyncio
class TestVerifyEndpoint:
    """Tests for verify endpoint."""

    async def test_verify_unknown_audio(
        self, client: AsyncClient, sample_audio_base64
    ):
        """Test verify returns UNKNOWN for unregistered audio."""
        response = await client.post(
            "/verify",
            json={
                "audio_base64": sample_audio_base64,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["result"] == "UNKNOWN"


@pytest.mark.asyncio
class TestProvenanceEndpoint:
    """Tests for provenance endpoint."""

    async def test_provenance_not_found(self, client: AsyncClient):
        """Test provenance returns not found for unknown hash."""
        response = await client.get(
            "/provenance/0000000000000000000000000000000000000000000000000000000000000000"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["found"] is False
