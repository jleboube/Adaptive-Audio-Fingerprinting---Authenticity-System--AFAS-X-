"""Pytest configuration and fixtures."""

import asyncio
import base64
import os
from collections.abc import AsyncGenerator

import numpy as np
import pytest
import soundfile as sf
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base, get_db
from app.main import app

# Test database URL
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://afas:afas_secret@localhost:5432/afas_test",
)


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def engine():
    """Create test database engine."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=True)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
async def db_session(engine) -> AsyncGenerator[AsyncSession, None]:
    """Create database session for tests."""
    async_session = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def client(db_session) -> AsyncGenerator[AsyncClient, None]:
    """Create test client with database dependency override."""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
def sample_audio() -> np.ndarray:
    """Generate sample audio data for testing."""
    # Generate 1 second of audio at 22050 Hz
    sample_rate = 22050
    duration = 1.0
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)

    # Mix of frequencies to simulate speech
    audio = (
        0.3 * np.sin(2 * np.pi * 220 * t)  # A3
        + 0.2 * np.sin(2 * np.pi * 440 * t)  # A4
        + 0.1 * np.sin(2 * np.pi * 880 * t)  # A5
        + 0.05 * np.random.randn(len(t))  # Noise
    )

    # Normalize
    audio = audio / np.max(np.abs(audio)) * 0.8

    return audio.astype(np.float32)


@pytest.fixture
def sample_audio_base64(sample_audio) -> str:
    """Generate base64-encoded sample audio."""
    import io

    buffer = io.BytesIO()
    sf.write(buffer, sample_audio, 22050, format="WAV")
    buffer.seek(0)

    return base64.b64encode(buffer.read()).decode()
