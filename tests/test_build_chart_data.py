import json

import pytest

import build_chart_data as bcd


def test_load_candles_sorts_and_converts_types(tmp_path):
    raw = [
        {"date": "2026-06-02", "open": "155.6", "high": "156.1", "low": "155.3", "close": "155.9"},
        {"date": "2026-06-01", "open": "155.2", "high": "155.8", "low": "154.9", "close": "155.6"},
    ]
    path = tmp_path / "candles.json"
    path.write_text(json.dumps(raw), encoding="utf-8")

    candles = bcd.load_candles(str(path))

    assert [c["date"] for c in candles] == ["2026-06-01", "2026-06-02"]
    assert candles[0]["open"] == 155.2
    assert isinstance(candles[0]["open"], float)


def test_load_candles_missing_file_gives_friendly_error(tmp_path):
    missing = tmp_path / "no_such_candles.json"

    with pytest.raises(SystemExit, match="Candles file not found"):
        bcd.load_candles(str(missing))


def test_load_candles_invalid_json_gives_friendly_error(tmp_path):
    path = tmp_path / "candles.json"
    path.write_text("{not valid json", encoding="utf-8")

    with pytest.raises(SystemExit, match="Invalid JSON in candles file"):
        bcd.load_candles(str(path))


def test_load_trades_missing_file_gives_friendly_error(tmp_path):
    missing = tmp_path / "no_such_trades.csv"

    with pytest.raises(SystemExit, match="CSV file not found"):
        bcd.load_trades(str(missing), "", bcd.DEFAULT_MAPPING)


def test_load_candles_reports_missing_field(tmp_path):
    raw = [{"date": "2026-06-01", "open": "155.2", "high": "155.8", "low": "154.9"}]
    path = tmp_path / "candles.json"
    path.write_text(json.dumps(raw), encoding="utf-8")

    with pytest.raises(SystemExit, match="missing required field 'close'"):
        bcd.load_candles(str(path))


def test_load_candles_reports_bad_numeric_value(tmp_path):
    raw = [{"date": "2026-06-01", "open": "N/A", "high": "155.8", "low": "154.9", "close": "155.6"}]
    path = tmp_path / "candles.json"
    path.write_text(json.dumps(raw), encoding="utf-8")

    with pytest.raises(SystemExit, match="candle 0"):
        bcd.load_candles(str(path))


def test_load_trades_filters_by_symbol_and_sorts(tmp_path):
    csv_text = (
        "約定番号,日時,通貨ペア,売買,数量,約定価格,決済価格,損益,pips\n"
        "S0002,2026-06-03 14:10:00,USD/JPY,売,10000,156.30,155.90,40.0,4.0\n"
        "S0001,2026-06-01 09:30:00,USD/JPY,買,10000,155.30,155.75,45.0,4.5\n"
        "S0003,2026-06-02 10:00:00,EUR/USD,買,10000,1.10,1.11,10.0,1.0\n"
    )
    path = tmp_path / "trades.csv"
    path.write_text(csv_text, encoding="utf-8")

    trades = bcd.load_trades(str(path), "USD/JPY", bcd.DEFAULT_MAPPING)

    assert [t["id"] for t in trades] == ["S0001", "S0002"]
    assert trades[0]["date"] == "2026-06-01"
    assert trades[0]["qty"] == 10000.0
    assert trades[0]["pnl"] == 45.0


def test_load_trades_no_symbol_filter_keeps_all_pairs(tmp_path):
    csv_text = (
        "約定番号,日時,通貨ペア,売買,数量,約定価格,決済価格,損益,pips\n"
        "S0001,2026-06-01 09:30:00,USD/JPY,買,10000,155.30,155.75,45.0,4.5\n"
        "S0002,2026-06-02 10:00:00,EUR/USD,買,10000,1.10,1.11,10.0,1.0\n"
    )
    path = tmp_path / "trades.csv"
    path.write_text(csv_text, encoding="utf-8")

    trades = bcd.load_trades(str(path), "", bcd.DEFAULT_MAPPING)

    assert len(trades) == 2


def test_load_trades_symbol_typo_lists_pairs_found(tmp_path):
    csv_text = (
        "約定番号,日時,通貨ペア,売買,数量,約定価格,決済価格,損益,pips\n"
        "S0001,2026-06-01 09:30:00,USD/JPY,買,10000,155.30,155.75,45.0,4.5\n"
        "S0002,2026-06-02 10:00:00,EUR/USD,買,10000,1.10,1.11,10.0,1.0\n"
    )
    path = tmp_path / "trades.csv"
    path.write_text(csv_text, encoding="utf-8")

    with pytest.raises(SystemExit, match="EUR/USD, USD/JPY"):
        bcd.load_trades(str(path), "USDJPY", bcd.DEFAULT_MAPPING)


def test_load_trades_custom_mapping(tmp_path):
    csv_text = "id,dt,pair,side,qty,entry,exit,pnl,pips\n" "T1,2026-06-01 09:00:00,USD/JPY,buy,1,155.0,155.5,5.0,5.0\n"
    path = tmp_path / "trades.csv"
    path.write_text(csv_text, encoding="utf-8")

    mapping = dict(bcd.DEFAULT_MAPPING)
    mapping.update(
        {
            "id": "id",
            "datetime": "dt",
            "pair": "pair",
            "direction": "side",
            "qty": "qty",
            "entry": "entry",
            "exit": "exit",
            "pnl": "pnl",
            "pips": "pips",
        }
    )

    trades = bcd.load_trades(str(path), "USD/JPY", mapping)

    assert len(trades) == 1
    assert trades[0]["id"] == "T1"


def test_load_mapping_missing_file_gives_friendly_error(tmp_path):
    missing = tmp_path / "no_such_mapping.json"

    with pytest.raises(SystemExit, match="Mapping file not found"):
        bcd.load_mapping(str(missing))


def test_load_mapping_invalid_json_gives_friendly_error(tmp_path):
    path = tmp_path / "mapping.json"
    path.write_text("{not valid json", encoding="utf-8")

    with pytest.raises(SystemExit, match="Invalid JSON in mapping file"):
        bcd.load_mapping(str(path))


def test_load_mapping_valid_file_returns_dict(tmp_path):
    path = tmp_path / "mapping.json"
    path.write_text(json.dumps({"id": "trade_id"}), encoding="utf-8")

    assert bcd.load_mapping(str(path)) == {"id": "trade_id"}


def test_load_trades_reports_row_number_on_bad_numeric_value(tmp_path):
    csv_text = (
        "約定番号,日時,通貨ペア,売買,数量,約定価格,決済価格,損益,pips\n"
        "S0001,2026-06-01 09:30:00,USD/JPY,買,10000,155.30,155.75,45.0,4.5\n"
        "S0002,2026-06-02 10:00:00,USD/JPY,買,N/A,156.30,155.90,40.0,4.0\n"
    )
    path = tmp_path / "trades.csv"
    path.write_text(csv_text, encoding="utf-8")

    with pytest.raises(SystemExit, match="row 3"):
        bcd.load_trades(str(path), "", bcd.DEFAULT_MAPPING)
