"""
AlertParser — parse and validate TradingView webhook alert payloads.

TradingView sends JSON to your webhook URL when an alert fires.
Configure your alert message body in Pine Script like:

  alertcondition(condition, title="My Alert",
    message='{"ticker":"{{ticker}}","action":"{{strategy.order.action}}","price":{{close}}}')
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

log = logging.getLogger(__name__)

# Supported TradingView template variables
TV_VARIABLES = {
    "{{ticker}}",    "{{exchange}}",   "{{close}}",
    "{{open}}",      "{{high}}",       "{{low}}",
    "{{volume}}",    "{{time}}",       "{{timenow}}",
    "{{interval}}",  "{{plot_0}}",     "{{strategy.order.action}}",
    "{{strategy.order.price}}", "{{strategy.position_size}}",
}


@dataclass
class ParsedAlert:
    raw:        dict[str, Any]
    ticker:     str
    exchange:   str
    action:     str           # "buy" | "sell" | "close" | "custom"
    price:      float
    interval:   str
    timestamp:  datetime
    extra:      dict[str, Any] = field(default_factory=dict)
    valid:      bool = True
    error:      Optional[str] = None


class AlertParser:
    """Parse raw HTTP body from TradingView into a structured ParsedAlert."""

    REQUIRED = {"ticker", "price"}

    def parse(self, body: bytes | str) -> ParsedAlert:
        try:
            if isinstance(body, bytes):
                body = body.decode("utf-8", errors="replace")
            data = json.loads(body)
        except json.JSONDecodeError as exc:
            log.warning("Alert JSON parse error: %s | body=%r", exc, body[:200])
            return self._invalid(str(exc), {})

        missing = self.REQUIRED - set(data.keys())
        if missing:
            return self._invalid(f"Missing required fields: {missing}", data)

        try:
            return ParsedAlert(
                raw      = data,
                ticker   = str(data.get("ticker", "UNKNOWN")).upper(),
                exchange = str(data.get("exchange", "")).upper(),
                action   = str(data.get("action",   "custom")).lower(),
                price    = float(data.get("price",  0.0)),
                interval = str(data.get("interval", "unknown")),
                timestamp = datetime.utcnow(),
                extra    = {
                    k: v for k, v in data.items()
                    if k not in {"ticker","exchange","action","price","interval"}
                },
            )
        except (TypeError, ValueError) as exc:
            return self._invalid(str(exc), data)

    @staticmethod
    def _invalid(error: str, raw: dict) -> ParsedAlert:
        return ParsedAlert(
            raw=raw, ticker="", exchange="", action="",
            price=0.0, interval="", timestamp=datetime.utcnow(),
            valid=False, error=error,
        )
