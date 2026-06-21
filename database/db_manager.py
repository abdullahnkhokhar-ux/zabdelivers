import os
import bcrypt
from supabase import create_client, Client

# ── CONFIG ─────────────────────────────────────────────
# Priority: Railway env vars → Streamlit secrets → empty string
def _get_secret(key):
    val = os.environ.get(key, "")
    if val:
        return val
    try:
        import streamlit as st
        return st.secrets.get(key, "")
    except Exception:
        return ""

SUPABASE_URL = _get_secret("SUPABASE_URL")
SUPABASE_KEY = _get_secret("SUPABASE_KEY")

FREE_DELIVERY_THRESHOLD = 1000
DELIVERY_CHARGE = 100

PAKISTAN_CITIES = [
    "Karachi", "Lahore", "Islamabad", "Rawalpindi", "Faisalabad",
    "Multan", "Peshawar", "Quetta", "Sialkot", "Gujranwala",
    "Hyderabad", "Bahawalpur", "Sargodha", "Abbottabad", "Mardan",
]


class DatabaseManager:
    def __init__(self):
        self.sb: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        # Tables are created via Supabase SQL editor / migrations (see supabase_schema.sql)
        self._seed_if_empty()

    # ── LOW-LEVEL HELPERS ────────────────────────────────

    def _table(self, name):
        return self.sb.table(name)

    def _fetchone(self, table, filters: dict):
        q = self._table(table).select("*")
        for col, val in filters.items():
            q = q.eq(col, val)
        res = q.limit(1).execute()
        return res.data[0] if res.data else None

    def _fetchall(self, table, filters: dict = None, order_col=None, order_desc=False):
        q = self._table(table).select("*")
        if filters:
            for col, val in filters.items():
                q = q.eq(col, val)
        if order_col:
            q = q.order(order_col, desc=order_desc)
        return q.execute().data

    def _rpc(self, fn_name, params=None):
        """Call a Supabase/Postgres RPC function."""
        return self.sb.rpc(fn_name, params or {}).execute().data

    # ── SEED ─────────────────────────────────────────────
    def _seed_if_empty(self):
        res = self._table("users").select("id").limit(1).execute()
        if res.data:
            return  # already seeded

        def hp(pw):
            return bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()

        # Admin
        self._table("users").insert({
            "name": "Admin", "email": "admin@zabdelivers.com",
            "password": hp("zabdelivers123"), "role": "admin"
        }).execute()

        # Customers
        customers = [
            ("Ali Zaviyar",    "ali@customer.com",      hp("ali123")),
            ("Faiq Kashif",    "faiq@customer.com",     hp("faiq123")),
            ("Komail Khawaja", "komail@customer.com",   hp("komail123")),
            ("Abdullah Naeem", "abdullah@customer.com", hp("abdullah123")),
        ]
        for name, email, pw in customers:
            self._table("users").insert({
                "name": name, "email": email, "password": pw, "role": "customer"
            }).execute()

        # Restaurant owners
        owners = [
            ("Cheezious Owner",   "cheezious@restaurant.com", hp("cheezious123")),
            ("HN Foods Owner",    "hnfoods@restaurant.com",   hp("hnfoods123")),
            ("Asian Wok Owner",   "asianwok@restaurant.com",  hp("asianwok123")),
            ("Quetta Cafe Owner", "quetta@cafe.com",          hp("quetta123")),
        ]
        for name, email, pw in owners:
            self._table("users").insert({
                "name": name, "email": email, "password": pw, "role": "restaurant"
            }).execute()

        def uid(email):
            return self._fetchone("users", {"email": email})["id"]

        # Restaurants
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
            self._table("restaurants").insert({
                "owner_id": oid, "name": name, "cuisine": cuisine,
                "description": desc, "address": addr, "phone": phone, "rating": rating
            }).execute()

        def rid(name):
            return self._fetchone("restaurants", {"name": name})["id"]

        # Branches
        branches = [
            (rid("Cheezious"), "Lahore",     "MM Alam Road, Gulberg III, Lahore",   "042-35761234"),
            (rid("Cheezious"), "Lahore",     "Johar Town, Block E, Lahore",          "042-35769999"),
            (rid("Cheezious"), "Karachi",    "Clifton Block 5, Karachi",             "021-35311234"),
            (rid("Cheezious"), "Karachi",    "Lucky One Mall, Karachi",              "021-35319999"),
            (rid("Cheezious"), "Islamabad",  "F-7 Markaz, Islamabad",               "051-2611234"),
            (rid("Cheezious"), "Rawalpindi", "Saddar, Rawalpindi",                  "051-5561234"),
            (rid("HN Foods"),  "Lahore",     "Liberty Market, Gulberg, Lahore",     "0300-1234567"),
            (rid("HN Foods"),  "Lahore",     "Model Town, Lahore",                  "0300-9876543"),
            (rid("HN Foods"),  "Islamabad",  "Jinnah Super Market, F-7, Islamabad", "0300-1112233"),
            (rid("Asian Wok"), "Lahore",     "MM Alam Road, Lahore",                "0321-9876543"),
            (rid("Asian Wok"), "Karachi",    "Sea View, DHA Phase 6, Karachi",      "0321-1234567"),
            (rid("Quetta Royal Cafe"), "Lahore",    "Gulberg Main Boulevard, Lahore", "0333-4567890"),
            (rid("Quetta Royal Cafe"), "Islamabad", "Blue Area, Islamabad",           "0333-1234567"),
            (rid("Quetta Royal Cafe"), "Quetta",    "Jinnah Road, Quetta",            "0333-9876543"),
        ]
        for restaurant_id, city, address, phone in branches:
            self._table("restaurant_branches").insert({
                "restaurant_id": restaurant_id, "city": city,
                "address": address, "phone": phone
            }).execute()

        # City delivery settings
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
            self._table("city_delivery_settings").upsert({
                "city": city, "delivery_time_min": tmin, "delivery_time_max": tmax,
                "delivery_charge": charge, "free_delivery_above": free_above
            }, on_conflict="city").execute()

        # Menus
        cheezious_items = [
            ("Classic Beef Burger",          "Juicy beef patty with fresh lettuce, tomato and special sauce",       320,  "Burgers"),
            ("Zinger Burger",                "Crispy fried chicken fillet with spicy mayo and coleslaw",            350,  "Burgers"),
            ("Double Smash Burger",          "Two smashed beef patties with cheddar, pickles and mustard",          480,  "Burgers"),
            ("Chicken Club Burger",          "Grilled chicken with avocado, bacon and garlic aioli",                420,  "Burgers"),
            ("Cheezious Special Burger",     "Signature burger with three sauces and double cheese",                550,  "Burgers"),
            ("Crispy Fried Chicken (2 pcs)", "Golden crispy fried chicken with original seasoning",                 380,  "Fried Chicken"),
            ("Hot Wings (6 pcs)",            "Spicy hot wings tossed in signature buffalo sauce",                   290,  "Fried Chicken"),
            ("Chicken Strips (4 pcs)",       "Tender chicken strips with honey mustard dip",                        320,  "Fried Chicken"),
            ("Loaded Fries",                 "Crispy fries topped with cheese sauce and jalapenos",                 220,  "Sides"),
            ("Regular Fries",                "Classic salted crispy fries",                                         120,  "Sides"),
            ("Coleslaw",                     "Creamy homemade coleslaw",                                             80,  "Sides"),
            ("Onion Rings",                  "Crispy golden battered onion rings",                                  160,  "Sides"),
            ("Chocolate Shake",              "Thick creamy chocolate milkshake",                                    250,  "Drinks"),
            ("Strawberry Shake",             "Fresh strawberry blended milkshake",                                  250,  "Drinks"),
            ("Vanilla Shake",                "Classic vanilla milkshake",                                           230,  "Drinks"),
            ("Cold Coffee",                  "Chilled coffee blended with ice cream",                               220,  "Drinks"),
            ("Family Deal (4 burgers+fries)","Four classic burgers with four regular fries",                       1200,  "Deals"),
            ("Student Deal",                 "1 burger + fries + drink",                                            450,  "Deals"),
        ]
        for name, desc, price, cat in cheezious_items:
            self._table("menu_items").insert({
                "restaurant_id": rid("Cheezious"), "name": name,
                "description": desc, "price": price, "category": cat
            }).execute()

        hn_items = [
            ("Chicken Karahi",       "Tender chicken cooked in tomato-based spiced gravy",               750,  "Karahi"),
            ("Beef Karahi",          "Slow cooked beef karahi with ginger and green chilli",             850,  "Karahi"),
            ("Mutton Karahi",        "Premium mutton karahi cooked in traditional style",               1100,  "Karahi"),
            ("White Karahi",         "Cream-based karahi with minimal spices — mild and rich",           780,  "Karahi"),
            ("Beef Nihari",          "Slow overnight cooked beef nihari with nalli",                     680,  "Nihari & Haleem"),
            ("Mutton Nihari",        "Traditional Lahori mutton nihari served with sheermal",            780,  "Nihari & Haleem"),
            ("Beef Haleem",          "Slow cooked lentil and beef haleem garnished with ginger",         350,  "Nihari & Haleem"),
            ("Chicken Biryani",      "Fragrant basmati rice with spiced chicken and saffron",            450,  "Biryani & Rice"),
            ("Mutton Biryani",       "Dum-cooked mutton biryani with whole spices",                     550,  "Biryani & Rice"),
            ("Channa Rice",          "White rice served with spiced chickpea curry",                     280,  "Biryani & Rice"),
            ("Tandoori Naan",        "Fresh clay oven baked naan",                                        50,  "Bread"),
            ("Roghni Naan",          "Sesame topped butter naan",                                         70,  "Bread"),
            ("Sheermal",             "Saffron-flavoured sweet naan bread",                                80,  "Bread"),
            ("Paratha",              "Flaky layered whole wheat paratha",                                 60,  "Bread"),
            ("Kheer",                "Traditional rice pudding with cardamom and almonds",              150,  "Desserts"),
            ("Gulab Jamun (4 pcs)",  "Soft milk-solid dumplings in rose syrup",                        120,  "Desserts"),
            ("Lassi (Sweet)",        "Chilled sweet yogurt drink",                                      100,  "Drinks"),
            ("Lassi (Salted)",       "Refreshing salted yogurt drink",                                  100,  "Drinks"),
            ("Rooh Afza Milk",       "Chilled milk with rose syrup",                                     80,  "Drinks"),
        ]
        for name, desc, price, cat in hn_items:
            self._table("menu_items").insert({
                "restaurant_id": rid("HN Foods"), "name": name,
                "description": desc, "price": price, "category": cat
            }).execute()

        asian_items = [
            ("Hot & Sour Soup",          "Tangy spicy soup with mushrooms, bamboo shoots and egg",      280, "Soups"),
            ("Sweet Corn Chicken Soup",  "Creamy corn soup with shredded chicken",                      260, "Soups"),
            ("Tom Yum Soup",             "Thai-style spicy lemongrass soup with prawns",                320, "Soups"),
            ("Wonton Soup",              "Delicate wontons in clear chicken broth",                     290, "Soups"),
            ("Chicken Chow Mein",        "Stir-fried noodles with chicken, peppers and soy sauce",     480, "Noodles"),
            ("Beef Lo Mein",             "Soft noodles with tender beef strips and vegetables",         540, "Noodles"),
            ("Shrimp Hakka Noodles",     "Spicy hakka-style noodles with prawns",                      580, "Noodles"),
            ("Vegetable Fried Noodles",  "Wok-tossed noodles with seasonal vegetables",                380, "Noodles"),
            ("Chicken Fried Rice",       "Classic wok fried rice with chicken and eggs",               420, "Rice"),
            ("Beef Fried Rice",          "Fragrant fried rice with marinated beef",                    480, "Rice"),
            ("Kung Pao Chicken",         "Spicy stir-fried chicken with peanuts and dried chilies",    520, "Mains"),
            ("Mongolian Beef",           "Tender beef in sweet soy and ginger sauce",                  580, "Mains"),
            ("Sweet & Sour Chicken",     "Crispy chicken pieces in tangy sweet and sour sauce",        490, "Mains"),
            ("Chicken Dumplings (6 pcs)","Steamed chicken and cabbage dumplings",                      350, "Dim Sum"),
            ("Prawn Har Gow (4 pcs)",    "Crystal skin prawn dumplings",                               380, "Dim Sum"),
            ("Spring Rolls (4 pcs)",     "Crispy vegetable and chicken spring rolls",                  280, "Dim Sum"),
            ("Jasmine Green Tea",        "Delicate floral Chinese green tea",                          120, "Drinks"),
            ("Lychee Juice",             "Fresh chilled lychee juice",                                 150, "Drinks"),
        ]
        for name, desc, price, cat in asian_items:
            self._table("menu_items").insert({
                "restaurant_id": rid("Asian Wok"), "name": name,
                "description": desc, "price": price, "category": cat
            }).execute()

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
            self._table("menu_items").insert({
                "restaurant_id": rid("Quetta Royal Cafe"), "name": name,
                "description": desc, "price": price, "category": cat
            }).execute()

        print("Seed data loaded successfully.")

    # ── USER QUERIES ──────────────────────────────────────

    def get_user_by_email(self, email):
        return self._fetchone("users", {"email": email})

    def create_user(self, name, email, password, role="customer", phone=""):
        try:
            self._table("users").insert({
                "name": name, "email": email, "password": password,
                "role": role, "phone": phone
            }).execute()
            return True
        except Exception:
            return False

    def get_all_customers(self):
        return (
            self._table("users")
            .select("*")
            .eq("role", "customer")
            .order("created_at", desc=True)
            .execute()
            .data
        )

    # ── RESTAURANT QUERIES ────────────────────────────────

    def get_all_restaurants(self):
        return (
            self._table("restaurants")
            .select("*")
            .eq("is_open", True)
            .order("rating", desc=True)
            .execute()
            .data
        )

    def get_all_restaurants_admin(self):
        return (
            self._table("restaurants")
            .select("*, users!owner_id(email)")
            .order("name")
            .execute()
            .data
        )

    def get_restaurant_by_id(self, rid):
        return self._fetchone("restaurants", {"id": rid})

    def get_restaurant_by_owner(self, owner_id):
        return self._fetchone("restaurants", {"owner_id": owner_id})

    def create_restaurant(self, owner_id, name, cuisine, description, address, phone):
        self._table("restaurants").insert({
            "owner_id": owner_id, "name": name, "cuisine": cuisine,
            "description": description, "address": address, "phone": phone
        }).execute()

    def update_restaurant_status(self, restaurant_id, is_open):
        self._table("restaurants").update({"is_open": is_open}).eq("id", restaurant_id).execute()

    # ── BRANCH QUERIES ────────────────────────────────────

    def get_branches_by_restaurant(self, restaurant_id):
        return (
            self._table("restaurant_branches")
            .select("*")
            .eq("restaurant_id", restaurant_id)
            .order("city")
            .execute()
            .data
        )

    def get_branches_by_city(self, restaurant_id, city):
        return (
            self._table("restaurant_branches")
            .select("*")
            .eq("restaurant_id", restaurant_id)
            .eq("city", city)
            .eq("is_open", True)
            .execute()
            .data
        )

    def get_all_branches_admin(self):
        return (
            self._table("restaurant_branches")
            .select("*, restaurants!restaurant_id(name)")
            .order("restaurant_id")
            .execute()
            .data
        )

    def add_branch(self, restaurant_id, city, address, phone):
        self._table("restaurant_branches").insert({
            "restaurant_id": restaurant_id, "city": city,
            "address": address, "phone": phone
        }).execute()

    def toggle_branch(self, branch_id):
        row = self._fetchone("restaurant_branches", {"id": branch_id})
        if row:
            self._table("restaurant_branches").update(
                {"is_open": not row["is_open"]}
            ).eq("id", branch_id).execute()

    def delete_branch(self, branch_id):
        self._table("restaurant_branches").delete().eq("id", branch_id).execute()

    def get_cities_with_restaurant(self, restaurant_id):
        res = (
            self._table("restaurant_branches")
            .select("city")
            .eq("restaurant_id", restaurant_id)
            .eq("is_open", True)
            .execute()
        )
        return sorted({r["city"] for r in res.data})

    def get_all_active_cities(self):
        res = (
            self._table("restaurant_branches")
            .select("city, is_open, restaurants!restaurant_id(is_open)")
            .eq("is_open", True)
            .execute()
        )
        cities = set()
        for r in res.data:
            rest = r.get("restaurants") or {}
            if rest.get("is_open"):
                cities.add(r["city"])
        return sorted(cities)

    # ── CITY DELIVERY SETTINGS ────────────────────────────

    def get_city_delivery_settings(self, city):
        res = (
            self._table("city_delivery_settings")
            .select("*")
            .eq("city", city)
            .eq("is_active", True)
            .limit(1)
            .execute()
        )
        return res.data[0] if res.data else None

    def get_all_city_settings(self):
        return self._table("city_delivery_settings").select("*").order("city").execute().data

    def update_city_delivery_settings(self, city, tmin, tmax, charge, free_above):
        self._table("city_delivery_settings").upsert({
            "city": city,
            "delivery_time_min": tmin,
            "delivery_time_max": tmax,
            "delivery_charge": charge,
            "free_delivery_above": free_above,
        }, on_conflict="city").execute()

    def toggle_city_active(self, city, is_active):
        self._table("city_delivery_settings").update(
            {"is_active": is_active}
        ).eq("city", city).execute()

    # ── MENU QUERIES ──────────────────────────────────────

    def get_menu(self, restaurant_id):
        return (
            self._table("menu_items")
            .select("*")
            .eq("restaurant_id", restaurant_id)
            .eq("available", True)
            .order("category")
            .execute()
            .data
        )

    def get_all_menu(self, restaurant_id):
        return (
            self._table("menu_items")
            .select("*")
            .eq("restaurant_id", restaurant_id)
            .order("category")
            .execute()
            .data
        )

    def add_menu_item(self, restaurant_id, name, description, price, category):
        self._table("menu_items").insert({
            "restaurant_id": restaurant_id, "name": name,
            "description": description, "price": price, "category": category
        }).execute()

    def update_menu_item_price(self, item_id, new_price):
        self._table("menu_items").update({"price": new_price}).eq("id", item_id).execute()

    def toggle_item_availability(self, item_id):
        row = self._fetchone("menu_items", {"id": item_id})
        if row:
            self._table("menu_items").update(
                {"available": not row["available"]}
            ).eq("id", item_id).execute()

    def delete_menu_item(self, item_id):
        self._table("menu_items").delete().eq("id", item_id).execute()

    # ── ORDER QUERIES ─────────────────────────────────────

    def create_order(self, restaurant_id, branch_id,
                     customer_name, customer_email, customer_phone,
                     customer_country, customer_city, customer_address,
                     subtotal, delivery_charge, total,
                     estimated_delivery_time, notes, items):
        row = self._table("orders").insert({
            "restaurant_id": restaurant_id,
            "branch_id": branch_id,
            "customer_name": customer_name,
            "customer_email": customer_email,
            "customer_phone": customer_phone,
            "customer_country": customer_country,
            "customer_city": customer_city,
            "customer_address": customer_address,
            "subtotal": subtotal,
            "delivery_charge": delivery_charge,
            "total": total,
            "estimated_delivery_time": estimated_delivery_time,
            "notes": notes,
        }).execute()
        order_id = row.data[0]["id"]

        order_items = [
            {
                "order_id": order_id,
                "item_id": i["item_id"],
                "item_name": i["name"],
                "quantity": i["quantity"],
                "price": i["price"],
            }
            for i in items
        ]
        self._table("order_items").insert(order_items).execute()
        return order_id

    def get_orders_by_restaurant(self, restaurant_id):
        return (
            self._table("orders")
            .select("*, restaurant_branches!branch_id(city, address)")
            .eq("restaurant_id", restaurant_id)
            .order("created_at", desc=True)
            .execute()
            .data
        )

    def get_order_items(self, order_id):
        return self._fetchall("order_items", {"order_id": order_id})

    def update_order_status(self, order_id, status):
        self._table("orders").update({"status": status}).eq("id", order_id).execute()

    def get_all_orders(self):
        return (
            self._table("orders")
            .select("*, restaurants!restaurant_id(name), restaurant_branches!branch_id(city, address)")
            .order("created_at", desc=True)
            .execute()
            .data
        )

    def get_order_by_id(self, order_id):
        return self._fetchone("orders", {"id": order_id})

    # ── REVIEW QUERIES ────────────────────────────────────

    def add_review(self, order_id, restaurant_id, customer_name, rating, comment):
        try:
            self._table("reviews").insert({
                "order_id": order_id,
                "restaurant_id": restaurant_id,
                "customer_name": customer_name,
                "rating": rating,
                "comment": comment,
            }).execute()
            return True
        except Exception:
            return False

    def get_reviews_by_restaurant(self, restaurant_id):
        return (
            self._table("reviews")
            .select("*")
            .eq("restaurant_id", restaurant_id)
            .order("created_at", desc=True)
            .execute()
            .data
        )

    def has_reviewed(self, order_id):
        res = self._table("reviews").select("id").eq("order_id", order_id).limit(1).execute()
        return bool(res.data)

    # ── ADMIN STATS ───────────────────────────────────────

    def get_admin_stats(self):
        orders     = self._table("orders").select("id, status, total").execute().data
        users      = self._table("users").select("id, role").execute().data
        restaurants = self._table("restaurants").select("id").execute().data
        branches   = self._table("restaurant_branches").select("id").execute().data

        delivered_revenue = sum(
            float(o["total"]) for o in orders if o["status"] == "delivered"
        )
        return {
            "total_orders":      len(orders),
            "total_revenue":     delivered_revenue,
            "total_customers":   sum(1 for u in users if u["role"] == "customer"),
            "total_restaurants": len(restaurants),
            "pending_orders":    sum(1 for o in orders if o["status"] == "pending"),
            "total_branches":    len(branches),
        }

    def get_revenue_by_restaurant(self):
        rests = self._table("restaurants").select("id, name").execute().data
        orders = self._table("orders").select("restaurant_id, total, status").execute().data
        result = []
        for r in rests:
            r_orders = [o for o in orders if o["restaurant_id"] == r["id"]]
            revenue = sum(float(o["total"]) for o in r_orders if o["status"] == "delivered")
            result.append({"name": r["name"], "revenue": revenue, "orders": len(r_orders)})
        return sorted(result, key=lambda x: x["revenue"], reverse=True)

    def get_orders_by_status(self):
        orders = self._table("orders").select("status").execute().data
        counts = {}
        for o in orders:
            counts[o["status"]] = counts.get(o["status"], 0) + 1
        return [{"status": s, "total": c} for s, c in counts.items()]
