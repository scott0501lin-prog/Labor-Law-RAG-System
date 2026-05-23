import os
import streamlit as st
import google.generativeai as genai
import chromadb
from chromadb.utils import embedding_functions
from dotenv import load_dotenv

@st.cache_resource
def load_rag_backend():
    # 🌟 神級尋路技巧：自動抓取目前檔案的前兩層目錄作為「專案根目錄 (BASE_DIR)」
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # 1. 精準載入根目錄下的 .env
    load_dotenv(os.path.join(BASE_DIR, ".env"))
    api_key = os.getenv("GEMINI_API_KEY")
    genai.configure(api_key=api_key)
    
    # 2. 精準指向 backend 資料夾裡的 law_db
    db_path = os.path.join(BASE_DIR, "backend", "law_db")
    client = chromadb.PersistentClient(path=db_path)
    
    embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="shibing624/text2vec-base-chinese"
    )
    
    # ⚠️ 注意：如果你之前的偵探程式查出法規抽屜叫做 "labor_law_collection"
    # 請記得把下面這行的 "law_collection" 替換成你正確的名稱！
    law_coll = client.get_collection(name="labor_law_collection", embedding_function=embedding_fn)
    case_coll = client.get_collection(name="ptt_cases_collection", embedding_function=embedding_fn)
    
    # 初始化兩個乾淨的大腦模型（因為在 app_ui.py 裡會根據勞方/資方身分動態注入提示詞）
    chat_model = genai.GenerativeModel(model_name="gemini-2.5-flash")
    doc_model = genai.GenerativeModel(model_name="gemini-2.5-flash")
    
    return law_coll, case_coll, chat_model, doc_model