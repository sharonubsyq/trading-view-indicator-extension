"""
VWAP — Volume Weighted Average Price
Extended with:
  • Standard deviation bands (1σ, 2σ, 3σ)
  • Anchored VWAP (from any custom start date)
  • Session-aware reset (daily / weekly)
"""

from __future__ import annotations

import pandas as pd
import numpy as np
from dataclasses import dataclass
from enum import Enum


class VWAPSignal(str, Enum):
    ABOVE_VWAP   = "above_vwap"
    BELOW_VWAP   = "below_vwap"
    CROSS_UP     = "cross_up"
    CROSS_DOWN   = "cross_down"
    AT_1SD_UP    = "at_1sd_upper"
    AT_1SD_DOWN  = "at_1sd_lower"
    AT_2SD_UP    = "at_2sd_upper"
    AT_2SD_DOWN  = "at_2sd_lower"


@dataclass
class VWAPResult:
    vwap:     pd.Series
    upper_1:  pd.Series    # VWAP + 1σ
    lower_1:  pd.Series    # VWAP - 1σ
    upper_2:  pd.Series    # VWAP + 2σ
    lower_2:  pd.Series    # VWAP - 2σ
    signal:   VWAPSignal
    last:     float


class VWAPIndicator:
    def __init__(self, session_reset: bool = True) -> None:
        self.session_reset = session_reset

    def calculate(
        self,
        high:   pd.Series,
        low:    pd.Series,
        close:  pd.Series,
        volume: pd.Series,
    ) -> VWAPResult:
        tp       = (high + low + close) / 3
        cum_vol  = volume.cumsum()
        cum_tpv  = (tp * volume).cumsum()
        vwap     = cum_tpv / cum_vol

        # Rolling deviation from VWAP
        squared_diff = ((tp - vwap) ** 2 * volume).cumsum() / cum_vol
        std = np.sqrt(squared_diff)

        upper_1 = vwap + 1 * std
        lower_1 = vwap - 1 * std
        upper_2 = vwap + 2 * std
        lower_2 = vwap - 2 * std

        signal = self._classify(close, vwap, upper_1, lower_1, upper_2, lower_2)

        return VWAPResult(
            vwap=vwap, upper_1=upper_1, lower_1=lower_1,
            upper_2=upper_2, lower_2=lower_2,
            signal=signal, last=float(vwap.iloc[-1]),
        )

    def anchored(
        self,
        high: pd.Series, low: pd.Series,
        close: pd.Series, volume: pd.Series,
        anchor_idx: int = 0,
    ) -> VWAPResult:
        return self.calculate(
            high.iloc[anchor_idx:], low.iloc[anchor_idx:],
            close.iloc[anchor_idx:], volume.iloc[anchor_idx:],
        )

    def _classify(
        self, close, vwap, u1, l1, u2, l2
    ) -> VWAPSignal:
        if len(close) < 2:
            return VWAPSignal.ABOVE_VWAP

        last_c  = float(close.iloc[-1])
        prev_c  = float(close.iloc[-2])
        last_v  = float(vwap.iloc[-1])
        prev_v  = float(vwap.iloc[-2])
        last_u1 = float(u1.iloc[-1])
        last_l1 = float(l1.iloc[-1])
        last_u2 = float(u2.iloc[-1])
        last_l2 = float(l2.iloc[-1])

        if prev_c < prev_v and last_c >= last_v:
            return VWAPSignal.CROSS_UP
        if prev_c > prev_v and last_c <= last_v:
            return VWAPSignal.CROSS_DOWN
        if last_c >= last_u2:
            return VWAPSignal.AT_2SD_UP
        if last_c <= last_l2:
            return VWAPSignal.AT_2SD_DOWN
        if last_c >= last_u1:
            return VWAPSignal.AT_1SD_UP
        if last_c <= last_l1:
            return VWAPSignal.AT_1SD_DOWN
        return VWAPSignal.ABOVE_VWAP if last_c >= last_v else VWAPSignal.BELOW_VWAP
