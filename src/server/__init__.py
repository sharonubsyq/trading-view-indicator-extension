"""Flask webhook server for TradingView alerts."""
from .app import create_app

__all__ = ["create_app"]
