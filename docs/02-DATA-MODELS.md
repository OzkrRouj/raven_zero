# Data Models

## 🗄️ Redis Schema

```
upload:{key}          → HASH
  - filename          : string
  - size              : integer (bytes)
  - mime_type         : string
  - sha256            : string (file hash)
  - encryption_key    : string (Fernet key)
  - created_at        : ISO8601
  - expiry_at         : ISO8601
  TTL: expiry_minutes * 60

upload:{key}:uses     → STRING (integer)
  Value: Remaining downloads (1-5)
  TTL: Same as parent

upload:{key}:previewed → STRING ("true"/"false")
  Value: Has preview been accessed?
  TTL: Same as parent

health:scheduler_heartbeat → STRING (ISO8601)
  Value: Last heartbeat timestamp

block:{action}:{ip}   → STRING ("1")
  Value: IP block flag
  TTL: 1800 seconds (30 min)

fails:{action}:{ip}   → STRING (integer)
  Value: Failed attempt count
  TTL: 600 seconds (10 min)
```

---

## 📂 Filesystem Structure

```
storage/
└── uploads/
    └── {diceware_key}/
        └── {sanitized_filename}

Example:
storage/
└── uploads/
    ├── apple-banana-cherry/
    │   └── document.pdf
    └── correct-horse-battery/
        └── config.json
```

---

## 🔄 Data Flow

### Upload Flow

```
1. Client POST /upload/ with file + expiry + uses
2. Validate file size (≤ 10MB)
3. Detect MIME type (magic bytes)
4. Validate against allowed types (if configured)
5. Generate unique Diceware key (3 words)
6. Generate Fernet encryption key
7. Calculate SHA-256 of original content
8. Encrypt file content
9. Sanitize filename (remove dangerous chars)
10. Save encrypted file to storage/{key}/{filename}
11. Save metadata to Redis (with TTL)
12. Return: key, preview_url, download_url, expiry, sha256
```

### Download Flow

```
1. Client GET /download/{key}
2. Check IP block status
3. Decrement uses atomically (Lua script)
   - If uses was 0: return 410 "limit reached"
   - If key doesn't exist: return 404
4. Get metadata + encryption_key from Redis
5. Read encrypted file from disk
6. Decrypt with Fernet
7. Verify SHA-256 hash
   - If mismatch: return 500 "integrity failed"
8. If remaining uses = 0:
   - Schedule background autodestruction
9. Return file with:
   - Content-Disposition: attachment
   - X-SHA256: {hash}
```

### Preview Flow (One-Time)

```
1. Client GET /preview/{key}
2. Check IP block status
3. Check if key exists
4. Mark as previewed (atomic GETSET)
   - If already previewed: return 404
5. Get metadata + TTL
6. Return: filename, size, mime, expiry, uses, download_url
```

---

## 🧹 Cleanup Strategy

### Automatic Cleanup (Download Exhausted)

When `uses` reaches 0 after download:

1. Background task triggered
2. Secure shred file (overwrite + delete)
3. Delete all Redis keys

### Periodic Orphan Cleanup

Every 10 minutes (APScheduler):

1. Scan `storage/uploads/` directories
2. For each folder, check if Redis key exists
3. If NOT in Redis AND folder age > 15 minutes → delete

### Health Heartbeat

Every 1 minute:

- Write timestamp to `health:scheduler_heartbeat`
- Used by `/health` to verify scheduler is running
