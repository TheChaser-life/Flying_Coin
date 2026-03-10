"""
Forecast Service — Task 6.6
---------------------------
Load model từ MLflow → inference API (CPU) → dự báo 7/14/30 ngày.
"""

import logging
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import forecast
from app.core.config import config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=config.PROJECT_NAME,
    version=config.VERSION,
    openapi_url="/api/v1/forecast/openapi.json",
    docs_url="/api/v1/forecast/docs",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(forecast.router, prefix="/api/v1")


@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "ok", "service": config.PROJECT_NAME}
