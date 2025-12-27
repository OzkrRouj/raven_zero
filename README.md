# Raven Zero

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

**Ephemeral file sharing with auto-destruction.**

Raven Zero is a self-destructing file sharing service designed for secure, temporary data transfer. Files are encrypted at rest and automatically disappear after a preset number of downloads or time limit. No registration required, no tracking — privacy by design.

> *"The best way to protect data is to not have it."*

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🔥 **Auto-destruction** | Files expire by time (1-60 min) OR download count (1-5 uses) |
| 🔒 **Encrypted storage** | AES-128 encryption at rest using Fernet |
| 🎲 **Diceware keys** | Human-readable keys like `apple-banana-cherry` |
| ⚡ **No registration** | Completely anonymous, no accounts needed |
| 🛡️ **Integrity check** | SHA-256 hash verification on every download |
| 🗑️ **Secure deletion** | Files are overwritten with random bytes before removal |
| 🚫 **Rate limiting** | Protection against abuse and brute-force attacks |
| 📊 **Health monitoring** | Built-in health check endpoint for uptime monitoring |
| 🐳 **Self-hostable** | Easy Docker Compose deployment |

---

## 🚀 Quick Start

### 1. Upload a file

Upload a file with custom expiration (10 minutes) and download limit (3 uses):

```bash
curl -X POST http://localhost:8000/upload/ \
  -F "file=@document.pdf" \
  -F "expiry=10" \
  -F "uses=3"
```

**Response:**

```json
{
  "key": "apple-banana-cherry",
  "preview_url": "http://localhost:8000/preview/apple-banana-cherry",
  "download_url": "http://localhost:8000/download/apple-banana-cherry",
  "expiry": "2024-12-27T18:00:00Z",
  "uses": 3,
  "filename": "document.pdf",
  "size": 51200,
  "sha256": "e3b0c44298fc1c149afbf4c..."
}
```

### 2. Preview (one-time)

Check file details before downloading. **Warning:** This can only be accessed once for security.

```bash
curl http://localhost:8000/preview/apple-banana-cherry
```

### 3. Download

Download the file. Each download decreases the remaining uses:

```bash
curl http://localhost:8000/download/apple-banana-cherry -o file.pdf
```

When `uses` reaches 0, the file is automatically and securely deleted.

### 4. Check status

Check if a file is still available without consuming a download:

```bash
curl http://localhost:8000/status/apple-banana-cherry
```

**Response:**

```json
{
  "key": "apple-banana-cherry",
  "status": "active",
  "remaining_uses": 2,
  "expires_at": "2024-12-27T18:00:00Z",
  "is_accessible": true
}
```

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/upload/` | Upload a file with expiry and uses |
| `GET` | `/preview/{key}` | Preview file details (one-time only) |
| `GET` | `/download/{key}` | Download the file (decrements uses) |
| `GET` | `/status/{key}` | Check file status without downloading |
| `GET` | `/health/` | Service health check |
| `GET` | `/scalar` | Interactive API documentation |
| `GET` | `/docs` | Swagger UI documentation |

### Upload Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `file` | File | Required | ≤10MB | File to upload |
| `expiry` | int | 10 | 1-60 | Minutes until expiration |
| `uses` | int | 1 | 1-5 | Number of allowed downloads |

---

## 🐳 Docker Deployment

### Quick start

```bash
# Clone the repository
git clone https://github.com/your-username/raven-zero.git
cd raven-zero

# Start the service
docker compose up -d
```

The service will be available at `http://localhost:8000`.

### Services

- **app** — FastAPI application on port 8000
- **valkey** — Redis-compatible database (Valkey)

---

## 💻 Local Development

### Prerequisites

- Python 3.13+
- [uv](https://github.com/astral-sh/uv) — Fast Python package manager
- Docker (for Redis/Valkey)

### Setup

```bash
# Install dependencies
uv sync

# Start Valkey (Redis)
docker compose up valkey -d

# Run development server
uv run uvicorn app.main:app --reload --reload-exclude logs --host 127.0.0.1 --port 8000
```

> **Note:** The `--reload-exclude logs` flag prevents infinite log creation loops during development.

### Production mode

```bash
uv run fastapi run app/main.py
```

---

## 📖 Documentation

| Document | Description |
|----------|-------------|
| [Overview](./docs/00-OVERVIEW.md) | What is Raven Zero, philosophy, use cases |
| [Architecture](./docs/01-ARCHITECTURE.md) | System design, tech stack, project structure |
| [Data Models](./docs/02-DATA-MODELS.md) | Redis schema, filesystem, data flows |
| [Security](./docs/03-SECURITY.md) | Encryption, shredding, defense layers |
| [API Specification](./docs/04-API-SPEC.md) | Full API reference with examples |
| [Deployment](./docs/05-DEPLOYMENT.md) | Docker, configuration, environment |
| [Development](./docs/06-DEVELOPMENT.md) | Patterns, testing, conventions |
| [Decisions](./docs/07-DECISIONS.md) | Decision log, tradeoffs, references |

---

## ⚙️ Configuration

Key environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `REDIS_URL` | `redis://localhost:6379/0` | Redis/Valkey connection |
| `MAX_FILE_SIZE` | `10485760` | Maximum file size (10MB) |
| `UPLOAD_RATE_LIMIT` | `30/hour` | Upload rate limit per IP |
| `DOWNLOAD_FAIL_LIMIT` | `10` | Failed attempts before IP block |

See [Deployment docs](./docs/05-DEPLOYMENT.md) for complete configuration reference.

---

## 🛡️ Security

Raven Zero implements multiple layers of security:

- **Encryption at rest** — All files encrypted with Fernet (AES-128-CBC + HMAC-SHA256)
- **Integrity verification** — SHA-256 hash checked on every download
- **Secure deletion** — Files overwritten with random bytes before removal
- **Anti brute-force** — IP blocking after 10 failed attempts
- **Rate limiting** — Prevents abuse and resource exhaustion
- **Security headers** — `X-Frame-Options`, `X-XSS-Protection`, `no-cache`, etc.

See [Security docs](./docs/03-SECURITY.md) for complete security architecture.

---

## 🤝 Contributing

Contributions are welcome! Please read the documentation before submitting PRs.

- **Issues** — Bug reports and feature requests
- **Pull Requests** — Code contributions
- **Security** — Report vulnerabilities privately

---

## 📝 License

Open source. See [LICENSE](./LICENSE) for details.

---

*Ephemeral by design, private by default, open by principle.*
