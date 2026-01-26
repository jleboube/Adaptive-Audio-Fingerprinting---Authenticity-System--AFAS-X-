<div align="center">

# AFAS-X

### Adaptive Audio Fingerprinting & Authenticity System

![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white)
![React](https://img.shields.io/badge/React-18-61DAFB?style=for-the-badge&logo=react&logoColor=black)
![TypeScript](https://img.shields.io/badge/TypeScript-5.0-3178C6?style=for-the-badge&logo=typescript&logoColor=white)
![Next.js](https://img.shields.io/badge/Next.js-14-000000?style=for-the-badge&logo=nextdotjs&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-7-DC382D?style=for-the-badge&logo=redis&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![Ethereum](https://img.shields.io/badge/Ethereum-3C3C3D?style=for-the-badge&logo=ethereum&logoColor=white)

**Protect your voice with multi-layer audio fingerprinting and blockchain-verified provenance tracking.**

[Features](#-features) • [Quick Start](#-quick-start) • [Architecture](#-architecture) • [API Reference](#-api-reference) • [Tech Stack](#-tech-stack)

</div>

---

## Overview

AFAS-X is a comprehensive voice authentication system that embeds imperceptible fingerprints into audio files and tracks their provenance using both a local blockchain and Ethereum. In an era of deepfakes and voice cloning, AFAS-X provides cryptographic proof of audio authenticity and ownership.

**Key Capabilities:**
- **6-layer fingerprinting** that survives compression, noise, and manipulation
- **Dual blockchain verification** (local + Ethereum Sepolia)
- **User authentication** with JWT tokens and API keys
- **BIP-39 seed phrase** for cryptographic ownership proof
- **Real-time verification** of audio authenticity

---

## Features

| Feature | Description |
|---------|-------------|
| **Multi-Layer Fingerprinting** | 6 independent fingerprint layers analyzing spectral, temporal, physiological, semantic, adversarial, and meta features |
| **Blockchain Provenance** | Every fingerprint is recorded on both a local Python blockchain and Ethereum (Sepolia testnet) |
| **User Authentication** | Secure JWT-based authentication with refresh token rotation |
| **API Key Access** | Generate scoped API keys for programmatic access |
| **Seed Phrase Ownership** | BIP-39 24-word mnemonic proves fingerprint ownership (legal proof) |
| **Real-time Verification** | Instantly verify if audio matches a registered fingerprint |
| **Provenance Tracking** | Trace the complete history of any audio file |
| **Modern Web Dashboard** | Beautiful React/Next.js interface with 3D animations |
| **Docker Deployment** | Single command deployment with Docker Compose |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              AFAS-X Architecture                                 │
│                                                                                  │
│  ┌──────────────────────────────────────────────────────────────────────────┐   │
│  │                           Frontend (Next.js 14)                           │   │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────────────┐  │   │
│  │  │   Login    │  │ Dashboard  │  │  Settings  │  │   API Key Mgmt     │  │   │
│  │  │  Register  │  │ Fingerprint│  │   Profile  │  │   Seed Phrase      │  │   │
│  │  └────────────┘  └────────────┘  └────────────┘  └────────────────────┘  │   │
│  └──────────────────────────────────────────────────────────────────────────┘   │
│                                       │                                          │
│                                       ▼                                          │
│  ┌──────────────────────────────────────────────────────────────────────────┐   │
│  │                       Backend (FastAPI + Celery)                          │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                    │   │
│  │  │   Auth API   │  │ Fingerprint  │  │  Verify API  │                    │   │
│  │  │  JWT + Keys  │  │    API       │  │  Provenance  │                    │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘                    │   │
│  │         │                 │                 │                             │   │
│  │         └─────────────────┴─────────────────┘                             │   │
│  │                           │                                               │   │
│  │  ┌──────────────────────────────────────────────────────────────────┐    │   │
│  │  │                   6-Layer Fingerprint Pipeline                     │    │   │
│  │  │  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐                 │    │   │
│  │  │  │  A  │ │  B  │ │  C  │ │  D  │ │  E  │ │  F  │                 │    │   │
│  │  │  │Spec │ │Temp │ │Phys │ │Sem  │ │Adv  │ │Meta │                 │    │   │
│  │  │  └─────┘ └─────┘ └─────┘ └─────┘ └─────┘ └─────┘                 │    │   │
│  │  └──────────────────────────────────────────────────────────────────┘    │   │
│  └──────────────────────────────────────────────────────────────────────────┘   │
│                                       │                                          │
│         ┌─────────────────────────────┼─────────────────────────────┐           │
│         ▼                             ▼                             ▼           │
│  ┌─────────────┐              ┌─────────────┐              ┌─────────────┐      │
│  │ PostgreSQL  │              │    Redis    │              │  Ethereum   │      │
│  │   (Data)    │              │  (Cache/Q)  │              │  (Sepolia)  │      │
│  └─────────────┘              └─────────────┘              └─────────────┘      │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Tech Stack

### Backend
| Technology | Purpose |
|------------|---------|
| **FastAPI** | High-performance async API framework |
| **SQLAlchemy 2.0** | Async ORM with PostgreSQL |
| **Celery** | Distributed task queue |
| **librosa** | Audio feature extraction |
| **bcrypt** | Password hashing |
| **PyJWT** | JWT token management |
| **BIP-39 Mnemonic** | Seed phrase generation |
| **Web3.py** | Ethereum integration |
| **Ed25519** | Digital signatures |

### Frontend
| Technology | Purpose |
|------------|---------|
| **Next.js 14** | React framework with App Router |
| **TypeScript** | Type-safe development |
| **Tailwind CSS** | Utility-first styling |
| **Framer Motion** | Smooth animations |
| **Three.js** | 3D wave visualizations |
| **Radix UI** | Accessible components |

### Infrastructure
| Technology | Purpose |
|------------|---------|
| **Docker** | Containerization |
| **Docker Compose** | Multi-container orchestration |
| **PostgreSQL 15** | Primary database |
| **Redis 7** | Caching & message broker |
| **Alembic** | Database migrations |

---

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Git
- (Optional) Node.js 20+ for frontend development

### Installation

1. **Clone the repository**
   ```bash
   git clone https://gitea.my-house.dev/joe/Adaptive-Audio-Fingerprinting---Authenticity-System--AFAS-X-.git
   cd Adaptive-Audio-Fingerprinting---Authenticity-System--AFAS-X-
   ```

2. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your settings (see Configuration section)
   ```

3. **Start services**
   ```bash
   docker compose up --build
   ```

4. **Run database migrations**
   ```bash
   docker compose exec afas-api alembic upgrade head
   ```

5. **Access the application**
   - **API**: http://localhost:44638
   - **Swagger Docs**: http://localhost:44638/docs
   - **Frontend**: http://localhost:52847 (if running separately)

### Stopping

```bash
docker compose down
# To also remove volumes:
docker compose down -v
```

---

## Fingerprint Layers

AFAS-X uses 6 independent fingerprint layers, each analyzing different audio characteristics:

| Layer | Name | Technique | Survives |
|-------|------|-----------|----------|
| **A** | Spectral | Mel spectrogram analysis with psychoacoustic masking | Compression, EQ |
| **B** | Temporal | Phase coherence, onset detection, tempo analysis | Speed changes |
| **C** | Physiological | Pitch tracking, jitter/shimmer, HNR, formants | Voice cloning |
| **D** | Semantic | MFCC features, prosody, emphasis, pause patterns | Re-recording |
| **E** | Adversarial | Anti-cloning perturbations (imperceptible noise) | AI synthesis |
| **F** | Meta | Cross-layer consistency validation | Targeted attacks |

---

## API Reference

### Authentication

All fingerprint operations require authentication via **JWT token** or **API key**.

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/auth/register` | POST | None | Register new user, returns seed phrase **once** |
| `/auth/login` | POST | None | Login with email/password |
| `/auth/refresh` | POST | None | Refresh access token |
| `/auth/logout` | POST | JWT | Revoke refresh token |
| `/auth/me` | GET | JWT | Get current user info |
| `/auth/api-keys` | GET | JWT | List API keys |
| `/auth/api-keys` | POST | JWT | Create new API key |
| `/auth/api-keys/{id}` | DELETE | JWT | Revoke API key |
| `/auth/verify-ownership` | POST | None | Verify seed phrase ownership |

### Fingerprinting

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/fingerprint` | POST | **Required** | Create fingerprint and blockchain record |
| `/verify` | POST | Optional | Verify audio authenticity |
| `/provenance/{hash}` | GET | None | Get blockchain provenance |
| `/health` | GET | None | Health check |
| `/stats` | GET | None | System statistics |

### Example Requests

**Register a new user:**
```bash
curl -X POST http://localhost:44638/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123!"
  }'
```

**Login:**
```bash
curl -X POST http://localhost:44638/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123!"
  }'
```

**Create fingerprint (with JWT):**
```bash
curl -X POST http://localhost:44638/fingerprint \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "audio_base64": "<base64-encoded-wav>",
    "file_name": "recording.wav"
  }'
```

**Create fingerprint (with API key):**
```bash
curl -X POST http://localhost:44638/fingerprint \
  -H "X-API-Key: afas_your_api_key_here" \
  -H "Content-Type: application/json" \
  -d '{
    "audio_base64": "<base64-encoded-wav>"
  }'
