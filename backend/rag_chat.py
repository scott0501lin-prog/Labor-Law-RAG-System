import os
import google.generativeai as genai
import chromadb
from chromadb.utils import embedding_functions
from dotenv import load_dotenv

# 1. 喚醒隱形斗篷裡的 API 金鑰
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)

print("🔗 正在載入雙核心大腦（法規資料庫 + PTT 實戰案例庫）...")

# 2. 連線到 ChromaDB
client = chromadb.PersistentClient(path="./law_db")
embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="shibing624/text2vec-base-chinese"
)

# 3. 取得兩個 Collection (確保名稱跟你建立時一模一樣)
try:
    law_collection = client.get_collection(name="labor_law_collection", embedding_function=embedding_fn)
    case_collection = client.get_collection(name="ptt_cases_collection", embedding_function=embedding_fn)
    print("✅ 雙核心大腦載入成功！\n")
except Exception as e:
    print(f"❌ 資料庫載入失敗，請檢查 Collection 名稱是否正確：{e}")
    exit()

# 設定 Gemini 模型 (使用最新支援 System Instruction 的語法)
system_prompt = """你是一位專業、充滿同理心的「AI 勞資顧問」。
當使用者發問時，我會提供你兩份參考資料：【相關法規】與【PTT實戰案例】。

【最高排版原則】：
你必須將所有資訊「融合為單一一個自然段落」。
絕對禁止使用任何標題、數字編號（1. 2. 3.）、列點符號（* 或 -）、或是粗體字（**）。請只輸出純文字對話。

【正確示範】（請完全模仿這種單一段落、像前輩聊天的語氣）：
依照勞基法第 XX 條的規定，其實你是可以爭取加班費的喔！我看過很多 PTT 網友分享類似的經驗，公司通常會想用補休來打發你，但我強烈建議你直接向人資表明拒絕，並保留好打卡紀錄，這才是對你最有利的作法！

【錯誤示範】（絕對、絕對不可以使用以下這種格式）：
法律怎麼說：勞基法規定...
真實世界長怎樣：PTT網友說...
顧問行動建議：你應該...

如果提供的資料中沒有相關資訊，請誠實告知，絕對不可以自己捏造。請記住，只能輸出一段純文字！
"""
model = genai.GenerativeModel(
    model_name="gemini-2.5-flash", # 或 gemini-1.5-flash
    system_instruction=system_prompt
)

print("=========================================")
print("🤖 雙核心 AI 勞資顧問已上線！(輸入 'quit' 離開)")
print("=========================================")

# 4. 開始聊天迴圈
while True:
    user_input = input("\n👤 提問：")
    
    if user_input.lower() in ['quit', 'exit', 'q']:
        print("👋 顧問下線，祝你職場順心！")
        break
        
    if not user_input.strip():
        continue
        
    print("⏳ 顧問正在翻閱法條與鄉民經驗...")
    
    # [檢索階段] 同時查詢兩個資料庫
    # 抓取 2 條最相關的法規
    law_results = law_collection.query(query_texts=[user_input], n_results=2)
    # 抓取 3 篇最相關的 PTT 文章
    case_results = case_collection.query(query_texts=[user_input], n_results=3)
    
    # 將檢索結果整理成純文字
    law_context = "\n".join(law_results['documents'][0])
    case_context = "\n".join(case_results['documents'][0])
    
    # [增強階段] 將檢索到的資料與使用者的問題組合成最終 Prompt
    final_prompt = f"""
    【相關法規】：
    {law_context}
    
    【PTT實戰案例】：
    {case_context}
    
    使用者問題：{user_input}
    """
    
    try:
        # [生成階段] 呼叫 Gemini 給出回答
        response = model.generate_content(final_prompt)
        print("\n🤖 AI 顧問：\n")
        print(response.text)
        print("\n" + "-"*40)
    except Exception as e:
        print(f"\n⚠️ 系統發生異常：{e}")