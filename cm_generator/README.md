# ツイテル鑑定所 CM generator

ツイテル鑑定所の案内、毎日のワクワクメッセージ、占い師募集案内、画像、オリジナルBGMを組み合わせた縦型CMを生成します。断定的な占いではなく、前向きな広告メッセージを表示します。画像とBGMはローカルで合成するため、外部の著作権素材を同梱しません。

標準背景は`assets/cm_default_space.jpeg`です。CM画面では、既存の背景に加えて添付フォルダの画像12種類と大アルカナ画像25種類も選択できます。メッセージは10,000種類の組み合わせから日付をもとに毎日切り替わり、CM内では読みやすい3行に分けて表示します。同じ日付なら同じ文面を再生成できます。

BGMは`assets/cm_bgm_cc0.wav`を使用します。この音源は本プロジェクトで生成し、
CC0（著作権を主張しない、無償利用・改変・再配布可能）として公開しています。
外部サイトから音源を自動取得しません。

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

## PCで使う

```bash
python3 cm_generator/local_server.py
```

ブラウザで `http://127.0.0.1:8000/#cm-maker` を開き、背景を選んで「CMを生成」を押します。
ページとAPIは同じPCから配信されるため、別の接続先を入力する必要はありません。

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
