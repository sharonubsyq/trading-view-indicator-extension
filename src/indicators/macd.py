"""
MACD — Moving Average Convergence Divergence
Extended with:
  • Signal line crossover detection
  • Histogram momentum scoring
  • Zero-line cross alerts
"""

from __future__ import annotations

import pandas as pd
from dataclasses import dataclass
from enum import Enum


class MACDSignal(str, Enum):
    BULLISH_CROSS  = "bullish_cross"
    BEARISH_CROSS  = "bearish_cross"
    ZERO_CROSS_UP  = "zero_cross_up"
    ZERO_CROSS_DN  = "zero_cross_dn"
    MOMENTUM_UP    = "momentum_up"
    MOMENTUM_DOWN  = "momentum_down"
    NEUTRAL        = "neutral"


@dataclass
class MACDResult:
    macd:      pd.Series
    signal:    pd.Series
    histogram: pd.Series
    event:     MACDSignal
    last_macd: float
    last_hist: float


class MACDIndicator:
    def __init__(
        self,
        fast:   int = 12,
        slow:   int = 26,
        signal: int = 9,
    ) -> None:
        self.fast   = fast
        self.slow   = slow
        self.signal = signal

    def calculate(self, close: pd.Series) -> MACDResult:
        ema_fast = close.ewm(span=self.fast,   adjust=False).mean()
        ema_slow = close.ewm(span=self.slow,   adjust=False).mean()
        macd     = ema_fast - ema_slow
        sig      = macd.ewm(span=self.signal,  adjust=False).mean()
        hist     = macd - sig

        event = self._classify(macd, sig, hist)
        return MACDResult(
            macd      = macd,
            signal    = sig,
            histogram = hist,
            event     = event,
            last_macd = float(macd.iloc[-1]),
            last_hist = float(hist.iloc[-1]),
        )

    def _classify(
        self, macd: pd.Series, sig: pd.Series, hist: pd.Series
    ) -> MACDSignal:
        if len(macd) < 2:
            return MACDSignal.NEUTRAL

        # Signal line cross
        prev_above = macd.iloc[-2] > sig.iloc[-2]
        curr_above = macd.iloc[-1] > sig.iloc[-1]
        if not prev_above and curr_above:
            return MACDSignal.BULLISH_CROSS
        if prev_above and not curr_above:
            return MACDSignal.BEARISH_CROSS

        # Zero-line cross
        prev_pos = macd.iloc[-2] > 0
        curr_pos = macd.iloc[-1] > 0
        if not prev_pos and curr_pos:
            return MACDSignal.ZERO_CROSS_UP
        if prev_pos and not curr_pos:
            return MACDSignal.ZERO_CROSS_DN

        # Histogram momentum
        if hist.iloc[-1] > hist.iloc[-2]:
            return MACDSignal.MOMENTUM_UP
        if hist.iloc[-1] < hist.iloc[-2]:
            return MACDSignal.MOMENTUM_DOWN

        return MACDSignal.NEUTRAL
