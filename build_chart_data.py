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
    candles_path = Path(path)
    if not candles_path.exists():
        raise SystemExit(f"Candles file not found: {path}")
    try:
        raw = json.loads(candles_path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as e:
        raise SystemExit(f"Invalid JSON in candles file {path}: {e}")
    candles = []
    for i, c in enumerate(raw):
        try:
            candles.append(
                {
                    "date": c["date"],
                    "open": float(c["open"]),
                    "high": float(c["high"]),
                    "low": float(c["low"]),
                    "close": float(c["close"]),
                }
            )
        except KeyError as e:
            raise SystemExit(f"{path}: candle {i} is missing required field {e}.\nCandle data: {c}")
        except (TypeError, ValueError) as e:
            raise SystemExit(f"{path}: candle {i} has a non-numeric OHLC value ({e}).\nCandle data: {c}")
    candles.sort(key=lambda c: c["date"])
    return candles


def load_mapping(path: str):
    mapping_path = Path(path)
    if not mapping_path.exists():
        raise SystemExit(f"Mapping file not found: {path}")
    try:
        return json.loads(mapping_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise SystemExit(f"Invalid JSON in mapping file {path}: {e}")


def load_trades(csv_path: str, symbol: str, mapping: dict):
    if not Path(csv_path).exists():
        raise SystemExit(f"CSV file not found: {csv_path}")
    trades = []
    seen_pairs = set()
    with open(csv_path, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []
        missing = [col for col in mapping.values() if col not in fieldnames]
        if missing:
            raise SystemExit(
                "CSV is missing expected column(s): "
                + ", ".join(missing)
                + f"\nColumns found in {csv_path}: "
                + ", ".join(fieldnames)
                + "\nIf your broker's export uses different column names, pass "
                "--mapping mapping.json to override them (see README)."
            )
        for row_num, row in enumerate(reader, start=2):
            pair = row[mapping["pair"]]
            seen_pairs.add(pair)
            if symbol and pair != symbol:
                continue
            dt = row[mapping["datetime"]]
            try:
                trade = {
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
            except ValueError as e:
                raise SystemExit(
                    f"{csv_path}: row {row_num}: could not parse a numeric column ({e}).\n"
                    f"Row data: {row}"
                )
            trades.append(trade)
    if symbol and not trades and seen_pairs:
        raise SystemExit(
            f"No trades matched --symbol '{symbol}' in {csv_path}.\n"
            "Pairs found in this file: "
            + ", ".join(sorted(seen_pairs))
            + "\nCheck for a typo, or omit --symbol to include all pairs."
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
        mapping.update(load_mapping(args.mapping))

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
