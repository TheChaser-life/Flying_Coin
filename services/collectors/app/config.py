from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Tìm .env: ưu tiên thư mục hiện tại, rồi project root
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
_ENV_PATHS = [".env", _PROJECT_ROOT / ".env"]


class CollectorConfig(BaseSettings):
    RABBITMQ_URL: str = "amqp://guest:guest@localhost:5672/"
    REDIS_URL: str = "redis://localhost:6379/0"

    # Yahoo Finance symbols (VN stocks, US stocks)
    YAHOO_STOCK_SYMBOLS: list[str] = [
        "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA",
        "VNM", "VIC.VN", "VHM.VN", "VCB.VN", "BID.VN",
    ]
    YAHOO_INTERVAL: str = "1d"       # 1m,2m,5m,15m,30m,60m,90m,1h,1d,5d,1wk,1mo,3mo
    YAHOO_PERIOD: str = "1mo"       # fetch last N days on each run (1mo ~ 21 trading days)

    # Binance symbols (crypto)
    BINANCE_BASE_URL: str = "https://api.binance.com"
    BINANCE_SYMBOLS: list[str] = [
        "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "ADAUSDT",
    ]
    BINANCE_INTERVAL: str = "1d"     # 1m,3m,5m,15m,30m,1h,2h,4h,6h,8h,12h,1d,3d,1w,1M
    BINANCE_LIMIT: int = 100        # number of candles per fetch (cần ≥50 cho dataset builder)

    # Collector schedule (seconds between runs)
    COLLECT_INTERVAL_SECONDS: int = 60

    # NewsAPI (Task 8.4) — free tier 100 req/day
    NEWSAPI_KEY: str = ""
    NEWSAPI_KEYWORDS: list[str] = [
        "stock market", "bitcoin", "crypto", "fed", "earnings",
        "inflation", "interest rate", "recession",
    ]
    NEWSAPI_PAGE_SIZE: int = 20

    # RSS feeds (url, display_name)
    RSS_FEEDS: list[tuple[str, str]] = [
        ("https://feeds.content.dowjones.io/public/rss/RSSMarketsMain", "Wall Street Journal"),
        ("https://feeds.content.dowjones.io/public/rss/mw_topstories", "MarketWatch"),
        ("https://finance.yahoo.com/news/rssindex", "Yahoo Finance"),
        ("https://www.cnbc.com/id/100003114/device/rss/rss.html", "CNBC"),
        ("https://news.google.com/rss/search?q=when:1h+finance&hl=en-US&gl=US&ceid=US:en", "Google News"),
    ]

    model_config = SettingsConfigDict(
        env_file=[str(p) for p in _ENV_PATHS],
        env_file_encoding="utf-8",
        extra="ignore",
    )


config = CollectorConfig()
