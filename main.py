#!/usr/bin/env python3
"""
trading-view-indicator-extension
=================================
Webhook server + indicator engine for TradingView alerts.

Usage:
  python main.py                    # Start webhook server (default)
  python main.py --signal AAPL      # Query signal for a ticker
  python main.py --signal BTCUSD --interval 4h
  python main.py --demo             # Run with synthetic data
  python main.py --port 8080        # Custom port
"""

from __future__ import annotations

import argparse
import sys

from config import cfg
from src.utils.logger import setup_logging


def run_server(host: str, port: int, debug: bool) -> None:
    from src.server    import create_app
    from src.alerts    import AlertRouter
    from src.utils     import DataFetcher

    fetcher = DataFetcher(use_synthetic=cfg.USE_SYNTHETIC)
    router  = AlertRouter()

    if cfg.TELEGRAM_TOKEN and cfg.TELEGRAM_CHAT_ID:
        router.add_telegram(cfg.TELEGRAM_TOKEN, cfg.TELEGRAM_CHAT_ID)
    if cfg.SLACK_WEBHOOK:
        router.add_slack(cfg.SLACK_WEBHOOK)
    if cfg.DISCORD_WEBHOOK:
        router.add_discord(cfg.DISCORD_WEBHOOK)

    app = create_app(fetcher=fetcher, router=router)

    print(f"""
  ┌─────────────────────────────────────────────────┐
  │    trading-view-indicator-extension v1.0.0      │
  │                                                 │
  │  Webhook:  http://{host}:{port}/webhook          │
  │  Health:   http://{host}:{port}/health           │
  │  Signal:   http://{host}:{port}/signal/<ticker>  │
  │                                                 │
  │  Point your TradingView alerts at:              │
  │    POST http://<your-ip>:{port}/webhook          │
  └─────────────────────────────────────────────────┘
""")

    app.run(host=host, port=port, debug=debug)


def run_signal(ticker: str, interval: str) -> None:
    from src.indicators import CustomSignalEngine
    from src.utils      import DataFetcher

    fetcher = DataFetcher(use_synthetic=cfg.USE_SYNTHETIC)
    ohlcv   = fetcher.get(ticker, interval)
    engine  = CustomSignalEngine()
    result  = engine.run(
        high   = ohlcv["high"],
        low    = ohlcv["low"],
        close  = ohlcv["close"],
        volume = ohlcv.get("volume"),
    )

    print(f"""
  Ticker:  {ticker}
  Interval:{interval}
  ──────────────────────────────
  Rating:  {result.rating}
  Score:   {result.score:+.4f}
  ──────────────────────────────
  RSI:     {result.rsi_signal}
  MACD:    {result.macd_signal}
  BB:      {result.bb_signal}
  SuperTrend: {result.st_signal}
  VWAP:    {result.vwap_signal}
""")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="TradingView Indicator Extension — webhook server + signal engine"
    )
    parser.add_argument("--signal",   metavar="TICKER", help="Query composite signal for ticker")
    parser.add_argument("--interval", default=cfg.DEFAULT_INTERVAL, help="Timeframe (default: 1h)")
    parser.add_argument("--port",     type=int, default=cfg.PORT,   help="Server port (default: 5000)")
    parser.add_argument("--host",     default=cfg.HOST,             help="Bind host (default: 0.0.0.0)")
    parser.add_argument("--demo",     action="store_true",          help="Use synthetic demo data")
    parser.add_argument("--debug",    action="store_true",          help="Enable debug mode")
    parser.add_argument("--log-level",default=cfg.LOG_LEVEL,        help="LOG level (default: INFO)")
    args = parser.parse_args()

    setup_logging(args.log_level)

    if args.demo:
        import os; os.environ["USE_SYNTHETIC"] = "true"

    if args.signal:
        run_signal(args.signal.upper(), args.interval)
    else:
        run_server(args.host, args.port, args.debug or cfg.DEBUG)


if __name__ == "__main__":
    main()
