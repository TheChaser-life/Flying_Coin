"""
NewsAPI Collector — Task 8.4
---------------------------
Fetches financial news from NewsAPI.org and publishes to `news.raw` RabbitMQ queue.
Free tier: 100 requests/day. Requires NEWSAPI_KEY env var.
"""

import logging
from datetime import datetime, timezone

from newsapi import NewsApiClient

from app.base_news_collector import BaseNewsCollector, RawNewsPayload

logger = logging.getLogger(__name__)

# Map NewsAPI source id → display name
SOURCE_NAMES = {
    "reuters": "Reuters",
    "bloomberg": "Bloomberg",
    "cnbc": "CNBC",
    "financial-times": "Financial Times",
    "business-insider": "Business Insider",
    "marketwatch": "MarketWatch",
    "yahoo-finance": "Yahoo Finance",
    "the-wall-street-journal": "Wall Street Journal",
    "bbc-news": "BBC",
    "techcrunch": "TechCrunch",
}


def _extract_symbol_from_title(title: str, keywords: list[tuple[str, str]]) -> str:
    """Extract symbol from title based on keyword mapping (e.g. 'Apple' → AAPL)."""
    title_lower = title.lower()
    for keyword, symbol in keywords:
        if keyword.lower() in title_lower:
            return symbol
    return "GENERAL"


class NewsAPICollector(BaseNewsCollector):
    """Collects financial news from NewsAPI.org."""

    def __init__(
        self,
        rabbitmq_url: str,
        api_key: str,
        keywords: list[str] | None = None,
        keyword_symbol_map: list[tuple[str, str]] | None = None,
        page_size: int = 20,
        language: str = "en",
    ) -> None:
        super().__init__(rabbitmq_url)
        self._api_key = api_key
        self._keywords = keywords or ["stock market", "bitcoin", "crypto", "fed", "earnings"]
        self._keyword_symbol_map = keyword_symbol_map or [
            ("apple", "AAPL"),
            ("microsoft", "MSFT"),
            ("google", "GOOGL"),
            ("amazon", "AMZN"),
            ("nvidia", "NVDA"),
            ("bitcoin", "BTC"),
            ("ethereum", "ETH"),
            ("tesla", "TSLA"),
            ("meta", "META"),
        ]
        self._page_size = min(page_size, 100)
        self._language = language

    def _process_article(
        self, art: dict
    ) -> RawNewsPayload | None:
        """Process a single NewsAPI article into a payload, or None if invalid."""
        title = art.get("title") or ""
        description = art.get("description") or ""
        content = f"{title}. {description}".strip() or title
        if not content or content == "[]":
            return None

        source_data = art.get("source") or {}
        source_id = source_data.get("id") or "unknown"
        source_name = SOURCE_NAMES.get(source_id)
        
        if not source_name:
            source_name = source_data.get("name") or source_id.replace("-", " ").title()

        published_at = art.get("publishedAt")
        if published_at:
            try:
                ts = datetime.fromisoformat(
                    published_at.replace("Z", "+00:00")
                )
            except ValueError:
                ts = datetime.now(timezone.utc)
        else:
            ts = datetime.now(timezone.utc)

        symbol = _extract_symbol_from_title(
            title, self._keyword_symbol_map
        )

        return RawNewsPayload(
            title=title,
            content=content[:2000],
            source=source_name,
            symbol=symbol,
            timestamp=ts,
            url=art.get("url") or "",
        )

    async def collect(self) -> None:
        if not self._api_key or self._api_key == "your-api-key":
            logger.warning("NewsAPI: No valid API key — skipping. Set NEWSAPI_KEY env var.")
            return

        published = 0
        errors = 0
        client = NewsApiClient(api_key=self._api_key)

        from_date = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
        # Hoặc đơn giản hơn là 24h trước
        from_date = (datetime.now(timezone.utc).timestamp() - 86400)
        from_date_str = datetime.fromtimestamp(from_date, tz=timezone.utc).strftime('%Y-%m-%dT%H:%M:%S')

        for keyword in self._keywords[:5]:  # Limit to 5 keywords per run (rate limit)
            try:
                response = client.get_everything(
                    q=keyword,
                    language=self._language,
                    sort_by="publishedAt",
                    page_size=min(self._page_size, 20),
                    page=1,
                    from_param=from_date_str
                )

                articles = response.get("articles") or []
                for art in articles:
                    try:
                        payload = self._process_article(art)
                        if payload is None:
                            continue
                        await self._publish(payload)
                        published += 1
                    except Exception:
                        logger.warning("NewsAPI | skip malformed article: %s", art, exc_info=True)

                if articles:
                    logger.info(
                        "NewsAPI | q=%s → %d articles published",
                        keyword[:20],
                        len(articles),
                    )

            except Exception:
                errors += 1
                logger.error(
                    "NewsAPI | failed for keyword %s", keyword, exc_info=True
                )

        logger.info(
            "NewsAPI collect run finished | published=%d errors=%d",
            published,
            errors,
        )

