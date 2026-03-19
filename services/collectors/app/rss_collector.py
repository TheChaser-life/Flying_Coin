"""
RSS Collector — Task 8.4
------------------------
Fetches financial news from RSS feeds and publishes to `news.raw` RabbitMQ queue.
No API key required.
"""

import logging
from datetime import datetime, timezone
from html import unescape
import re

import aiohttp
import feedparser

from app.base_news_collector import BaseNewsCollector, RawNewsPayload

logger = logging.getLogger(__name__)

# Default financial RSS feeds (Reuters removed — feeds.reuters.com DNS issues in some regions)
DEFAULT_RSS_FEEDS = [
    ("https://feeds.content.dowjones.io/public/rss/RSSMarketsMain", "Wall Street Journal"),
    ("https://feeds.content.dowjones.io/public/rss/mw_topstories", "MarketWatch"),
    ("https://finance.yahoo.com/news/rssindex", "Yahoo Finance"),
    ("https://www.cnbc.com/id/100003114/device/rss/rss.html", "CNBC"),
    ("https://news.google.com/rss/search?q=stock+market+finance&hl=en-US&gl=US&ceid=US:en", "Google News (Finance)"),
]


def _strip_html(html: str) -> str:
    """Remove HTML tags and decode entities."""
    if not html:
        return ""
    text = re.sub(r"<[^>]+>", " ", html)
    text = unescape(text)
    return " ".join(text.split()).strip()[:2000]


def _parse_date(date_str: str | None) -> datetime:
    """Parse RSS date to datetime."""
    if not date_str:
        return datetime.now(timezone.utc)
    try:
        from email.utils import parsedate_to_datetime
        dt = parsedate_to_datetime(date_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (ValueError, TypeError):
        return datetime.now(timezone.utc)


def _extract_symbol(title: str, content: str) -> str:
    """Simple symbol extraction from title/content."""
    text = f"{title} {content}".lower()
    symbols = [
        ("bitcoin", "BTC"), ("btc", "BTC"),
        ("ethereum", "ETH"), ("eth", "ETH"),
        ("apple", "AAPL"), ("microsoft", "MSFT"),
        ("amazon", "AMZN"), ("nvidia", "NVDA"),
        ("google", "GOOGL"), ("tesla", "TSLA"),
        ("meta", "META"), ("fed", "FED"),
    ]
    for keyword, sym in symbols:
        if keyword in text:
            return sym
    return "GENERAL"


class RSSCollector(BaseNewsCollector):
    """Collects financial news from RSS feeds."""

    def __init__(
        self,
        rabbitmq_url: str,
        feeds: list[tuple[str, str]] | None = None,
    ) -> None:
        super().__init__(rabbitmq_url)
        self._feeds = feeds or DEFAULT_RSS_FEEDS

    def _process_entry(
        self, entry: dict, source_name: str
    ) -> RawNewsPayload | None:
        """Process a single RSS entry into a payload, or None if invalid."""
        title = _strip_html(entry.get("title") or "")
        summary = _strip_html(
            entry.get("summary") or entry.get("description") or ""
        )
        content = f"{title}. {summary}".strip() or title
        if not content or len(content) < 20:
            return None

        # Cleanup link: strip whitespace and mysterious "web:" prefix seen in some feeds
        link = (entry.get("link") or "").strip()
        if link.startswith("web:"):
            link = link[4:].strip()
        
        published_at = _parse_date(
            entry.get("published") or entry.get("updated")
        )
        symbol = _extract_symbol(title, summary)

        return RawNewsPayload(
            title=title,
            content=content[:2000],
            source=source_name,
            symbol=symbol,
            timestamp=published_at,
            url=link,
        )

    async def _fetch_feed(
        self, session: aiohttp.ClientSession, feed_url: str, source_name: str
    ) -> int:
        """Fetch and process a single RSS feed. Returns number of articles published."""
        published = 0
        async with session.get(
            feed_url,
            timeout=aiohttp.ClientTimeout(total=15),
            headers={"User-Agent": "MDMFS-NewsCollector/1.0"},
        ) as resp:
            if resp.status != 200:
                logger.warning("RSS | %s returned %d", source_name, resp.status)
                return 0

            body = await resp.text()
            feed = feedparser.parse(body)

        entries = getattr(feed, "entries", []) or []
        for entry in entries[:15]:
            try:
                payload = self._process_entry(entry, source_name)
                if payload is None:
                    continue
                await self._publish(payload)
                published += 1
            except Exception:
                logger.warning(
                    "RSS | skip malformed entry from %s",
                    source_name,
                    exc_info=True,
                )

        if entries:
            logger.info(
                "RSS | %s → %d articles published",
                source_name,
                min(len(entries), 15),
            )
        return published

    async def collect(self) -> None:
        published = 0
        errors = 0

        async with aiohttp.ClientSession() as session:
            for feed_url, source_name in self._feeds:
                try:
                    published += await self._fetch_feed(session, feed_url, source_name)
                except Exception:
                    errors += 1
                    logger.error(
                        "RSS | failed for %s: %s",
                        source_name,
                        feed_url,
                        exc_info=True,
                    )

        logger.info(
            "RSS collect run finished | published=%d errors=%d",
            published,
            errors,
        )

