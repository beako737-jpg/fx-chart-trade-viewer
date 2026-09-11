"""Fetch daily OHLC candles from Twelve Data's free API and cache them as JSON.

Usage:
    python fetch_daily_candles.py --symbol USD/JPY --start 2026-01-01 --end 2026-07-28 \
        --api-key YOUR_KEY --out candles_cache.json

Free plan limits (as of writing): 800 requests/day, 8 requests/minute.
This script makes exactly one request per run, so normal use never comes
close to the limit.
"""
import argparse
import json
from pathlib import Path

import requests


def fetch_daily_candles(symbol: str, api_key: str, start_date: str, end_date: str):
    url = "https://api.twelvedata.com/time_series"
    params = {
        "symbol": symbol,
        "interval": "1day",
        "start_date": start_date,
        "end_date": end_date,
        "apikey": api_key,
    }
    try:
        resp = requests.get(url, params=params, timeout=30)
    except requests.exceptions.RequestException as e:
        raise SystemExit(
            f"Could not reach Twelve Data (network error): {e}\n"
            "Check your internet connection and try again."
        )

    try:
        data = resp.json()
    except ValueError:
        raise SystemExit(
            f"Twelve Data returned a non-JSON response (HTTP {resp.status_code}).\n"
            "This usually means the API is down or a proxy/firewall intercepted the request."
        )

    if data.get("status") != "ok":
        message = data.get("message", data)
        raise SystemExit(f"Twelve Data API error: {message}")
    return sorted(data["values"], key=lambda c: c["datetime"])


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--symbol", required=True, help="e.g. USD/JPY")
    ap.add_argument("--start", required=True, help="YYYY-MM-DD")
    ap.add_argument("--end", required=True, help="YYYY-MM-DD")
    ap.add_argument("--api-key", required=True, help="Twelve Data API key (free tier works)")
    ap.add_argument("--out", default="candles_cache.json")
    args = ap.parse_args()

    raw = fetch_daily_candles(args.symbol, args.api_key, args.start, args.end)
    candles = [
        {
            "date": c["datetime"],
            "open": float(c["open"]),
            "high": float(c["high"]),
            "low": float(c["low"]),
            "close": float(c["close"]),
        }
        for c in raw
    ]
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(candles, f, ensure_ascii=False)
    print(f"{len(candles)} candles written to {args.out}")


if __name__ == "__main__":
    main()
