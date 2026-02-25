"""
AlertHandler — receives a ParsedAlert, fetches OHLCV data,
runs the CustomSignalEngine, and emits an enriched AlertResult.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime

import pandas as pd

from .parser import ParsedAlert
from ..indicators import CustomSignalEngine
from ..utils.data_fetcher import DataFetcher

log = logging.getLogger(__name__)


@dataclass
class AlertResult:
    alert:        ParsedAlert
    composite:    object    # CompositeSignal
    processed_at: datetime
    latency_ms:   float


class AlertHandler:
    def __init__(self, fetcher: DataFetcher | None = None) -> None:
        self._engine  = CustomSignalEngine()
        self._fetcher = fetcher or DataFetcher()

    def handle(self, alert: ParsedAlert) -> AlertResult | None:
        if not alert.valid:
            log.warning("Skipping invalid alert: %s", alert.error)
            return None

        t0 = datetime.utcnow()
        log.info("Handling alert: %s %s @ %s", alert.action, alert.ticker, alert.price)

        try:
            ohlcv = self._fetcher.get(alert.ticker, alert.interval)
        except Exception as exc:
            log.error("Data fetch failed for %s: %s", alert.ticker, exc)
            return None

        try:
            signal = self._engine.run(
                high   = ohlcv["high"],
                low    = ohlcv["low"],
                close  = ohlcv["close"],
                volume = ohlcv.get("volume"),
            )
        except Exception as exc:
            log.error("Indicator calculation failed: %s", exc)
            return None

        latency = (datetime.utcnow() - t0).total_seconds() * 1000

        log.info(
            "Signal for %s: %s (score=%.3f) | RSI=%s MACD=%s ST=%s",
            alert.ticker, signal.rating, signal.score,
            signal.rsi_signal, signal.macd_signal, signal.st_signal,
        )

        return AlertResult(
            alert=alert, composite=signal,
            processed_at=datetime.utcnow(), latency_ms=latency,
        )
