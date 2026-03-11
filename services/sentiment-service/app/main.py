"""
Sentiment Service — Task 8.6
-----------------------------
Consume news from RabbitMQ (news.raw) → FinBERT (CPU) → publish to Redis (sentiment:{symbol}).
"""

import asyncio
import logging
import sys

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import config
from app.core.dependencies import get_redis, close_redis
from app.services.news_consumer import NewsConsumer
from app.api.v1 import sentiment

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

_consumer: NewsConsumer | None = None
_consumer_task: asyncio.Task | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _consumer, _consumer_task

    redis = get_redis()
    try:
        await redis.ping()
    except Exception as e:
        logger.error("Redis không kết nối được (%s). Kiểm tra Redis đang chạy và REDIS_URL đúng.", e)
        raise RuntimeError("Redis unreachable") from e

    _consumer = NewsConsumer(
        rabbitmq_url=config.RABBITMQ_URL,
        redis=redis,
    )

    logger.info("Connecting sentiment consumer …")
    await _consumer.connect()

    _consumer_task = asyncio.create_task(
        _consumer.start_consuming(), name="sentiment-consumer"
    )
    logger.info("Sentiment Service started")

    yield

    logger.info("Shutting down Sentiment Service …")
    if _consumer_task and not _consumer_task.done():
        _consumer_task.cancel()
        try:
            await _consumer_task
        except asyncio.CancelledError:
            pass

    if _consumer:
        await _consumer.close()

    await close_redis()
    logger.info("Sentiment Service stopped")


app = FastAPI(
    title=config.PROJECT_NAME,
    version=config.VERSION,
    openapi_url="/api/v1/sentiment/openapi.json",
    docs_url="/api/v1/sentiment/docs",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "ok", "service": config.PROJECT_NAME}


@app.get("/ready", tags=["health"])
async def readiness_check():
    return {"status": "ready"}


app.include_router(sentiment.router, prefix="/api/v1")
