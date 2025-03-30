# 必要なライブラリをインポート
from flask import Flask, request, abort  # Flask：Webアプリケーションを作成するためのフレームワーク
from linebot import LineBotApi, WebhookHandler  # LINEのAPIを利用するためのライブラリ
from linebot.exceptions import InvalidSignatureError, LineBotApiError  # エラー処理用の例外
from linebot.models import MessageEvent, TextMessage, TextSendMessage  # LINEで扱うメッセージモデル
import openai  # OpenAIのAPIを利用するためのライブラリ
import os  # 環境変数を扱うためのライブラリ
import threading  # 非同期処理（スレッド）のためのライブラリ
from datetime import datetime  # 日時を扱うためのライブラリ

# Flaskアプリケーションのインスタンスを作成
app = Flask(__name__)

# 環境変数からAPIキーやシークレット情報を取得
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")             # LINEのチャネルシークレット
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")     # LINEのチャネルアクセストークン
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")                           # OpenAI APIキー

# LINEのAPIクライアントを初期化
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# OpenAIのクライアントを初期化
client = openai.OpenAI(api_key=OPENAI_API_KEY)

# /webhook URLにPOSTリクエストがあったときのエンドポイントを定義
@app.route("/webhook", methods=["POST"])
def webhook():
    # リクエストヘッダーからLINEの署名を取得
    signature = request.headers["X-Line-Signature"]
    # リクエストボディ（送信されたデータ）をテキスト形式で取得
    body = request.get_data(as_text=True)
    try:
        # 署名とボディを使って、LINEからのイベントを処理
        handler.handle(body, signature)
    except InvalidSignatureError:
        # 署名が無効な場合、400エラー（Bad Request）を返す
        abort(400)
    # 正常に処理が終了した場合は、'OK'を返す
    return 'OK'

# LINEからのテキストメッセージイベントを処理する関数を定義
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    # ユーザーが送信したテキストを取得
    user_text = event.message.text
    # ユーザーIDを取得（返信先の指定に使用）
    user_id = event.source.user_id

    # 非同期でOpenAIへの問い合わせ処理を実行するため、新しいスレッドを開始
    # これにより、LINEからの応答は即時に返し、後からプッシュメッセージで返信する
    threading.Thread(target=reply_gpt, args=(user_text, user_id)).start()

# ユーザーのテキストに対して、OpenAIのGPT-3.5-turboモデルで返信を生成する関数
def reply_gpt(user_text, user_id):
    # OpenAI APIを使用して、ユーザーからのメッセージを基に返信を生成
    res = client.chat.completions.create(
        model="gpt-3.5-turbo",  # 使用するGPTモデルの名前
        messages=[{"role": "user", "content": user_text}],  # ユーザーのメッセージを送信
    )
    # 生成された返信内容を取り出す
    reply = res.choices[0].message.content

    try:
        # LINEのpushメッセージを使い、生成された返信をユーザーに送信
        line_bot_api.push_message(user_id, TextSendMessage(reply))

        # 返信内容などの会話ログを "chat_log.txt" というファイルに保存
        with open("chat_log.txt", "a", encoding="utf-8") as f:
            # 現在の日時を取得して整形
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    except LineBotApiError as e:
        # LINEのAPIでエラーが発生した場合は、エラーメッセージを出力
        print(f"LINE APIエラー: {e}")

# このスクリプトが直接実行された場合にFlaskアプリケーションを起動
if __name__ == "__main__":
    # ホストを0.0.0.0（全てのネットワークインターフェースで受信）に設定し、ポート8000でサーバーを起動
    app.run(host="0.0.0.0", port=8000)