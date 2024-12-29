from SQLHelper import SQLHelper

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options
import time

def get_post_rating(driver, content):
    try:
        driver.get("https://deepai.org/chat")
        time.sleep(3)
        
        # 找到對話框並輸入內容
        try:
            input_box = driver.find_element(By.CSS_SELECTOR, "textarea.chatbox")
        except Exception as e:
            print("[get_post_rating] 找不到輸入框，錯誤：", e)
            return 0
        
        input_box.send_keys(
            f"你是一位餐廳評論助手。請根據以下用戶評論，判斷該評論對餐廳的整體評分，並用0到5之間的整數表示，0表示極差，5表示極好。只返回數字，不要包含其他內容。\n"
            f"以下是用戶的評論：\n\n\"{content}\"\n\n請給出0到5之間的整數評分。"
        )
        input_box.send_keys(Keys.RETURN)  # 提交問題
        time.sleep(5)  # 等待回覆
        
        # 取得回覆內容
        responses = driver.find_elements(By.CSS_SELECTOR, "div.markdownContainer p")
        if not responses:
            print("[get_post_rating] 無回覆內容，預設評分為 0")
            return 0
        
        rating_text = responses[0].text.strip()
        
        # 檢查是否為合法的 0–5 整數
        if rating_text.isdigit():
            rating_int = int(rating_text)
            if 0 <= rating_int <= 5:
                return rating_int
        
        # 若格式不符，回傳 0 當作 fallback
        return 0
    except Exception as e:
        print("[get_post_rating] 發生未知錯誤，預設評分為 0，錯誤：", e)
        return 0

if __name__ == '__main__':
    try:
        db = SQLHelper('localhost', 'root', 'your_passeord', 'your_db')
    except Exception as e:
        print("[main] 資料庫連線失敗：", e)
        exit(1)

    options = Options()
    options.add_argument('--disable-blink-features=AutomationControlled')  # 防止被測出用Selenium的方法
    options.set_preference("profile.managed_default_content_settings.images", 2)  # 關閉圖片以加速
    
    try:
        driver = webdriver.Firefox(options=options)
    except Exception as e:
        print("[main] 初始化失敗：", e)
        exit(1)
    
    try:
        try:
            temp = db.fetch_query("SELECT post_id, content FROM post WHERE rating IS NULL")
        except Exception as e:
            print("[main] 無法從資料庫抓取資料：", e)
            temp = []
        
        for row in temp:
            post_id = row['post_id']
            content = row['content']
            
            # 取得評分
            try:
                rating = get_post_rating(driver, content)
            except Exception as e:
                print(f"[main] post_id={post_id} 取得評分時發生錯誤：", e)
                rating = 0
            
            # 將評分更新回資料庫
            try:
                update_query = "UPDATE post SET rating = %s WHERE post_id = %s"
                db.execute_query(update_query, (rating, post_id))
            except Exception as e:
                print(f"[main] post_id={post_id} 更新資料庫時發生錯誤：", e)
    finally:
        driver.quit()
        db.close_connection()
