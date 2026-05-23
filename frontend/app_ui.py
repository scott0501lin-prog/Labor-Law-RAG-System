import streamlit as st
import json
import os
from datetime import datetime
from dotenv import load_dotenv

# 強制讀取外層 (final project) 的 .env 檔案以載入 GOOGLE_API_KEY
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env_path = os.path.join(base_dir, ".env")
load_dotenv(env_path)

# ==========================================
# 1. 系統初始化與資料夾設定
# ==========================================
HISTORY_DIR = "chat_histories"
if not os.path.exists(HISTORY_DIR):
    os.makedirs(HISTORY_DIR)

# 初始化必要的 Session State 防止網頁重整時報錯
if "user_role" not in st.session_state:
    st.session_state.user_role = "Employee"  # 預設為勞方身分

if "messages" not in st.session_state:
    st.session_state.messages = []

if "current_chat_file" not in st.session_state:
    st.session_state.current_chat_file = None

if "btn_input" not in st.session_state:
    st.session_state.btn_input = None


# ==========================================
# 2. 後端 RAG 呼叫介面 (Gemini + ChromaDB 完美對齊版)
# ==========================================
def query_rag_system(user_prompt, system_prompt):
    try:
        import os
        import google.generativeai as genai
        import chromadb
        from chromadb.utils import embedding_functions

        # 1. 喚醒隱形斗篷裡的 API 金鑰 (加上 GPS 定位強制讀取外層的 .env)
        from dotenv import load_dotenv
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        env_path = os.path.join(base_dir, ".env")
        load_dotenv(env_path)

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            # 如果還是找不到，它會直接在網頁上印出它去哪裡找的，方便我們抓蟲
            return f"🚨 找不到金鑰：請確認 {env_path} 檔案中是否有寫 GEMINI_API_KEY"
        genai.configure(api_key=api_key)

        # 2. 定位大腦資料庫的路徑
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        db_path = os.path.join(base_dir, "backend", "law_db")

        # 3. 連線到 ChromaDB 與你的專屬中文向量模型
        client = chromadb.PersistentClient(path=db_path)
        embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="shibing624/text2vec-base-chinese"
        )

        # 4. 取得雙核心 Collection
        law_collection = client.get_collection(name="labor_law_collection", embedding_function=embedding_fn)
        case_collection = client.get_collection(name="ptt_cases_collection", embedding_function=embedding_fn)

        # 5. [檢索階段] 抓取法規與 PTT 文章
        law_results = law_collection.query(query_texts=[user_prompt], n_results=2)
        case_results = case_collection.query(query_texts=[user_prompt], n_results=3)

        # ✨ 關鍵升級：把內文 (documents) 和包含網址的隱藏資訊 (metadatas) 綁在一起！
        law_context = ""
        if law_results['documents'] and law_results['documents'][0]:
            for doc, meta in zip(law_results['documents'][0], law_results['metadatas'][0]):
                law_context += f"【法規內容】：{doc}\n【來源資訊】：{meta}\n\n"
        else:
            law_context = "無相關法規\n"

        case_context = ""
        if case_results['documents'] and case_results['documents'][0]:
            for doc, meta in zip(case_results['documents'][0], case_results['metadatas'][0]):
                case_context += f"【案例內容】：{doc}\n【來源資訊】：{meta}\n\n"
        else:
            case_context = "無相關案例\n"

        # 6. [增強階段] 將檢索到的資料與使用者的問題組合
        # ✨ 加入強制 Markdown 網址生成的指令
        final_prompt = f"""
        【特別指令】：請務必檢查下方的「來源資訊」，若其中包含網址 (url 或 link)，請在「參考案例與來源」區塊中，嚴格使用 Markdown 語法產生可點擊的超連結，格式為：[文章標題或來源](此處放入真實網址)。絕對不要只輸出純文字網址。

        【相關法規】：
        {law_context}

        【PTT實戰案例】：
        {case_context}

        使用者問題：{user_prompt}
        """

        # 7. [生成階段] 呼叫 Gemini 給出回答
        model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            system_instruction=system_prompt
        )

        response = model.generate_content(final_prompt)
        return response.text

    except Exception as e:
        return f"🚨 系統發生異常：\n{str(e)}"


# ==========================================
# 3. 根據身分設定 UI 文字與提示詞
# ==========================================
if st.session_state.user_role == "Employee":
    role_title = "勞方專屬 AI 顧問"
    sys_persona = """你是一位專門替「勞工」爭取權益的 AI 律師。
請根據系統提供的【參考資料】來回答使用者的問題。

為了讓使用者能快速掌握資訊，你的回答必須嚴格遵守以下格式結構：

### 💡 核心重點 
(請以 2 到 3 個條列式重點，直接告訴勞工這是否合法、有哪些權益可以爭取。字句要精煉精準。)

### 📖 詳細說明與法規依據
(詳細解釋原因、適用的勞基法條文，以及實務上的申訴或自救建議。)

### 📚 參考案例與來源
(請列出你有使用到的參考資料標題與網址。若無提供網址則不需列出。)"""

    btn_1, val_1 = "被公司惡意資遣怎麼辦？", "我被公司惡意資遣了，請問有什麼法律權益可以爭取？"
    btn_2, val_2 = "過年加班費怎麼算？", "過年期間被要求加班，公司說沒雙倍薪水合法嗎？"
    btn_3, val_3 = "請病假會被扣全勤嗎？", "我生病想請病假，但公司說會扣整個月全勤，合法嗎？"

