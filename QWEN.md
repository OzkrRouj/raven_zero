# Raven Zero Project Context

## Project Overview
Raven Zero is a secure file sharing API built with FastAPI that implements end-to-end encryption, auto-destructing files, and time-limited downloads. The system provides a complete solution for temporary file sharing with strong security and privacy controls.

### Core Technologies
- FastAPI: Web framework providing high-performance API
- Redis: Used for metadata storage and session management
- structlog: Structured logging system
- python-magic: MIME type detection
- APScheduler: Background task scheduling
- Diceware: Human-readable key generation

### Architecture
The system follows a layered architecture with clear separation of concerns:
- **Core Layer**: Handles infrastructure concerns (logging, security, Redis)
- **Services Layer**: Implements business logic (storage, caching, scheduling)
- **Routers Layer**: Provides REST API endpoints (upload, download, preview, health)

## Key Components

### Core
- `logger.py`: Structured logging system using structlog
- `logging_middleware.py`: HTTP request logging with correlation IDs
- `redis.py`: Redis connection management

### Services
- `storage/`: File storage, validation, and security services
- `cache.py`: Redis metadata management
- `scheduler.py`: Background cleanup and health monitoring
- `diceware.py`: Secure human-readable key generation

### Routers
- `upload.py`: File upload with encryption and metadata
- `download.py`: Secure file retrieval with integrity checks
- `preview.py`: One-time file preview functionality
- `health.py`: System health monitoring

## Security Features
- End-to-end encryption of uploaded files
- Time-limited file links with configurable expiration
- Limited download attempts per file
- One-time preview URLs
- File integrity verification using SHA-256 hashes
- Filename sanitization to prevent path traversal
- MIME type validation

## Development Conventions

### Logging
The project uses a structured logging system following these guidelines:
- Import logger from `app.core.logger`
- Use static event messages as keys (e.g., "file_upload_success")
- Pass dynamic data through the `extra` parameter
- Use appropriate log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Use `logger.exception` for exception contexts

### Error Handling
- Use HTTPException with appropriate status codes
- Implement auto-cleanup for failed operations
- Ensure data consistency through atomic Redis operations

### Testing
- (TODO: Add details about testing framework and test locations when discovered)

### Building and Running
The project appears to use uv for dependency management based on the uv.lock file and pyproject.toml. To run:
```bash
uv run python -m app.main  # or however the main application is started
```

### Configuration
Settings are managed through the config.py file with storage paths, cleanup intervals, file size limits, and security parameters.

## File Structure
```
raven_zero/
├── app/
│   ├── core/           # Infrastructure components
│   ├── models/         # Data models
│   ├── routers/        # API endpoints
│   └── services/       # Business logic
├── data/              # Diceware wordlist
├── docker/            # Docker configuration
├── storage/           # File storage location
├── pyproject.toml     # Project dependencies
└── uv.lock           # Lock file for uv
```