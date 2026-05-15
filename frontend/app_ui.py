import os
import streamlit as st
import google.generativeai as genai
import chromadb
from chromadb.utils import embedding_functions
from dotenv import load_dotenv

# 1. 設定網頁基本資訊
st.set_page_config(page_title="AI 勞資顧問系統", page_icon="⚖️", layout="wide")

# =====================================================================
# 🌟 快取後端資源 (維持你剛剛完美的絕對路徑架構)
# =====================================================================
@st.cache_resource
def load_rag_backend():
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    load_dotenv(os.path.join(BASE_DIR, ".env"))
    
    api_key = os.getenv("GEMINI_API_KEY")
    genai.configure(api_key=api_key)
    
    db_path = os.path.join(BASE_DIR, "backend", "law_db")
    client = chromadb.PersistentClient(path=db_path)
    embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="shibing624/text2vec-base-chinese"
    )
    
    law_coll = client.get_collection(name="labor_law_collection", embedding_function=embedding_fn)
    case_coll = client.get_collection(name="ptt_cases_collection", embedding_function=embedding_fn)
    
    # 這裡我們只先初始化一個基礎的 Chat Model，語氣等一下根據身分動態調整
    chat_model = genai.GenerativeModel(model_name="gemini-2.5-flash")
    doc_model = genai.GenerativeModel(model_name="gemini-2.5-flash") # 文書處理模型
    
    return law_coll, case_coll, chat_model, doc_model

try:
    law_collection, case_collection, ai_chat_model, ai_doc_model = load_rag_backend()
except Exception as e:
    st.error(f"❌ 後端載入失敗：{e}")
    st.stop()

# =====================================================================
# 🧠 初始化全域狀態
# =====================================================================
if "user_role" not in st.session_state:
    st.session_state.user_role = None  # None 代表還沒選擇身分
if "messages" not in st.session_state:
    st.session_state.messages = []

# =====================================================================
# 🚪 畫面一：入口大廳 (身分選擇)
# =====================================================================
if st.session_state.user_role is None:
    st.title("⚖️ 歡迎來到 AI 勞資顧問系統")
    st.subheader("請問您今天希望以什麼身分進行諮詢？")
    st.write("系統將根據您的身分，提供專屬的法律建議與快捷功能。")
    
    # 用 Columns 排版兩個大按鈕
    col1, col2 = st.columns(2)
    
    with col1:
        st.info("### 👷 我是勞方 (員工)\n\n我想了解我的工作權益、加班費計算，或是遇到不平等待遇時該如何爭取。")
        if st.button("👉 進入勞方諮詢室", use_container_width=True):
            st.session_state.user_role = "Employee"
            st.rerun() # 選擇後立刻重新載入網頁
            
    with col2:
        st.success("### 🏢 我是資方 (雇主/人資)\n\n我想了解如何合法制定公司規範、處理不適任員工，避免觸犯勞基法。")
        if st.button("👉 進入資方諮詢室", use_container_width=True):
            st.session_state.user_role = "Employer"
            st.rerun()

