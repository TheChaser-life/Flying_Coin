"""
News Consumer — Task 8.6
------------------------
Consume from news.raw queue → FinBERT inference → publish sentiment to Redis.
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
import time
from typing import Callable, Awaitable

import aio_pika
import aio_pika.abc
import redis
import redis.asyncio as aioredis

from aiormq.exceptions import ChannelInvalidStateError
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import config
from app.services.finbert_service import predict_sentiment

from prometheus_client import Counter, Histogram, Gauge

logger = logging.getLogger(__name__)

# Sentiment Metrics
SENTIMENT_LATENCY = Histogram(
    "ml_sentiment_latency_seconds",
    "Time spent in FinBERT inference",
    ["source"]
)
SENTIMENT_SCORE = Gauge(
    "ml_sentiment_score",
    "Latest sentiment score per symbol",
    ["symbol", "source"]
)
SENTIMENT_PROCESSED_TOTAL = Counter(
    "ml_sentiment_processed_total",
    "Total number of news articles processed",
    ["symbol", "source"]
)

QUEUE_NEWS = "news.raw"


class NewsConsumer:
    def __init__(self, rabbitmq_url: str, redis: aioredis.Redis) -> None:
        self._rabbitmq_url = rabbitmq_url
        self._redis = redis
        self._connection: aio_pika.abc.AbstractRobustConnection | None = None
        self._channel: aio_pika.abc.AbstractChannel | None = None
        self._ttl = config.REDIS_SENTIMENT_TTL

    @retry(
        stop=stop_after_attempt(10),
        wait=wait_exponential(multiplier=1, min=2, max=60),
        reraise=True,
    )
    async def connect(self) -> None:
        self._connection = await aio_pika.connect_robust(self._rabbitmq_url)
        self._channel = await self._connection.channel()
        await self._channel.set_qos(prefetch_count=config.CONSUMER_PREFETCH_COUNT)
        logger.info("News consumer connected to RabbitMQ")

    async def start_consuming(self) -> None:
        if self._channel is None:
            raise RuntimeError("Consumer not connected")

        queue = await self._channel.declare_queue(QUEUE_NEWS, durable=True)
        await queue.consume(self._make_handler())
        logger.info("Consuming queue: %s", QUEUE_NEWS)
        await asyncio.Future()  # Run forever

    def _make_handler(self) -> Callable[[aio_pika.abc.AbstractIncomingMessage], Awaitable[None]]:
        async def handle(message: aio_pika.abc.AbstractIncomingMessage) -> None:
            try:
                async with message.process(requeue=True):
                    await self._process_message(message)
            except ChannelInvalidStateError as e:
                logger.warning("Channel closed (shutdown?) — skip: %s", e)
        return handle

    async def _process_message(
        self, message: aio_pika.abc.AbstractIncomingMessage
    ) -> None:
        try:
            raw = json.loads(message.body)
        except json.JSONDecodeError:
            logger.error("Invalid JSON in news message — discarding")
            return

        title = raw.get("title") or ""
        content = raw.get("content") or ""
        source = raw.get("source") or "unknown"
        symbol = raw.get("symbol") or "GENERAL"
        timestamp_str = raw.get("timestamp", "")
        url = raw.get("url") or ""

        text = f"{title}. {content}".strip()
        if not text:
            logger.warning("Empty news text — skipping")
            return

        # FinBERT inference (CPU, sync — run in executor to not block)
        import time
        start_time = time.time()
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, predict_sentiment, text
        )

        # Metrics recording
        latency = time.time() - start_time
        SENTIMENT_LATENCY.labels(source=source).observe(latency)
        SENTIMENT_PROCESSED_TOTAL.labels(symbol=symbol, source=source).inc()
        SENTIMENT_SCORE.labels(symbol=symbol, source=source).set(float(result["sentiment_score"]))

        # 0. Lọc tin tức quá cũ (ví dụ > 48 giờ)
        now_utc = datetime.now(timezone.utc)
        news_ts = timestamp_str
        if isinstance(news_ts, str):
            try:
                news_ts = datetime.fromisoformat(news_ts.replace("Z", "+00:00"))
            except ValueError:
                news_ts = now_utc
        
        if (now_utc - news_ts).total_seconds() > 172800: # 48 hours
            logger.info("NewsConsumer | Bỏ qua tin tức quá cũ (>48h): %s", title)
            return

        # 1. Cơ chế chống trùng lặp (Deduplication) dựa trên tiêu đề
        # Sử dụng Redis SET với TTL 24h để đánh dấu bài báo đã xử lý
        dedup_key = f"sentiment:processed:{symbol}"
        title_hash = str(hash(title)) # Đơn giản hóa hash tiêu đề
        
        is_new = await self._redis.sadd(dedup_key, title_hash)
        if not is_new:
            logger.info("NewsConsumer | Bỏ qua bài báo trùng lặp: %s", title)
            return
        
        # Đặt TTL cho dedup set nếu chưa có (ví dụ 24h)
        await self._redis.expire(dedup_key, 86400)

        sentiment_score = result["sentiment_score"]
        sentiment_label = result["sentiment_label"]

        # Lưu điểm số vào Redis List theo ngày để tính trung bình cộng (Rolling Daily Average)
        today = datetime.now().strftime("%Y-%m-%d")
        list_key = f"sentiment:scores:{symbol}:{today}"
        
        try:
            # 1. Thêm điểm số mới vào danh sách
            # 2. Đặt TTL cho danh sách (ví dụ 48h để đảm bảo dọn dẹp)
            # 3. Lấy toàn bộ danh sách để tính trung bình
            pipe = self._redis.pipeline()
            pipe.rpush(list_key, sentiment_score)
            pipe.expire(list_key, 172800)  # 48 hours
            pipe.lrange(list_key, 0, -1)
            results = await pipe.execute()
            
            all_scores = [float(s) for s in results[2]] # results[2] là kết quả của lrange
            avg_score = round(sum(all_scores) / len(all_scores), 4) if all_scores else sentiment_score
            count = len(all_scores)
        except (redis.RedisError, OSError) as e:
            logger.error("Redis list operation failed: %s", e)
            avg_score = sentiment_score
            count = 1

        payload = {
            "channel": f"sentiment:{symbol}",
            "symbol": symbol,
            "sentiment_score": avg_score,
            "sentiment_label": sentiment_label,
            "source": source,
            "timestamp": timestamp_str,
            "url": url,
            "title": title[:200],
            "daily_count": count,
            "latest_score": sentiment_score
        }

        # 2. Lưu lịch sử vào Redis Sorted Set (ZSET) - Giữ trong 24h hoặc tối đa 1000 tin
        history_key = f"sentiment:history:{symbol}"
        try:
            now_ts = time.time()
            cutoff_ts = now_ts - 86400  # 24 hours ago
            history_payload = json.dumps(payload)
            
            pipe = self._redis.pipeline()
            # Thêm tin mới (score là timestamp)
            pipe.zadd(history_key, {history_payload: now_ts})
            # Xóa tin cũ hơn 24 giờ
            pipe.zremrangebyscore(history_key, "-inf", cutoff_ts)
            # Giữ tối đa 1000 tin mới nhất (xóa các tin có rank thấp nhất)
            # ZREMRANGEBYRANK dùng index 0-based, -1001 là phần tử thứ 1001 từ cuối lên
            pipe.zremrangebyrank(history_key, 0, -1001)
            # Đặt expiry cho toàn bộ key (để dọn dẹp nếu không có tin mới)
            pipe.expire(history_key, 172800) # 48h
            await pipe.execute()
        except (redis.RedisError, OSError) as e:
            logger.error("Failed to store sentiment history in ZSET: %s", e)

        try:
            pipe = self._redis.pipeline()
            pipe.set(key, json_payload, ex=self._ttl)
            pipe.publish(key, json_payload)
            await pipe.execute()
        except (redis.RedisError, OSError) as e:
            logger.error("Redis publish failed — message sẽ được requeue: %s", e)
            raise

        logger.info(
            "Sentiment | %s → avg_score=%.3f (count=%d) latest=%.3f",
            symbol, avg_score, count, sentiment_score,
        )

    async def close(self) -> None:
        if self._connection and not self._connection.is_closed:
            await self._connection.close()
        logger.info("News consumer connection closed")
