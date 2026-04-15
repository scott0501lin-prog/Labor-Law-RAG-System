import os
import chromadb
from chromadb.utils import embedding_functions
import google.generativeai as genai
from dotenv import load_dotenv
from google.api_core.exceptions import ResourceExhausted

# ==========================================
# 1. 載入環境變數與設定 API 金鑰
# ==========================================
# 讀取 .env 檔案，保護你的 API Key 不外流
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    print("⚠️ 錯誤：找不到 API Key，請檢查 .env 檔案是否有正確設定 GEMINI_API_KEY。")
    exit()

# 設定 Gemini 模型 (使用適合 RAG 的輕量級快速模型)
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-3.1-flash-lite-preview')

# ==========================================
# 2. 連線至本地向量資料庫 (ChromaDB)
# ==========================================
print("🔗 正在載入法規大腦 (向量資料庫)...")
embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="shibing624/text2vec-base-chinese"
)

# 讀取先前建置好的 law_db 資料夾
client = chromadb.PersistentClient(path="./law_db")
collection = client.get_collection(
    name="labor_law_collection", 
    embedding_function=embedding_fn
)

# ==========================================
# 3. 核心 RAG 處理函式
# ==========================================
def ask_labor_law(query):
    # 【Retrieval 檢索階段】找出最相關的 5 條法規
    results = collection.query(query_texts=[query], n_results=5)
    
    # 將找到的法規拼成一大段文字，作為 AI 的參考資料
    context = "\n\n".join(results['documents'][0])
    
    # 【Generation 生成階段】建構 Prompt (提示詞)
    prompt = f"""
    你是一位專業的台灣勞資爭議顧問。請嚴格根據以下提供的【參考法規】來回答問題。
    如果法規中沒有提到，請回答「根據目前的勞基法資料庫，我無法準確回答這個問題」，絕對不可以自己瞎掰。
    
    【參考法規】：
    {context}
    
    【使用者問題】：
    {query}
    
    請以專業、親切且條理清晰的白話文方式回答。
    """
    
    print(f"🤖 AI 顧問：\n")
    
    # 🌟 加入防護網：處理 API 呼叫與串流輸出
    try:
        # stream=True 開啟打字機效果
        response = model.generate_content(prompt, stream=True)
        
        full_answer = ""
        for chunk in response:
            print(chunk.text, end="", flush=True)
            full_answer += chunk.text
            
        print("\n") # 換行收尾
        return full_answer
        
    except ResourceExhausted:
        error_msg = "\n⏳ 系統提示：目前詢問人數過多（已達免費 API 呼叫上限），請稍等 1 分鐘後再重新發問喔！"
        print(error_msg)
        return error_msg
        
    except Exception as e:
        error_msg = f"\n⚠️ 系統發生異常：{e}"
        print(error_msg)
        return "系統發生未預期錯誤，請稍後再試。"

# ==========================================
# 4. 系統執行與測試
# ==========================================
if __name__ == "__main__":
    print("✅ 系統準備就緒！\n")
    
    user_query = "過年期間被老闆要求加班，薪水補償怎麼算？"
    
    print(f"👤 提問：{user_query}")
    print("-" * 40)
    
    # 呼叫函式
    ask_labor_law(user_query)
    
    print("-" * 40)