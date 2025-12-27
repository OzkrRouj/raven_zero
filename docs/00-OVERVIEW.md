# Raven Zero - Overview

## 🎯 What is Raven Zero?

**Raven Zero is a self-destructing file sharing service designed for ephemeral data transfer.**

Send files that automatically disappear after a preset number of downloads or time limit. No registration, no tracking — just secure temporary transfer with end-to-end encryption.

> *"The best way to protect data is to not have it."*

---

## 🔥 The Problem

### Real-World Use Case

Transferring sensitive data between devices securely is challenging:

- Traditional cloud sync exposes data to third parties
- Email/messaging leaves permanent traces
- Most file sharing services keep files indefinitely
- Existing solutions like Data Dead Drop are no longer available

**The core problem:** How do you transfer sensitive data without leaving it accessible forever?

### Why Existing Alternatives Fall Short

| Solution | Problem |
|----------|---------|
| **Dropbox/Google Drive** | Files persist indefinitely, full access to content |
| **WeTransfer** | 7-day retention, email required, no self-hosting |
| **Pastebin/Gist** | Public URLs, no guaranteed deletion |
| **Data Dead Drop** | No longer available |

**Raven Zero fills this gap:** Ephemeral by design, encrypted at rest, self-hostable, open source.

---

## 👥 Who is Raven Zero For?

### Primary Users

- **Privacy-conscious individuals** who need temporary file transfer
- **Developers** syncing configs, tokens, or keys between environments
- **Security professionals** sharing sensitive data with time constraints
- **Teams** that need quick, trace-free file exchange

### Core Use Cases

1. **Password Manager Sync** — Transfer encrypted vault files between devices
2. **Temporary API Key Sharing** — Share tokens that auto-delete after retrieval
3. **Cross-Device Quick Transfer** — Screenshots, configs, logs with automatic cleanup
4. **Secure Code Snippet Sharing** — One-time access for code review

---

## 🚫 What Raven Zero is NOT

### Anti-Goals

❌ **Not a Backup Service** — Files are designed to disappear (max 60 minutes)

❌ **Not for Large Files** — Limit: 10MB per file, optimized for text/configs/images

❌ **Not a Content Platform** — Pure utility: upload → share → delete

❌ **Not a Social Network** — No accounts, no profiles, anonymous by design

---

## 🏛️ Design Principles

### 1. Ephemeral by Design
Files MUST disappear by time OR download count. Default: 10 minutes, 1 use. Maximum: 60 minutes, 5 uses.

### 2. Privacy by Default
No user accounts, no tracking, no analytics. Zero-knowledge architecture — we encrypt your files but don't read them.

### 3. Security First
- **AES-128 encryption** at rest (Fernet)
- **SHA-256 integrity verification**
- **Secure file deletion** (byte overwriting before removal)
- **Anti brute-force protection** with IP blocking

### 4. Radical Transparency
Fully open source. Every line auditable.

### 5. Self-Hosting First
Easy deployment with Docker Compose. Your data, your server, your rules.

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🔥 **Auto-destruction** | Files expire by time OR download count |
| 🔒 **Encrypted storage** | AES-128 encryption at rest |
| 🎲 **Diceware keys** | Human-readable, shareable keys (`apple-banana-cherry`) |
| ⚡ **No registration** | Anonymous by design |
| 🛡️ **Integrity check** | SHA-256 hash verification on download |
| 🚫 **Rate limiting** | Protection against abuse |
| 📊 **Health monitoring** | `/health` endpoint with service status |

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [Architecture](./01-ARCHITECTURE.md) | System overview, tech stack, project structure |
| [Data Models](./02-DATA-MODELS.md) | Redis schema, filesystem, data flows |
| [Security](./03-SECURITY.md) | Encryption, shredding, defense layers |
| [API Specification](./04-API-SPEC.md) | Endpoints, examples, error codes |
| [Deployment](./05-DEPLOYMENT.md) | Docker, configuration, observability |
| [Development](./06-DEVELOPMENT.md) | Patterns, testing, conventions |
| [Decisions](./07-DECISIONS.md) | Decision log, tradeoffs, references |

---

## 🚀 Quick Start

### Upload a file
```bash
curl -F "file=@document.pdf" -F "expiry=10" -F "uses=1" https://your-domain.com/upload/
```

### Download
```bash
curl https://your-domain.com/download/apple-banana-cherry -o file.pdf
```

---

## 📞 Contributing

- **GitHub Issues:** Bug reports and feature requests
- **Pull Requests:** Contributions welcome
- **Security:** Report vulnerabilities privately

---

*Ephemeral by design, private by default, open by principle.*
