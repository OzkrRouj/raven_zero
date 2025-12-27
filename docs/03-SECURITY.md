# Security

## 🔐 Encryption Architecture

### Encryption Flow

```
Upload:
1. Read file content
2. Generate Fernet key (AES-128-CBC)
3. Calculate SHA-256 hash of original content
4. Encrypt content with Fernet
5. Save encrypted file to disk
6. Store encryption_key + hash in Redis

Download:
1. Retrieve encryption_key from Redis
2. Read encrypted file
3. Decrypt with Fernet
4. Verify SHA-256 hash
5. Return decrypted content
```

### Fernet Encryption

- **Algorithm:** AES-128-CBC
- **Integrity:** HMAC-SHA256
- **Key size:** 256 bits (URL-safe base64)
- **Library:** `cryptography` (Python)

```python
from cryptography.fernet import Fernet

key = Fernet.generate_key()  # Unique per file
f = Fernet(key)
encrypted = f.encrypt(content)
decrypted = f.decrypt(encrypted)
```

---

## 🗑️ Secure Deletion

Files are overwritten with random bytes before deletion:

```python
async def _shred_file(self, path: Path, passes: int = 1):
    file_size = path.stat().st_size
    with open(path, "ba+", buffering=0) as f:
        for _ in range(passes):
            f.seek(0)
            f.write(os.urandom(file_size))  # Random bytes
            os.fsync(f.fileno())            # Force disk write
    path.unlink()  # Then delete
```

**Why shredding?**

- Prevents data recovery from disk
- Defense in depth for sensitive files
- Configurable passes via `SECURE_SHRED_PASSES`

---

## 🛡️ Defense in Depth

```
Layer 1: Network (Optional Reverse Proxy)
├─> SSL/TLS termination
├─> Rate limiting (L7)
└─> Request size limits

Layer 2: Application (FastAPI)
├─> CORS policy (GET, POST only)
├─> Security headers middleware
├─> Rate limiting (Slowapi + Redis)
├─> MIME type validation (magic bytes)
├─> Filename sanitization
└─> Diceware key generation (secrets module)

Layer 3: Storage
├─> Fernet encryption (AES-128-CBC)
├─> SHA-256 integrity verification
├─> Secure shredding (byte overwriting)
└─> No directory traversal (path validation)

Layer 4: Data
├─> Redis: ephemeral by design
├─> Files: encrypted + auto-cleanup
└─> No logs of file contents
```

---

## 🚫 Anti Brute-Force Protection

```
1. Track failed attempts per IP: fails:{action}:{ip}
2. After 10 failures → block IP for 30 minutes
3. Block key: block:{action}:{ip}
4. Applies to: download, preview, status
```

### Rate Limiting

| Endpoint | Limit |
|----------|-------|
| `POST /upload/` | 30/hour |
| `GET /health/` | 1/second |

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

## ✅ Integrity Verification

Every download verifies file integrity:

1. Original SHA-256 stored at upload time
2. Decrypted content hashed on download
3. Hashes compared before returning file
4. Mismatch → 500 error with integrity report

```json
{
  "error_code": "INTEGRITY_CHECK_FAILED",
  "integrity_report": {
    "expected": "abc123...",
    "actual": "def456..."
  }
}
```
