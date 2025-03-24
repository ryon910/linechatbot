from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import openai, os, threading, json
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials

app = Flask(__name__)

LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)
client = openai.OpenAI(api_key=OPENAI_API_KEY)

# Google Sheets接続設定（環境変数からJSONを取得）
scope = ["https://www.googleapis.com/auth/spreadsheets"]
json_str = os.getenv("GCP_CREDENTIALS")
json_data = json.loads(json_str)
creds = Credentials.from_service_account_info(json_data, scopes=scope)
client_gs = gspread.authorize(creds)
sheet = client_gs.open("LINE ChatGPT Log").sheet1

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
    res = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": user_text}],
    )
    reply = res.choices[0].message.content

    try:
        line_bot_api.push_message(user_id, TextSendMessage(reply))
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sheet.append_row([timestamp, user_text, reply])
    except LineBotApiError as e:
        print(f"LINE APIエラー: {e}")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)