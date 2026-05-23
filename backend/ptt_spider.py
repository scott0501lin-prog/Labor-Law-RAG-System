import cloudscraper
from bs4 import BeautifulSoup
import time
import json

# 初始設定
url = "https://www.ptt.cc/bbs/Salary/index.html"
scraper = cloudscraper.create_scraper()
cookies = {"over18": "1"}
all_articles = []

# 🌟 新增：設定你要爬取的總頁數
TARGET_PAGES = 3  
current_page = 1

print(f"🕵️‍♂️ 啟動自動翻頁爬蟲，目標：爬取 PTT 薪水板 {TARGET_PAGES} 頁資料...\n")

try:
    # 🌟 新增：使用 while 迴圈來控制翻頁
    while current_page <= TARGET_PAGES:
        print(f"==========================================")
        print(f"📄 正在處理第 {current_page} 頁...")
        print(f"🔗 當前網址: {url}")
        print(f"==========================================")
        
        response = scraper.get(url, cookies=cookies)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        
        # 1. 先抓取這一頁所有的文章區塊
        posts = soup.find_all("div", class_="r-ent")
        
        # 2. 處理這一頁的每一篇文章
        # 這次我們不切前三篇了，全抓！
        for post in posts:
            title_element = post.find("div", class_="title").find("a")
            
            # 如果這篇文章被刪除了 (沒有標題連結)，就跳過
            if not title_element:
                continue 
                
            title = title_element.text.strip()
            link = "https://www.ptt.cc" + title_element["href"]
            date = post.find("div", class_="date").text.strip()
            author = post.find("div", class_="author").text.strip()
            
            # 【關鍵字過濾 (選配)】
            # 如果你只想收集勞資糾紛，可以把這段打開：
            # if "資遣" not in title and "加班" not in title and "勞基法" not in title:
            #     continue 
                
            print(f"  > 抓取文章: {title}")
            
            content_text = ""
            try:
                inner_response = scraper.get(link, cookies=cookies)
                inner_soup = BeautifulSoup(inner_response.text, "html.parser")
                main_content = inner_soup.find("div", id="main-content")
                if main_content:
                    content_text = main_content.text.strip()
            except Exception as e:
                print(f"  ❌ 抓取內文失敗: {e}")
                
            article_data = {
                "title": title,
                "author": author,
                "date": date,
                "link": link,
                "content": content_text
            }
            all_articles.append(article_data)
            
            time.sleep(1.5) # 乖寶寶休息
            
        # ==========================================
        # 🌟 核心翻頁邏輯
        # ==========================================
        # 尋找「‹ 上頁」的按鈕連結
        paging_div = soup.find("div", class_="btn-group btn-group-paging")
        prev_btn = paging_div.find_all("a")[1] # [1] 通常是「上一頁」的按鈕
        
        # 如果還沒達到目標頁數，就把網址換成上一頁的網址，準備下一次迴圈
        if current_page < TARGET_PAGES:
            url = "https://www.ptt.cc" + prev_btn["href"]
            print(f"\n🔄 準備翻頁，休息 3 秒...")
            time.sleep(3) # 翻頁之間休息久一點，避免被封鎖
            
        current_page += 1

    # 所有頁面都爬完後，進行存檔
    print(f"\n💾 總共抓取了 {len(all_articles)} 篇文章，準備存檔...")
    with open("ptt_cases.json", "w", encoding="utf-8") as f:
        json.dump(all_articles, f, ensure_ascii=False, indent=4)
        
    print("🎉 存檔成功！你的 PTT 實戰資料庫已經建立！")

except Exception as e:
    print(f"\n❌ 程式發生錯誤：{e}")
    # 就算中途發生錯誤當機，我們也試著把已經抓到的資料存下來！
    if len(all_articles) > 0:
        print("正在嘗試將已抓取的殘存資料存檔...")
        with open("ptt_cases_error_backup.json", "w", encoding="utf-8") as f:
            json.dump(all_articles, f, ensure_ascii=False, indent=4)
        print("✅ 殘存資料已備份至 ptt_cases_error_backup.json")