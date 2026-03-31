# ── Stage 1: build ───────────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends gcc libpq-dev && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ── Stage 2: runtime ──────────────────────────────────────────────────────────
FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends libpq5 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=builder /install /usr/local
COPY . .

EXPOSE 8003

# FastAPI service + RQ worker for screen_queue
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port 8003 & rq worker screen_queue --url redis://${REDIS_HOST:-redis}:${REDIS_PORT:-6379}"]
