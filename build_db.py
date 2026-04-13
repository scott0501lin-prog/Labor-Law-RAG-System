import json
import chromadb
from chromadb.utils import embedding_functions

print("正在載入 Embedding 模型... (第一次執行會需要一點時間下載模型檔)")

# 步驟 1: 設定 Embedding 模型
# 這裡我們使用一個輕量級且支援中文的開源模型，完全免費，會在你的電腦本地端執行
sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="shibing624/text2vec-base-chinese"
)

# 步驟 2: 初始化 ChromaDB 向量資料庫
# 我們設定將資料庫存在目前資料夾下一個名為 'law_db' 的新資料夾中
client = chromadb.PersistentClient(path="./law_db")

# 步驟 3: 建立一個 Collection (類似關聯式資料庫的 Table)
# 如果已經存在，就重新建立一個乾淨的
collection_name = "labor_law_collection"
try:
    client.delete_collection(name=collection_name)
except Exception:
    pass # 如果是第一次跑，找不到 collection 會報錯，我們直接忽略

collection = client.create_collection(
    name=collection_name,
    embedding_function=sentence_transformer_ef
)

# 步驟 4: 讀取我們上一關做好的乾淨 JSON 檔
print("正在讀取 labor_law_cleaned.json...")
with open('labor_law_cleaned.json', 'r', encoding='utf-8') as f:
    law_data = json.load(f)

# 步驟 5: 將資料分批塞進資料庫
print(f"準備將 {len(law_data)} 條法規寫入向量資料庫...")

documents = []
metadatas = []
ids = []

for index, chunk in enumerate(law_data):
    # 這是 AI 實際要去「閱讀」和「比較」的文字內容
    documents.append(chunk['text'])
    
    # 這是附加資訊，未來可以依據這個做精準過濾
    metadatas.append({
        "source": chunk['source'],
        "article_no": chunk['article_no']
    })
    
    # 給每一筆資料一個獨一無二的 ID
    ids.append(f"law_{index}")

# 將資料正式加入 ChromaDB (這一步模型會開始運算，把所有文字轉成向量，會花個幾秒鐘)
collection.add(
    documents=documents,
    metadatas=metadatas,
    ids=ids
)

print("✅ 法規向量資料庫建置完成！資料已儲存在 './law_db' 資料夾中。")

# 步驟 6: 來做個簡單的檢索測試！
print("\n--- 🧠 系統測試：讓電腦試著找答案 ---")
test_query = "過年放假如果有去上班，薪水怎麼算？"
print(f"使用者提問：{test_query}")

results = collection.query(
    query_texts=[test_query],
    n_results=2 # 設定只找最相關的前 2 條法規
)

print("\n🔍 系統找到最相關的法規如下：")
for i in range(len(results['documents'][0])):
    print(f"[{i+1}] 關聯度排名")
    print(results['documents'][0][i])
    print("-" * 30)