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

    data_obj = json.loads(Path(args.data).read_text(encoding="utf-8-sig"))
    data_json = json.dumps(data_obj, ensure_ascii=False, separators=(",", ":"))

    template = Path(args.template).read_text(encoding="utf-8")
    final_html = template.replace("__DATA_JSON__", data_json)

    Path(args.out).write_text(final_html, encoding="utf-8")
    print(f"written: {args.out} ({len(final_html)} chars)")


if __name__ == "__main__":
    main()
