import json
import sys

import pytest

import fetch_daily_candles as fdc


class FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def json(self):
        return self._payload


def test_fetch_daily_candles_sorts_by_datetime(monkeypatch):
    payload = {
        "status": "ok",
        "values": [
            {"datetime": "2026-06-02", "open": "1", "high": "2", "low": "0.5", "close": "1.5"},
            {"datetime": "2026-06-01", "open": "1", "high": "2", "low": "0.5", "close": "1.5"},
        ],
    }

    def fake_get(url, params, timeout):
        return FakeResponse(payload)

    monkeypatch.setattr(fdc.requests, "get", fake_get)

    result = fdc.fetch_daily_candles("USD/JPY", "key", "2026-06-01", "2026-06-02")

    assert [c["datetime"] for c in result] == ["2026-06-01", "2026-06-02"]


def test_fetch_daily_candles_raises_on_error_status(monkeypatch):
    payload = {"status": "error", "message": "invalid api key"}

    def fake_get(url, params, timeout):
        return FakeResponse(payload)

    monkeypatch.setattr(fdc.requests, "get", fake_get)

    with pytest.raises(SystemExit):
        fdc.fetch_daily_candles("USD/JPY", "bad-key", "2026-06-01", "2026-06-02")


def test_parse_date_accepts_valid_date():
    assert fdc.parse_date("start", "2026-06-01") == "2026-06-01"


def test_parse_date_rejects_malformed_date():
    with pytest.raises(SystemExit, match="--start must be in YYYY-MM-DD format"):
        fdc.parse_date("start", "2026/06/01")


def test_main_creates_missing_output_directory(tmp_path, monkeypatch):
    payload = {
        "status": "ok",
        "values": [
            {"datetime": "2026-06-01", "open": "1", "high": "2", "low": "0.5", "close": "1.5"},
        ],
    }

    def fake_get(url, params, timeout):
        return FakeResponse(payload)

    monkeypatch.setattr(fdc.requests, "get", fake_get)

    out_path = tmp_path / "nested" / "does" / "not" / "exist" / "candles_cache.json"

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "fetch_daily_candles.py",
            "--symbol",
            "USD/JPY",
            "--start",
            "2026-06-01",
            "--end",
            "2026-06-01",
            "--api-key",
            "key",
            "--out",
            str(out_path),
        ],
    )

    fdc.main()

    assert out_path.exists()
    written = json.loads(out_path.read_text(encoding="utf-8"))
    assert len(written) == 1


def test_main_falls_back_to_api_key_env_var(tmp_path, monkeypatch):
    payload = {
        "status": "ok",
        "values": [
            {"datetime": "2026-06-01", "open": "1", "high": "2", "low": "0.5", "close": "1.5"},
        ],
    }
    seen_params = {}

    def fake_get(url, params, timeout):
        seen_params.update(params)
        return FakeResponse(payload)

    monkeypatch.setattr(fdc.requests, "get", fake_get)
    monkeypatch.setenv("TWELVEDATA_API_KEY", "env-key")

    out_path = tmp_path / "candles_cache.json"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "fetch_daily_candles.py",
            "--symbol",
            "USD/JPY",
            "--start",
            "2026-06-01",
            "--end",
            "2026-06-01",
            "--out",
            str(out_path),
        ],
    )

    fdc.main()

    assert seen_params["apikey"] == "env-key"


def test_main_requires_api_key_from_flag_or_env(monkeypatch):
    monkeypatch.delenv("TWELVEDATA_API_KEY", raising=False)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "fetch_daily_candles.py",
            "--symbol",
            "USD/JPY",
            "--start",
            "2026-06-01",
            "--end",
            "2026-06-01",
        ],
    )

    with pytest.raises(SystemExit, match="No API key given"):
        fdc.main()
