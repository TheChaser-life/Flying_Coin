# Forecast Service — Task 6.6 (CPU serving only)
# Phase 1: install dependencies
FROM python:3.11-slim AS builder

WORKDIR /app

COPY services/forecast-service/requirements.txt .

RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Phase 2: running
FROM python:3.11-slim

WORKDIR /app

COPY --from=builder /install /usr/local

COPY services/forecast-service/ .

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
