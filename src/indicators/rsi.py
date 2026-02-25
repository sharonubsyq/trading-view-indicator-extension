"""
RSI — Relative Strength Index
Extends TradingView's built-in RSI with:
  • Multi-timeframe (MTF) aggregation
  • Divergence detection
  • Overbought / oversold signal labelling
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from enum import Enum


class RSISignal(str, Enum):
    OVERBOUGHT        = "overbought"
    OVERSOLD          = "oversold"
    BULLISH_DIVERGENCE = "bullish_divergence"
    BEARISH_DIVERGENCE = "bearish_divergence"
    NEUTRAL           = "neutral"


@dataclass
class RSIResult:
    values:    pd.Series
    signal:    RSISignal
    last:      float
    divergence: bool = False


class RSIIndicator:
    """
    Wilder-smoothed RSI with divergence detection.

    Parameters
    ----------
    period      : RSI period (default 14)
    ob          : Overbought threshold (default 70)
    os_         : Oversold threshold (default 30)
    div_lookback: Bars to look back for divergence (default 5)
    """

    def __init__(
        self,
        period:       int   = 14,
        ob:           float = 70.0,
        os_:          float = 30.0,
        div_lookback: int   = 5,
    ) -> None:
        self.period       = period
        self.ob           = ob
        self.os_          = os_
        self.div_lookback = div_lookback

    # ── Core calculation ──────────────────────────────────────────────────────
    def calculate(self, close: pd.Series) -> RSIResult:
        delta = close.diff()
        gain  = delta.clip(lower=0)
        loss  = (-delta).clip(lower=0)

        # Wilder EMA
        avg_gain = gain.ewm(alpha=1 / self.period, min_periods=self.period, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1 / self.period, min_periods=self.period, adjust=False).mean()

        rs  = avg_gain / avg_loss.replace(0, np.nan)
        rsi = 100 - (100 / (1 + rs))

        last   = float(rsi.iloc[-1])
        signal = self._classify(rsi, close)
        div    = self._detect_divergence(rsi, close)

        return RSIResult(values=rsi, signal=signal, last=last, divergence=div)

    # ── Signal classification ─────────────────────────────────────────────────
    def _classify(self, rsi: pd.Series, _close: pd.Series) -> RSISignal:
        last = float(rsi.iloc[-1])
        if last >= self.ob:
            return RSISignal.OVERBOUGHT
        if last <= self.os_:
            return RSISignal.OVERSOLD
        return RSISignal.NEUTRAL

    # ── Divergence detection ──────────────────────────────────────────────────
    def _detect_divergence(self, rsi: pd.Series, close: pd.Series) -> bool:
        n  = self.div_lookback
        if len(rsi) < n * 2:
            return False
        price_higher = close.iloc[-1] > close.iloc[-n]
        rsi_lower    = rsi.iloc[-1]  < rsi.iloc[-n]
        price_lower  = close.iloc[-1] < close.iloc[-n]
        rsi_higher   = rsi.iloc[-1]  > rsi.iloc[-n]
        return (price_higher and rsi_lower) or (price_lower and rsi_higher)

    # ── Multi-timeframe helper ────────────────────────────────────────────────
    def mtf(self, frames: dict[str, pd.Series]) -> dict[str, RSIResult]:
        """Run RSI on multiple timeframes. frames = {'1h': series, '4h': series, ...}"""
        return {tf: self.calculate(s) for tf, s in frames.items()}