# =====================================================================
# 💬 畫面二：專屬聊天室 (根據身分變換介面)
# =====================================================================
else:
    # 根據身分設定 UI 文字與 AI 提示詞
    if st.session_state.user_role == "Employee":
        role_title = "👷 勞方專屬 AI 顧問"
        sys_persona = "你是一位專門替「勞工」爭取權益的 AI 律師。語氣要像溫暖的前輩，必須融合為單一自然段落，嚴禁列點。"
        btn_1, val_1 = "💥 被公司惡意資遣怎麼辦？", "我被公司惡意資遣了，請問有什麼法律權益可以爭取？"
        btn_2, val_2 = "💰 過年加班費怎麼算？", "過年期間被要求加班，公司說沒雙倍薪水合法嗎？"
        btn_3, val_3 = "🤒 請病假會被扣全勤嗎？", "我生病想請病假，但公司說會扣整個月全勤，合法嗎？"
    else:
        role_title = "🏢 資方專屬 AI 顧問 (法遵專家)"
        sys_persona = "你是一位專門協助「企業雇主與人資」遵循勞基法的 AI 法遵顧問。語氣要專業嚴謹，必須融合為單一自然段落，嚴禁列點。"
        btn_1, val_1 = "📜 如何合法資遣不適任員工？", "公司有一名員工長期表現不佳且態度惡劣，我想請他走人，請問合法的資遣流程是什麼？"
        btn_2, val_2 = "⚠️ 員工連續曠職怎麼辦？", "有員工已經連續三天無故未到班也聯絡不上，我可以合法解僱他嗎？需要付資遣費嗎？"
        btn_3, val_3 = "🕒 排班與加班費的合法設定", "我們是排班制餐飲業，遇上國定假日排班，薪水和補休應該怎麼給才不會被勞工局開罰？"

    # --- 側邊欄設計 ---
    with st.sidebar:
        st.title(f"🚀 {st.session_state.user_role == 'Employee' and '勞方' or '資方'}快速發問")
        
        if st.button(btn_1): st.session_state.btn_input = val_1
        if st.button(btn_2): st.session_state.btn_input = val_2
        if st.button(btn_3): st.session_state.btn_input = val_3

        st.divider()
        st.title("💼 實戰反擊武器")
        
        # 存證信函按鈕的文字也跟著改變
        doc_btn_text = "📝 生成【存證信函/申訴書】" if st.session_state.user_role == "Employee" else "📝 生成【合法解僱通知/警告信】"
        if st.button(doc_btn_text):
            if len(st.session_state.messages) > 1:
                st.session_state.generate_doc = True
            else:
                st.warning("請先在右側描述狀況，才有素材生成文件喔！")
                
        st.divider()
        if st.button("🚪 登出 / 重新選擇身分"):
            st.session_state.user_role = None
            st.session_state.messages = []
            st.rerun()

    # --- 聊天室主畫面 ---
    st.title(role_title)
    st.caption("融合【勞基法規】與【PTT實戰案例】的專屬職場護身符")

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    user_input = st.chat_input("請描述您遇到的狀況...")
    if "btn_input" in st.session_state:
        user_input = st.session_state.btn_input
        del st.session_state.btn_input

    # 正常對話邏輯
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
                
                # 🌟 每次對話時，動態注入當前身分的系統提示詞
                chat = ai_chat_model.start_chat(history=history)
                combined_prompt = f"【系統指令】：{sys_persona}\n\n【參考法規】：\n{law_context}\n\n【PTT案例】：\n{case_context}\n\n問題：{user_input}"
                response = chat.send_message(combined_prompt)
                
                full_answer = response.text + sources_md
                status_placeholder.markdown(full_answer)
                st.session_state.messages.append({"role": "assistant", "content": full_answer})
            except Exception as e:
                status_placeholder.markdown(f"⚠️ 異常：{e}")

    # 文書生成邏輯
    if st.session_state.get("generate_doc", False):
        st.session_state.generate_doc = False
        dialogue_history_text = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages])
        
        # 根據身分產生不同的文書要求
        if st.session_state.user_role == "Employee":
            doc_type = "勞方存證信函或勞資爭議調解書"
        else:
            doc_type = "資方合法解僱通知書或警告信"
            
        doc_request_prompt = f"""請以專業律師身分，根據以下完整對話紀錄，產出一份排版完美的「{doc_type}」：
        【完整對話紀錄】：\n{dialogue_history_text}"""
        
        st.session_state.messages.append({"role": "user", "content": f"👉 系統指令：請幫我撰寫一份正式的{doc_type}。"})
        with st.chat_message("user"):
            st.markdown(f"👉 系統指令：請幫我撰寫一份正式的{doc_type}。")
            
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