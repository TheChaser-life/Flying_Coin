# Phase 1: Install dependencies
FROM python:3.11-slim AS builder

WORKDIR /app

COPY services/market-data-service/requirements.txt .

RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Phase 2: Copy dependencies, source code and shared utilities
FROM python:3.11-slim

WORKDIR /app

COPY --from=builder /install /usr/local

COPY shared /app/shared

COPY services/market-data-service/ .

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app

EXPOSE 8001

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]