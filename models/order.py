from database.db_manager import FREE_DELIVERY_THRESHOLD, DELIVERY_CHARGE


class CartItem:
    def __init__(self, item_id, name, price, quantity=1):
        self.item_id  = item_id
        self.name     = name
        self.price    = float(price)
        self.quantity = quantity

    @property
    def subtotal(self):
        return self.price * self.quantity

    def to_dict(self):
        return {"item_id": self.item_id, "name": self.name,
                "price": self.price, "quantity": self.quantity}


class Cart:
    def __init__(self):
        self.restaurant_id   = None
        self.restaurant_name = ""
        self.items: dict[int, CartItem] = {}

    def add_item(self, item_id, name, price, restaurant_id, restaurant_name):
        if self.restaurant_id and self.restaurant_id != restaurant_id:
            self.clear()
        self.restaurant_id   = restaurant_id
        self.restaurant_name = restaurant_name
        if item_id in self.items:
            self.items[item_id].quantity += 1
        else:
            self.items[item_id] = CartItem(item_id, name, price)

    def remove_item(self, item_id):
        if item_id in self.items:
            if self.items[item_id].quantity > 1:
                self.items[item_id].quantity -= 1
            else:
                del self.items[item_id]

    def delete_item(self, item_id):
        self.items.pop(item_id, None)

    def clear(self):
        self.items           = {}
        self.restaurant_id   = None
        self.restaurant_name = ""

    @property
    def subtotal(self):
        return sum(i.subtotal for i in self.items.values())

    @property
    def delivery_charge(self):
        if self.subtotal == 0:
            return 0
        return 0 if self.subtotal >= FREE_DELIVERY_THRESHOLD else DELIVERY_CHARGE

    @property
    def total(self):
        return self.subtotal + self.delivery_charge

    @property
    def item_count(self):
        return sum(i.quantity for i in self.items.values())

    def is_empty(self):
        return len(self.items) == 0

    def to_order_items(self):
        return [i.to_dict() for i in self.items.values()]


class Order:
    STATUS_FLOW = ["pending", "confirmed", "preparing", "ready", "picked_up", "delivered"]
    STATUS_LABELS = {
        "pending":   "Pending",
        "confirmed": "Confirmed",
        "preparing": "Preparing",
        "ready":     "Ready for Pickup",
        "picked_up": "Out for Delivery",
        "delivered": "Delivered",
        "cancelled": "Cancelled",
    }
    STATUS_COLORS = {
        "pending":   "orange",
        "confirmed": "blue",
        "preparing": "violet",
        "ready":     "green",
        "picked_up": "blue",
        "delivered": "green",
        "cancelled": "red",
    }

    def __init__(self, row):
        self.id               = row["id"]
        self.restaurant_id    = row["restaurant_id"]
        self.customer_name    = row["customer_name"]
        self.customer_email   = row["customer_email"]
        self.customer_phone   = row.get("customer_phone", "")
        self.customer_country = row.get("customer_country", "")
        self.customer_city    = row.get("customer_city", "")
        self.customer_address = row.get("customer_address", "")
        self.subtotal         = float(row["subtotal"])
        self.delivery_charge  = float(row["delivery_charge"])
        self.total            = float(row["total"])
        self.status           = row["status"]
        self.notes                  = row.get("notes", "")
        self.estimated_delivery_time= row.get("estimated_delivery_time", "")
        self.branch_id              = row.get("branch_id")
        self.branch_city            = row.get("branch_city", "")
        self.branch_address         = row.get("branch_address", "")
        self.created_at             = str(row["created_at"])
        self.restaurant_name        = row.get("restaurant_name", "")

    def status_label(self):
        return self.STATUS_LABELS.get(self.status, self.status)

    def status_color(self):
        return self.STATUS_COLORS.get(self.status, "gray")

    def next_status(self):
        if self.status in self.STATUS_FLOW:
            idx = self.STATUS_FLOW.index(self.status)
            if idx + 1 < len(self.STATUS_FLOW):
                return self.STATUS_FLOW[idx + 1]
        return None

    def can_cancel(self):
        return self.status == "pending"
