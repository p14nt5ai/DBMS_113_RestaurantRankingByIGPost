from flask import Flask, render_template, request, redirect, flash, session, url_for, jsonify
import SQLHelper
from math import ceil
from datetime import datetime

app = Flask(__name__)
app.secret_key = "your_secret_key"
app.jinja_env.globals.update(max=max, min=min)

# Instantiate SQLHelper
db = SQLHelper.SQLHelper('localhost', 'root', '', 'final_project')

# Number of restaurants per page
RESTAURANTS_PER_PAGE = 10

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']
        user = db.get_user(username, password)
        if user:
            session['username'] = username
            session['user_id'] = user[0]['user_id']
            return redirect("/home")
        else:
            flash("Incorrect username or password", "danger")
    return render_template("login.html")

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']
        email = request.form.get('email')
        address = request.form.get('address')
        gender = request.form.get('gender')
        birthday = request.form.get('birthday')

        if not gender:
            gender = None
        if not birthday:
            birthday = None

        try:
            # 插入用戶資料
            db.add_user(username, password, email, address, gender, birthday)
            flash("Registration successful! Please log in.", "success")
            return redirect("/")
        except Exception as e:
            flash(f"Error: {e}", "danger")
    return render_template("signup.html")

@app.route("/check_username", methods=["POST"])
def check_username():
    username = request.json.get('username')  # 從 AJAX 請求中獲取 username
    if not username:
        return {"status": "error", "message": "Username is required"}, 400

    # 檢查用戶名是否已存在
    user = db.fetch_query("SELECT * FROM user WHERE username = %s", (username,))
    if user:
        return {"status": "error", "message": "Username already exists"}, 409
    return {"status": "success", "message": "Username is available"}, 200

@app.route("/home", methods=["GET", "POST"])
def home():
    if 'username' not in session:
        return redirect("/")
    
    # Handle search query
    search_query = request.args.get('search', '').strip()
    page = int(request.args.get('page', 1))
    user_id = session['user_id']

    # 每頁顯示的餐廳數量
    RESTAURANTS_PER_PAGE = 10

    # 獲取當前用戶已儲存的餐廳 ID
    saved_restaurants = db.fetch_query("""
        SELECT li.restaurant_id 
        FROM list_item li
        JOIN list l ON li.list_id = l.list_id
        WHERE l.user_id = %s
    """, (user_id,))
    saved_ids = {r['restaurant_id'] for r in saved_restaurants}

    # 查詢餐廳列表和總數據量
    if search_query:
        # 搜尋餐廳
        total_restaurants = db.fetch_query(
            "SELECT COUNT(*) AS total FROM restaurant WHERE name LIKE %s",
            (f"%{search_query}%",)
        )[0]['total']

        offset = (page - 1) * RESTAURANTS_PER_PAGE
        restaurants = db.fetch_query(
            "SELECT * FROM restaurant WHERE name LIKE %s LIMIT %s OFFSET %s",
            (f"%{search_query}%", RESTAURANTS_PER_PAGE, offset)
        )
    else:
        # 無搜尋條件時
        total_restaurants = db.fetch_query("SELECT COUNT(*) AS total FROM restaurant")[0]['total']

        offset = (page - 1) * RESTAURANTS_PER_PAGE
        restaurants = db.fetch_query(
            "SELECT * FROM restaurant LIMIT %s OFFSET %s",
            (RESTAURANTS_PER_PAGE, offset)
        )
    
    total_pages = ceil(total_restaurants / RESTAURANTS_PER_PAGE)
    
    return render_template(
        "home.html", 
        username=session['username'], 
        restaurants=restaurants, 
        saved_ids=saved_ids, 
        search_query=search_query, 
        page=page, 
        total_pages=total_pages
    )

@app.route("/profile")
def profile():
    if 'username' not in session:
        return redirect("/")
    
    # 獲取 user_id
    user_id = session['user_id']

    # 獲取用戶的清單
    user_lists = db.get_user_lists(user_id)

    # 查詢每個清單的餐廳資訊
    lists_with_restaurants = []
    for user_list in user_lists:
        restaurants = db.get_list_items(user_list['list_id'])
        lists_with_restaurants.append({
            "list_id": user_list['list_id'],
            "name": user_list['name'],
            "restaurants": restaurants
        })

    return render_template("profile.html", lists_with_restaurants=lists_with_restaurants)

@app.route("/edit_account", methods=["GET", "POST"])
def edit_account():
    if 'username' not in session:
        return redirect("/")
    
    user_id = session['user_id']
    if request.method == "POST":
        # 處理提交的資料
        password = request.form.get('password') or None
        email = request.form.get('email') or ""
        address = request.form.get('address') or ""
        gender = request.form.get('gender') or None
        birthday = request.form.get('birthday') or None

        # 更新用戶資料
        update_data = {
            "password": password,
            "email": email,
            "address": address,
            "gender": gender,
            "birthday": birthday
        }

        # 排除未修改的欄位
        update_data = {k: v for k, v in update_data.items() if v is not None or k in ["email", "address"]}

        if update_data:
            db.update_user(user_id, **update_data)
        # 完成後直接重定向回 profile 頁面
        return redirect("/profile")
    
    # 如果是 GET 請求，顯示編輯頁面
    user_info = db.fetch_query("SELECT * FROM user WHERE user_id = %s", (user_id,))[0]

    # 格式化生日為 YYYY-MM-DD
    if user_info.get('birthday'):
        user_info['birthday'] = user_info['birthday'].strftime('%Y-%m-%d')
    else:
        user_info['birthday'] = ''  # 無生日時保持空

    return render_template("edit_account.html", user_info=user_info)