else:
    role_title = "資方專屬 AI 顧問 (法遵專家)"
    sys_persona = """你是一位專門協助「企業雇主與人資」遵循勞基法的 AI 法遵顧問。語氣要專業嚴謹。
請根據系統提供的【參考資料】來回答使用者的問題。

為了讓使用者能快速掌握資訊，你的回答必須嚴格遵守以下格式結構：

### 💡 核心重點 
(請以 2 到 3 個條列式重點，直接提醒雇主此舉的違法風險、最高罰鍰，或合法的處理大原則。)

### 📖 詳細說明與法規依據
(詳細解釋適用的勞基法條文，並提供企業合規的操作流程或制度修改建議。)

### 📚 參考案例與來源
(請列出你有使用到的參考資料標題與網址。若無提供網址則不需列出。)"""

    btn_1, val_1 = "如何合法資遣不適任員工？", "公司有一名員工長期表現不佳且態度惡劣，我想請他走人，請問合法的資遣流程是什麼？"
    btn_2, val_2 = "員工連續曠職怎麼辦？", "有員工已經連續三天無故未到班也聯絡不上，我可以合法解僱他嗎？需要付資遣費嗎？"
    btn_3, val_3 = "排班與加班費的合法設定", "我們是排班制餐飲食業，遇上國定假日排班，薪水和補休應該怎麼給才不會被勞工局開罰？"


# ==========================================
# 4. 側邊欄設計 (身分切換、快速發問、歷史紀錄)
# ==========================================
with st.sidebar:
    st.title("⚙️ 智慧法遵控制台")
    
    # 身份切換選單
    current_role_idx = 0 if st.session_state.user_role == "Employee" else 1
    selected_role = st.selectbox(
        "選擇您的模擬身分入口：", 
        ["🙋‍♂️ 勞方門戶（Employee）", "🏢 資方門戶（Employer）"], 
        index=current_role_idx
    )
    new_role = "Employee" if "🙋‍♂️ 勞方" in selected_role else "Employer"
    if new_role != st.session_state.user_role:
        st.session_state.user_role = new_role
        st.rerun()

    st.divider()

    # 快速推薦按鈕
    st.markdown("### ⚡ 快速推薦發問")
    if st.button(btn_1, use_container_width=True): st.session_state.btn_input = val_1
    if st.button(btn_2, use_container_width=True): st.session_state.btn_input = val_2
    if st.button(btn_3, use_container_width=True): st.session_state.btn_input = val_3

    st.divider()

    # 近期歷史對話管理
    st.markdown("### 🗂️ 近期歷史對話")
    if st.button("➕ 開啟全新對話", use_container_width=True):
        st.session_state.messages = []
        st.session_state.current_chat_file = None
        st.rerun()

    # 讀取本地 JSON 檔並動態擷取第一句話作為標題
    saved_chats = sorted(os.listdir(HISTORY_DIR), reverse=True)
    if not saved_chats:
        st.info("目前尚無歷史紀錄")
    else:
        for chat_file in saved_chats:
            try:
                with open(os.path.join(HISTORY_DIR, chat_file), "r", encoding="utf-8") as f:
                    chat_data = json.load(f)
                
                if len(chat_data) > 0 and chat_data[0]["role"] == "user":
                    first_msg = chat_data[0]["content"]
                    display_name = first_msg[:12] + "..." if len(first_msg) > 12 else first_msg
                else:
                    display_name = "未命名對話"
            except:
                display_name = "無效的對話紀錄"
                chat_data = []

            if st.button(display_name, key=chat_file, use_container_width=True):
                st.session_state.messages = chat_data
                st.session_state.current_chat_file = chat_file
                st.rerun()


# ==========================================
# 5. 主畫面聊天室渲染
# ==========================================
st.title(f"⚖️ {role_title}")
st.caption("結合生成式 AI 與勞動基準法資料庫的對話式決策支援平台")

# 渲染 Session State 內留存的對話訊息
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])


# ==========================================
# 6. 對話輸入核心邏輯
# ==========================================
chat_prompt = st.chat_input("請輸入您的勞資問題，或點選側邊欄快捷發問...")

# 檢查是否觸發了快速推薦發問按鈕
if st.session_state.btn_input:
    chat_prompt = st.session_state.btn_input
    st.session_state.btn_input = None

if chat_prompt:
    # A. 渲染並記錄使用者訊息
    with st.chat_message("user"):
        st.markdown(chat_prompt)
    st.session_state.messages.append({"role": "user", "content": chat_prompt})

    # B. 呼叫 RAG 後端引擎並渲染 AI 回覆
    with st.chat_message("assistant"):
        with st.spinner("智慧顧問正在檢索法律條文與真實案例庫..."):
            ai_response = query_rag_system(chat_prompt, sys_persona)
            st.markdown(ai_response)
    st.session_state.messages.append({"role": "assistant", "content": ai_response})

    # C. 自動將歷史紀錄寫入實體 JSON 檔案中
    if st.session_state.current_chat_file is None:
        st.session_state.current_chat_file = f"chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    file_path = os.path.join(HISTORY_DIR, st.session_state.current_chat_file)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(st.session_state.messages, f, ensure_ascii=False, indent=4)
        
    # 強制重整網頁以刷新側邊欄的歷史對話名稱
    st.rerun()