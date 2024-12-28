-- User Table
CREATE TABLE user (
    user_id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(50) NOT NULL,
    email VARCHAR(50),
    address NVARCHAR(50),
    gender ENUM('male', 'female'),
    birthday DATETIME
);


-- User List Table
CREATE TABLE list (
    list_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    name NVARCHAR(50) NOT NULL,
    modified_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user(user_id)
);

-- Restaurant Table
CREATE TABLE restaurant (
    restaurant_id INT PRIMARY KEY AUTO_INCREMENT,
    name NVARCHAR(50) NOT NULL,
    address NVARCHAR(50),
    contact_number CHAR(10)
);

-- List Item Table
CREATE TABLE list_item (
    list_id INT NOT NULL,
    restaurant_id INT NOT NULL,
    inserted_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (list_id, restaurant_id),
    FOREIGN KEY (list_id) REFERENCES list(list_id),
    FOREIGN KEY (restaurant_id) REFERENCES restaurant(restaurant_id)
);

-- IG Poster Table
CREATE TABLE ig_poster (
    poster_id VARCHAR(50) PRIMARY KEY,
    profile_link VARCHAR(100),
    fan_num INT,
    following_num INT,
    post_num INT
);

-- Post Table
CREATE TABLE post (
    post_id INT PRIMARY KEY AUTO_INCREMENT,
    poster_id VARCHAR(50) NOT NULL,
    restaurant_id INT NOT NULL,
    rating INT CHECK (rating >= 0 AND rating <= 5), -- 1~5 stars
    post_link VARCHAR(100),
    content TEXT,
    FOREIGN KEY (poster_id) REFERENCES ig_poster(poster_id),
    FOREIGN KEY (restaurant_id) REFERENCES restaurant(restaurant_id)
);
