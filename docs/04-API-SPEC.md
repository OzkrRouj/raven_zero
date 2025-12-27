# Raven Zero - API Specification

## 📡 API Overview

**Content Type:** `application/json` (except file uploads)  
**Authentication:** None (anonymous service)  
**Rate Limiting:** Yes (per IP)  
**API Documentation:** `/scalar` (interactive), `/docs` (Swagger), `/redoc` (ReDoc)

---

## 🔗 Endpoints Summary

| Method | Endpoint | Purpose | Rate Limit |
|--------|----------|---------|------------|
| `POST` | `/upload/` | Upload file | 30/hour |
| `GET` | `/preview/{key}` | Preview upload (one-time) | — |
| `GET` | `/download/{key}` | Download file | — |
| `GET` | `/status/{key}` | Check file status | — |
| `GET` | `/health/` | Health check | 1/second |

---

## 📤 POST /upload/

Upload a file with auto-destruction parameters.

### Request

**Content-Type:** `multipart/form-data`

| Field | Type | Required | Default | Validation | Description |
|-------|------|----------|---------|------------|-------------|
| `file` | File | ✅ Yes | — | ≤ 10MB | File to upload |
| `expiry` | Integer | No | 10 | 1-60 | Minutes until expiration |
| `uses` | Integer | No | 1 | 1-5 | Number of allowed downloads |

### Response

**Status Code:** `201 Created`

```json
{
  "key": "correct-horse-battery",
  "preview_url": "https://domain.com/preview/correct-horse-battery",
  "download_url": "https://domain.com/download/correct-horse-battery",
  "expiry": "2024-12-10T16:00:00Z",
  "uses": 3,
  "filename": "document.pdf",
  "size": 51200,
  "created_at": "2024-12-10T15:50:00Z",
  "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
}
```

### Examples

**cURL:**
```bash
curl -X POST https://domain.com/upload/ \
  -F "file=@document.pdf" \
  -F "expiry=10" \
  -F "uses=3"
```

**Python (httpx):**
```python
import httpx

files = {"file": ("document.pdf", open("document.pdf", "rb"), "application/pdf")}
data = {"expiry": 10, "uses": 3}

response = httpx.post("https://domain.com/upload/", files=files, data=data)
print(response.json())
```

### Error Responses

| Status | Condition | Response |
|--------|-----------|----------|
| `400` | File too large | `{"detail": "File too large: X bytes (Max Size: 10,485,760 bytes)"}` |
| `400` | Invalid MIME type | `{"detail": "File type not suported: application/x-executable"}` |
| `429` | Rate limit exceeded | `{"detail": "Rate limit exceeded"}` |
| `500` | Server error | `{"detail": "Internal error while processing upload: ..."}` |

---

## 👁️ GET /preview/{key}

Preview upload details. **Can only be accessed once** for security.

### Request

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `key` | string | ✅ Yes | Diceware key (e.g., `correct-horse-battery`) |

### Response

**Status Code:** `200 OK`

```json
{
  "key": "correct-horse-battery",
  "filename": "document.pdf",
  "size": 51200,
  "mime_type": "application/pdf",
  "expiry": "2024-12-10T16:00:00Z",
  "uses": 3,
  "minutes_left": 8,
  "download_url": "https://domain.com/download/correct-horse-battery",
  "curl_example": "curl -O https://domain.com/download/correct-horse-battery",
  "created_at": "2024-12-10T15:50:00Z",
  "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
}
```

### Error Responses

| Status | Condition | Response |
|--------|-----------|----------|
| `404` | Upload not found | `{"detail": "Upload not found or link expired"}` |
| `404` | Already previewed | `{"detail": "This file preview has already been accessed..."}` |
| `429` | IP blocked | `{"detail": "Demasiados intentos fallidos. Inténtalo más tarde."}` |

---

## 📥 GET /download/{key}

Download the file. Decrements remaining uses and verifies integrity.

### Request

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `key` | string | ✅ Yes | Diceware key |

### Response

**Status Code:** `200 OK`

**Headers:**
```
Content-Disposition: attachment; filename="document.pdf"
Content-Type: application/pdf
X-SHA256: e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
```

**Body:** Decrypted file binary content

### Examples

**cURL (save to file):**
```bash
curl -O https://domain.com/download/correct-horse-battery
```

**wget:**
```bash
wget https://domain.com/download/correct-horse-battery
```

### Behavior

1. **First download:** Uses decremented 3 → 2
2. **Second download:** Uses decremented 2 → 1
3. **Third download:** Uses decremented 1 → 0 → **File auto-deletes**
4. **Fourth attempt:** Returns 404

### Error Responses

