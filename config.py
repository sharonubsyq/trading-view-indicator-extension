"""
Configuration — reads from .env via python-dotenv.
All settings can be overridden by environment variables.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

_ENV = Path(__file__).parent / ".env"
load_dotenv(_ENV, override=False)


class Config:
    # ── Server ────────────────────────────────────────────────────────────────
    HOST:    str = os.getenv("HOST",    "0.0.0.0")
    PORT:    int = int(os.getenv("PORT", "5000"))
    DEBUG:   bool = os.getenv("DEBUG", "false").lower() == "true"

    # ── Security ──────────────────────────────────────────────────────────────
    WEBHOOK_SECRET: str = os.getenv("WEBHOOK_SECRET", "")   # Set to secure random string in prod

    # ── Notifications ─────────────────────────────────────────────────────────
    TELEGRAM_TOKEN:   str = os.getenv("TELEGRAM_TOKEN",   "")
    TELEGRAM_CHAT_ID: str = os.getenv("TELEGRAM_CHAT_ID", "")
    SLACK_WEBHOOK:    str = os.getenv("SLACK_WEBHOOK",    "")
    DISCORD_WEBHOOK:  str = os.getenv("DISCORD_WEBHOOK",  "")

    # ── Data ──────────────────────────────────────────────────────────────────
    USE_SYNTHETIC:    bool = os.getenv("USE_SYNTHETIC", "false").lower() == "true"
    DEFAULT_INTERVAL: str  = os.getenv("DEFAULT_INTERVAL", "1h")

    # ── Indicator defaults ─────────────────────────────────────────────────────
    RSI_PERIOD:   int   = int(os.getenv("RSI_PERIOD",   "14"))
    RSI_OB:       float = float(os.getenv("RSI_OB",     "70"))
    RSI_OS:       float = float(os.getenv("RSI_OS",     "30"))
    BB_PERIOD:    int   = int(os.getenv("BB_PERIOD",    "20"))
    BB_STD:       float = float(os.getenv("BB_STD",     "2.0"))
    ST_PERIOD:    int   = int(os.getenv("ST_PERIOD",    "10"))
    ST_MULT:      float = float(os.getenv("ST_MULT",    "3.0"))

    # ── Logging ───────────────────────────────────────────────────────────────
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")


cfg = Config()
