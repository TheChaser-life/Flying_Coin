"""
Collector Entry Point
---------------------
Runs Yahoo Finance and Binance collectors on a fixed schedule.
Each collector fetches data and publishes to the appropriate RabbitMQ queue.
"""

import asyncio
import logging
import signal
import sys

from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import config
from app.yahoo_collector import YahooCollector
from app.binance_collector import BinanceCollector
from app.binance_ws_collector import BinanceWebSocketCollector
from app.newsapi_collector import NewsAPICollector
from app.rss_collector import RSSCollector

from aiohttp import web

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


def handle_health(request):
    """Simple health check endpoint."""
    return web.json_response({"status": "ok", "service": "collectors"})


async def run_health_server():
    """Starts a minimal web server for health checks on port 8000."""
    app = web.Application()
    app.router.add_get("/health", handle_health)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8000)
    logger.info("Health check server starting on port 8000")
    await site.start()
    # Keep the server running indefinitely
    while True:
        await asyncio.sleep(3600)


class CollectorOrchestrator:
    def __init__(self) -> None:
        self._yahoo = YahooCollector(
            rabbitmq_url=config.RABBITMQ_URL,
            symbols=config.YAHOO_STOCK_SYMBOLS,
            interval=config.YAHOO_INTERVAL,
            period=config.YAHOO_PERIOD,
        )
        self._binance = BinanceCollector(
            rabbitmq_url=config.RABBITMQ_URL,
            symbols=config.BINANCE_SYMBOLS,
            base_url=config.BINANCE_BASE_URL,
            interval=config.BINANCE_INTERVAL,
            limit=config.BINANCE_LIMIT,
        )
        self._newsapi = NewsAPICollector(
            rabbitmq_url=config.RABBITMQ_URL,
            api_key=config.NEWSAPI_KEY,
            keywords=config.NEWSAPI_KEYWORDS,
            page_size=config.NEWSAPI_PAGE_SIZE,
        )
        self._rss = RSSCollector(
            rabbitmq_url=config.RABBITMQ_URL,
            feeds=config.RSS_FEEDS,
        )
        self._binance_ws = BinanceWebSocketCollector(
            rabbitmq_url=config.RABBITMQ_URL,
            symbols=config.BINANCE_SYMBOLS,
        )
        self._running = False

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        reraise=True,
    )
    async def _connect_all(self) -> None:
        await self._yahoo.connect()
        await self._binance.connect()
        await self._binance_ws.connect()
        await self._newsapi.connect()
        await self._rss.connect()

    async def start(self) -> None:
        logger.info("Connecting collectors to RabbitMQ …")
        await self._connect_all()
        self._running = True
        logger.info(
            "Collectors started — interval=%ds", config.COLLECT_INTERVAL_SECONDS
        )

        while self._running:
            logger.info("=== Starting collection run ===")
            
            # Run tasks independently so one failure doesn't block others
            async def run_safe(name, coro):
                try:
                    await coro
                    logger.info(f"{name} collection successful")
                except Exception as e:
                    logger.error(f"{name} collection failed: {e}", exc_info=True)

            await asyncio.gather(
                run_safe("Yahoo", self._yahoo.collect()),
                run_safe("Binance", self._binance.collect()),
                run_safe("NewsAPI", self._newsapi.collect()),
                run_safe("RSS", self._rss.collect()),
            )

            logger.info(
                "=== Collection run complete — sleeping %ds ===",
                config.COLLECT_INTERVAL_SECONDS,
            )
            await asyncio.sleep(config.COLLECT_INTERVAL_SECONDS)

    async def stop(self) -> None:
        self._running = False
        await self._yahoo.disconnect()
        await self._binance.disconnect()
        await self._binance_ws.disconnect()
        await self._newsapi.disconnect()
        await self._rss.disconnect()
        logger.info("Collectors stopped")


async def main() -> None:
    orchestrator = CollectorOrchestrator()

    loop = asyncio.get_running_loop()

    def _shutdown(sig: signal.Signals) -> None:
        logger.info("Received signal %s — shutting down …", sig.name)
        loop.create_task(orchestrator.stop())

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, _shutdown, sig)
        except NotImplementedError:
            # Windows does not support add_signal_handler for all signals
            signal.signal(sig, lambda s, f: loop.create_task(orchestrator.stop()))

    # Run health server, periodic collectors, and Binance WS stream in parallel
    await asyncio.gather(
        run_health_server(),
        orchestrator.start(),
        orchestrator._binance_ws.stream(),
    )


if __name__ == "__main__":
    asyncio.run(main())
