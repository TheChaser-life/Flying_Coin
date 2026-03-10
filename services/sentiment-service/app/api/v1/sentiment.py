"""Sentiment API — đọc từ Redis cache."""

from fastapi import APIRouter, HTTPException

from app.core.dependencies import get_redis

router = APIRouter(prefix="/sentiment", tags=["sentiment"])


@router.get("/{symbol}")
async def get_sentiment(symbol: str):
    """Lấy sentiment score hiện tại từ Redis (sentiment:{symbol})."""
    redis = get_redis()
    key = f"sentiment:{symbol}"
    data = await redis.get(key)
    if not data:
        raise HTTPException(status_code=404, detail=f"No sentiment data for {symbol}")
    import json
    return json.loads(data)
