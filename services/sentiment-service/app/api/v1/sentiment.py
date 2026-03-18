"""Sentiment API — đọc từ Redis cache."""

import json

from fastapi import APIRouter, HTTPException

from app.core.dependencies import get_redis

router = APIRouter(prefix="/sentiment", tags=["sentiment"])


@router.get("/{symbol}", responses={404: {"description": "No sentiment data for symbol"}})
async def get_sentiment(symbol: str):
    """Lấy sentiment score hiện tại từ Redis (sentiment:{symbol})."""
    redis = get_redis()
    key = f"sentiment:{symbol}"
    data = await redis.get(key)
    if not data:
        raise HTTPException(status_code=404, detail=f"No sentiment data for {symbol}")
    return json.loads(data)

