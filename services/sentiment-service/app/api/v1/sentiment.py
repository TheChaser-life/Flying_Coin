"""Sentiment API — đọc từ Redis cache."""

import json

from fastapi import APIRouter, HTTPException

from app.core.dependencies import get_redis

router = APIRouter(prefix="/sentiment", tags=["sentiment"])


@router.get("/{symbol}")
async def get_sentiment(symbol: str):
    """Lấy sentiment score hiện tại (trung bình ngày) từ Redis (sentiment:{symbol})."""
    redis = get_redis()
    key = f"sentiment:{symbol}"
    data = await redis.get(key)
    if not data:
        raise HTTPException(status_code=404, detail=f"No sentiment data for {symbol}")
    return json.loads(data)


@router.get("/{symbol}/history")
async def get_sentiment_history(symbol: str):
    """Lấy lịch sử tin bài từ Redis Sorted Set (tối đa 24h qua hoặc 1000 bài)."""
    redis = get_redis()
    key = f"sentiment:history:{symbol}"
    # Lấy từ mới nhất đến cũ nhất (descending)
    data = await redis.zrevrange(key, 0, -1)
    return [json.loads(item) for item in data]

