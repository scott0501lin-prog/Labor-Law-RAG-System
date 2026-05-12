import os
import streamlit as st
import google.generativeai as genai
import chromadb
from chromadb.utils import embedding_functions
from dotenv import load_dotenv

# 1. 設定網頁基本資訊
st.set_page_config(page_title="AI 勞資顧問系統", page_icon="⚖️", layout="wide")

# =====================================================================
# 🌟 快取後端資源 (新增雙人設 AI 大腦)
# =====================================================================
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
    
    law_coll = client.get_collection(name="labor_law_collection", embedding_function=embedding_fn)
    case_coll = client.get_collection(name="ptt_cases_collection", embedding_function=embedding_fn)
    
    # 🧠 第一大腦：親切的前輩顧問
    chat_prompt = """你是一位專業、充滿同理心的「AI 勞資顧問」。
    你會參考【法規】與【PTT案例】回答，並融合對話歷史，給出連貫的建議。
    格式要求：嚴禁標題與列點，必須融合為單一自然段落，語氣親切像前輩。"""
    chat_model = genai.GenerativeModel(model_name="gemini-2.5-flash", system_instruction=chat_prompt)
    
    # ⚖️ 第二大腦：嚴謹的勞道法律師
    doc_prompt = """你是一位專業的勞資訴訟律師。請根據使用者提供的「對話歷史紀錄」與引用的法規，
    幫使用者撰寫一份正式、格式嚴謹的「存證信函」或「勞工局勞資爭議調解申請書」草稿。
    
    格式要求：
    1. 必須使用標準的法律文書排版（包含：主旨、事實及理由說明、請求權依據等段落）。
    2. 語氣必須嚴正、客觀、具備法律威嚇力。
    3. 不確定的個資（如姓名、公司名、確切金額）請留下 [請填寫您的姓名] 這種待填空欄位。"""
    doc_model = genai.GenerativeModel(model_name="gemini-2.5-flash", system_instruction=doc_prompt)
    
    return law_coll, case_coll, chat_model, doc_model

try:
    law_collection, case_collection, ai_chat_model, ai_doc_model = load_rag_backend()
except Exception as e:
    st.error(f"❌ 後端載入失敗：{e}")
    st.stop()

# =====================================================================
# 🛠️ 側邊欄：快速功能與實戰武器
# =====================================================================
with st.sidebar:
    st.title("🚀 快速發問")
    if st.button("💥 被公司惡意資遣怎麼辦？"):
        st.session_state.btn_input = "我被公司惡意資遣了，請問有什麼法律權益可以爭取？PTT鄉民建議怎麼做？"
    if st.button("💰 過年加班費怎麼算？"):
        st.session_state.btn_input = "過年期間如果被要求加班，薪水應該怎麼計算？公司說沒給雙倍薪水合法嗎？"
    if st.button("🤒 請病假會被扣全勤嗎？"):
        st.session_state.btn_input = "我因為生病想請病假，但公司說會扣掉整個月的全勤獎金，這樣是合法的嗎？"

    st.divider()
    
    # 🌟 殺手級新功能區塊
    st.title("💼 實戰反擊武器")
    st.info("💡 建議先在右側與顧問討論完你的狀況後，再點擊下方按鈕產出正式文件。")
    if st.button("📝 根據上述對話生成【存證信函 / 申訴書】"):
        # 確保使用者已經有對話紀錄才給生成
        if "messages" in st.session_state and len(st.session_state.messages) > 1:
            st.session_state.generate_doc = True
        else:
            st.warning("請先在右側描述你的勞資狀況，律師才有素材幫你寫信喔！")
            
    st.divider()
    if st.button("🧹 清除對話紀錄"):
        st.session_state.messages = []
        st.rerun()

# =====================================================================
# 🎨 主介面 UI 與對話處理
# =====================================================================
st.title("⚖️ 雙核心 AI 勞資顧問")
st.caption("融合【勞基法規】與【PTT實戰案例】的專屬職場護身符")

if "messages" not in st.session_state:
    st.session_state.messages = []

# 顯示歷史訊息
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 處理輸入（包含對話框與側邊欄提問按鈕）
user_input = st.chat_input("請描述你遇到的狀況...")
if "btn_input" in st.session_state:
    user_input = st.session_state.btn_input
    del st.session_state.btn_input

# 1. 正常對話邏輯
if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)
        
    with st.chat_message("assistant"):
        status_placeholder = st.empty()
        status_placeholder.markdown("⏳ *顧問正在思考並回顧之前的對話...*")
        try:
            law_results = law_collection.query(query_texts=[user_input], n_results=2)
            case_results = case_collection.query(query_texts=[user_input], n_results=3)
            
            law_context = "\n".join(law_results['documents'][0])
            case_context = "\n".join(case_results['documents'][0])
            
            sources_md = "\n\n---\n**📚 參考實戰案例：**\n"
            for meta in case_results['metadatas'][0]:
                sources_md += f"- 🔗 [{meta.get('author')} 的經驗 ({meta.get('date')})]({meta.get('link')})\n"
            
            history = []
            for m in st.session_state.messages[:-1]:
                role = "user" if m["role"] == "user" else "model"
                history.append({"role": role, "parts": [m["content"]]})
            
            chat = ai_chat_model.start_chat(history=history)
            combined_prompt = f"【參考法規】：\n{law_context}\n\n【PTT案例】：\n{case_context}\n\n問題：{user_input}"
            response = chat.send_message(combined_prompt)
            
            full_answer = response.text + sources_md
            status_placeholder.markdown(full_answer)
            st.session_state.messages.append({"role": "assistant", "content": full_answer})
        except Exception as e:
            status_placeholder.markdown(f"⚠️ 異常：{e}")

# =====================================================================
# 🌟 2. 獨立攔截邏輯：一鍵生成正式文書
# =====================================================================
if st.session_state.get("generate_doc", False):
    # 用完立刻重置狀態
    st.session_state.generate_doc = False
    
    # 整理過去的所有對話作為律師的起訴素材
    dialogue_history_text = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages])
    
    doc_request_prompt = f"""
    請根據以下使用者與顧問的完整對話紀錄，直接產出一份排版完美的「存證信函」或「勞資爭議調解書」：
    
    【完整對話紀錄】：
    {dialogue_history_text}
    """
    
    # 將需求顯示在介面上
    st.session_state.messages.append({"role": "user", "content": "👉 系統指令：請根據上述對話，幫我撰寫一份正式的反擊法律文書。"})
    with st.chat_message("user"):
        st.markdown("👉 系統指令：請根據上述對話，幫我撰寫一份正式的反擊法律文書。")
        
    # 召喚第二大腦（律師模型）產出報告
    with st.chat_message("assistant"):
        doc_placeholder = st.empty()
        doc_placeholder.markdown("⏳ *專業律師大腦已接手，正在為您起草正式法律文書，請稍候...*")
        try:
            doc_response = ai_doc_model.generate_content(doc_request_prompt)
            formal_doc = doc_response.text
            doc_placeholder.markdown(formal_doc)
            st.session_state.messages.append({"role": "assistant", "content": formal_doc})
        except Exception as e:
            doc_placeholder.markdown(f"⚠️ 文書生成異常：{e}")