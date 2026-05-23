import os
from dotenv import load_dotenv
from huggingface_hub import HfApi

print("🚀 啟動精準發射引擎：準備發射完整專案到 Hugging Face...")

# 1. 喚醒隱形斗篷，去 .env 裡面拿出 HF_TOKEN
load_dotenv()
hf_token = os.getenv("HF_TOKEN")

if not hf_token:
    print("🚨 錯誤：找不到金鑰！請確認 .env 檔案中有設定 HF_TOKEN")
    exit()

# 2. 把拿到的金鑰交給發射器
api = HfApi(token=hf_token)

# 3. 執行安全上傳
api.upload_folder(
    folder_path=".",                            
    repo_id="scott0501lin-prog/Labor-Law-RAG-System", # 請確認這是你真實的 Space 名稱
    repo_type="space",                          
    ignore_patterns=[
        ".env",               
        ".venv", "venv", "env", "ENV",  
        "__pycache__",        
        ".git",               
        "chat_histories/*",   
        "upload.py",          
        "*.csv", "*.jsonl"    
    ]
)

print("✅ 發射成功！大腦與超美 UI 已經完美登陸雲端！")