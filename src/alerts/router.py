"""
AlertRouter — fan out AlertResult notifications to configured channels:
  • Telegram bot
  • Slack webhook
  • Discord webhook
  • Custom HTTP callback
  • Console / log (always active)
"""

from __future__ import annotations

import json
import logging
import urllib.request
import urllib.parse
from typing import Callable

from .handler import AlertResult

log = logging.getLogger(__name__)


class AlertRouter:
    def __init__(self) -> None:
        self._channels: list[Callable[[AlertResult], None]] = [self._log_channel]

    # ── Register channels ─────────────────────────────────────────────────────
    def add_telegram(self, token: str, chat_id: str) -> None:
        def _send(r: AlertResult) -> None:
            msg = self._format_message(r)
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            self._post_json(url, {"chat_id": chat_id, "text": msg, "parse_mode": "HTML"})
        self._channels.append(_send)
        log.info("Telegram channel registered (chat_id=%s)", chat_id)

    def add_slack(self, webhook_url: str) -> None:
        def _send(r: AlertResult) -> None:
            self._post_json(webhook_url, {"text": self._format_message(r)})
        self._channels.append(_send)
        log.info("Slack channel registered")

    def add_discord(self, webhook_url: str) -> None:
        def _send(r: AlertResult) -> None:
            self._post_json(webhook_url, {"content": self._format_message(r)})
        self._channels.append(_send)
        log.info("Discord channel registered")

    def add_custom(self, fn: Callable[[AlertResult], None]) -> None:
        self._channels.append(fn)

    # ── Dispatch ──────────────────────────────────────────────────────────────
    def dispatch(self, result: AlertResult) -> None:
        for ch in self._channels:
            try:
                ch(result)
            except Exception as exc:
                log.error("Channel dispatch error: %s", exc)

    # ── Formatters ────────────────────────────────────────────────────────────
    @staticmethod
    def _format_message(r: AlertResult) -> str:
        a = r.alert
        c = r.composite
        emoji = {"STRONG BUY":"🟢","BUY":"🔵","NEUTRAL":"⚪","SELL":"🟠","STRONG SELL":"🔴"}.get(c.rating,"⚪")
        return (
            f"{emoji} <b>Kalshi-Claw Alert</b>\n"
            f"Ticker:  <b>{a.ticker}</b>  ({a.exchange})\n"
            f"Action:  {a.action.upper()}\n"
            f"Price:   {a.price:,.4f}\n"
            f"Rating:  <b>{c.rating}</b>  (score {c.score:+.3f})\n"
            f"RSI:     {c.rsi_signal}\n"
            f"MACD:    {c.macd_signal}\n"
            f"ST:      {c.st_signal}\n"
            f"Latency: {r.latency_ms:.0f}ms"
        )

    @staticmethod
    def _log_channel(r: AlertResult) -> None:
        log.info(
            "ALERT RESULT | %s | %s | score=%+.3f",
            r.alert.ticker, r.composite.rating, r.composite.score,
        )

    @staticmethod
    def _post_json(url: str, payload: dict) -> None:
        data  = json.dumps(payload).encode()
        req   = urllib.request.Request(
            url, data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            if resp.status >= 400:
                log.warning("Notification HTTP %d for %s", resp.status, url)