| Status | Condition | Response |
|--------|-----------|----------|
| `404` | Not found/expired | `{"detail": "File not found"}` |
| `410` | No uses remaining | `{"detail": "Download limit has been reached"}` |
| `429` | IP blocked | `{"detail": "Demasiados intentos fallidos. Bloqueado temporalmente."}` |
| `500` | Integrity failed | `{"error_code": "INTEGRITY_CHECK_FAILED", ...}` |

---

## 📊 GET /status/{key}

Check the status of an upload without consuming downloads.

### Request

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `key` | string | ✅ Yes | Diceware key |

### Response

**Status Code:** `200 OK`

```json
{
  "key": "correct-horse-battery",
  "status": "active",
  "remaining_uses": 2,
  "expires_at": "2024-12-10T16:00:00Z",
  "is_accessible": true
}
```

**Possible Status Values:**
- `active` — File is available for download
- `expired` — Time limit reached
- `burned` — Download limit reached
- `expired_or_burned` — File no longer exists

---

## 🏥 GET /health/

Health check endpoint for monitoring.

### Response

**Status Code:** `200 OK`

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

| Field | Description |
|-------|-------------|
| `status` | `healthy` or `degraded` |
| `services.redis` | Redis connectivity |
| `services.storage` | Filesystem writability |
| `services.scheduler` | Background job status |
| `services.diceware` | Wordlist loaded correctly |
| `uptime_seconds` | Time since application start |

---

## 🔒 Security Headers

All responses include:

```
Cache-Control: no-store, no-cache, must-revalidate, max-age=0
Pragma: no-cache
Expires: 0
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Referrer-Policy: no-referrer
X-Request-ID: {uuid}
```

---

## 🚦 Rate Limiting

| Endpoint | Limit |
|----------|-------|
| `POST /upload/` | 30/hour |
| `GET /health/` | 1/second |

**Anti Brute-Force:**
- 10 failed attempts → IP blocked for 30 minutes
- Applies to: `/download`, `/preview`, `/status`

---

## 🌐 CORS Policy

**Allowed Origins:** `*` (configurable)  
**Allowed Methods:** `GET`, `POST`  
**Allowed Headers:** `Content-Type`, `Accept`

---

## 📊 Error Response Format

**Standard error:**
```json
{
  "detail": "Human-readable error message"
}
```

**Validation error (Pydantic):**
```json
{
  "detail": [
    {
      "type": "error_type",
      "loc": ["body", "field_name"],
      "msg": "Error message"
    }
  ]
}
```

---

## 🔢 HTTP Status Codes

| Code | Meaning | When Used |
|------|---------|-----------|
| `200` | OK | Successful GET |
| `201` | Created | Successful upload |
| `400` | Bad Request | Validation error |
| `404` | Not Found | Upload doesn't exist/expired |
| `410` | Gone | Download limit exhausted |
| `429` | Too Many Requests | Rate limit/IP blocked |
| `500` | Internal Server Error | Server error |

---

## 🔢 Data Types

### Diceware Key Format

**Pattern:** `word1-word2-word3`  
**Example:** `correct-horse-battery`

**Rules:**
- Exactly 3 words
- Lowercase letters only
- Separated by hyphens
- 7,776 word dictionary
- **Combinations:** 470,184,984,576 (~38.9 bits entropy)

### Timestamp Format

**Standard:** ISO 8601 (UTC)  
**Format:** `YYYY-MM-DDTHH:MM:SSZ`  
**Example:** `2024-12-10T15:50:00Z`

### File Size

**Format:** Integer (bytes)  
**Maximum:** `10,485,760` (10 MB)

---

## 🧪 Testing the API

### Quick Test Flow

```bash
# 1. Upload a file
KEY=$(curl -s -X POST http://localhost:8000/upload/ \
  -F "file=@test.txt" \
  -F "expiry=10" \
  -F "uses=2" | jq -r '.key')

echo "Key: $KEY"

# 2. Preview (first time works)
curl http://localhost:8000/preview/$KEY | jq

# 3. Preview again (should fail - one-time only)
curl http://localhost:8000/preview/$KEY | jq

# 4. Check status
curl http://localhost:8000/status/$KEY | jq

# 5. Download (first time)
curl -O http://localhost:8000/download/$KEY

# 6. Download (second time, last use, file auto-deletes)
curl -O http://localhost:8000/download/$KEY

# 7. Download (should fail - no uses remaining)
curl http://localhost:8000/download/$KEY | jq
```

---

## 📚 Interactive Documentation

| URL | Description |
|-----|-------------|
| `/scalar` | Scalar API documentation (modern UI) |
| `/docs` | Swagger UI |
| `/redoc` | ReDoc |
| `/openapi.json` | OpenAPI schema |

---

*API Version: 0.1.0*
