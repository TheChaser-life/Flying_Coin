# Phase 1: Install dependencies
FROM python:3.11-slim AS builder

WORKDIR /app

COPY services/collectors/requirements.txt .

RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Phase 2: Copy dependencies, source code and shared utilities
FROM python:3.11-slim

WORKDIR /app

COPY --from=builder /install /usr/local

COPY shared /app/shared

COPY services/collectors/app ./app/
COPY services/collectors/requirements.txt ./

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app

CMD ["python", "app/main.py"]