import requests

# 1. 偽裝成真實的瀏覽器 (非常重要！)
# 很多網站會阻擋沒有 User-Agent 的程式發出請求
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
}

# 2. 設定你要爬取的目標網址 (這裡先以 PTT 勞工板為例)
url = "https://www.ptt.cc/bbs/regimen/index.html" # 替換成你的目標網址

print(f"正在前往 {url} 抓取資料...")

# 3. 發送 GET 請求
response = requests.get(url, headers=headers)

# 4. 檢查是否成功 (HTTP 狀態碼 200 代表成功)
if response.status_code == 200:
    print("✅ 成功連線！")
    
    # 印出抓到的前 500 個字元看看長怎樣
    print("-" * 40)
    print(response.text[:500]) 
    print("-" * 40)
    
else:
    print(f"❌ 連線失敗，狀態碼：{response.status_code}")