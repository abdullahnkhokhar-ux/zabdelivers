import streamlit as st
from database.db_manager import DatabaseManager
from pages.auth       import show_auth_page
from pages.customer   import show_customer_page
from pages.restaurant import show_restaurant_page
from pages.admin      import show_admin_page

st.set_page_config(
    page_title="ZabDelivers",
    page_icon="🍔",
    layout="centered",
    initial_sidebar_state="collapsed"
)

@st.cache_resource
def get_db():
    return DatabaseManager()

db = get_db()

if "user" not in st.session_state:
    st.session_state.user = None

user = st.session_state.user

if user is None:
    show_auth_page(db)
else:
    role = user.get("role")
    if role == "customer":
        show_customer_page(db)
    elif role == "restaurant":
        show_restaurant_page(db)
    elif role == "admin":
        show_admin_page(db)
    else:
        st.error("Unknown role.")
        if st.button("Logout"):
            del st.session_state.user
            st.rerun()
