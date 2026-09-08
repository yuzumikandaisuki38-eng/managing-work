# ツイテル鑑定所 CM generator

ツイテル鑑定所の案内、画像、オリジナルBGMを組み合わせた縦型CMを生成します。毎日の占いメッセージは使用しません。画像とBGMはローカルで合成するため、外部の著作権素材を同梱しません。

標準背景は`assets/cm_default_space.jpeg`です。CM画面では、添付された7種類の画像から選択できます。

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

`generated/` にPNG、WAV、12秒の縦型MP4が作成されます。CMには「ツイテル鑑定所」
「心と運気に寄り添う個人鑑定」「12月オープン予定｜個人鑑定受付中」を表示します。

```bash
python generate_cm.py --date 2026-12-01 --output-dir ../generated
```

## ブラウザから生成

ローカル環境でページを開き、「CMを作る」欄の「CMを生成」ボタンを使えます。

```bash
cd /Users/hidemitogo/.copilot/repos/managing-work
python3 cm_generator/local_server.py
```

その後、`http://127.0.0.1:8000/#cm-maker` を開いてください。このサーバーは
`127.0.0.1` からのみ接続でき、SNSへの投稿機能は持ちません。生成後は必ず人が
画像・音声・文面を確認してから手動で公開してください。

## 携帯から使う構成（PCサーバー方式）

携帯電話から使う場合は、PCをCM生成サーバーにします。まずPCで次のように起動します。

```bash
python3 cm_generator/local_server.py --host 0.0.0.0 --port 8000
```

PCのIPアドレスを確認し、携帯とPCを同じWi-Fiに接続します。携帯のブラウザで
`http://PCのIPアドレス:8000/#cm-maker` を開いてください。
例えばPCのIPが `192.168.1.10` なら、次のURLです。

```text
http://192.168.1.10:8000/#cm-maker
```

CM画面の「接続確認」が成功してから生成してください。GitHub Pagesを携帯で開いたまま
ではなく、必ずPCのIPアドレスから開くのがポイントです。

より簡単な方法は、携帯のブラウザで `http://192.168.1.10:8000/#cm-maker` を
直接開くことです。この場合、ページとAPIが同じPCから配信されるため、API URLを
入力しなくてもPC側へ接続します。GitHub Pages（`https://`）を表示したまま
`http://`のPC APIへ接続すると、ブラウザの混在コンテンツ制限で失敗する場合があります。

Pythonから呼び出す場合も、HTMLがJSONとして扱われる問題を検出できます。

```bash
python3 cm_generator/api_client.py --date 2026-12-01
```

APIの応答は、HTTPステータス、`Content-Type`、JSONオブジェクト形式の順に検証されます。
HTMLやログインページが返った場合は、JSON解析を続行せず、URLまたは
`local_server.py` の起動状態をエラーとして表示します。

## 告知文の例

> ツイテル鑑定所｜12月オープン予定。オープン前から個人鑑定を承っています。

この文言は「候補」であり、公開前に人による最終確認を必須としてください。

占いは娯楽・生活のヒントとして利用し、健康や金銭に関する重要な判断は専門家へ相談してください。
