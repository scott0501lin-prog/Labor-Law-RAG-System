import chromadb

# 1. 連線到你的資料庫資料夾
client = chromadb.PersistentClient(path="./law_db")

# 2. 取得所有 Collection 的清單
collections = client.list_collections()

print("🔍 你的 law_db 資料庫裡目前有以下 Collection：")
print("=" * 40)

# 3. 把名字一個一個印出來
if not collections:
    print("⚠️ 裡面空空如也，沒有任何 Collection！")
else:
    for c in collections:
        print(f"- {c.name}")
print("=" * 40)