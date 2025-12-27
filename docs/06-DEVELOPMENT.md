# Development

## 🏗️ Design Patterns

### 1. Dependency Injection (FastAPI `Depends`)

```python
async def get_redis() -> Redis:
    return redis_client

@app.post("/upload")
async def upload(redis: Redis = Depends(get_redis)):
    # Redis injected automatically
```

**Benefits:** Testable, reusable, clean code.

### 2. Repository Pattern (Storage Module)

```python
class FileRepository(ABC):
    async def save(self, content: bytes, path: Path) -> bool: ...
    async def delete(self, path: Path) -> bool: ...

class LocalFileRepository(FileRepository):
    # Implementation with secure shredding
```

**Benefits:** Easy to swap implementations (filesystem → S3).

### 3. Strategy Pattern (Validators)

```python
class FileValidator(ABC):
    async def validate(self, content, metadata) -> tuple[bool, str]: ...

class FileSizeValidator(FileValidator): ...
class FileMimeTypeValidator(FileValidator): ...
```

**Benefits:** Composable validation rules.

### 4. Middleware Pattern

```python
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(BaseHTTPMiddleware, dispatch=logging_middleware)
```

**Benefits:** Cross-cutting concerns separated from routes.

---

## 🧪 Testing Strategy

### Test Pyramid

```
           /\
          /E2E\        ← Few (full lifecycle)
         /──────\
        /Intgr.  \     ← Some (API endpoints)
       /──────────\
      /   Unit     \   ← Many (services, utils)
     /──────────────\
```

### Coverage Targets

| Component | Target | Rationale |
|-----------|--------|-----------|
| **Services** | >90% | Core logic, must be bulletproof |
| **Routers** | >80% | API contracts, critical paths |
| **Utils** | >85% | Reused everywhere |
| **Overall** | >75% | Balance coverage vs pragmatism |

### Run Tests

```bash
# Run all tests
uv run pytest

# With coverage report
uv run pytest --cov=app --cov-report=html

# Fail if under 75%
uv run pytest --cov=app --cov-fail-under=75
```

### Testing Tools

| Tool | Purpose |
|------|---------|
| pytest | Test framework |
| pytest-asyncio | Async test support |
| pytest-cov | Coverage reporting |
| httpx | Async HTTP client |
| fakeredis | Mock Redis |

---

## 📝 Naming Conventions

| Context | Format | Example |
|---------|--------|---------|
| **Product name** | Title Case | Raven Zero |
| **Repository** | kebab-case | raven-zero |
| **Python package** | snake_case | raven_zero |
| **Docker image** | kebab-case | raven-zero:latest |
| **Environment vars** | UPPER_SNAKE | REDIS_URL |
| **Redis keys** | colon-separated | upload:key:uses |
| **File paths** | snake_case | storage/uploads/ |

---

## 🔧 Development Workflow

### Setup

```bash
# Clone repository
git clone https://github.com/your-username/raven-zero.git
cd raven-zero

# Install dependencies
uv sync

# Copy environment file
cp .env.example .env

# Start services
docker compose up -d
```

### Code Quality

```bash
# Format code
uv run ruff format .

# Lint code
uv run ruff check .

# Auto-fix lints
uv run ruff check --fix .
```

### Run Locally

```bash
# Development server
uv run fastapi dev app/main.py

# Production mode
uv run fastapi run app/main.py
```

---

## 📦 Dependencies

### Production

- fastapi
- uvicorn[standard]
- redis (async)
- python-multipart
- pydantic-settings
- python-magic
- cryptography
- structlog
- apscheduler
- aiofiles
- slowapi
- scalar-fastapi

### Development

- pytest
- pytest-asyncio
- pytest-cov
- httpx
- fakeredis
- ruff
