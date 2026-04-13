import chromadb
from chromadb.utils import embedding_functions

print("正在連線至本地向量資料庫...")

# 步驟 1: 載入與當初建置時一模一樣的 Embedding 模型
sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="shibing624/text2vec-base-chinese"
)

# 步驟 2: 連接剛剛做好的資料庫 (不用重建，直接讀取 ./law_db)
client = chromadb.PersistentClient(path="./law_db")
collection = client.get_collection(
    name="labor_law_collection", 
    embedding_function=sentence_transformer_ef
)

# 步驟 3: 隨時可以更改你想問的問題
question = "過年放假如果有去上班，薪水怎麼算？"
print(f"\n❓ 使用者提問：{question}\n")

# 步驟 4: 進行檢索 (這次我們把 n_results 提高到 5 條！)
results = collection.query(
    query_texts=[question],
    n_results=5 
)

print("🔍 系統找出的 Top 5 相關法規：\n")
for i, doc in enumerate(results['documents'][0]):
    print(f"[{i+1}] 關聯度排名")
    print(doc)
    print("-" * 40)