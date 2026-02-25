"""
SuperTrend — ATR-based trend-following indicator.
Extended with:
  • Direction flip detection
  • Trend strength scoring
  • Support / resistance level tracking
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from dataclasses import dataclass
from enum import Enum


class STSignal(str, Enum):
    BUY_SIGNAL  = "buy_signal"    # flipped from SELL → BUY
    SELL_SIGNAL = "sell_signal"   # flipped from BUY → SELL
    BULLISH     = "bullish"       # ongoing uptrend
    BEARISH     = "bearish"       # ongoing downtrend


@dataclass
class STResult:
    supertrend: pd.Series
    direction:  pd.Series    # +1 = bullish, -1 = bearish
    signal:     STSignal
    support:    float        # last computed support level
    resistance: float        # last computed resistance level
    strength:   float        # 0.0–1.0 (distance from price / ATR)


class SuperTrend:
    def __init__(self, period: int = 10, multiplier: float = 3.0) -> None:
        self.period     = period
        self.multiplier = multiplier

    def calculate(
        self, high: pd.Series, low: pd.Series, close: pd.Series
    ) -> STResult:
        hl2  = (high + low) / 2
        atr  = self._atr(high, low, close)

        upper_band = hl2 + self.multiplier * atr
        lower_band = hl2 - self.multiplier * atr

        # Smooth bands
        for i in range(1, len(upper_band)):
            upper_band.iloc[i] = (
                upper_band.iloc[i]
                if upper_band.iloc[i] < upper_band.iloc[i - 1]
                or close.iloc[i - 1] > upper_band.iloc[i - 1]
                else upper_band.iloc[i - 1]
            )
            lower_band.iloc[i] = (
                lower_band.iloc[i]
                if lower_band.iloc[i] > lower_band.iloc[i - 1]
                or close.iloc[i - 1] < lower_band.iloc[i - 1]
                else lower_band.iloc[i - 1]
            )

        direction = pd.Series(index=close.index, dtype=float)
        st        = pd.Series(index=close.index, dtype=float)

        for i in range(len(close)):
            if i == 0:
                direction.iloc[i] = 1
                st.iloc[i]        = lower_band.iloc[i]
                continue
            prev_st   = st.iloc[i - 1]
            prev_dir  = direction.iloc[i - 1]
            curr_close = close.iloc[i]

            if prev_st == upper_band.iloc[i - 1]:
                direction.iloc[i] = -1 if curr_close <= upper_band.iloc[i] else 1
            else:
                direction.iloc[i] = 1  if curr_close >= lower_band.iloc[i] else -1

            st.iloc[i] = (
                lower_band.iloc[i] if direction.iloc[i] == 1 else upper_band.iloc[i]
            )

        curr_dir  = int(direction.iloc[-1])
        prev_dir  = int(direction.iloc[-2]) if len(direction) >= 2 else curr_dir
        last_atr  = float(atr.iloc[-1])
        last_st   = float(st.iloc[-1])
        last_c    = float(close.iloc[-1])

        if prev_dir == -1 and curr_dir == 1:
            signal = STSignal.BUY_SIGNAL
        elif prev_dir == 1 and curr_dir == -1:
            signal = STSignal.SELL_SIGNAL
        elif curr_dir == 1:
            signal = STSignal.BULLISH
        else:
            signal = STSignal.BEARISH

        strength = min(1.0, abs(last_c - last_st) / (last_atr + 1e-9))

        return STResult(
            supertrend = st,
            direction  = direction,
            signal     = signal,
            support    = last_st if curr_dir == 1  else float("nan"),
            resistance = last_st if curr_dir == -1 else float("nan"),
            strength   = strength,
        )

    def _atr(self, high: pd.Series, low: pd.Series, close: pd.Series) -> pd.Series:
        tr = pd.concat([
            high - low,
            (high - close.shift()).abs(),
            (low  - close.shift()).abs(),
        ], axis=1).max(axis=1)
        return tr.ewm(span=self.period, adjust=False).mean()
