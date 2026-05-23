import json

# 步驟 1: 模擬從「全國法規資料庫」取得的勞基法 JSON 資料
# （實務上，你會去下載整份勞基法的 JSON 檔，並用 open('law.json') 來讀取）
mock_law_data = """
[
    {
        "ArticleNo": "第 24 條",
        "ArticleContent": "雇主延長勞工工作時間者，其延長工作時間之工資，依下列標準加給：一、延長工作時間在二小時以內者，按平日每小時工資額加給三分之一以上。二、再延長工作時間在二小時以內者，按平日每小時工資額加給三分之二以上。"
    },
    {
        "ArticleNo": "第 39 條",
        "ArticleContent": "第三十六條所定之例假、休息日、第三十七條所定之休假及第三十八條所定之特別休假，工資應由雇主照給。雇主經徵得勞工同意於休假日工作者，工資應加倍發給。"
    }
]
"""

# 步驟 2: 將 JSON 字串解析為 Python 的字典串列 (List of Dictionaries)
laws = json.loads(mock_law_data)

# 步驟 3: 建立一個乾淨的串列，用來儲存處理後的「切片」(Chunks)
processed_chunks = []

for law in laws:
    article_no = law.get("ArticleNo")
    content = law.get("ArticleContent")
    
    # 【關鍵步驟】將法規名稱、條號與內容合併！
    # 這樣 AI 檢索到這段文字時，才會知道「這是勞基法的哪一條」
    chunk_text = f"【勞動基準法 {article_no}】\n{content}"
    
    # 將整理好的資料存入字典中，保留 Meta-data 
    # (未來存入 ChromaDB 等向量資料庫時，Meta-data 可以用來做精準過濾)
    processed_chunks.append({
        "source": "勞動基準法",
        "article_no": article_no,
        "text": chunk_text
    })

# 步驟 4: 印出結果檢查
print("=== 資料清洗與切片完成 ===")
for chunk in processed_chunks:
    print(f"即將進行向量化的文本:\n{chunk['text']}")
    print("-" * 40)