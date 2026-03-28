import mysql.connector
from mysql.connector import Error
import bcrypt
import streamlit as st

DB_CONFIG = {
    "host":     st.secrets["DB_HOST"],
    "port":     3306,
    "user":     st.secrets["DB_USER"],
    "password": st.secrets["DB_PASSWORD"],
    "database": st.secrets["DB_NAME"],
}

FREE_DELIVERY_THRESHOLD = 1000
DELIVERY_CHARGE = 100

# All supported cities in Pakistan
PAKISTAN_CITIES = [
    "Karachi", "Lahore", "Islamabad", "Rawalpindi", "Faisalabad",
    "Multan", "Peshawar", "Quetta", "Sialkot", "Gujranwala",
    "Hyderabad", "Bahawalpur", "Sargodha", "Abbottabad", "Mardan",
]


class DatabaseManager:
    def __init__(self):
        self.conn = mysql.connector.connect(**DB_CONFIG)
        self.conn.autocommit = True
        self.create_tables()
        self.seed_data()

    def cursor(self):
        if not self.conn.is_connected():
            self.conn.reconnect(attempts=3, delay=1)
        return self.conn.cursor(dictionary=True)

    def execute(self, sql, params=None):
        cur = self.cursor()
        cur.execute(sql, params or ())
        return cur

    def fetchone(self, sql, params=None):
        return self.execute(sql, params).fetchone()

    def fetchall(self, sql, params=None):
        return self.execute(sql, params).fetchall()

    # ── CREATE TABLES ─────────────────────────────────────
    def create_tables(self):
        stmts = [
            # Users table
            """CREATE TABLE IF NOT EXISTS users (
                id          INT AUTO_INCREMENT PRIMARY KEY,
                name        VARCHAR(150) NOT NULL,
                email       VARCHAR(150) UNIQUE NOT NULL,
                password    VARCHAR(255) NOT NULL,
                role        ENUM('customer','restaurant','admin') DEFAULT 'customer',
                phone       VARCHAR(30),
                created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",

            # Restaurants table
            """CREATE TABLE IF NOT EXISTS restaurants (
                id          INT AUTO_INCREMENT PRIMARY KEY,
                owner_id    INT NOT NULL,
                name        VARCHAR(150) NOT NULL,
                cuisine     VARCHAR(80),
                description TEXT,
                address     TEXT,
                phone       VARCHAR(30),
                rating      FLOAT DEFAULT 0.0,
                is_open     TINYINT DEFAULT 1,
                created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE CASCADE
            )""",

            # ── NEW: Restaurant Branches ──────────────────
            """CREATE TABLE IF NOT EXISTS restaurant_branches (
                id            INT AUTO_INCREMENT PRIMARY KEY,
                restaurant_id INT NOT NULL,
                city          VARCHAR(100) NOT NULL,
                address       TEXT NOT NULL,
                phone         VARCHAR(30),
                is_open       TINYINT DEFAULT 1,
                created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (restaurant_id) REFERENCES restaurants(id) ON DELETE CASCADE
            )""",

            # ── NEW: City Delivery Settings (admin-controlled) ──
            """CREATE TABLE IF NOT EXISTS city_delivery_settings (
                id                  INT AUTO_INCREMENT PRIMARY KEY,
                city                VARCHAR(100) UNIQUE NOT NULL,
                delivery_time_min   INT DEFAULT 30,
                delivery_time_max   INT DEFAULT 45,
                delivery_charge     DECIMAL(10,2) DEFAULT 100.00,
                free_delivery_above DECIMAL(10,2) DEFAULT 1000.00,
                is_active           TINYINT DEFAULT 1,
                updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )""",

            # Menu items table
            """CREATE TABLE IF NOT EXISTS menu_items (
                id            INT AUTO_INCREMENT PRIMARY KEY,
                restaurant_id INT NOT NULL,
                name          VARCHAR(150) NOT NULL,
                description   TEXT,
                price         DECIMAL(10,2) NOT NULL,
                category      VARCHAR(80),
                available     TINYINT DEFAULT 1,
                created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (restaurant_id) REFERENCES restaurants(id) ON DELETE CASCADE
            )""",

            # Orders table — added branch_id + estimated_delivery_time
            """CREATE TABLE IF NOT EXISTS orders (
                id                      INT AUTO_INCREMENT PRIMARY KEY,
                restaurant_id           INT NOT NULL,
                branch_id               INT,
                customer_name           VARCHAR(150) NOT NULL,
                customer_email          VARCHAR(150) NOT NULL,
                customer_phone          VARCHAR(30),
                customer_country        VARCHAR(100),
                customer_city           VARCHAR(100),
                customer_address        TEXT,
                subtotal                DECIMAL(10,2) NOT NULL,
                delivery_charge         DECIMAL(10,2) DEFAULT 0,
                total                   DECIMAL(10,2) NOT NULL,
                estimated_delivery_time VARCHAR(50),
                status                  ENUM('pending','confirmed','preparing','ready','picked_up','delivered','cancelled') DEFAULT 'pending',
                notes                   TEXT,
                created_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (restaurant_id) REFERENCES restaurants(id),
                FOREIGN KEY (branch_id) REFERENCES restaurant_branches(id)
            )""",

            # Order items table
            """CREATE TABLE IF NOT EXISTS order_items (
                id        INT AUTO_INCREMENT PRIMARY KEY,
                order_id  INT NOT NULL,
                item_id   INT NOT NULL,
                item_name VARCHAR(150) NOT NULL,
                quantity  INT NOT NULL DEFAULT 1,
                price     DECIMAL(10,2) NOT NULL,
                FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
                FOREIGN KEY (item_id)  REFERENCES menu_items(id)
            )""",

            # Reviews table
            """CREATE TABLE IF NOT EXISTS reviews (
                id            INT AUTO_INCREMENT PRIMARY KEY,
                order_id      INT NOT NULL UNIQUE,
                restaurant_id INT NOT NULL,
                customer_name VARCHAR(150),
                rating        TINYINT NOT NULL,
                comment       TEXT,
                created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (order_id)      REFERENCES orders(id) ON DELETE CASCADE,
                FOREIGN KEY (restaurant_id) REFERENCES restaurants(id) ON DELETE CASCADE
            )""",
        ]
        for s in stmts:
            self.execute(s)

        # Migrate existing orders table to add new columns if upgrading
        try:
            self.execute("ALTER TABLE orders ADD COLUMN branch_id INT AFTER restaurant_id")
        except Exception:
            pass
        try:
            self.execute("ALTER TABLE orders ADD COLUMN estimated_delivery_time VARCHAR(50) AFTER total")
        except Exception:
            pass

    # ── SEED DATA ─────────────────────────────────────────
    def seed_data(self):
        if self.fetchone("SELECT COUNT(*) AS c FROM users")["c"] > 0:
            return

        def hp(pw): return bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()

        # Admin
        self.execute(
            "INSERT INTO users(name,email,password,role) VALUES(%s,%s,%s,'admin')",
            ("Admin", "admin@zabdelivers.com", hp("zabdelivers123"))
        )

        # Customers
        customers = [
            ("Ali Zaviyar",    "ali@customer.com",      hp("ali123")),
            ("Faiq Kashif",    "faiq@customer.com",     hp("faiq123")),
            ("Komail Khawaja", "komail@customer.com",   hp("komail123")),
            ("Abdullah Naeem", "abdullah@customer.com", hp("abdullah123")),
        ]
        for name, email, pw in customers:
            self.execute(
                "INSERT INTO users(name,email,password,role) VALUES(%s,%s,%s,'customer')",
                (name, email, pw)
            )

        # Restaurant owners
        restaurants = [
            ("Cheezious Owner",   "cheezious@restaurant.com", hp("cheezious123")),
            ("HN Foods Owner",    "hnfoods@restaurant.com",   hp("hnfoods123")),
            ("Asian Wok Owner",   "asianwok@restaurant.com",  hp("asianwok123")),
            ("Quetta Cafe Owner", "quetta@cafe.com",          hp("quetta123")),
        ]
        for name, email, pw in restaurants:
            self.execute(
                "INSERT INTO users(name,email,password,role) VALUES(%s,%s,%s,'restaurant')",
                (name, email, pw)
            )

        def uid(email):
            return self.fetchone("SELECT id FROM users WHERE email=%s", (email,))["id"]

        # Restaurants (head office)
        rest_data = [
            (uid("cheezious@restaurant.com"), "Cheezious", "Fast Food",
             "Pakistan's favourite fast food chain with signature burgers, crispy fried chicken and loaded fries.",
             "Head Office, Lahore", "042-111-111-222", 4.6),
            (uid("hnfoods@restaurant.com"), "HN Foods", "Desi",
             "Authentic Pakistani home-style cooking — karahi, nihari, biryani and traditional breads.",
             "Head Office, Lahore", "0300-1234567", 4.7),
            (uid("asianwok@restaurant.com"), "Asian Wok", "Chinese",
             "Premium Chinese cuisine featuring woks, soups, dim sum and authentic noodle dishes.",
             "Head Office, Lahore", "0321-9876543", 4.4),
            (uid("quetta@cafe.com"), "Quetta Royal Cafe", "Tea Cafe",
             "Famous Quetta-style kahwa, noon chai, Balochi doodh pati and traditional cafe snacks.",
             "Head Office, Quetta", "0333-4567890", 4.8),
        ]
        for oid, name, cuisine, desc, addr, phone, rating in rest_data:
            self.execute(
                "INSERT INTO restaurants(owner_id,name,cuisine,description,address,phone,rating) VALUES(%s,%s,%s,%s,%s,%s,%s)",
                (oid, name, cuisine, desc, addr, phone, rating)
            )

        def rid(name):
            return self.fetchone("SELECT id FROM restaurants WHERE name=%s", (name,))["id"]

        # ── Seed Branches ─────────────────────────────────
        branches = [
            # Cheezious — 3 cities
            (rid("Cheezious"), "Lahore",     "MM Alam Road, Gulberg III, Lahore",           "042-35761234"),
            (rid("Cheezious"), "Lahore",     "Johar Town, Block E, Lahore",                 "042-35769999"),
            (rid("Cheezious"), "Karachi",    "Clifton Block 5, Karachi",                    "021-35311234"),
            (rid("Cheezious"), "Karachi",    "Lucky One Mall, Karachi",                     "021-35319999"),
            (rid("Cheezious"), "Islamabad",  "F-7 Markaz, Islamabad",                       "051-2611234"),
            (rid("Cheezious"), "Rawalpindi", "Saddar, Rawalpindi",                          "051-5561234"),
            # HN Foods — 2 cities
            (rid("HN Foods"),  "Lahore",     "Liberty Market, Gulberg, Lahore",             "0300-1234567"),
            (rid("HN Foods"),  "Lahore",     "Model Town, Lahore",                          "0300-9876543"),
            (rid("HN Foods"),  "Islamabad",  "Jinnah Super Market, F-7, Islamabad",         "0300-1112233"),
            # Asian Wok — 2 cities
            (rid("Asian Wok"), "Lahore",     "MM Alam Road, Lahore",                        "0321-9876543"),
            (rid("Asian Wok"), "Karachi",    "Sea View, DHA Phase 6, Karachi",              "0321-1234567"),
            # Quetta Cafe — 3 cities
            (rid("Quetta Royal Cafe"), "Lahore",    "Gulberg Main Boulevard, Lahore",       "0333-4567890"),
            (rid("Quetta Royal Cafe"), "Islamabad", "Blue Area, Islamabad",                  "0333-1234567"),
            (rid("Quetta Royal Cafe"), "Quetta",    "Jinnah Road, Quetta",                  "0333-9876543"),
        ]
        for restaurant_id, city, address, phone in branches:
            self.execute(
                "INSERT INTO restaurant_branches(restaurant_id,city,address,phone) VALUES(%s,%s,%s,%s)",
                (restaurant_id, city, address, phone)
            )

        # ── Seed City Delivery Settings ───────────────────
        city_settings = [
            ("Karachi",     25, 40,  80,  800),
            ("Lahore",      20, 35,  70,  700),
            ("Islamabad",   30, 45, 100, 1000),
            ("Rawalpindi",  30, 45, 100, 1000),
            ("Faisalabad",  35, 50, 120, 1200),
            ("Multan",      35, 55, 120, 1200),
            ("Peshawar",    40, 60, 150, 1500),
            ("Quetta",      40, 60, 150, 1500),
            ("Sialkot",     35, 50, 120, 1200),
            ("Gujranwala",  30, 45, 100, 1000),
            ("Hyderabad",   35, 50, 120, 1200),
            ("Bahawalpur",  40, 60, 150, 1500),
            ("Sargodha",    40, 60, 150, 1500),
            ("Abbottabad",  45, 65, 150, 1500),
            ("Mardan",      45, 65, 150, 1500),
        ]
        for city, tmin, tmax, charge, free_above in city_settings:
            self.execute(
                """INSERT INTO city_delivery_settings
                   (city, delivery_time_min, delivery_time_max, delivery_charge, free_delivery_above)
                   VALUES(%s,%s,%s,%s,%s)
                   ON DUPLICATE KEY UPDATE city=city""",
                (city, tmin, tmax, charge, free_above)
            )

        # ── Menus ─────────────────────────────────────────
        cheezious_items = [
            ("Classic Beef Burger",          "Juicy beef patty with fresh lettuce, tomato and special sauce",        320,  "Burgers"),
            ("Zinger Burger",                "Crispy fried chicken fillet with spicy mayo and coleslaw",             350,  "Burgers"),
            ("Double Smash Burger",          "Two smashed beef patties with cheddar, pickles and mustard",           480,  "Burgers"),
            ("Chicken Club Burger",          "Grilled chicken with avocado, bacon and garlic aioli",                 420,  "Burgers"),
            ("Cheezious Special Burger",     "Signature burger with three sauces and double cheese",                 550,  "Burgers"),
            ("Crispy Fried Chicken (2 pcs)", "Golden crispy fried chicken with original seasoning",                  380,  "Fried Chicken"),
            ("Hot Wings (6 pcs)",            "Spicy hot wings tossed in signature buffalo sauce",                    290,  "Fried Chicken"),
            ("Chicken Strips (4 pcs)",       "Tender chicken strips with honey mustard dip",                         320,  "Fried Chicken"),
            ("Loaded Fries",                 "Crispy fries topped with cheese sauce and jalapenos",                  220,  "Sides"),
            ("Regular Fries",                "Classic salted crispy fries",                                          120,  "Sides"),
            ("Coleslaw",                     "Creamy homemade coleslaw",                                              80,  "Sides"),
            ("Onion Rings",                  "Crispy golden battered onion rings",                                   160,  "Sides"),
            ("Chocolate Shake",              "Thick creamy chocolate milkshake",                                     250,  "Drinks"),
            ("Strawberry Shake",             "Fresh strawberry blended milkshake",                                   250,  "Drinks"),
            ("Vanilla Shake",               "Classic vanilla milkshake",                                             230,  "Drinks"),
            ("Cold Coffee",                  "Chilled coffee blended with ice cream",                                 220,  "Drinks"),
            ("Family Deal (4 burgers+fries)","Four classic burgers with four regular fries",                        1200,  "Deals"),
            ("Student Deal",                 "1 burger + fries + drink",                                             450,  "Deals"),
        ]
        for name, desc, price, cat in cheezious_items:
            self.execute(
                "INSERT INTO menu_items(restaurant_id,name,description,price,category) VALUES(%s,%s,%s,%s,%s)",
                (rid("Cheezious"), name, desc, price, cat)
            )

        hn_items = [
            ("Chicken Karahi",       "Tender chicken cooked in tomato-based spiced gravy",              750,  "Karahi"),
            ("Beef Karahi",          "Slow cooked beef karahi with ginger and green chilli",            850,  "Karahi"),
            ("Mutton Karahi",        "Premium mutton karahi cooked in traditional style",              1100,  "Karahi"),
            ("White Karahi",         "Cream-based karahi with minimal spices — mild and rich",          780,  "Karahi"),
            ("Beef Nihari",          "Slow overnight cooked beef nihari with nalli",                    680,  "Nihari & Haleem"),
            ("Mutton Nihari",        "Traditional Lahori mutton nihari served with sheermal",           780,  "Nihari & Haleem"),
            ("Beef Haleem",          "Slow cooked lentil and beef haleem garnished with ginger",        350,  "Nihari & Haleem"),
            ("Chicken Biryani",      "Fragrant basmati rice with spiced chicken and saffron",           450,  "Biryani & Rice"),
            ("Mutton Biryani",       "Dum-cooked mutton biryani with whole spices",                    550,  "Biryani & Rice"),
            ("Channa Rice",          "White rice served with spiced chickpea curry",                    280,  "Biryani & Rice"),
            ("Tandoori Naan",        "Fresh clay oven baked naan",                                       50,  "Bread"),
            ("Roghni Naan",          "Sesame topped butter naan",                                        70,  "Bread"),
            ("Sheermal",             "Saffron-flavoured sweet naan bread",                               80,  "Bread"),
            ("Paratha",              "Flaky layered whole wheat paratha",                                60,  "Bread"),
            ("Kheer",                "Traditional rice pudding with cardamom and almonds",              150,  "Desserts"),
            ("Gulab Jamun (4 pcs)",  "Soft milk-solid dumplings in rose syrup",                        120,  "Desserts"),
            ("Lassi (Sweet)",        "Chilled sweet yogurt drink",                                      100,  "Drinks"),
            ("Lassi (Salted)",       "Refreshing salted yogurt drink",                                  100,  "Drinks"),
            ("Rooh Afza Milk",       "Chilled milk with rose syrup",                                     80,  "Drinks"),
        ]
        for name, desc, price, cat in hn_items:
            self.execute(
                "INSERT INTO menu_items(restaurant_id,name,description,price,category) VALUES(%s,%s,%s,%s,%s)",
                (rid("HN Foods"), name, desc, price, cat)
            )

        asian_items = [
            ("Hot & Sour Soup",          "Tangy spicy soup with mushrooms, bamboo shoots and egg",     280, "Soups"),
            ("Sweet Corn Chicken Soup",  "Creamy corn soup with shredded chicken",                     260, "Soups"),
            ("Tom Yum Soup",             "Thai-style spicy lemongrass soup with prawns",               320, "Soups"),
            ("Wonton Soup",              "Delicate wontons in clear chicken broth",                    290, "Soups"),
            ("Chicken Chow Mein",        "Stir-fried noodles with chicken, peppers and soy sauce",    480, "Noodles"),
            ("Beef Lo Mein",             "Soft noodles with tender beef strips and vegetables",        540, "Noodles"),
            ("Shrimp Hakka Noodles",     "Spicy hakka-style noodles with prawns",                     580, "Noodles"),
            ("Vegetable Fried Noodles",  "Wok-tossed noodles with seasonal vegetables",               380, "Noodles"),
            ("Chicken Fried Rice",       "Classic wok fried rice with chicken and eggs",              420, "Rice"),
            ("Beef Fried Rice",          "Fragrant fried rice with marinated beef",                   480, "Rice"),
            ("Kung Pao Chicken",         "Spicy stir-fried chicken with peanuts and dried chilies",   520, "Mains"),
            ("Mongolian Beef",           "Tender beef in sweet soy and ginger sauce",                 580, "Mains"),
            ("Sweet & Sour Chicken",     "Crispy chicken pieces in tangy sweet and sour sauce",       490, "Mains"),
            ("Chicken Dumplings (6 pcs)","Steamed chicken and cabbage dumplings",                     350, "Dim Sum"),
            ("Prawn Har Gow (4 pcs)",    "Crystal skin prawn dumplings",                              380, "Dim Sum"),
            ("Spring Rolls (4 pcs)",     "Crispy vegetable and chicken spring rolls",                 280, "Dim Sum"),
            ("Jasmine Green Tea",        "Delicate floral Chinese green tea",                         120, "Drinks"),
            ("Lychee Juice",             "Fresh chilled lychee juice",                                150, "Drinks"),
        ]
        for name, desc, price, cat in asian_items:
            self.execute(
                "INSERT INTO menu_items(restaurant_id,name,description,price,category) VALUES(%s,%s,%s,%s,%s)",
                (rid("Asian Wok"), name, desc, price, cat)
            )

        quetta_items = [
            ("Quetta Doodh Pati",          "Rich creamy tea brewed Quetta-style with full cream milk",    120, "Chai & Kahwa"),
            ("Green Kahwa",                "Traditional cardamom and saffron green tea with almonds",      150, "Chai & Kahwa"),
            ("Noon Chai (Pink Tea)",       "Authentic Kashmiri pink salty tea with pistachios",            160, "Chai & Kahwa"),
            ("Kashmiri Chai",              "Creamy pink Kashmiri chai with cardamom and cinnamon",         150, "Chai & Kahwa"),
            ("Sheer Chai",                 "Balochi salty milk tea with a rich buttery flavour",           140, "Chai & Kahwa"),
            ("Masala Chai",                "Spiced tea brewed with ginger, cardamom and cloves",           100, "Chai & Kahwa"),
            ("Qehwa",                      "Traditional Afghan herbal tea with saffron",                   130, "Chai & Kahwa"),
            ("Baaqarkhani",                "Traditional crispy layered bread from Quetta",                  80, "Snacks"),
            ("Sheermal",                   "Saffron sweet bread — Quetta style",                            90, "Snacks"),
            ("Naan Channay",               "Fresh naan with spiced chickpeas",                             180, "Snacks"),
            ("Aloo Bokhara Samosa (4 pcs)","Crispy samosas filled with spiced potato and plum",            160, "Snacks"),
            ("Club Sandwich",              "Triple layered chicken club sandwich",                          280, "Snacks"),
            ("Firni",                      "Chilled rice flour pudding with rose water and pistachios",    180, "Desserts"),
            ("Shahi Tukray",               "Fried bread soaked in saffron cream and dry fruits",           220, "Desserts"),
            ("Sattu Sherbet",              "Traditional energy drink made from roasted barley flour",       120, "Cold Drinks"),
            ("Rose Sharbat",               "Chilled rose syrup with basil seeds and milk",                 130, "Cold Drinks"),
            ("Mango Lassi",                "Thick blended mango yogurt drink",                             150, "Cold Drinks"),
        ]
        for name, desc, price, cat in quetta_items:
            self.execute(
                "INSERT INTO menu_items(restaurant_id,name,description,price,category) VALUES(%s,%s,%s,%s,%s)",
                (rid("Quetta Royal Cafe"), name, desc, price, cat)
            )

        print("Seed data loaded successfully.")

    # ── USER QUERIES ──────────────────────────────────────
    def get_user_by_email(self, email):
        return self.fetchone("SELECT * FROM users WHERE email=%s", (email,))

    def create_user(self, name, email, password, role="customer", phone=""):
        try:
            self.execute(
                "INSERT INTO users(name,email,password,role,phone) VALUES(%s,%s,%s,%s,%s)",
                (name, email, password, role, phone)
            )
            return True
        except Error:
            return False

    def get_all_customers(self):
        return self.fetchall("SELECT * FROM users WHERE role='customer' ORDER BY created_at DESC")

    # ── RESTAURANT QUERIES ────────────────────────────────
    def get_all_restaurants(self):
        return self.fetchall("SELECT * FROM restaurants WHERE is_open=1 ORDER BY rating DESC")

    def get_all_restaurants_admin(self):
        return self.fetchall("""
            SELECT r.*, u.email AS owner_email
            FROM restaurants r JOIN users u ON r.owner_id=u.id
            ORDER BY r.name
        """)

    def get_restaurant_by_id(self, rid):
        return self.fetchone("SELECT * FROM restaurants WHERE id=%s", (rid,))

    def get_restaurant_by_owner(self, owner_id):
        return self.fetchone("SELECT * FROM restaurants WHERE owner_id=%s", (owner_id,))

    def create_restaurant(self, owner_id, name, cuisine, description, address, phone):
        self.execute(
            "INSERT INTO restaurants(owner_id,name,cuisine,description,address,phone) VALUES(%s,%s,%s,%s,%s,%s)",
            (owner_id, name, cuisine, description, address, phone)
        )

    def update_restaurant_status(self, restaurant_id, is_open):
        self.execute("UPDATE restaurants SET is_open=%s WHERE id=%s", (is_open, restaurant_id))

    # ── BRANCH QUERIES ────────────────────────────────────
    def get_branches_by_restaurant(self, restaurant_id):
        return self.fetchall(
            "SELECT * FROM restaurant_branches WHERE restaurant_id=%s ORDER BY city, address",
            (restaurant_id,)
        )

    def get_branches_by_city(self, restaurant_id, city):
        return self.fetchall(
            "SELECT * FROM restaurant_branches WHERE restaurant_id=%s AND city=%s AND is_open=1",
            (restaurant_id, city)
        )

    def get_all_branches_admin(self):
        return self.fetchall("""
            SELECT b.*, r.name AS restaurant_name
            FROM restaurant_branches b
            JOIN restaurants r ON b.restaurant_id = r.id
            ORDER BY r.name, b.city
        """)

    def add_branch(self, restaurant_id, city, address, phone):
        self.execute(
            "INSERT INTO restaurant_branches(restaurant_id,city,address,phone) VALUES(%s,%s,%s,%s)",
            (restaurant_id, city, address, phone)
        )

    def toggle_branch(self, branch_id):
        self.execute(
            "UPDATE restaurant_branches SET is_open=IF(is_open=1,0,1) WHERE id=%s",
            (branch_id,)
        )

    def delete_branch(self, branch_id):
        self.execute("DELETE FROM restaurant_branches WHERE id=%s", (branch_id,))

    def get_cities_with_restaurant(self, restaurant_id):
        """Get distinct cities where this restaurant has active branches."""
        rows = self.fetchall(
            "SELECT DISTINCT city FROM restaurant_branches WHERE restaurant_id=%s AND is_open=1 ORDER BY city",
            (restaurant_id,)
        )
        return [r["city"] for r in rows]

    def get_all_active_cities(self):
        """Get all cities that have at least one restaurant branch."""
        rows = self.fetchall("""
            SELECT DISTINCT b.city
            FROM restaurant_branches b
            JOIN restaurants r ON b.restaurant_id=r.id
            WHERE b.is_open=1 AND r.is_open=1
            ORDER BY b.city
        """)
        return [r["city"] for r in rows]

    # ── CITY DELIVERY SETTINGS ────────────────────────────
    def get_city_delivery_settings(self, city):
        return self.fetchone(
            "SELECT * FROM city_delivery_settings WHERE city=%s AND is_active=1",
            (city,)
        )

    def get_all_city_settings(self):
        return self.fetchall(
            "SELECT * FROM city_delivery_settings ORDER BY city"
        )

    def update_city_delivery_settings(self, city, tmin, tmax, charge, free_above):
        self.execute(
            """INSERT INTO city_delivery_settings
               (city, delivery_time_min, delivery_time_max, delivery_charge, free_delivery_above)
               VALUES(%s,%s,%s,%s,%s)
               ON DUPLICATE KEY UPDATE
               delivery_time_min=%s, delivery_time_max=%s,
               delivery_charge=%s, free_delivery_above=%s""",
            (city, tmin, tmax, charge, free_above,
             tmin, tmax, charge, free_above)
        )

    def toggle_city_active(self, city, is_active):
        self.execute(
            "UPDATE city_delivery_settings SET is_active=%s WHERE city=%s",
            (is_active, city)
        )

    # ── MENU QUERIES ──────────────────────────────────────
    def get_menu(self, restaurant_id):
        return self.fetchall(
            "SELECT * FROM menu_items WHERE restaurant_id=%s AND available=1 ORDER BY category, name",
            (restaurant_id,)
        )

    def get_all_menu(self, restaurant_id):
        return self.fetchall(
            "SELECT * FROM menu_items WHERE restaurant_id=%s ORDER BY category, name",
            (restaurant_id,)
        )

    def add_menu_item(self, restaurant_id, name, description, price, category):
        self.execute(
            "INSERT INTO menu_items(restaurant_id,name,description,price,category) VALUES(%s,%s,%s,%s,%s)",
            (restaurant_id, name, description, price, category)
        )

    def update_menu_item_price(self, item_id, new_price):
        self.execute("UPDATE menu_items SET price=%s WHERE id=%s", (new_price, item_id))

    def toggle_item_availability(self, item_id):
        self.execute("UPDATE menu_items SET available=IF(available=1,0,1) WHERE id=%s", (item_id,))

    def delete_menu_item(self, item_id):
        self.execute("DELETE FROM menu_items WHERE id=%s", (item_id,))

    # ── ORDER QUERIES ─────────────────────────────────────
    def create_order(self, restaurant_id, branch_id,
                     customer_name, customer_email, customer_phone,
                     customer_country, customer_city, customer_address,
                     subtotal, delivery_charge, total,
                     estimated_delivery_time, notes, items):
        cur = self.cursor()
        cur.execute(
            """INSERT INTO orders
               (restaurant_id, branch_id, customer_name, customer_email, customer_phone,
                customer_country, customer_city, customer_address,
                subtotal, delivery_charge, total, estimated_delivery_time, notes)
               VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (restaurant_id, branch_id, customer_name, customer_email, customer_phone,
             customer_country, customer_city, customer_address,
             subtotal, delivery_charge, total, estimated_delivery_time, notes)
        )
        order_id = cur.lastrowid
        cur.executemany(
            "INSERT INTO order_items(order_id,item_id,item_name,quantity,price) VALUES(%s,%s,%s,%s,%s)",
            [(order_id, i["item_id"], i["name"], i["quantity"], i["price"]) for i in items]
        )
        return order_id

    def get_orders_by_restaurant(self, restaurant_id):
        return self.fetchall(
            """SELECT o.*, b.city AS branch_city, b.address AS branch_address
               FROM orders o
               LEFT JOIN restaurant_branches b ON o.branch_id=b.id
               WHERE o.restaurant_id=%s ORDER BY o.created_at DESC""",
            (restaurant_id,)
        )

    def get_order_items(self, order_id):
        return self.fetchall("SELECT * FROM order_items WHERE order_id=%s", (order_id,))

    def update_order_status(self, order_id, status):
        self.execute("UPDATE orders SET status=%s WHERE id=%s", (status, order_id))

    def get_all_orders(self):
        return self.fetchall("""
            SELECT o.*, r.name AS restaurant_name,
                   b.city AS branch_city, b.address AS branch_address
            FROM orders o
            JOIN restaurants r ON o.restaurant_id=r.id
            LEFT JOIN restaurant_branches b ON o.branch_id=b.id
            ORDER BY o.created_at DESC
        """)

    def get_order_by_id(self, order_id):
        return self.fetchone("SELECT * FROM orders WHERE id=%s", (order_id,))

    # ── REVIEW QUERIES ────────────────────────────────────
    def add_review(self, order_id, restaurant_id, customer_name, rating, comment):
        try:
            self.execute(
                "INSERT INTO reviews(order_id,restaurant_id,customer_name,rating,comment) VALUES(%s,%s,%s,%s,%s)",
                (order_id, restaurant_id, customer_name, rating, comment)
            )
            return True
        except Error:
            return False

    def get_reviews_by_restaurant(self, restaurant_id):
        return self.fetchall(
            "SELECT * FROM reviews WHERE restaurant_id=%s ORDER BY created_at DESC",
            (restaurant_id,)
        )

    def has_reviewed(self, order_id):
        r = self.fetchone("SELECT id FROM reviews WHERE order_id=%s", (order_id,))
        return r is not None

    # ── ADMIN STATS ───────────────────────────────────────
    def get_admin_stats(self):
        return {
            "total_orders":      self.fetchone("SELECT COUNT(*) AS c FROM orders")["c"],
            "total_revenue":     float(self.fetchone("SELECT COALESCE(SUM(total),0) AS c FROM orders WHERE status='delivered'")["c"]),
            "total_customers":   self.fetchone("SELECT COUNT(*) AS c FROM users WHERE role='customer'")["c"],
            "total_restaurants": self.fetchone("SELECT COUNT(*) AS c FROM restaurants")["c"],
            "pending_orders":    self.fetchone("SELECT COUNT(*) AS c FROM orders WHERE status='pending'")["c"],
            "total_branches":    self.fetchone("SELECT COUNT(*) AS c FROM restaurant_branches")["c"],
        }

    def get_revenue_by_restaurant(self):
        return self.fetchall("""
            SELECT r.name, COALESCE(SUM(o.total),0) AS revenue, COUNT(o.id) AS orders
            FROM restaurants r
            LEFT JOIN orders o ON r.id=o.restaurant_id AND o.status='delivered'
            GROUP BY r.id, r.name ORDER BY revenue DESC
        """)

    def get_orders_by_status(self):
        return self.fetchall("SELECT status, COUNT(*) AS total FROM orders GROUP BY status")
