import json
import sys

import build_chart_html as bch


def test_main_injects_data_json_into_template(tmp_path, monkeypatch):
    data_obj = {"candles": [{"date": "2026-06-01", "open": 1.0}], "trades": []}
    data_path = tmp_path / "data.json"
    data_path.write_text(json.dumps(data_obj), encoding="utf-8")

    template_path = tmp_path / "template.html"
    template_path.write_text("<html><script>var DATA=__DATA_JSON__;</script></html>", encoding="utf-8")

    out_path = tmp_path / "chart.html"

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "build_chart_html.py",
            "--data",
            str(data_path),
            "--template",
            str(template_path),
            "--out",
            str(out_path),
        ],
    )

    bch.main()

    output = out_path.read_text(encoding="utf-8")
    assert "__DATA_JSON__" not in output
    assert json.dumps(data_obj, ensure_ascii=False, separators=(",", ":")) in output
