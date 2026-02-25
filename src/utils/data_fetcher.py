"""
DataFetcher — fetch OHLCV data for indicator calculations.
Primary source: yfinance (Yahoo Finance — free, no API key needed).
Fallback: synthetic random-walk data for testing/demo.
"""

from __future__ import annotations

import logging
from typing import Optional
from functools import lru_cache

import numpy as np
import pandas as pd

log = logging.getLogger(__name__)

# Map TradingView intervals to yfinance periods/intervals
_TV_TO_YF = {
    "1":    ("7d",   "1m"),
    "5":    ("60d",  "5m"),
    "15":   ("60d",  "15m"),
    "30":   ("60d",  "30m"),
    "60":   ("730d", "60m"),
    "1h":   ("730d", "60m"),
    "2h":   ("730d", "2h"),
    "4h":   ("730d", "4h"),  # yfinance doesn't support 4h — we resample
    "D":    ("5y",   "1d"),
    "1D":   ("5y",   "1d"),
    "W":    ("10y",  "1wk"),
    "1W":   ("10y",  "1wk"),
}


class DataFetcher:
    def __init__(self, use_synthetic: bool = False) -> None:
        self._synthetic = use_synthetic

    def get(self, ticker: str, interval: str = "1h") -> pd.DataFrame:
        if self._synthetic:
            return self._synthetic_data(ticker, 200)

        try:
            return self._yfinance(ticker, interval)
        except Exception as exc:
            log.warning("yfinance failed for %s/%s: %s — using synthetic data", ticker, interval, exc)
            return self._synthetic_data(ticker, 200)

    # ── yfinance ──────────────────────────────────────────────────────────────
    @staticmethod
    def _yfinance(ticker: str, tv_interval: str) -> pd.DataFrame:
        import yfinance as yf   # lazy import — not in stdlib

        period, yf_interval = _TV_TO_YF.get(tv_interval, ("730d", "1d"))

        hist = yf.Ticker(ticker).history(period=period, interval=yf_interval)
        if hist.empty:
            raise ValueError(f"No data returned from yfinance for {ticker}")

        hist.columns = [c.lower() for c in hist.columns]
        df = hist[["open","high","low","close","volume"]].copy()
        df.dropna(inplace=True)

        # Resample 4h from 1h if needed
        if tv_interval == "4h" and yf_interval == "60m":
            df = df.resample("4h").agg({
                "open":   "first",
                "high":   "max",
                "low":    "min",
                "close":  "last",
                "volume": "sum",
            }).dropna()

        return df

    # ── Synthetic fallback ────────────────────────────────────────────────────
    @staticmethod
    def _synthetic_data(ticker: str, bars: int = 200) -> pd.DataFrame:
        rng     = np.random.default_rng(sum(ord(c) for c in ticker))
        returns = rng.normal(0.0002, 0.015, bars)
        close   = 100.0 * np.exp(np.cumsum(returns))
        high    = close * (1 + np.abs(rng.normal(0, 0.008, bars)))
        low     = close * (1 - np.abs(rng.normal(0, 0.008, bars)))
        open_   = np.roll(close, 1); open_[0] = close[0]
        volume  = rng.integers(100_000, 5_000_000, bars).astype(float)

        idx = pd.date_range("2023-01-01", periods=bars, freq="h")
        return pd.DataFrame({
            "open": open_, "high": high, "low": low,
            "close": close, "volume": volume,
        }, index=idx)
