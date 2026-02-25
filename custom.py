"""
CustomSignalEngine — combines all indicators into a unified signal score.
Outputs a composite rating from -1.0 (strong sell) to +1.0 (strong buy).
"""

from __future__ import annotations

import pandas as pd
from dataclasses import dataclass, field
from typing import Optional

from .rsi       import RSIIndicator, RSISignal
from .macd      import MACDIndicator, MACDSignal
from .bb        import BollingerBands, BBSignal
from .supertrend import SuperTrend, STSignal
from .vwap      import VWAPIndicator, VWAPSignal


@dataclass
class CompositeSignal:
    score:        float           # -1.0 to +1.0
    rating:       str             # STRONG BUY / BUY / NEUTRAL / SELL / STRONG SELL
    rsi_signal:   str
    macd_signal:  str
    bb_signal:    str
    st_signal:    str
    vwap_signal:  str
    components:   dict[str, float] = field(default_factory=dict)


_WEIGHTS = {
    "rsi":  0.20,
    "macd": 0.25,
    "bb":   0.15,
    "st":   0.25,
    "vwap": 0.15,
}

_RSI_SCORES = {
    RSISignal.OVERSOLD:           +1.0,
    RSISignal.BULLISH_DIVERGENCE: +0.8,
    RSISignal.NEUTRAL:             0.0,
    RSISignal.BEARISH_DIVERGENCE: -0.8,
    RSISignal.OVERBOUGHT:         -1.0,
}
_MACD_SCORES = {
    MACDSignal.BULLISH_CROSS: +1.0,
    MACDSignal.ZERO_CROSS_UP: +0.8,
    MACDSignal.MOMENTUM_UP:   +0.4,
    MACDSignal.NEUTRAL:        0.0,
    MACDSignal.MOMENTUM_DOWN: -0.4,
    MACDSignal.ZERO_CROSS_DN: -0.8,
    MACDSignal.BEARISH_CROSS: -1.0,
}
_BB_SCORES = {
    BBSignal.LOWER_BREAK:  +1.0,
    BBSignal.LOWER_TOUCH:  +0.6,
    BBSignal.SQUEEZE:       0.0,
    BBSignal.NEUTRAL:       0.0,
    BBSignal.EXPANSION:     0.0,
    BBSignal.UPPER_TOUCH:  -0.6,
    BBSignal.UPPER_BREAK:  -1.0,
}
_ST_SCORES = {
    STSignal.BUY_SIGNAL:  +1.0,
    STSignal.BULLISH:     +0.7,
    STSignal.BEARISH:     -0.7,
    STSignal.SELL_SIGNAL: -1.0,
}
_VWAP_SCORES = {
    VWAPSignal.CROSS_UP:    +1.0,
    VWAPSignal.AT_2SD_DOWN: +0.8,
    VWAPSignal.AT_1SD_DOWN: +0.4,
    VWAPSignal.ABOVE_VWAP:  +0.2,
    VWAPSignal.BELOW_VWAP:  -0.2,
    VWAPSignal.AT_1SD_UP:   -0.4,
    VWAPSignal.AT_2SD_UP:   -0.8,
    VWAPSignal.CROSS_DOWN:  -1.0,
}


def _rating(score: float) -> str:
    if score >= 0.6:  return "STRONG BUY"
    if score >= 0.2:  return "BUY"
    if score >= -0.2: return "NEUTRAL"
    if score >= -0.6: return "SELL"
    return "STRONG SELL"


class CustomSignalEngine:
    def __init__(self) -> None:
        self.rsi  = RSIIndicator()
        self.macd = MACDIndicator()
        self.bb   = BollingerBands()
        self.st   = SuperTrend()
        self.vwap = VWAPIndicator()

    def run(
        self,
        high:   pd.Series,
        low:    pd.Series,
        close:  pd.Series,
        volume: Optional[pd.Series] = None,
    ) -> CompositeSignal:
        rsi_r  = self.rsi.calculate(close)
        macd_r = self.macd.calculate(close)
        bb_r   = self.bb.calculate(close)
        st_r   = self.st.calculate(high, low, close)

        scores = {
            "rsi":  _RSI_SCORES.get(rsi_r.signal,   0.0),
            "macd": _MACD_SCORES.get(macd_r.event,  0.0),
            "bb":   _BB_SCORES.get(bb_r.signal,     0.0),
            "st":   _ST_SCORES.get(st_r.signal,     0.0),
        }

        if volume is not None and not volume.empty:
            vwap_r = self.vwap.calculate(high, low, close, volume)
            scores["vwap"] = _VWAP_SCORES.get(vwap_r.signal, 0.0)
            vwap_sig = vwap_r.signal.value
        else:
            scores["vwap"] = 0.0
            vwap_sig = "n/a"

        composite = sum(scores[k] * _WEIGHTS[k] for k in scores)

        return CompositeSignal(
            score       = round(composite, 4),
            rating      = _rating(composite),
            rsi_signal  = rsi_r.signal.value,
            macd_signal = macd_r.event.value,
            bb_signal   = bb_r.signal.value,
            st_signal   = st_r.signal.value,
            vwap_signal = vwap_sig,
            components  = scores,
        )
