# Deployment

## 🐳 Docker Deployment

### docker-compose.yml

```yaml
services:
  app:
    build: .
    expose:
      - 8000
    environment:
      - REDIS_URL=redis://valkey:6379/0
    volumes:
      - ./logs:/app/logs
      - ./storage:/app/storage  # Persist encrypted files
    depends_on:
      - valkey
    restart: on-failure
    networks:
      - raven-net

  valkey:
    image: valkey/valkey:9-alpine
    expose:
      - 6379
    networks:
      - raven-net

networks:
  raven-net:
    driver: bridge
```

### Dockerfile

```dockerfile
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY . .
RUN apt-get update && apt-get install -y libmagic1 && rm -rf /var/lib/apt/lists/*

EXPOSE 8000
CMD ["uv", "run", "fastapi", "run", "app/main.py"]
```

---

## 🔧 Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection URL |
| `STORAGE_PATH` | `./storage/uploads` | File storage directory |
| `TEMP_PATH` | `./storage/temp` | Temporary files directory |
| `MAX_FILE_SIZE` | `10485760` (10MB) | Maximum upload size |
| `ALLOWED_MIME_TYPES` | `[]` (all allowed) | Whitelist of MIME types |
| `UPLOAD_RATE_LIMIT` | `30/hour` | Rate limit for uploads |
| `HEALTH_RATE_LIMIT` | `1/second` | Rate limit for health checks |
| `DOWNLOAD_FAIL_LIMIT` | `10` | Failures before IP block |
| `DOWNLOAD_BLOCK_WINDOW` | `1800` | Block duration (seconds) |
| `CLEANUP_INTERVAL_MINUTES` | `10` | Orphan cleanup interval |
| `ORPHAN_AGE_MINUTES` | `15` | Age before orphan deletion |
| `SECURE_SHRED_PASSES` | `1` | Byte overwrite passes |
| `DICEWARE_WORDLIST_PATH` | `data/diceware_words.txt` | Path to wordlist |

---

## 📊 Observability

### Structured Logging

All logs are JSON formatted via structlog:

```json
{
  "event": "file_upload_started",
  "request_id": "abc123-...",
  "method": "POST",
  "path": "/upload/",
  "timestamp": "2024-12-10T15:30:00Z",
  "level": "info"
}
```

Fields included:
- `timestamp` (ISO8601)
- `level` (INFO, WARNING, ERROR)
- `request_id` (UUID per request)
- `method`, `path`, `status_code`, `duration`

### Log Files

- **Location:** `./logs/raven_zero.log`
- **Rotation:** 10MB max, 5 backups
- **Format:** JSON lines

### Health Check

`GET /health/` returns:

```json
{
  "status": "healthy",
  "version": "0.1.0",
  "timestamp": "2024-12-10T15:50:00Z",
  "services": {
    "redis": "online",
    "storage": "online",
    "scheduler": "online",
    "diceware": "online"
  },
  "uptime_seconds": 3600,
  "started_at": "2024-12-10T14:50:00Z"
}
```

---

## 🔄 Restart & Failure Modes

| Scenario | Data Loss | Recovery | User Impact |
|----------|-----------|----------|-------------|
| **Graceful restart** | All active uploads | 2-5 sec | In-flight complete, uploads lost |
| **Crash (hard kill)** | All active uploads | 5-10 sec | Orphans cleaned on startup |
| **Redis crash** | All metadata | 1-2 sec | Brief outage, service recovers |
| **Disk full** | None (fails safely) | Immediate | Uploads fail with clear error |

> **Key principle:** Ephemeral by design means restarts clearing data is expected, not a bug.

---

## 📊 Performance Expectations

| Metric | Target | Hardware |
|--------|--------|----------|
| Upload latency (p95) | < 500ms | 4-core, 8GB RAM |
| Download latency | < 100ms | Same |
| Redis operations | < 10ms | Same |
| Concurrent uploads | 50+ | Same |

### Scale Capacity

- 100 uploads/day: Easy
- 1,000 uploads/day: Comfortable
- 10,000 uploads/day: With tuning

**When to scale:** Measure first (logs/metrics), identify bottleneck, optimize.
