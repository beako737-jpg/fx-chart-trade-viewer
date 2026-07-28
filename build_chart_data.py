"""Merge a broker trade-history CSV with a daily-candle JSON cache into one
chart-ready JSON file.

Usage:
    python build_chart_data.py --csv trades.csv --candles candles_cache.json \
        --symbol USD/JPY --out chart_data.json

The CSV column names default to a common Japanese FX broker export format
(datetime/pair/side/qty/entry/exit/pnl/pips in Japanese headers). Pass
--mapping to point at a JSON file overriding any of those column names for
brokers that use different headers.
"""
import argparse
import csv
import json
from pathlib import Path

DEFAULT_MAPPING = {
    "id": "約定番号",
    "datetime": "日時",
    "pair": "通貨ペア",
    "direction": "売買",
    "qty": "数量",
    "entry": "約定価格",
    "exit": "決済価格",
    "pnl": "損益",
    "pips": "pips",
}


def load_candles(path: str):
    with open(path, encoding="utf-8-sig") as f:
        raw = json.load(f)
    return sorted(
        [
            {
                "date": c["date"],
                "open": float(c["open"]),
                "high": float(c["high"]),
                "low": float(c["low"]),
                "close": float(c["close"]),
            }
            for c in raw
        ],
        key=lambda c: c["date"],
    )


def load_trades(csv_path: str, symbol: str, mapping: dict):
    trades = []
    with open(csv_path, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if symbol and row[mapping["pair"]] != symbol:
                continue
            dt = row[mapping["datetime"]]
            trades.append(
                {
                    "id": row[mapping["id"]],
                    "datetime": dt,
                    "date": dt.split(" ")[0],
                    "direction": row[mapping["direction"]],
                    "qty": float(row[mapping["qty"]]),
                    "entry": float(row[mapping["entry"]]),
                    "exit": float(row[mapping["exit"]]),
                    "pnl": float(row[mapping["pnl"]]),
                    "pips": float(row[mapping["pips"]]),
                }
            )
    trades.sort(key=lambda t: t["datetime"])
    return trades


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--csv", required=True, help="Broker trade history CSV")
    ap.add_argument("--candles", required=True, help="Daily OHLC JSON cache")
    ap.add_argument("--symbol", default="", help="Filter to one pair, e.g. USD/JPY (blank = no filter)")
    ap.add_argument("--mapping", default="", help="Optional JSON file overriding column-name mapping")
    ap.add_argument("--out", default="chart_data.json")
    args = ap.parse_args()

    mapping = dict(DEFAULT_MAPPING)
    if args.mapping:
        mapping.update(json.loads(Path(args.mapping).read_text(encoding="utf-8")))

    candles = load_candles(args.candles)
    trades = load_trades(args.csv, args.symbol, mapping)

    out = {"candles": candles, "trades": trades}
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False)

    print(f"candles: {len(candles)}, trades: {len(trades)}")
    if trades:
        print(f"date range trades: {trades[0]['date']} - {trades[-1]['date']}")
    print(f"written to {args.out}")


if __name__ == "__main__":
    main()
