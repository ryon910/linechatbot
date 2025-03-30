from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import openai
import os
import threading
from datetime import datetime

app = Flask(__name__)

LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)
client = openai.OpenAI(api_key=OPENAI_API_KEY)

# 会話履歴を保存する辞書（ユーザーごとに履歴を管理）
conversation_histories = {}

@app.route("/webhook", methods=["POST"])
def webhook():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_text = event.message.text
    user_id = event.source.user_id
    threading.Thread(target=reply_gpt, args=(user_text, user_id)).start()

def reply_gpt(user_text, user_id):
    # ユーザーごとの履歴を取得または初期化
    history = conversation_histories.get(user_id, [])
    
    # 新しいユーザーのメッセージを履歴に追加
    history.append({"role": "user", "content": user_text})

    # 会話履歴を含めてOpenAIに問い合わせ
    res = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=history
    )
    reply = res.choices[0].message.content

    try:
        # LINEへ返信
        line_bot_api.push_message(user_id, TextSendMessage(reply))

        # 会話履歴にChatGPTの返答も追加
        history.append({"role": "assistant", "content": reply})

        # 最新10件に制限
        conversation_histories[user_id] = history[-10:]

        # ログに記録
        with open("chat_log.txt", "a", encoding="utf-8") as f:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"{timestamp}\tユーザー: {user_text}\n")
            f.write(f"{timestamp}\tChatGPT: {reply}\n")

    except LineBotApiError as e:
        print(f"LINE APIエラー: {e}")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
