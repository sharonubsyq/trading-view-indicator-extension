"""Logging configuration."""

from __future__ import annotations

import logging
import sys


def setup_logging(level: str = "INFO") -> None:
    fmt = logging.Formatter(
        fmt     = "%(asctime)s [%(levelname)-8s] %(name)s: %(message)s",
        datefmt = "%Y-%m-%d %H:%M:%S",
    )
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(fmt)

    root = logging.getLogger()
    root.setLevel(getattr(logging, level.upper(), logging.INFO))
    root.handlers = [handler]

    # Silence noisy third-party loggers
    for noisy in ("urllib3", "yfinance", "peewee", "werkzeug"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
