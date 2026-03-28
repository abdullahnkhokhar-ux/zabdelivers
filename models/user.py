import bcrypt


class User:
    def __init__(self, id, name, email, role, phone=""):
        self.id    = id
        self.name  = name
        self.email = email
        self.role  = role
        self.phone = phone

    @staticmethod
    def hash_password(pw: str) -> str:
        return bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()

    @staticmethod
    def verify_password(pw: str, hashed: str) -> bool:
        return bcrypt.checkpw(pw.encode(), hashed.encode())

    @classmethod
    def login(cls, db, email: str, password: str):
        row = db.get_user_by_email(email.strip().lower())
        if row and cls.verify_password(password, row["password"]):
            return cls(row["id"], row["name"], row["email"], row["role"], row.get("phone") or "")
        return None

    @classmethod
    def register(cls, db, name, email, password, role="customer", phone=""):
        hashed = cls.hash_password(password)
        ok = db.create_user(name.strip(), email.strip().lower(), hashed, role, phone)
        if ok:
            row = db.get_user_by_email(email.strip().lower())
            return cls(row["id"], row["name"], row["email"], row["role"], row.get("phone") or "")
        return None

    def to_dict(self):
        return {"id": self.id, "name": self.name, "email": self.email,
                "role": self.role, "phone": self.phone}

    def __repr__(self):
        return f"User({self.name}, {self.role})"
