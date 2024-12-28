import time
from SQLHelper import SQLHelper
from selenium import webdriver

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options


import sys
import io
import random

 


options = Options()
options.add_argument('--disable-blink-features=AutomationControlled') # 防止被測出用Selenium的方法
driver = webdriver.Firefox(options=options)   


def driver_init(driver=None):
    driver = webdriver.Firefox(options=options)
    return driver

def text2int(textnum):
    try:
        pointflag = False
        if textnum.find(".") != -1:
            pointflag = True

        textnum = textnum.replace(".", "")
        textnum = textnum.replace(" ", "")
        textnum = textnum.replace(",", "")
        if textnum[-1] == "K":
            textnum = int(textnum[:-1]) * 1000
        elif textnum[-1] == "M":
            textnum = int(textnum[:-1]) * 1000000
        if pointflag:
            textnum = int(textnum) / 10
    except:
        textnum = None
    return textnum

def insert_data_to_db(restaurant, 
                      restaurant_link, 
                      restaurant_address, 
                      restaurant_number, 
                      poster_id, 
                      poster_link, 
                      follower, 
                      following, 
                      num_post, 
                      post_link, 
                      content,
                      rating):

    db = SQLHelper(
        host="localhost",
        user="root",
        password="your_password",
        database="your_database"
    )
    restaurant_number = restaurant_number.replace(" ", "")
    if restaurant_number[:4] == "+886":
        restaurant_number = restaurant_number[4:]

    # Check existing restaurant
    res_sql = "SELECT restaurant_id FROM restaurant WHERE name=%s AND address=%s AND contact_number=%s"
    result = db.fetch_query(res_sql, (restaurant, restaurant_address, restaurant_number))
    if result:
        restaurant_id = result[0]["restaurant_id"]
    else:
        insert_sql = "INSERT INTO restaurant (name, address, contact_number) VALUES (%s, %s, %s)"
        db.execute_query(insert_sql, (restaurant, restaurant_address, restaurant_number))
        restaurant_id = db.fetch_query("SELECT LAST_INSERT_ID()")[0]["LAST_INSERT_ID()"]

    # Check existing poster
    poster_sql = "SELECT poster_id FROM ig_poster WHERE poster_id=%s"
    result = db.fetch_query(poster_sql, (poster_id,))
    if not result:
        insert_sql = "INSERT INTO ig_poster (poster_id, profile_link, fan_num, following_num, post_num) VALUES (%s, %s, %s, %s, %s)"
        db.execute_query(insert_sql, (poster_id, poster_link, follower, following, num_post))

    # Insert post
    insert_sql = "INSERT INTO post (restaurant_id, poster_id, rating, post_link, content) VALUES (%s, %s, %s, %s, %s)"
    db.execute_query(insert_sql, (restaurant_id, poster_id, None, post_link, content))

    db.close_connection()



