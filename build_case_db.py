import json
import chromadb
from chromadb.utils import embedding_functions

print("讀取 PTT 案例檔案...")
# 1. 讀取我們剛剛爬下來的 JSON 檔案
with open("ptt_cases.json", "r", encoding="utf-8") as f:
    cases_data = json.load(f)

print(f"成功讀取 {len(cases_data)} 筆案例！準備載入向量轉換模型...")

# 2. 載入跟你之前法規資料庫一模一樣的 Embedding 模型
embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="shibing624/text2vec-base-chinese"
)

# 3. 連線到你現有的資料庫資料夾 (law_db)
client = chromadb.PersistentClient(path="./law_db")

# 4. 建立一個「全新」的 Collection 專門放案例
# 使用 get_or_create_collection，這樣就算你以後重複執行這支程式，也不會報錯
collection = client.get_or_create_collection(
    name="ptt_cases_collection", 
    embedding_function=embedding_fn
)

print("正在將文字轉換為向量並存入資料庫 (這可能會花幾分鐘時間)...")

# 5. 準備三個空串列，ChromaDB 規定要這樣餵給它
documents = [] # 準備被轉換成向量的文字內容
metadatas = [] # 附加資訊 (例如作者、日期、網址，這對以後 AI 附上參考來源很有用！)
ids = []       # 每筆資料的身分證字號

for i, case in enumerate(cases_data):
    title = case.get("title", "")
    content = case.get("content", "")
    
    # 把標題和內文拼在一起，讓 AI 搜尋時能同時對比標題和內文
    full_text = f"【文章標題】：{title}\n【文章內文】：{content}"
    documents.append(full_text)
    
    # 把網址和日期存進 metadata，以後 AI 回答時就可以附上 PTT 連結證明不是瞎掰的
    metadatas.append({
        "author": case.get("author", "未知"),
        "date": case.get("date", "未知"),
        "link": case.get("link", "")
    })
    
    # 給它一個專屬的 ID
    ids.append(f"case_{i}")

# 6. 一口氣將所有資料灌進資料庫！
collection.add(
    documents=documents,
    metadatas=metadatas,
    ids=ids
)

print("🎉 大功告成！PTT 實戰案例已成功轉化為向量，存入你的法規大腦中！")