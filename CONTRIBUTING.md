# Contributing to Raven Zero

Thank you for your interest in contributing to Raven Zero! 🎉

## How to Contribute

### 1. Fork and Clone

```bash
git clone https://github.com/your-username/raven-zero.git
cd raven-zero
```

### 2. Set Up Development Environment

```bash
# Install dependencies
uv sync

# Start Redis/Valkey
docker compose up valkey -d

# Run development server
uv run uvicorn app.main:app --reload --reload-exclude logs
```

See [Development docs](./docs/06-DEVELOPMENT.md) for detailed setup.

### 3. Create a Feature Branch

```bash
git checkout -b feature/your-feature-name
```

### 4. Make Your Changes

- Follow existing code style and patterns
- Add docstrings to new functions/classes
- Update documentation if needed

### 5. Code Quality

```bash
# Format code
uv run ruff format .

# Check linting
uv run ruff check .

# Fix auto-fixable issues
uv run ruff check --fix .
```

### 6. Commit Your Changes

```bash
git add .
git commit -m "feat: add your feature description"
```


### 7. Push and Create Pull Request

```bash
git push origin feature/your-feature-name
```

Then open a Pull Request on GitHub with:
- Clear description of changes
- Why the change is needed
- Any breaking changes

---

## Code Style Guidelines

- **Python:** Follow PEP 8
- **Type hints:** Use type annotations
- **Docstrings:** Google style for functions/classes
- **Imports:** Organized (stdlib → third-party → local)

---

## Project Structure

```
app/
├── core/          # Infrastructure (logging, security, etc.)
├── models/        # Pydantic schemas
├── routers/       # API endpoints
└── services/      # Business logic
```

See [Architecture docs](./docs/01-ARCHITECTURE.md) for details.

---

## Areas for Contribution

### Good First Issues
- Documentation improvements
- Code comments and docstrings
- Error message improvements

### Feature Ideas
- Unit tests (pytest)
- Integration tests
- S3/MinIO storage backend
- Web UI for uploads
- Password protection for files

### Bug Reports
Please include:
- Steps to reproduce
- Expected behavior
- Actual behavior
- Environment (OS, Python version)

---

## Questions?

- **Issues:** For bug reports and feature requests
- **Discussions:** For questions and ideas

---

## License

By contributing, you agree that your contributions will be licensed under the [Apache License 2.0](./LICENSE).
