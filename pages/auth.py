import streamlit as st
from models.user import User
from models.order import Cart
from utils.theme import inject_css, render_html, render_navbar, PRIMARY, TEXT, TEXT_MUTED


def show_auth_page(db):
    inject_css()
    render_navbar()

    _, mid, _ = st.columns([1, 1.4, 1])
    with mid:
        st.markdown("<div style='height:2.5rem'></div>", unsafe_allow_html=True)
        render_html(f"""
        <div style="text-align:center; margin-bottom:2rem;">
            <div style="font-family:'Space Grotesk',sans-serif; font-size:2.8rem; font-weight:800;
                        color:{TEXT}; letter-spacing:-0.03em; line-height:1;">
                ZAB<span style="color:{PRIMARY};">DELIVERS</span>
            </div>
            <div style="font-size:0.8rem; letter-spacing:0.18em; text-transform:uppercase;
                        color:{TEXT_MUTED}; font-weight:600; margin-top:0.4rem;">
                Fast Food Delivery Platform
            </div>
            <div style="width:40px; height:3px; background:{PRIMARY};
                        border-radius:2px; margin:0.9rem auto 0;"></div>
        </div>
        """)

        tab_login, tab_signup = st.tabs(["Sign In", "Create Account"])
        with tab_login:
            _login_form(db)
        with tab_signup:
            _signup_form(db)

        render_html(f"""
        <div style="text-align:center; margin-top:2rem; padding-bottom:3rem;
                    color:{TEXT_MUTED}; font-size:0.75rem; letter-spacing:0.04em;">
            Abdullah Naeem &nbsp;·&nbsp; Ali Zaviyar &nbsp;·&nbsp;
            Faiq Kashif &nbsp;·&nbsp; Komail Khawaja
        </div>
        """)


def _login_form(db):
    st.markdown("<div style='height:0.8rem'></div>", unsafe_allow_html=True)

    with st.form("login_form", clear_on_submit=False):
        email    = st.text_input("Email Address", placeholder="Enter your email")
        password = st.text_input("Password", type="password", placeholder="Enter your password")
        submitted = st.form_submit_button("Sign In", use_container_width=True)

    if submitted:
        if not email or not password:
            st.error("Please enter your email and password.")
        else:
            user = User.login(db, email, password)
            if user:
                st.session_state.user = user.to_dict()
                st.session_state.cart = Cart()
                st.rerun()
            else:
                st.error("Invalid email or password. Please try again.")


def _signup_form(db):
    st.markdown("<div style='height:0.8rem'></div>", unsafe_allow_html=True)

    # Role toggle OUTSIDE form but using on_change callback to avoid rerun conflicts
    if "signup_role" not in st.session_state:
        st.session_state["signup_role"] = "Customer"

    def _set_role():
        st.session_state["signup_role"] = st.session_state["_role_radio"]

    st.radio(
        "Register as",
        ["Customer", "Restaurant"],
        index=0 if st.session_state["signup_role"] == "Customer" else 1,
        horizontal=True,
        key="_role_radio",
        on_change=_set_role,
    )

    is_restaurant = st.session_state["signup_role"] == "Restaurant"

    with st.form("signup_form", clear_on_submit=False):
        name     = st.text_input("Full Name", placeholder="Your full name")
        email    = st.text_input("Email Address", placeholder="your@email.com")
        col1, col2 = st.columns(2)
        with col1:
            password = st.text_input("Password", type="password", placeholder="Min 6 characters")
        with col2:
            confirm  = st.text_input("Confirm Password", type="password", placeholder="Repeat password")
        phone    = st.text_input("Phone Number", placeholder="03XX-XXXXXXX")

        rest_name = cuisine = description = rest_address = rest_phone = None

        if is_restaurant:
            st.markdown(
                '<div style="font-size:0.76rem;font-weight:700;letter-spacing:0.07em;'
                'text-transform:uppercase;color:#64748B;margin:0.6rem 0 0.2rem;">Restaurant Details</div>',
                unsafe_allow_html=True,
            )
            rest_name    = st.text_input("Restaurant Name", placeholder="e.g. My Desi Kitchen")
            cuisine      = st.selectbox("Cuisine Type", ["Fast Food","Desi","Chinese","Tea Cafe","Bakery","BBQ","Seafood","Pizza","Desserts","Other"])
            description  = st.text_area("Short Description", placeholder="Tell customers about your restaurant...", height=70)
            rest_address = st.text_input("Restaurant Address", placeholder="Full address")
            rest_phone   = st.text_input("Restaurant Phone", placeholder="Restaurant contact number")

        submitted = st.form_submit_button("Create Account", use_container_width=True)

    if submitted:
        role = "restaurant" if is_restaurant else "customer"
        if not all([name, email, password, confirm]):
            st.error("Please fill all required fields.")
        elif password != confirm:
            st.error("Passwords do not match.")
        elif len(password) < 6:
            st.error("Password must be at least 6 characters.")
        elif is_restaurant and not rest_name:
            st.error("Please enter your restaurant name.")
        else:
            user = User.register(db, name, email, password, role, phone)
            if user:
                if role == "restaurant":
                    db.create_restaurant(
                        user.id, rest_name, cuisine,
                        description or "", rest_address or "", rest_phone or ""
                    )
                st.session_state.user = user.to_dict()
                st.session_state.cart = Cart()
                st.success(f"Welcome to ZabDelivers, {name}!")
                st.rerun()
            else:
                st.error("An account with this email already exists.")