```

**Verify audio:**
```bash
curl -X POST http://localhost:44638/verify \
  -H "Content-Type: application/json" \
  -d '{
    "audio_base64": "<base64-encoded-wav>"
  }'
```

---

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+asyncpg://...` |
| `REDIS_URL` | Redis connection string | `redis://redis:6379/0` |
| `SECRET_KEY` | Application secret key | **Change in production** |
| `JWT_ALGORITHM` | JWT signing algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | JWT access token lifetime | `15` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token lifetime | `30` |
| `ED25519_PRIVATE_KEY` | Base64-encoded signing key | Auto-generated |
| `API_PORT` | API server port | `44638` |
| `ALCHEMY_RPC_URL` | Ethereum RPC endpoint | Optional |
| `ETHEREUM_PRIVATE_KEY` | Wallet private key (hex) | Optional |

---

## Development

### Local Setup

```bash
# Clone repository
git clone https://gitea.my-house.dev/joe/Adaptive-Audio-Fingerprinting---Authenticity-System--AFAS-X-.git
cd Adaptive-Audio-Fingerprinting---Authenticity-System--AFAS-X-

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt

# Start PostgreSQL and Redis (via Docker)
docker compose up db redis -d

# Run migrations
alembic upgrade head

# Start API server
uvicorn app.main:app --host 0.0.0.0 --port 44638 --reload
```

