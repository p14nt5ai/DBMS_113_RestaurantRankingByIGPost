from SQLHelper import SQLHelper

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options
import time

def get_post_rating(driver, content):
    driver.get("https://deepai.org/chat")
    time.sleep(3)
    
    input_box = driver.find_element(By.CSS_SELECTOR, "textarea.chatbox")
    input_box.send_keys(f"你是一位餐廳評論助手。請根據以下用戶評論，判斷該評論對餐廳的整體評分，並用0到5之間的整數表示，0表示極差，5表示極好。只返回數字，不要包含其他內容。\n以下是用戶的評論：\n\n\"{content}\"\n\n請給出0到5之間的整數評分。")
    input_box.send_keys(Keys.RETURN)  # Submit the question
    time.sleep(5)  # Wait for the response
    
    responses = driver.find_elements(By.CSS_SELECTOR, "div.markdownContainer p") 
    rating = responses[0].text.strip()
    return int(rating) if rating.isdigit() and 0 <= int(rating) <= 5 else 0

if __name__ == '__main__':
    db = SQLHelper('localhost', 'root', '', 'test_db')
    options = Options()
    options.add_argument('--disable-blink-features=AutomationControlled') # 防止被測出用Selenium的方法
    options.set_preference("profile.managed_default_content_settings.images", 2)  # Disable images for faster loading
    driver = webdriver.Firefox(options=options)    
    
    # Fetch post data
    temp = db.fetch_query("SELECT post_id, content FROM post WHERE rating IS NULL")
    
    for row in temp:
        id = row['post_id']
        content = row['content']
        
        # Get rating from ChatGPT API
        rating = get_post_rating(driver, content)
        
        # Update the rating in the database
        update_query = "UPDATE post SET rating = %s WHERE post_id = %s"
        db.execute_query("UPDATE post SET rating = %s WHERE post_id = %s", (rating, id))
        
    driver.quit()
