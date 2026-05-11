import os
import time
import streamlit as st
import google.generativeai as genai
import chromadb
from chromadb.utils import embedding_functions
from dotenv import load_dotenv

# 1. 設定網頁基本資訊
st.set_page_config(page_title="AI 勞資顧問系統", page_icon="⚖️", layout="centered")

# =====================================================================
# 🌟 核心技巧：快取後端資源 (只在網頁初次啟動時載入一次，拒絕重複連線 Lag)
# =====================================================================
@st.cache_resource
def load_rag_backend():
    print("🔄 [系統啟動] 正在將 ChromaDB 與 Gemini 載入快取記憶體...")
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    genai.configure(api_key=api_key)
    
    # 連線本地端的向量資料庫
    client = chromadb.PersistentClient(path="./law_db")
    embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="shibing624/text2vec-base-chinese"
    )
    
    # 抓取法規與案例的 Collection
    law_coll = client.get_collection(name="labor_law_collection", embedding_function=embedding_fn)
    case_coll = client.get_collection(name="ptt_cases_collection", embedding_function=embedding_fn)
    
    # 沿用你之前調教成功的「單一段落核彈版」前輩人設提示詞
    system_prompt = """你是一位專業、充滿同理心的「AI 勞資顧問」。
    當使用者發問時，我會提供你兩份參考資料：【相關法規】與【PTT實戰案例】。

    【最高排版原則】：
    你必須將所有資訊「融合為單一一個自然段落」。
    絕對禁止使用任何標題、數字編號（1. 2. 3.）、列點符號（* 或 -）、或是粗體字（**）。請只輸出純文字對話。

    【正確示範】（請完全模仿這種單一段落、像前輩聊天的語氣）：
    依照勞基法第 XX 條的規定，其實你是可以爭取加班費的喔！我看過很多 PTT 網友分享類似的經驗，公司通常會想用補休來打發你，但我強烈建議你直接向人資表明拒絕，並保留好打卡紀錄，這才是對你最有利的作法！

    如果提供的資料中沒有相關資訊，請誠實告知，絕對不可以自己捏造。請記住，只能輸出一段純文字！
    """
    
    model = genai.GenerativeModel(
        model_name="gemini-2.5-flash", # 或 gemini-1.5-flash
        system_instruction=system_prompt
    )
    
    return law_coll, case_coll, model

# 啟動載入程序
try:
    law_collection, case_collection, ai_model = load_rag_backend()
except Exception as e:
    st.error(f"❌ 後端系統載入失敗，請檢查資料庫路徑或 API 金鑰：{e}")
    st.stop()

# =====================================================================
# 🎨 網頁前端 UI 與對話邏輯
# =====================================================================
st.title("⚖️ 雙核心 AI 勞資顧問")
st.caption("融合【勞基法規】與【PTT實戰案例】的專屬職場護身符")

# 初始化使用者的對話紀錄 (存在 session_state 中)
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "你好！我是你的專屬 AI 勞資顧問。請問今天遇到什麼職場難題？（例如：過年期間被排班加班，老闆不給雙倍薪水合法嗎？）"}
    ]

# 把過去的對話氣泡依序畫出來
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 底部對話框接收輸入
# 底部對話框接收輸入
if user_input := st.chat_input("請描述你遇到的狀況或想查詢的法規..."):
    
    # 1. 將使用者的提問印在畫面上，並存入歷史紀錄
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)
        
    # 2. 召喚 AI 進行 RAG 檢索與生成回答
    with st.chat_message("assistant"):
        status_placeholder = st.empty()
        status_placeholder.markdown("⏳ *顧問正在快速翻閱法規與 PTT 鄉民經驗...*")
        
        try:
            # [右腦與左腦檢索] 
            law_results = law_collection.query(query_texts=[user_input], n_results=2)
            case_results = case_collection.query(query_texts=[user_input], n_results=3)
            
            law_context = "\n".join(law_results['documents'][0])
            case_context = "\n".join(case_results['documents'][0])
            
            # [組裝最終 Prompt]
            final_prompt = f"""
            【相關法規】：
            {law_context}
            
            【PTT實戰案例】：
            {case_context}
            
            使用者問題：{user_input}
            """
            
            # [生成階段] 呼叫 Gemini 產生文字建議
            response = ai_model.generate_content(final_prompt)
            ai_answer = response.text
            
            # =========================================================
            # 🌟 亮點新功能：萃取 Metadata，組裝「參考文獻超連結卡片」
            # =========================================================
            sources_md = "\n\n---\n**📚 參考實戰案例來源：**\n"
            
            # 撈出剛剛查詢到的 3 筆 PTT 案例的 metadata
            case_metadatas = case_results['metadatas'][0]
            
            for idx, meta in enumerate(case_metadatas):
                link = meta.get("link", "")
                author = meta.get("author", "未知")
                date = meta.get("date", "未知")
                
                # 利用 Markdown 語法將網址包裝成可點擊的連結
                if link:
                    sources_md += f"- 🔗 [{author} 的經驗分享 ({date})]({link})\n"
                else:
                    sources_md += f"- 👤 {author} 的經驗分享 ({date})\n"
            
            # 把 AI 的回答跟參考來源完美拼接在一起
            full_complete_answer = ai_answer + sources_md
            
            # 顯示在畫面上
            status_placeholder.markdown(full_complete_answer)
            
            # 3. 將包含連結的完整回答存入歷史紀錄
            st.session_state.messages.append({"role": "assistant", "content": full_complete_answer})
            
        except Exception as e:
            status_placeholder.markdown(f"⚠️ 系統檢索或生成時發生異常：{e}")