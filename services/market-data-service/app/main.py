"""
Market Data Service — FastAPI Application
-----------------------------------------
Starts the RabbitMQ consumer in the background via lifespan,
and exposes the REST API on /api/v1/market-data.
"""

import asyncio
import logging
import sys

import redis.asyncio as aioredis
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.api.v1 import market_data as market_data_router
from app.core.config import config
from app.core.dependencies import get_redis_pool
from app.services.consumer import MarketDataConsumer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

_consumer: MarketDataConsumer | None = None
_consumer_task: asyncio.Task | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _consumer, _consumer_task

    redis = get_redis_pool()
    _consumer = MarketDataConsumer(
        rabbitmq_url=config.RABBITMQ_URL,
        redis=redis,
    )

    logger.info("Connecting market data consumer …")
    await _consumer.connect()

    _consumer_task = asyncio.create_task(
        _consumer.start_consuming(), name="market-data-consumer"
    )
    logger.info("Market Data Service started")

    yield

    logger.info("Shutting down Market Data Service …")
    if _consumer_task and not _consumer_task.done():
        _consumer_task.cancel()
        try:
            await _consumer_task
        except asyncio.CancelledError:
            pass

    if _consumer:
        await _consumer.close()

    redis_pool = get_redis_pool()
    await redis_pool.aclose()
    logger.info("Market Data Service stopped")


app = FastAPI(
    title=config.PROJECT_NAME,
    version=config.VERSION,
    openapi_url="/api/v1/market-data/openapi.json",
    docs_url="/api/v1/market-data/docs",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(market_data_router.router, prefix="/api/v1/market-data")


@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "ok", "service": config.PROJECT_NAME}
