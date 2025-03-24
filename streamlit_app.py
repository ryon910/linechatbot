import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import time, os, json

st.title("LINE × ChatGPT 会話ログ（リアルタイム）")

scope = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
json_str = os.getenv("GCP_CREDENTIALS")
json_data = json.loads(json_str)
creds = Credentials.from_service_account_info(json_data, scopes=scope)
client_gs = gspread.authorize(creds)
sheet = client_gs.open("LINE ChatGPT Log").sheet1

placeholder = st.empty()

while True:
    records = sheet.get_all_records()
    df = pd.DataFrame(records)[::-1]
    placeholder.dataframe(df, height=600)
    time.sleep(5)