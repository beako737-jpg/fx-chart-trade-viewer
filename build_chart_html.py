"""Inject chart_data.json into template.html to produce one self-contained,
offline-viewable HTML file.

Usage:
    python build_chart_html.py --data chart_data.json --template template.html --out chart.html
"""
import argparse
import json
from pathlib import Path


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data", required=True)
    ap.add_argument("--template", default="template.html")
    ap.add_argument("--out", default="chart.html")
    args = ap.parse_args()

    data_path = Path(args.data)
    if not data_path.exists():
        raise SystemExit(f"Data file not found: {args.data}")
    template_path = Path(args.template)
    if not template_path.exists():
        raise SystemExit(f"Template file not found: {args.template}")

    try:
        data_obj = json.loads(data_path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as e:
        raise SystemExit(f"Invalid JSON in {args.data}: {e}")
    if (
        not isinstance(data_obj, dict)
        or not isinstance(data_obj.get("candles"), list)
        or not isinstance(data_obj.get("trades"), list)
    ):
        raise SystemExit(
            f"{args.data}: expected a JSON object with \"candles\" and \"trades\" list "
            f"fields (the output of build_chart_data.py), got {type(data_obj).__name__}.\n"
            "Did you pass --data at candles_cache.json or another file instead of "
            "the merged chart_data.json?"
        )
    data_json = json.dumps(data_obj, ensure_ascii=False, separators=(",", ":"))

    template = template_path.read_text(encoding="utf-8")
    if "__DATA_JSON__" not in template:
        raise SystemExit(
            f"Template {args.template} has no __DATA_JSON__ placeholder "
            "— did you pass the wrong --template file?"
        )
    final_html = template.replace("__DATA_JSON__", data_json)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(final_html, encoding="utf-8")
    print(f"written: {args.out} ({len(final_html)} chars)")


if __name__ == "__main__":
    main()
