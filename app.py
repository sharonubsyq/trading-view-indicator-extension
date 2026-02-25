"""
Flask webhook server.
Receives TradingView alert POST requests and processes them through
the indicator engine and notification router.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime
from typing import Optional

from flask import Flask, Response, jsonify, request

from ..alerts.parser  import AlertParser
from ..alerts.handler import AlertHandler
from ..alerts.router  import AlertRouter
from ..utils.data_fetcher import DataFetcher

log = logging.getLogger(__name__)


def create_app(
    fetcher: Optional[DataFetcher] = None,
    router:  Optional[AlertRouter] = None,
) -> Flask:
    app = Flask(__name__)

    parser  = AlertParser()
    handler = AlertHandler(fetcher)
    _router = router or AlertRouter()

    # ── Health check ──────────────────────────────────────────────────────────
    @app.get("/")
    @app.get("/health")
    def health() -> Response:
        return jsonify({
            "status": "ok",
            "service": "trading-view-indicator-extension",
            "time":    datetime.utcnow().isoformat() + "Z",
        })

    # ── Webhook endpoint ──────────────────────────────────────────────────────
    @app.post("/webhook")
    @app.post("/alert")
    def webhook() -> Response:
        secret = os.getenv("WEBHOOK_SECRET", "")
        if secret:
            provided = request.headers.get("X-Webhook-Secret", "")
            if provided != secret:
                log.warning("Unauthorized webhook call from %s", request.remote_addr)
                return jsonify({"error": "unauthorized"}), 401

        body = request.get_data()
        log.debug("Incoming alert body: %r", body[:500])

        alert = parser.parse(body)
        if not alert.valid:
            return jsonify({"error": alert.error}), 400

        result = handler.handle(alert)
        if result is None:
            return jsonify({"error": "processing failed"}), 500

        _router.dispatch(result)

        return jsonify({
            "status":    "ok",
            "ticker":    alert.ticker,
            "rating":    result.composite.rating,
            "score":     result.composite.score,
            "latency_ms": result.latency_ms,
        })

    # ── Signal endpoint (direct query) ────────────────────────────────────────
    @app.get("/signal/<ticker>")
    def signal(ticker: str) -> Response:
        interval = request.args.get("interval", "1h")
        from ..indicators import CustomSignalEngine
        from ..utils.data_fetcher import DataFetcher

        try:
            ohlcv  = (fetcher or DataFetcher()).get(ticker.upper(), interval)
            engine = CustomSignalEngine()
            result = engine.run(
                high=ohlcv["high"], low=ohlcv["low"],
                close=ohlcv["close"], volume=ohlcv.get("volume"),
            )
            return jsonify({
                "ticker":      ticker.upper(),
                "interval":    interval,
                "rating":      result.rating,
                "score":       result.score,
                "rsi_signal":  result.rsi_signal,
                "macd_signal": result.macd_signal,
                "bb_signal":   result.bb_signal,
                "st_signal":   result.st_signal,
                "vwap_signal": result.vwap_signal,
                "components":  result.components,
            })
        except Exception as exc:
            log.error("Signal query failed: %s", exc)
            return jsonify({"error": str(exc)}), 500

    return app