def infinite_scroll_instagram(max_scroll):
    """
    對指定的 IG hashtag 頁面做 scroll，並擷取貼文 URL 作為示範。
    :param hashtag: 要瀏覽的 hashtag 
    :param max_scroll: 最多滾動次數
    """
    total_post = 0

    # 修改 navigator.webdriver 屬性，防止被網站偵測出使用Selenium的一種手段
    
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")


    # 1. 紀錄已經抓取的貼文連結 (避免重複)
    post_links = set()
    post_buttons = set()
    
    # 2. 開始進行多次滾動
    last_height = driver.execute_script("return document.body.scrollHeight")
    scroll_count = 0

    while scroll_count < max_scroll:
        # (a) 向下捲動到頁面底部
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        # 等待頁面加載
        time.sleep(8)

        # (b) 再次取得頁面捲動後的新高度
        new_height = driver.execute_script("return document.body.scrollHeight")

        # (c) 若高度沒有變化，可能已到最底或載不出新貼文  可中斷
        if new_height == last_height:
            print("已無更多內容可載入，停止捲動。")
            break
        last_height = new_height

        # (d) 取得目前頁面所有貼文連結
        posts = driver.find_elements(By.CSS_SELECTOR, '.xwrv7xz > div > div > div > div > a')
        for post in posts:
            link = post.get_attribute("href")
            post_links.add(link)
            

        scroll_count += 1
        print(f"第 {scroll_count} 次捲動，目前蒐集到 {len(post_links)} 筆貼文連結。")

    # 3. 顯示所有蒐集到的連結
    print("==== 最終貼文連結清單 ====")
    for link in post_links:
        print(link)

    # 4. 造訪每一篇貼文
    for link in post_links:
        print(f"造訪貼文：{link}")
        # 隨機等候 2-5 秒
        time.sleep(random.randint(2, 7))
        driver.get(link)
        try:
            text = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, 'span.x5n08af:nth-child(2)')
                )
            ).text
        except:
            print("No text found on this post.")
            continue
        
        text = text
        print(text)
        try:
            poster = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, '.xyinxu5 > div:nth-child(1) > div:nth-child(2) > div:nth-child(1) > div:nth-child(1) > div:nth-child(1) > div:nth-child(1) > span:nth-child(1) > span:nth-child(1) > div:nth-child(1) > a:nth-child(1) > div:nth-child(1) > div:nth-child(1) > span:nth-child(1)')
                )
            )

            poster_text = poster.text
            print(poster_text)
            poster_link = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, '.xyinxu5 > div:nth-child(1) > div:nth-child(2) > div:nth-child(1) > div:nth-child(1) > div:nth-child(1) > div:nth-child(1) > span:nth-child(1) > span:nth-child(1) > div:nth-child(1) > a:nth-child(1)')
                )
            ).get_attribute("href")
        except:
            try:
                poster = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, 'span > div > div > span > div > a > div > div > span')
                    )
                )

                poster_text = poster.text
                print(poster_text)
                poster_link = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, 'span > div > div > span > div > a')
                    )
                ).get_attribute("href")
            except:
                print("No poster name found on this post.")
                continue
        
        no_restaurant_flag = False
        try:
            restaurant = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, 'a.x5n08af')
                )
            )
            restaurant_link = restaurant.get_attribute("href")
            restaurant_name = restaurant.text
            
            print(restaurant_name)
            print(restaurant.get_attribute("href"))

        except:
            print("No restaurant name found on this post.")
            no_restaurant_flag = True

        rating = None   # rating 在 get_rating.py 中取得
        
        if no_restaurant_flag:
            continue

        # 造訪該餐廳的 IG 頁面

        driver.get(restaurant_link)
        # restaurant.click()

        # 有時抓到的非餐廳連結，會是行政區連結
        # 這時候會跳過這個連結

        try:
            price = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, 'div.x1pha0wt:nth-child(2) > span')
                )
            )
        except:
            print("No price found on this post.")
            continue
        
        if price.text == "":  # 這是一個行政區連結
            print("This is not a restaurant link.")
            continue # 跳過這則貼文的資料抓取
        print(price.text) 

        try:
            restaurant_address = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, '.x7l2uk3')
                )
            ).text
            print(restaurant_address)

            restaurant_number = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, '.x1gslohp > span')
                )
            ).text
            print(restaurant_number)
        except:
            print("No address or number found on this post.")
            restaurant_address = ""
            restaurant_number = ""
        
        # 造訪作者的 IG 頁面
        driver.get(poster_link)
        follower = None
        following = None
        num_post = None
        try:

            follower = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, 'li.xl565be:nth-child(2) > div:nth-child(1) > a:nth-child(1) > span:nth-child(1) > span')
                )
            ).text
            print("follower: ", follower)
            following = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, 'li.xl565be:nth-child(3) > div:nth-child(1) > a:nth-child(1) > span:nth-child(1) > span:nth-child(1)')
                )
            ).text
            print("following: ", following)
            num_post = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, 'li.xl565be:nth-child(1) > div:nth-child(1) > span:nth-child(1) > span:nth-child(1)')
                )
            ).text
            print("num_post: ", num_post)

        except:
            print("No follower, following or num_post found on this poster_page.")
            
        # 將小數點與其他無關符號去除 
        # K, M 等字串轉換為數字

        
        
        follower = text2int(follower)
        following = text2int(following)
        num_post = text2int(num_post)

        # 寫入資料庫
        insert_data_to_db(restaurant_name, 
                            restaurant_link, 
                            restaurant_address, 
                            restaurant_number, 
                            poster_text, 
                            poster_link, 
                            follower, 
                            following, 
                            num_post, 
                            link, 
                            text,
                            rating)
    
    

def main():
    
    place_list = ["澎湖", "金門", "馬祖", "高雄", "台南", "台中", "台北", "新竹", "桃園", "新北", "基隆", "宜蘭", "花蓮", "台東", "屏東",]  
    # goto post_page

    driver.get('https://www.instagram.com')   # 打開瀏覽器，開啟網頁
        

    # wait until login page is loaded
    driver.implicitly_wait(5)

    # find account and password input box
    account = driver.find_element('css selector', 'input[name="username"]')
    password = driver.find_element('css selector', 'input[name="password"]')
    # fill in account and password
    account.send_keys('your_ig_account')
    password.send_keys('your_ig_password')

    driver.implicitly_wait(3)
    # click login button
    login_button = driver.find_element('css selector', 'button[type="submit"]')
    login_button.click()
    # wait search button

    # 建立 WebDriverWait，等待最長 10 秒 (可依需求調整)
    element = WebDriverWait(driver, 30).until(
        EC.presence_of_element_located(
            (By.CSS_SELECTOR, 'section > div > div > svg')
        )
    )
    for place in place_list:
        
        driver.get(f'https://www.instagram.com/explore/search/keyword/?q=%23{place}美食') # 進入指定 hashtag 頁面
        element = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, '.xwrv7xz > div > div > div > div > a')
            )
        )
        infinite_scroll_instagram(2) # 捲動次數 (可自調)
        print(f"Finished {place} page")

        time.sleep(3)
    driver.close()


if __name__ == "__main__":
    main()