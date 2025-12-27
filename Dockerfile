FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

WORKDIR /app


COPY pyproject.toml uv.lock ./


RUN uv sync --frozen --no-dev


COPY . .


RUN apt-get update && apt-get install -y libmagic1 && rm -rf /var/lib/apt/lists/*

EXPOSE 8000

CMD ["uv", "run", "fastapi", "run", "app/main.py"]
