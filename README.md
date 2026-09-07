# fx-chart-trade-viewer

[![CI](https://github.com/beako737-jpg/fx-chart-trade-viewer/actions/workflows/ci.yml/badge.svg)](https://github.com/beako737-jpg/fx-chart-trade-viewer/actions/workflows/ci.yml)

証券会社の約定履歴CSVと、無料の価格データAPI（[Twelve Data](https://twelvedata.com/)）の日足チャートを重ね合わせて、**1つのオフラインHTMLファイル**として可視化するツールです。有料の売買分析ツールを使わなくても、自分のエントリー・決済タイミングをチャート上で振り返れます。

- 依存ライブラリなしの自己完結HTML（`requests` 以外は標準ライブラリのみ）
- 価格データの取得はキャッシュ済みJSONを使い回すので、無料APIの上限（800回/日）を気にしなくていい設計
- 証券会社ごとにCSVの列名が違っても `--mapping` で吸収できる

## クイックスタート（サンプルデータ）

```bash
pip install -r requirements.txt  # fetch_daily_candles.py を使う場合のみ必要
python build_chart_data.py --csv sample_data/sample_trades.csv --candles sample_data/sample_candles.json --symbol "USD/JPY" --out sample_data/sample_chart_data.json
python build_chart_html.py --data sample_data/sample_chart_data.json --template template.html --out demo.html
```

`demo.html` をブラウザで開くと、日足チャートに売買マーカー（利益は緑、損失は赤）が重なって表示されます。ホバーでその日の取引明細も見られます。

Python を実行せずにまず見た目を確認したい場合は、リポジトリに同梱済みの [`sample_demo.html`](sample_demo.html) をブラウザで直接開いても、同じ表示を確認できます。

## 自分のデータで使う

1. 証券会社から約定履歴CSVをダウンロード
2. `python fetch_daily_candles.py --symbol USD/JPY --start 2026-01-01 --end 2026-07-28 --api-key YOUR_TWELVEDATA_KEY --out candles_cache.json`（[Twelve Data](https://twelvedata.com/)で無料キー取得）
3. `python build_chart_data.py --csv your_trades.csv --candles candles_cache.json --out chart_data.json`
   - デフォルトの列名は `約定番号 / 日時 / 通貨ペア / 売買 / 数量 / 約定価格 / 決済価格 / 損益 / pips`。違う場合は `--mapping mapping.json` で上書き可能。
4. `python build_chart_html.py --data chart_data.json --out my_chart.html`

## 開発（テストの実行）

```bash
pip install requests pytest
pytest -q
```

`push` / PR 作成時は GitHub Actions が同じテストを自動実行します（[`.github/workflows/ci.yml`](.github/workflows/ci.yml)）。

## ライセンス

MIT License（`LICENSE` 参照）

## 免責事項

このツールは取引記録の可視化を補助するもので、投資助言ではありません。価格データAPIの仕様・利用規約は変更される可能性があるため、利用前に提供元の最新情報をご確認ください。
