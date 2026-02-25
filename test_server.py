"""Tests for the Flask webhook server."""

import json
import pytest
from src.server     import create_app
from src.utils      import DataFetcher


@pytest.fixture
def client():
    fetcher = DataFetcher(use_synthetic=True)
    app     = create_app(fetcher=fetcher)
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json["status"] == "ok"


def test_webhook_valid_alert(client):
    payload = json.dumps({
        "ticker":   "AAPL",
        "exchange": "NASDAQ",
        "price":    180.5,
        "action":   "buy",
        "interval": "1h",
    })
    r = client.post("/webhook", data=payload, content_type="application/json")
    assert r.status_code == 200
    data = r.json
    assert data["ticker"] == "AAPL"
    assert data["rating"] in {"STRONG BUY","BUY","NEUTRAL","SELL","STRONG SELL"}


def test_webhook_missing_fields(client):
    payload = json.dumps({"ticker": "AAPL"})   # no price
    r = client.post("/webhook", data=payload, content_type="application/json")
    assert r.status_code == 400


def test_webhook_invalid_json(client):
    r = client.post("/webhook", data=b"not json", content_type="application/json")
    assert r.status_code == 400


def test_signal_endpoint(client):
    r = client.get("/signal/AAPL?interval=1h")
    assert r.status_code == 200
    data = r.json
    assert "rating" in data
    assert "score"  in data