### Frontend Development

```bash
cd frontend

# Install dependencies
npm install

# Create local env
echo "NEXT_PUBLIC_API_URL=http://localhost:44638" > .env.local

# Start development server
npm run dev
```

### Running Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=app --cov-report=html

# Specific test file
pytest tests/test_fingerprint_layers.py -v
```

### Project Structure

```
AFAS-X/
├── app/
│   ├── api/
│   │   ├── dependencies/     # FastAPI dependencies (auth)
│   │   └── routes/           # API endpoints
│   ├── core/
│   │   ├── config.py         # Settings management
│   │   ├── database.py       # Database connection
│   │   └── security.py       # Auth & crypto utilities
│   ├── models/               # SQLAlchemy models
│   ├── schemas/              # Pydantic schemas
│   ├── services/             # Business logic
│   │   └── fingerprinting/   # 6-layer pipeline
│   ├── workers/              # Celery tasks
│   └── main.py               # FastAPI app
├── alembic/                  # Database migrations
├── frontend/
│   ├── app/                  # Next.js App Router
│   ├── components/           # React components
│   └── lib/                  # Utilities & auth context
├── tests/                    # pytest tests
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

---

## Security Considerations

### Seed Phrase
- Generated using BIP-39 (256 bits entropy = 24 words)
- Shown **only once** at registration
- Only the SHA-256 hash is stored
- **Cannot be recovered** if lost
- Used to prove ownership in legal disputes

### Passwords
- Hashed with bcrypt (work factor 12)
- Minimum 8 characters with complexity requirements

### Tokens
- Access tokens: 15 minutes (configurable)
- Refresh tokens: 30 days, rotated on use
- All tokens can be revoked

### API Keys
- Format: `afas_<64-char-random>`
- Only hash stored in database
- Scoped permissions
- Optional expiration

---

## Troubleshooting

### Common Issues

**Database connection errors:**
```bash
# Ensure PostgreSQL is healthy
docker compose ps
docker compose logs db
```

**Migration errors:**
```bash
# Reset database (WARNING: destroys data)
docker compose down -v
docker compose up -d
docker compose exec afas-api alembic upgrade head
```

**Audio processing errors:**
- Ensure audio is WAV format (or convertible)
- Check FFmpeg is installed in container
- Verify audio file is not corrupted

**Authentication errors:**
- Check token hasn't expired
- Verify API key is active and not expired
- Ensure correct header format (`Bearer <token>` or `X-API-Key: <key>`)

---

## License

MIT License - see [LICENSE](LICENSE) for details.

---

<div align="center">

**Built with security in mind for the age of AI-generated audio.**

</div>
