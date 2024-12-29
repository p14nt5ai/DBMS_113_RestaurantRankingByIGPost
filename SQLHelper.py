import mysql.connector
from mysql.connector import Error

class SQLHelper:
    def __init__(self, host, user, password, database):
        try:
            self.connection = mysql.connector.connect(
                host=host,
                user=user,
                password=password,
                database=database
            )
            if self.connection.is_connected():
                print('Connected to MySQL database')
        except Error as e:
            print(f"Error: {e}")

    def execute_query(self, query, params=None):
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, params)
            self.connection.commit()
            return cursor
        except Error as e:
            print(f"Error: {e}")

    def fetch_query(self, query, params=None):
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute(query, params)
            return cursor.fetchall()
        except Error as e:
            print(f"Error: {e}")

    # User Operations
    def add_user(self, username, password, email, address, gender, birthday):
        query = """
            INSERT INTO user (username, password, email, address, gender, birthday)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        self.execute_query(query, (username, password, email, address, gender, birthday))

    def delete_user(self, user_id):
        query = "DELETE FROM user WHERE user_id = %s"
        self.execute_query(query, (user_id,))

    def update_user(self, user_id, **kwargs):
        updates = ', '.join(f"{k} = %s" for k in kwargs.keys())
        query = f"UPDATE user SET {updates} WHERE user_id = %s"
        self.execute_query(query, (*kwargs.values(), user_id))

    # List Operations
    def create_list(self, user_id, name):
        query = "INSERT INTO list (user_id, name) VALUES (%s, %s)"
        self.execute_query(query, (user_id, name))

    def delete_list(self, list_id):
        query = "DELETE FROM list WHERE list_id = %s"
        self.execute_query(query, (list_id,))
        
    def update_list_name(self, list_id, new_name):
        query = "UPDATE list SET name = %s WHERE list_id = %s"
        self.execute_query(query, (new_name, list_id))

    # List Item Operations
    def add_item_to_list(self, list_id, restaurant_id):
        query = "INSERT INTO list_item (list_id, restaurant_id) VALUES (%s, %s)"
        self.execute_query(query, (list_id, restaurant_id))

    def delete_item_from_list(self, list_id, restaurant_id):
        query = "DELETE FROM list_item WHERE list_id = %s AND restaurant_id = %s"
        self.execute_query(query, (list_id, restaurant_id))

    # Searching queries
    def get_user(self, username, password):
        query = "SELECT * FROM user WHERE username = %s AND password = %s"
        return self.fetch_query(query, (username, password))
    
    def get_user_lists(self, user_id):
        query = "SELECT * FROM list WHERE user_id = %s"
        return self.fetch_query(query, (user_id,))
    
    def get_list_items(self, list_id):
        query = """
            SELECT li.restaurant_id, r.name, r.address, r.contact_number
            FROM list_item li
            JOIN restaurant r ON li.restaurant_id = r.restaurant_id
            WHERE li.list_id = %s
        """
        return self.fetch_query(query, (list_id,))

    # Restaurant Search
    def search_restaurant_by_name(self, keyword):
        query = """
            SELECT r.*, COUNT(p.post_id) AS post_count, AVG(p.rating) AS avg_rating
            FROM restaurant r
            LEFT JOIN post p ON r.restaurant_id = p.restaurant_id
            WHERE r.name LIKE %s
            GROUP BY r.restaurant_id
        """
        return self.fetch_query(query, (f"%{keyword}%",))

    def search_restaurant_by_address(self, keyword):
        query = """
            SELECT r.*, COUNT(p.post_id) AS post_count, AVG(p.rating) AS avg_rating
            FROM restaurant r
            LEFT JOIN post p ON r.restaurant_id = p.restaurant_id
            WHERE r.address LIKE %s
            GROUP BY r.restaurant_id
        """
        return self.fetch_query(query, (f"%{keyword}%",))

    def search_restaurant_by_avg_rating(self, min_rating, max_rating):
        query = """
            SELECT r.*, AVG(p.rating) AS avg_rating, COUNT(p.post_id) as post_count
            FROM restaurant r
            JOIN post p ON r.restaurant_id = p.restaurant_id
            GROUP BY r.restaurant_id
            HAVING avg_rating BETWEEN %s AND %s
        """
        return self.fetch_query(query, (min_rating, max_rating))

    # Post and IG Poster
    def get_posts_for_restaurant(self, restaurant_id):
        query = "SELECT * FROM post WHERE restaurant_id = %s"
        return self.fetch_query(query, (restaurant_id,))

    def get_ig_poster_for_post(self, post_id):
        query = """
            SELECT ig.*
            FROM ig_poster ig
            JOIN post p ON ig.poster_id = p.poster_id
            WHERE p.post_id = %s
        """
        return self.fetch_query(query, (post_id,))

    def close_connection(self):
        if self.connection.is_connected():
            self.connection.close()
            print('MySQL connection closed')

# Example Usage
if __name__ == '__main__':
    db = SQLHelper('localhost', 'root', 'password', 'test_db')
    
    # User operations
    db.add_user('john_doe', 'password123', 'john@example.com', '123 Street', 'male', '1990-01-01')
    new_user = db.get_user('john_doe', 'password123')
    print(new_user)
    
    user_id = new_user[0]['user_id'] if new_user else None
    db.update_user(user_id, email='new_email@example.com')
    
    new_user = db.get_user('john_doe', 'password123')
    print(new_user)
    
    # List operations
    db.create_list(user_id, 'Favorite Restaurants')
    user_lists = db.get_user_lists(user_id)
    list_id = user_lists[0]['list_id'] if user_lists else None
    print(db.get_user_lists(user_id))
    print(db.get_list_items(list_id))
    
    db.update_list_name(list_id, 'Top Picks')
    db.add_item_to_list(list_id, 10)
    print(db.get_user_lists(user_id))
    print(db.get_list_items(list_id))
    
    # Restaurant search
    print(db.search_restaurant_by_name('Pizza'))
    print(db.search_restaurant_by_address('Main Street'))
    print(db.search_restaurant_by_avg_rating(3, 5))
    
    # Post and IG Poster
    print(db.get_posts_for_restaurant(1))
    print(db.get_ig_poster_for_post(1))
    
    db.delete_item_from_list(list_id, 10)
    db.delete_list(list_id)
    db.delete_user(user_id)
    db.close_connection()
