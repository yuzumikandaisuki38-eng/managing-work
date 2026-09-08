# ツイテル鑑定所 CM generator

毎日の金運・健康運メッセージと、流体・数理波動をモチーフにした抽象画を組み合わせた縦型CMを生成します。画像とBGMはローカルで合成するため、外部の著作権素材を同梱しません。12月のオープン前から個人鑑定を受け付けている告知文は、生成された画像をSNS投稿の説明文と組み合わせて利用してください。

## 実行

```bash
cd cm_generator
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python generate_cm.py --output-dir ../generated
```

`generated/` にPNG（抽象画）とWAV（合成BGM）が作成されます。FFmpegがインストール済みなら、同じ場所に12秒の縦型MP4も作成されます。

日付を固定すると同じ日の投稿を再生成できます。

```bash
python generate_cm.py --date 2026-12-01 --output-dir ../generated
```

## 告知文の例

> ツイテル鑑定所｜12月オープン予定。オープン前から個人鑑定を承っています。金運・健康運を中心に、毎日のメッセージをお届けします。

占いは娯楽・生活のヒントとして利用し、健康や金銭に関する重要な判断は専門家へ相談してください。
