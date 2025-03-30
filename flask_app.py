# 必要なライブラリをインポート
from flask import Flask, request, abort       # Flask：Webアプリケーションを作成するためのフレームワーク
from linebot import LineBotApi, WebhookHandler    # LINE APIを扱うライブラリ
from linebot.exceptions import InvalidSignatureError, LineBotApiError  # エラー処理用の例外
from linebot.models import MessageEvent, TextMessage, TextSendMessage    # LINEメッセージ関連のモデル
import openai                                     # ChatGPT APIを利用するためのライブラリ
import os                                         # 環境変数を扱うためのライブラリ
import threading                                  # 非同期処理（スレッド）用のライブラリ

# Flaskアプリケーションのインスタンスを作成
app = Flask(__name__)

# 環境変数から各種シークレットやAPIキーを取得
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# LINE APIクライアントの初期化
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# OpenAI APIキーを設定（openaiライブラリでの認証に使用）
openai.api_key = OPENAI_API_KEY

# LINEからのWebhookリクエストを受け取るエンドポイント
@app.route("/webhook", methods=["POST"])
def webhook():
    # リクエストヘッダーからLINEの署名を取得
    signature = request.headers.get("X-Line-Signature")
    # リクエストボディ（送られてきたデータ）をテキストとして取得
    body = request.get_data(as_text=True)
    try:
        # 署名とボディを使用してLINEのイベントを処理
        handler.handle(body, signature)
    except InvalidSignatureError:
        # 署名が無効な場合は400エラーを返す
        abort(400)
    # 正常に処理できたら「OK」を返す
    return 'OK'

# LINEからテキストメッセージが送られたときの処理
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    # ユーザーが送信したメッセージとユーザーIDを取得
    user_text = event.message.text
    user_id = event.source.user_id

    # ChatGPT APIの問い合わせ処理を別スレッドで実行（非同期処理）
    threading.Thread(target=reply_gpt, args=(user_text, user_id)).start()

# ChatGPT APIに問い合わせ、返信メッセージを生成してLINEに送信する関数
def reply_gpt(user_text, user_id):
    # ChatGPT APIを呼び出して、ユーザーのメッセージに対する返信を生成
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",  # 使用するモデル名
        messages=[{"role": "user", "content": user_text}],
    )
    # 生成された返信テキストを取得
    reply = response.choices[0].message.content

    try:
        # 生成した返信をLINEのpushメッセージで送信
        line_bot_api.push_message(user_id, TextSendMessage(text=reply))
    except LineBotApiError as e:
        # LINE APIでエラーが発生した場合はエラーメッセージを表示
        print(f"LINE APIエラー: {e}")

# Renderなどのクラウドホスティングサービスでは、環境変数PORTが設定されるためそれを利用
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))  # PORTがなければ8000をデフォルトに
    app.run(host="0.0.0.0", port=port)