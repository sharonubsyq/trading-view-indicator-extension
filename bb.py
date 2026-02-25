"""
Bollinger Bands — extended with:
  • %B (position within bands)
  • Bandwidth (squeeze detection)
  • Squeeze alerts (low volatility periods)
"""

from __future__ import annotations

import pandas as pd
from dataclasses import dataclass
from enum import Enum


class BBSignal(str, Enum):
    SQUEEZE          = "squeeze"
    EXPANSION        = "expansion"
    UPPER_TOUCH      = "upper_touch"
    LOWER_TOUCH      = "lower_touch"
    UPPER_BREAK      = "upper_break"
    LOWER_BREAK      = "lower_break"
    NEUTRAL          = "neutral"


@dataclass
class BBResult:
    upper:     pd.Series
    middle:    pd.Series
    lower:     pd.Series
    pct_b:     pd.Series      # %B: 0 = lower band, 1 = upper band
    bandwidth: pd.Series      # (upper - lower) / middle
    signal:    BBSignal
    squeeze:   bool


class BollingerBands:
    def __init__(
        self,
        period:      int   = 20,
        std_dev:     float = 2.0,
        sq_threshold: float = 0.04,   # bandwidth below this = squeeze
    ) -> None:
        self.period       = period
        self.std_dev      = std_dev
        self.sq_threshold = sq_threshold

    def calculate(self, close: pd.Series) -> BBResult:
        middle = close.rolling(self.period).mean()
        std    = close.rolling(self.period).std(ddof=0)

        upper  = middle + self.std_dev * std
        lower  = middle - self.std_dev * std
        bw     = (upper - lower) / middle
        pct_b  = (close - lower) / (upper - lower)

        squeeze = bool(float(bw.iloc[-1]) < self.sq_threshold)
        signal  = self._classify(close, upper, lower, bw, squeeze)

        return BBResult(
            upper=upper, middle=middle, lower=lower,
            pct_b=pct_b, bandwidth=bw, signal=signal, squeeze=squeeze,
        )

    def _classify(
        self,
        close:   pd.Series,
        upper:   pd.Series,
        lower:   pd.Series,
        bw:      pd.Series,
        squeeze: bool,
    ) -> BBSignal:
        if squeeze:
            return BBSignal.SQUEEZE
        if len(bw) >= 2 and bw.iloc[-1] > bw.iloc[-2] * 1.05:
            return BBSignal.EXPANSION

        last_c = float(close.iloc[-1])
        last_u = float(upper.iloc[-1])
        last_l = float(lower.iloc[-1])
        prev_c = float(close.iloc[-2]) if len(close) >= 2 else last_c

        if last_c > last_u and prev_c <= last_u:
            return BBSignal.UPPER_BREAK
        if last_c < last_l and prev_c >= last_l:
            return BBSignal.LOWER_BREAK
        if last_c >= last_u * 0.995:
            return BBSignal.UPPER_TOUCH
        if last_c <= last_l * 1.005:
            return BBSignal.LOWER_TOUCH

        return BBSignal.NEUTRAL