@app.route("/delete_account", methods=["POST"])
def delete_account():
    if 'username' not in session:
        return redirect("/")
    
    user_id = session['user_id']

    # 刪除與用戶相關的所有資料
    user_lists = db.get_user_lists(user_id)
    for user_list in user_lists:
        db.execute_query("DELETE FROM list_item WHERE list_id = %s", (user_list['list_id'],))
        db.delete_list(user_list['list_id'])
    db.delete_user(user_id)

    # 清除 session 並跳轉到登入頁面
    session.pop('username', None)
    flash("Account deleted successfully.", "success")
    return redirect("/")

@app.route("/rankings")
def rankings():
    if 'username' not in session:
        return redirect("/")
    
    # 處理搜尋查詢
    search_query = request.args.get('search', '').strip()
    page = int(request.args.get('page', 1))
    
    # 每頁顯示的餐廳數量
    RESTAURANTS_PER_PAGE = 10
    
    if search_query:
        # 搜尋含有特定名稱的餐廳
        total_restaurants = db.fetch_query(
            """
            SELECT COUNT(*) as total 
            FROM restaurant r
            LEFT JOIN post p ON r.restaurant_id = p.restaurant_id
            WHERE r.name LIKE %s
            GROUP BY r.restaurant_id
            """,
            (f"%{search_query}%",)
        )
        total_count = len(total_restaurants) if total_restaurants else 0

        offset = (page - 1) * RESTAURANTS_PER_PAGE
        ranked_restaurants = db.fetch_query(
            """
            SELECT r.*, COUNT(p.post_id) as post_count, 
                   AVG(p.rating) as avg_rating
            FROM restaurant r
            LEFT JOIN post p ON r.restaurant_id = p.restaurant_id
            WHERE r.name LIKE %s
            GROUP BY r.restaurant_id
            ORDER BY avg_rating DESC, post_count DESC
            LIMIT %s OFFSET %s
            """,
            (f"%{search_query}%", RESTAURANTS_PER_PAGE, offset)
        )
    else:
        # 無搜尋條件時顯示所有餐廳
        total_count = len(db.fetch_query(
            """
            SELECT r.restaurant_id
            FROM restaurant r
            LEFT JOIN post p ON r.restaurant_id = p.restaurant_id
            GROUP BY r.restaurant_id
            """
        ))

        offset = (page - 1) * RESTAURANTS_PER_PAGE
        ranked_restaurants = db.fetch_query(
            """
            SELECT r.*, COUNT(p.post_id) as post_count, 
                   AVG(p.rating) as avg_rating
            FROM restaurant r
            LEFT JOIN post p ON r.restaurant_id = p.restaurant_id
            GROUP BY r.restaurant_id
            ORDER BY avg_rating DESC, post_count DESC
            LIMIT %s OFFSET %s
            """,
            (RESTAURANTS_PER_PAGE, offset)
        )
    
    total_pages = ceil(total_count / RESTAURANTS_PER_PAGE)
    
    return render_template(
        "rankings.html",
        ranked_restaurants=ranked_restaurants,
        search_query=search_query,
        page=page,
        total_pages=total_pages
    )

@app.route("/get_restaurant_posts/<int:restaurant_id>")
def get_restaurant_posts(restaurant_id):
    if 'username' not in session:
        return redirect("/")
    
    # 獲取餐廳的所有貼文及其 IG 作者資訊
    posts = db.fetch_query(
        """
        SELECT p.*, ig.*
        FROM post p
        JOIN ig_poster ig ON p.poster_id = ig.poster_id
        WHERE p.restaurant_id = %s
        ORDER BY p.rating DESC
        """,
        (restaurant_id,)
    )
    
    return jsonify(posts)

@app.route("/instagram/<poster_id>")
def instagram_author(poster_id):
    ig_data = db.get_ig_poster_for_post(poster_id)
    return render_template("instagram_author.html", ig_data=ig_data)

@app.route("/logout")
def logout():
    session.pop('username', None)
    return redirect("/")

@app.route("/add_to_list", methods=["POST"])
def add_to_list():
    if 'username' not in session:
        return redirect("/")
    
    # 獲取用戶 ID 和餐廳 ID
    user_id = session['user_id']
    restaurant_id = request.form['restaurant_id']
    page = request.form.get('page', 1)  # 獲取當前頁碼，默認為 1
    search_query = request.form.get('search', '')  # 獲取搜尋關鍵字

    # 獲取用戶的清單
    user_lists = db.get_user_lists(user_id)
    if not user_lists:
        # 如果用戶沒有清單，創建默認清單
        db.create_list(user_id, "My Favorites")
        user_lists = db.get_user_lists(user_id)

    # 使用第一個清單作為默認的 list_id
    list_id = user_lists[0]['list_id']

    # 將餐廳添加到清單
    db.add_item_to_list(list_id, restaurant_id)
    flash("Restaurant added to your list.", "success")

    # 根據是否有搜尋查詢決定重定向路徑，將 Flash message 傳遞到頁面
    return redirect(url_for('home', page=page, search=search_query))

@app.route("/remove_from_list", methods=["POST"])
def remove_from_list():
    if 'username' not in session:
        return redirect("/")
    
    list_id = request.form['list_id']
    restaurant_id = request.form['restaurant_id']
    
    # 從清單中移除餐廳
    db.delete_item_from_list(list_id, restaurant_id)
    flash("Restaurant removed from your list.", "success")
    
    # 返回到 Profile 頁面，立即顯示消息
    return redirect("/profile")

if __name__ == "__main__":
    app.run(debug=True)