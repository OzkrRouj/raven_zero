# Raven Zero - Architecture

## 📐 System Overview

Raven Zero is built on a **hybrid ephemeral architecture** where Redis acts as the source of truth for active uploads, the filesystem provides encrypted storage, and all components are designed for data to disappear by default.

### High-Level Architecture

```
┌─────────────┐
│   Client    │ (Browser, cURL, App)
└──────┬──────┘
       │ HTTPS
       ▼
┌─────────────────────────────────────────┐
│          FastAPI Application            │
│  ┌────────────────────────────────┐     │
│  │  Routers                       │     │
│  │  - /upload    - /download      │     │
│  │  - /preview   - /status        │     │
│  │  - /health    - /scalar        │     │
│  └────────────┬───────────────────┘     │
│               │                         │
│  ┌────────────▼───────────────────┐     │
│  │  Services                      │     │
│  │  - StorageService (encrypted)  │     │
│  │  - CacheService (Redis)        │     │
│  │  - DicewareService (keys)      │     │
│  │  - SecurityService (Fernet)    │     │
│  └────────┬───────────┬───────────┘     │
│           │           │                 │
│  ┌────────▼───────────▼───────────┐     │
│  │   Background Jobs (APScheduler)│     │
│  │  - Orphan cleanup (10 min)     │     │
│  │  - Health heartbeat (1 min)    │     │
│  └────────────────────────────────┘     │
└───────────┼───────────┼─────────────────┘
            │           │
            ▼           ▼
    ┌───────────┐  ┌──────────┐
    │   Redis   │  │Filesystem│
    │ (Valkey)  │  │(Encrypted│
    │ Metadata  │  │  Files)  │
    └───────────┘  └──────────┘
```

---

## 🎯 Technology Stack

### Core Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Language** | Python 3.13 | Async/await, type hints |
| **Web Framework** | FastAPI | Async, Pydantic validation, auto-docs |
| **Cache/Metadata** | Redis/Valkey | TTL native, atomic ops |
| **File Storage** | Filesystem | Encrypted files with secure deletion |
| **Package Manager** | uv | Fast, modern Python package management |
| **Containerization** | Docker | Reproducible deployments |

### Security & Encryption

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Encryption** | Fernet (cryptography) | AES-128-CBC + HMAC-SHA256 |
| **Integrity** | hashlib SHA-256 | File verification |
| **MIME Detection** | python-magic | Magic bytes detection |
| **Secure Delete** | Custom shredding | Byte overwriting before deletion |

### Observability

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Logging** | structlog | Structured JSON logging |
| **Scheduling** | APScheduler | Background cleanup jobs |
| **API Docs** | Scalar | Interactive API documentation |

---

## 📁 Project Structure

```
app/
├── main.py              # FastAPI app, lifespan, middlewares
├── config.py            # Pydantic Settings (env vars)
│
├── core/                # Infrastructure layer
│   ├── logger.py        # Structlog JSON configuration
│   ├── logging_middleware.py  # Request ID, timing
│   ├── rate_limiting.py # Slowapi with Redis backend
│   ├── redis.py         # Async Redis client
│   ├── security.py      # Fernet encryption service
│   ├── security_headers.py    # HTTP security headers
│   └── uptime.py        # Application uptime tracker
│
├── models/
│   └── schemas.py       # Pydantic request/response models
│
├── routers/             # API endpoints
│   ├── upload.py        # POST /upload/
│   ├── download.py      # GET /download/{key}
│   ├── preview.py       # GET /preview/{key}
│   ├── status.py        # GET /status/{key}
│   └── health.py        # GET /health/
│
└── services/
    ├── cache.py         # Redis metadata operations
    ├── diceware.py      # Key generation (7776 words)
    ├── scheduler.py     # APScheduler cleanup jobs
    │
    └── storage/         # File storage module
        ├── storage_service.py  # Main orchestrator
        ├── repository.py       # File I/O + secure shredding
        ├── validators.py       # Size/MIME validation
        ├── sanitizer.py        # Filename sanitization
        ├── path_manager.py     # Path resolution
        └── mime_detector.py    # libmagic MIME detection
```

---

## 📖 Documentation Index

| Document | Description |
|----------|-------------|
| [Data Models](./02-DATA-MODELS.md) | Redis schema, filesystem structure |
| [Security](./03-SECURITY.md) | Encryption, shredding, defense layers |
| [API Specification](./04-API-SPEC.md) | Endpoints, examples, errors |
| [Deployment](./05-DEPLOYMENT.md) | Docker, configuration, environment |
| [Development](./06-DEVELOPMENT.md) | Patterns, testing, conventions |
| [Decisions](./07-DECISIONS.md) | Decision log, references |
