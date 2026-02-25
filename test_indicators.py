"""Unit tests for indicator calculations."""

import numpy as np
import pandas as pd
import pytest
from src.indicators.rsi     import RSIIndicator, RSISignal
from src.indicators.macd    import MACDIndicator, MACDSignal
from src.indicators.bb      import BollingerBands, BBSignal
from src.indicators.supertrend import SuperTrend
from src.indicators.custom  import CustomSignalEngine


def make_price_series(n: int = 100, seed: int = 42) -> pd.Series:
    rng     = np.random.default_rng(seed)
    returns = rng.normal(0.0002, 0.015, n)
    prices  = 100.0 * np.exp(np.cumsum(returns))
    return pd.Series(prices, name="close")


def make_ohlcv(n: int = 100, seed: int = 42) -> pd.DataFrame:
    close  = make_price_series(n, seed)
    noise  = np.abs(np.random.default_rng(seed).normal(0, 0.01, n))
    return pd.DataFrame({
        "open":   close * 0.999,
        "high":   close * (1 + noise),
        "low":    close * (1 - noise),
        "close":  close,
        "volume": np.random.default_rng(seed).integers(1_000_000, 5_000_000, n).astype(float),
    })


class TestRSI:
    def test_values_in_range(self):
        rsi = RSIIndicator().calculate(make_price_series())
        valid = rsi.values.dropna()
        assert (valid >= 0).all() and (valid <= 100).all()

    def test_overbought_signal(self):
        # Series that trends strongly up should produce overbought
        close = pd.Series(np.linspace(100, 200, 200))
        rsi   = RSIIndicator().calculate(close)
        assert rsi.signal == RSISignal.OVERBOUGHT

    def test_oversold_signal(self):
        close = pd.Series(np.linspace(200, 50, 200))
        rsi   = RSIIndicator().calculate(close)
        assert rsi.signal == RSISignal.OVERSOLD

    def test_last_matches_series(self):
        close = make_price_series()
        rsi   = RSIIndicator().calculate(close)
        assert rsi.last == pytest.approx(float(rsi.values.iloc[-1]), abs=1e-6)


class TestMACD:
    def test_series_lengths_match(self):
        close = make_price_series()
        r     = MACDIndicator().calculate(close)
        assert len(r.macd) == len(r.signal) == len(r.histogram) == len(close)

    def test_histogram_is_macd_minus_signal(self):
        close = make_price_series()
        r     = MACDIndicator().calculate(close)
        np.testing.assert_allclose(r.histogram, r.macd - r.signal, atol=1e-10)


class TestBollingerBands:
    def test_close_within_bands_mostly(self):
        ohlcv  = make_ohlcv()
        bb     = BollingerBands().calculate(ohlcv["close"])
        inside = ((ohlcv["close"] >= bb.lower) & (ohlcv["close"] <= bb.upper)).sum()
        assert inside / len(ohlcv) >= 0.90   # >90% of bars inside 2σ

    def test_bandwidth_positive(self):
        bb = BollingerBands().calculate(make_price_series())
        assert (bb.bandwidth.dropna() >= 0).all()


class TestSuperTrend:
    def test_direction_is_binary(self):
        df = make_ohlcv()
        st = SuperTrend().calculate(df["high"], df["low"], df["close"])
        assert set(st.direction.dropna().unique()).issubset({1.0, -1.0})

    def test_strength_in_range(self):
        df = make_ohlcv()
        st = SuperTrend().calculate(df["high"], df["low"], df["close"])
        assert 0.0 <= st.strength <= 1.0


class TestCustomSignalEngine:
    def test_score_in_range(self):
        df  = make_ohlcv()
        eng = CustomSignalEngine()
        sig = eng.run(df["high"], df["low"], df["close"], df["volume"])
        assert -1.0 <= sig.score <= 1.0

    def test_rating_is_valid(self):
        df  = make_ohlcv()
        eng = CustomSignalEngine()
        sig = eng.run(df["high"], df["low"], df["close"], df["volume"])
        assert sig.rating in {"STRONG BUY","BUY","NEUTRAL","SELL","STRONG SELL"}

    def test_no_volume_still_works(self):
        df  = make_ohlcv()
        eng = CustomSignalEngine()
        sig = eng.run(df["high"], df["low"], df["close"])   # no volume
        assert sig.rating is not None
