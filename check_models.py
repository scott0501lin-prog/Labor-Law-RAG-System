import os
import google.generativeai as genai
from dotenv import load_dotenv

# 讀取你的 .env 檔案裡的 API KEY
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

print("🔍 正在查詢你的 API Key 支援的模型清單...\n")

# 叫 Google 交出支援「文字生成 (generateContent)」的模型名單
for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        print(m.name)