# Decisions & References

## 📋 Decision Log

| Decision | Rationale |
|----------|-----------|
| **FastAPI** | Async, Pydantic validation, modern Python, auto-generated docs |
| **Redis/Valkey** | Native TTL, atomic operations, ephemeral by design |
| **Filesystem (not S3)** | Simple for MVP, sufficient for scale, easy to debug |
| **Fernet encryption** | AES-128-CBC + HMAC-SHA256, standard library quality |
| **3-word Diceware** | Balance security (38.9 bits entropy) + UX (memorable) |
| **uv package manager** | Speed (Rust-based), modern tooling, lock files |
| **No user accounts** | Privacy-first, complexity reduction |
| **Preview one-time only** | Security: prevents key exposure via link sharing |
| **Secure shredding** | Defense in depth for sensitive files |
| **Valkey (not Redis)** | Open source fork, Redis-compatible, BSD license |
| **Structlog** | JSON structured logging, context variables |
| **APScheduler** | Simple background jobs, no Celery overhead |

---

## 🤔 Design Tradeoffs

### Why not S3?

**Chosen:** Filesystem storage

**Considered:** AWS S3, MinIO

**Decision:** Filesystem is simpler for MVP:
- No external dependencies
- Easy to debug (just `ls` the folder)
- Sufficient for expected scale (100-1000 files/day)
- Migration path exists via Repository pattern

### Why 3-word Diceware?

**Considered options:**
- UUID: More secure, but horrible UX
- 4-word keys: Overkill for 60-minute TTL
- Random hex: Secure but error-prone to transcribe

**Decision:** 3 words = 470 billion combinations
- Human-readable (QR codes, voice)
- Secure enough for ephemeral use case
- 38.9 bits entropy

### Why ephemeral Redis (no persistence)?

**Decision:** No RDB/AOF persistence

**Rationale:**
- Redis as pure cache, not database
- Server restart = clean slate (by design)
- Ephemeral principle: data should disappear
- Simpler operations (no backup/restore)

---

## 📚 References

### Technical

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Redis Commands](https://redis.io/commands/)
- [Fernet Specification](https://github.com/fernet/spec/)
- [Diceware FAQ](https://theworld.com/~reinhold/diceware.html)
- [OWASP Security Headers](https://owasp.org/www-project-secure-headers/)

### Inspirations

- [Data Dead Drop](https://github.com/hschne/data-dead-drop) — Ruby/Rails (discontinued)
- [PrivateBin](https://github.com/PrivateBin/PrivateBin) — PHP
- [Firefox Send](https://github.com/mozilla/send) — Node.js (discontinued)

---

## 📜 License

Raven Zero is open source software.

---

## 🔮 Future Considerations

### Potential Additions

- **PostgreSQL** for analytics (historical stats, not operations)
- **S3/MinIO** if storage needs exceed local disk
- **Prometheus metrics** for observability
- **WebSocket** for real-time countdown on preview
- **Password protection** for files (optional encryption layer)

### Won't Implement

- User accounts (anti-goal)
- File previews/thumbnails (privacy concern)
- Permanent storage option (ephemeral by design)
- Content moderation AI (privacy concern)
