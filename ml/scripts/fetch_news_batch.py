#!/usr/bin/env python3
"""
Fetch News Batch — Task 8.5
----------------------------
Lấy tin tức từ NewsAPI + RSS, lưu JSON cho FinBERT batch.
Chạy trong Airflow (PythonOperator) hoặc standalone.
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def fetch_newsapi(api_key: str | None, keywords: list[str] | None = None) -> list[dict]:
    """Fetch từ NewsAPI (nếu có key)."""
    if not api_key or api_key == "your-api-key":
        logger.warning("NewsAPI key không có — bỏ qua")
        return []

    try:
        from newsapi import NewsApiClient
    except ImportError:
        logger.warning("newsapi-python chưa cài — bỏ qua NewsAPI")
        return []

    keywords = keywords or ["stock market", "bitcoin", "fed", "earnings"]
    client = NewsApiClient(api_key=api_key)
    articles: list[dict] = []

    for q in keywords[:3]:
        try:
            r = client.get_everything(q=q, language="en", sort_by="publishedAt", page_size=10)
            for a in (r.get("articles") or []):
                title = a.get("title") or ""
                desc = a.get("description") or ""
                content = f"{title}. {desc}".strip() or title
                if not content:
                    continue
                source = (a.get("source") or {}).get("name") or "NewsAPI"
                articles.append({
                    "id": len(articles) + 1,
                    "title": title,
                    "content": content[:2000],
                    "source": source,
                    "symbol": "GENERAL",
                    "timestamp": a.get("publishedAt") or datetime.now(timezone.utc).isoformat(),
                    "url": a.get("url") or "",
                })
        except Exception as e:
            logger.warning("NewsAPI %s: %s", q, e)

    logger.info("NewsAPI: %d articles", len(articles))
    return articles


def fetch_rss(feeds: list[tuple[str, str]] | None = None) -> list[dict]:
    """Fetch từ RSS feeds."""
    feeds = feeds or [
        ("https://finance.yahoo.com/news/rssindex", "Yahoo Finance"),
        ("https://www.cnbc.com/id/100003114/device/rss/rss.html", "CNBC"),
    ]
    articles: list[dict] = []
    base_id = 100

    try:
        import feedparser
        import aiohttp
    except ImportError:
        logger.warning("feedparser/aiohttp chưa cài — bỏ qua RSS")
        return []

    import asyncio

    async def _fetch():
        async with aiohttp.ClientSession() as session:
            for url, source in feeds:
                try:
                    async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                        if resp.status != 200:
                            continue
                        body = await resp.text()
                        feed = feedparser.parse(body)
                        for e in (feed.entries or [])[:5]:
                            title = (e.get("title") or "").strip()
                            summary = (e.get("summary") or e.get("description") or "").strip()
                            from html import unescape
                            import re
                            summary = re.sub(r"<[^>]+>", " ", summary)
                            summary = unescape(summary)
                            content = f"{title}. {summary}"[:2000]
                            if len(content) < 20:
                                continue
                            articles.append({
                                "id": base_id + len(articles),
                                "title": title,
                                "content": content,
                                "source": source,
                                "symbol": "GENERAL",
                                "timestamp": e.get("published") or datetime.now(timezone.utc).isoformat(),
                                "url": e.get("link") or "",
                            })
                except Exception as ex:
                    logger.warning("RSS %s: %s", source, ex)

    asyncio.run(_fetch())
    logger.info("RSS: %d articles", len(articles))
    return articles


def main() -> int:
    import os
    output_path = Path(os.environ.get("NEWS_BATCH_OUTPUT", str(PROJECT_ROOT / "ml" / "outputs" / "news_batch.json")))
    output_path.parent.mkdir(parents=True, exist_ok=True)

    api_key = os.environ.get("NEWSAPI_KEY", "")
    news = fetch_newsapi(api_key) + fetch_rss()

    if not news:
        logger.warning("Không có tin nào — tạo file rỗng")
        news = []

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(news, f, ensure_ascii=False, indent=2)

    logger.info("Đã lưu %d tin → %s", len(news), output_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
