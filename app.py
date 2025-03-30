from flask import Flask, request, abort  # Webアプリケーション用フレームワーク
from linebot import LineBotApi, WebhookHandler  # LINEメッセージの送受信とWebhook処理用ライブラリ
from linebot.exceptions import InvalidSignatureError, LineBotApiError  # LINE Botで発生するエラーを処理するための例外
from linebot.models import MessageEvent, TextMessage, TextSendMessage  # LINEのイベントやメッセージ送受信モデル
import openai  # OpenAIのAPIを使うためのライブラリ（ChatGPT利用）
import os  # 環境変数を扱うためのライブラリ
import threading  # 並行処理を行うためのライブラリ（非同期処理）

app = Flask(__name__)

# 環境変数からAPIキーやトークンを取得
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")  # LINEのチャンネルシークレット
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")  # LINEのチャンネルアクセストークン
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # OpenAIのAPIキー

# LINE BotとOpenAIクライアントの初期化
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)
client = openai.OpenAI(api_key=OPENAI_API_KEY)

# 会話履歴をユーザーIDごとに管理する辞書
conversation_histories = {}

# LINEのWebhookからのリクエストを処理する
@app.route("/webhook", methods=["POST"])
def webhook():
    signature = request.headers["X-Line-Signature"]  # LINEの署名を取得
    body = request.get_data(as_text=True)  # リクエストの内容をテキストで取得

    try:
        handler.handle(body, signature)  # 署名を検証し、メッセージを処理
    except InvalidSignatureError:
        abort(400)  # 署名が無効な場合はエラーを返す

    return 'OK'  # 正常終了

# ユーザーからのテキストメッセージを処理する関数
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_text = event.message.text  # ユーザーの送信したテキストを取得
    user_id = event.source.user_id  # ユーザーのLINE IDを取得

    # 別スレッドでOpenAIへの問い合わせと返信を実行（処理を高速化するため）
    threading.Thread(target=reply_gpt, args=(user_text, user_id)).start()

# OpenAIに問い合わせて、LINEに返信する関数
def reply_gpt(user_text, user_id):
    # 会話履歴を取得（無ければ空のリストで初期化）
    history = conversation_histories.get(user_id, [])

    # 履歴にユーザーのメッセージを追加
    history.append({"role": "user", "content": user_text})

    # OpenAIのChatGPTモデルに、会話履歴を送信して回答を生成
    res = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=history
    )

    # ChatGPTの返答を取得
    reply = res.choices[0].message.content

    try:
        # LINEにChatGPTの返答を送信
        line_bot_api.push_message(user_id, TextSendMessage(reply))

        # 履歴にChatGPTの返答を追加
        history.append({"role": "assistant", "content": reply})

        # 会話履歴が長くなりすぎないように最新10件に制限
        conversation_histories[user_id] = history[-10:]

    except LineBotApiError as e:
        # LINE APIでエラーが発生した場合にログに出力
        print(f"LINE APIエラー: {e}")

# このスクリプトを直接実行した場合、指定のホストとポートでFlaskアプリを起動
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)