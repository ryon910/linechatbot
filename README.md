## LINE API、ChatGPT API、Flaskを使ったAIチャットボットの作り方
LINEメッセージを送ると、ChatGPTがレスポンスを生成して返してくれるLINE AIチャットボットを作ります．
メッセージを受け取ってレスポンスを生成しLINEに戻すためには、FlaskというPythonのフレームワークを
使用して、それをデプロイする必要があります。今回はRenderというサーバーにデプロイしていきます。
具体的な手順は以下です。LINE API, Flask, Renderについて調べながら取り組んでみてください。
※STEP3以後にFlaskを触ることになると思います。

---

## ① LINE公式アカウント準備
- LINE公式アカウントを作成する。
  [https://developers.line.biz/ja/]

- 「Messaging API」のチャネルを作り、以下をメモする。
```
LINE_CHANNEL_SECRET
LINE_CHANNEL_ACCESS_TOKEN
```
- WebhookのURLは後ほど設定する。

---

## ② OpenAI APIキーを取得
- [https://platform.openai.com/api-keys]
- APIキーを作成してメモする。
```
OPENAI_API_KEY
```
---

## ③ Pythonコード（Flaskアプリ本体）

`app.py`を用意：

### 必要なライブラリをrequirements.txtとして用意

```
flask
line-bot-sdk
openai
gunicorn
```

---

## ④ Renderでのデプロイ設定

Renderで新規Webサービスを作成する際の設定：

- **Environment**: Python
- **Build Command**:
```
pip install -r requirements.txt
```
- **Start Command**:
```
gunicorn app:app
```

- 以下の環境変数を設定する。
```
LINE_CHANNEL_SECRET
LINE_CHANNEL_ACCESS_TOKEN
OPENAI_API_KEY
```

- Renderのデプロイ後、以下のようにLINEのWebhook URLを設定する。
```
https://（あなたのRenderアプリURL）/webhook
```
---
## 動作確認
LINE公式アカウントにメッセージを送ると、ChatGPTによる自動応答が届く。
---

## 参考ドキュメント
- [LINE Developers公式](https://developers.line.biz/ja/)
- [OpenAI APIリファレンス](https://platform.openai.com/docs/introduction)
- [Render公式ドキュメント](https://render.com/docs)