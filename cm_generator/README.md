# ツイテル鑑定所 CM generator

毎日の金運・健康運メッセージと、流体・数理波動をモチーフにした抽象画を組み合わせた縦型CMを生成します。画像とBGMはローカルで合成するため、外部の著作権素材を同梱しません。

## 安全な運用方針

- 生成は自動化するが、SNS投稿は自動化しない
- 生成されたアセットは `generated/` に出力し、GitHub Actions の Artifact としてレビュー対象にする
- 人間が画像・メッセージ・音声を確認してから、手動で投稿する
- 公開前に必ず文言と画像の最終確認を行う

## 実行

```bash
cd cm_generator
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python generate_cm.py --output-dir ../generated
```

`generated/` にPNG（抽象画）とWAV（合成BGM）が作成されます。FFmpegがインストール済みなら、同じ場所に12秒の縦型MP4も作成されます。

日付を固定すると同じ日の投稿候補を再生成できます。

```bash
python generate_cm.py --date 2026-12-01 --output-dir ../generated
```

## 告知文の例

> ツイテル鑑定所｜12月オープン予定。オープン前から個人鑑定を承っています。金運・健康運を中心に、毎日のメッセージをお届けします。

この文言は「候補」であり、公開前に人による最終確認を必須としてください。

占いは娯楽・生活のヒントとして利用し、健康や金銭に関する重要な判断は専門家へ相談してください。
