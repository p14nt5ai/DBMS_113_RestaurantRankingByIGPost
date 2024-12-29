from flask import Flask, render_template, request, redirect, flash, session, url_for, jsonify
import SQLHelper
from math import ceil
import hashlib

app = Flask(__name__)
app.secret_key = "your_secret_key"
app.jinja_env.globals.update(max=max, min=min)

# Instantiate SQLHelper
db = SQLHelper.SQLHelper('localhost', 'root', '', 'final_project')

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
    search_type = request.args.get('search_type', 'name')
    search_query = request.args.get('search_query', '').strip()
    page = int(request.args.get('page', 1))
    user_id = session['user_id']

    # 每頁顯示的餐廳數量
    RESTAURANTS_PER_PAGE = 10

    # 獲取當前用戶所有清單中已儲存的餐廳 ID
    user_lists = db.get_user_lists(user_id)
    # 建立一個字典，key 是餐廳 ID，value 是一個字典，包含所有的 list_id 和其對應的 list 名稱
    saved_restaurants = {}
    for user_list in user_lists:
        list_items = db.get_list_items(user_list['list_id'])
        for item in list_items:
            if item['restaurant_id'] not in saved_restaurants:
                saved_restaurants[item['restaurant_id']] = {}
            saved_restaurants[item['restaurant_id']][user_list['list_id']] = user_list['name']

    # 根據搜尋類型執行不同的搜尋
    if search_query:
        if search_type == 'name':
            restaurants = db.search_restaurant_by_name(search_query)
        elif search_type == 'address':
            restaurants = db.search_restaurant_by_address(search_query)
        else:
            restaurants = []
        
        total_restaurants = len(restaurants)
        # 手動進行分頁
        start_idx = (page - 1) * RESTAURANTS_PER_PAGE
        end_idx = start_idx + RESTAURANTS_PER_PAGE
        restaurants = restaurants[start_idx:end_idx]
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
        saved_restaurants=saved_restaurants,
        user_lists=user_lists,
        search_query=search_query,
        search_type=search_type,
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
        # 餐廳已經在 SQL 查詢中按 inserted_time 排序
        restaurants = db.get_list_items(user_list['list_id'])
        lists_with_restaurants.append({
            "list_id": user_list['list_id'],
            "name": user_list['name'],
            "restaurants": restaurants
        })
    
    # 獲取需要展開的清單 ID
    expanded_list = request.args.get('expanded_list', type=int)

    return render_template(
        "profile.html",
        lists_with_restaurants=lists_with_restaurants,
        expanded_list=expanded_list
    )

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
    
    search_type = request.args.get('search_type', 'name')
    search_query = request.args.get('search_query', '').strip()
    min_rating = request.args.get('min_rating', '')
    max_rating = request.args.get('max_rating', '')
    page = int(request.args.get('page', 1))
    
    # 每頁顯示的餐廳數量
    RESTAURANTS_PER_PAGE = 10

    # 根據搜尋類型執行不同的搜尋
    if search_type == 'rating' and min_rating and max_rating:
        try:
            min_rating = float(min_rating)
            max_rating = float(max_rating)
            ranked_restaurants = db.search_restaurant_by_avg_rating(min_rating, max_rating)
        except ValueError:
            ranked_restaurants = []
    elif search_query:
        if search_type == 'name':
            ranked_restaurants = db.search_restaurant_by_name(search_query)
        elif search_type == 'address':
            ranked_restaurants = db.search_restaurant_by_address(search_query)
        else:
            ranked_restaurants = []
    else:
        # 無搜尋條件時，獲取所有餐廳並按評分排序
        ranked_restaurants = db.fetch_query("""
            SELECT r.*, COUNT(p.post_id) as post_count, 
                   AVG(p.rating) as avg_rating
            FROM restaurant r
            LEFT JOIN post p ON r.restaurant_id = p.restaurant_id
            GROUP BY r.restaurant_id
            ORDER BY avg_rating DESC, post_count DESC
        """)

    total_count = len(ranked_restaurants)
    
    # 手動進行分頁
    start_idx = (page - 1) * RESTAURANTS_PER_PAGE
    end_idx = start_idx + RESTAURANTS_PER_PAGE
    ranked_restaurants = ranked_restaurants[start_idx:end_idx]
    
    total_pages = ceil(total_count / RESTAURANTS_PER_PAGE)
    
    return render_template(
        "rankings.html",
        ranked_restaurants=ranked_restaurants,
        search_query=search_query,
        search_type=search_type,
        min_rating=min_rating,
        max_rating=max_rating,
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
    
    user_id = session['user_id']
    restaurant_id = request.form['restaurant_id']
    list_id = request.form['list_id']
    page = request.form.get('page', 1)
    search_query = request.form.get('search_query', '')
    search_type = request.form.get('search_type', 'name')  # 接收 search_type
    
    # 檢查該餐廳是否已在選擇的 list 中
    list_items = db.get_list_items(list_id)
    if any(str(item['restaurant_id']) == str(restaurant_id) for item in list_items):
        flash("This restaurant is already in the selected list.", "warning")
    else:
        # 將餐廳添加到選擇的 list
        db.add_item_to_list(list_id, restaurant_id)
        flash("Restaurant added to your list successfully.", "success")

    # 將 search_type 傳回 home 頁面
    return redirect(url_for('home', page=page, search_query=search_query, search_type=search_type))

@app.route("/create_list", methods=["POST"])
def create_list():
    if 'username' not in session:
        return redirect("/")
    
    user_id = session['user_id']
    list_name = request.form.get('list_name', '').strip()
    
    if list_name:
        db.create_list(user_id, list_name)
        flash("New list created successfully.", "success")
    else:
        flash("List name cannot be empty.", "danger")
    
    return redirect("/profile")

@app.route("/rename_list", methods=["POST"])
def rename_list():
    if 'username' not in session:
        return redirect("/")
    
    list_id = request.form.get('list_id')
    new_name = request.form.get('new_name', '').strip()
    
    if new_name:
        db.update_list_name(list_id, new_name)
        flash("List renamed successfully.", "success")
    else:
        flash("List name cannot be empty.", "danger")
    
    # 重定向時傳遞展開的清單 ID
    return redirect(url_for("profile", expanded_list=list_id))

@app.route("/delete_list", methods=["POST"])
def delete_list():
    if 'username' not in session:
        return redirect("/")
    
    list_id = request.form.get('list_id')
    
    # First delete all items in the list
    list_items = db.get_list_items(list_id)
    for item in list_items:
        db.delete_item_from_list(list_id, item['restaurant_id'])
    
    # Then delete the list itself
    db.delete_list(list_id)
    flash("List deleted successfully.", "success")
    
    return redirect("/profile")

@app.route("/remove_from_list", methods=["POST"])
def remove_from_list():
    if 'username' not in session:
        return redirect("/")
    
    list_id = request.form['list_id']
    restaurant_id = request.form['restaurant_id']
    
    # 從清單中移除餐廳
    db.delete_item_from_list(list_id, restaurant_id)
    flash("Restaurant removed from your list.", "success")
    
    # 重定向時傳遞展開的清單 ID
    return redirect(url_for("profile", expanded_list=list_id))

if __name__ == "__main__":
    app.run(debug=True)