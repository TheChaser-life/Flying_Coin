# Forecast Service — Task 6.6 (CPU serving only)
# Phase 1: install dependencies
FROM python:3.11-slim AS builder

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Phase 2: running
FROM python:3.11-slim

COPY app/ ./app/

COPY --from=builder /install /usr/local

ENV PYTHONPATH=/app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
