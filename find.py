import urllib.request
import json
import ssl
import io
import zipfile

print("正在連線至政府開放資料平台，下載中央法規庫...")
print("（全國法規資料庫檔案龐大，請稍候約 10~30 秒...）")

url = "https://law.moj.gov.tw/api/Ch/Law/JSON"
# 略過 SSL 憑證驗證，避免政府網站憑證問題
context = ssl._create_unverified_context()

try:
    # 步驟 1: 加上 User-Agent 模擬瀏覽器，並下載檔案
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, context=context) as response:
        file_bytes = response.read()
        print("✅ 檔案下載完成！開始處理格式...")

    # 步驟 2: 破解「隱藏的壓縮檔」陷阱
    try:
        # 嘗試將下載的二進位資料當作 ZIP 壓縮檔來解壓縮
        with zipfile.ZipFile(io.BytesIO(file_bytes)) as z:
            json_filename = z.namelist()[0] # 取得壓縮檔內的第一個檔案名稱
            print(f"📦 發現 ZIP 壓縮檔！正在讀取裡面的 {json_filename}...")
            json_bytes = z.read(json_filename)
            
            # 使用 utf-8-sig 解碼，能自動過濾掉微軟系統常見的 BOM 標記
            json_text = json_bytes.decode('utf-8-sig')
            
    except zipfile.BadZipFile:
        # 如果解壓失敗，代表政府 API 改版變成純文字了，就直接讀取
        print("📄 檔案為一般文字格式，直接讀取...")
        json_text = file_bytes.decode('utf-8-sig')

    # 步驟 3: 將文字轉為 Python 的字典結構
    raw_data = json.loads(json_text)
    print("✅ JSON 解析成功！開始在法海中尋找《勞動基準法》...")

    # 步驟 4: 篩選與切片條文
    labor_law_chunks = []
    for law in raw_data.get('Laws', []): 
        if law.get('LawName') == '勞動基準法':
            print(f"🎯 找到目標：{law['LawName']}，開始整理條文...")
            for article in law.get('LawArticles', []):
                # ArticleType 'A' 代表實際條文
                if article.get('ArticleType') == 'A':
                    article_no = article.get('ArticleNo')
                    content = article.get('ArticleContent')
                    
                    # 將法規名稱、條號與內容拼接起來
                    chunk_text = f"【勞動基準法 {article_no}】\n{content}"
                    labor_law_chunks.append({
                        "source": "勞動基準法",
                        "article_no": article_no,
                        "text": chunk_text
                    })

    # 步驟 5: 儲存最終的乾淨資料
    if labor_law_chunks:
        print(f"🎉 大功告成！成功提取 {len(labor_law_chunks)} 條勞基法條文。")
        output_filename = "labor_law_cleaned.json"
        with open(output_filename, 'w', encoding='utf-8') as f:
            json.dump(labor_law_chunks, f, ensure_ascii=False, indent=4)
        print(f"💾 專題用的乾淨資料已儲存為：{output_filename}")
    else:
        print("❌ 在資料庫中沒有找到名稱為「勞動基準法」的法規。")

except Exception as e:
    print(f"⚠️ 發生錯誤：{e}")