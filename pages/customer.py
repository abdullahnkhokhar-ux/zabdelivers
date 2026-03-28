import streamlit as st
from models.order import Cart, Order
from utils.theme import inject_css, badge, render_html, render_navbar, render_nav_buttons, page_header, PRIMARY, BORDER, SURFACE, TEXT_MUTED, TEXT, TEXT_DIM, PRIMARY_LIGHT, PRIMARY_DARK
from database.db_manager import FREE_DELIVERY_THRESHOLD, DELIVERY_CHARGE, PAKISTAN_CITIES


CUISINE_COLORS = {
    "Fast Food": "#0D9488", "Desi": "#B45309",
    "Chinese": "#DC2626",   "Tea Cafe": "#7C3AED",
}


def show_customer_page(db):
    inject_css()
    user = st.session_state.user

    if "cart" not in st.session_state:
        st.session_state.cart = Cart()

    render_navbar(user)

    page = st.session_state.get("cust_page", "home")
    cart = st.session_state.cart

    nav_items = [
        ("home",   "Restaurants"),
        ("cart",   f"Cart ({cart.item_count})" if not cart.is_empty() else "Cart"),
        ("orders", "My Orders"),
    ]
    st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
    cols = render_nav_buttons(nav_items, page, "cust_page")
    with cols[-1]:
        if st.button("Sign Out", key="signout_cust", use_container_width=True):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()

    st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
    st.divider()

    if page == "home":
        _home(db, user)
    elif page == "cart":
        _cart_page(db, user)
    elif page == "orders":
        _orders_page(db, user)
    elif page == "menu":
        _menu_page(db, user)


def _home(db, user):
    _, content, _ = st.columns([0.1, 11, 0.1])
    with content:
        page_header(f"Welcome back, {user['name'].split()[0]}",
                    "Choose a restaurant and start your order")

        col_search, col_filter = st.columns([3, 1])
        with col_search:
            search = st.text_input("", placeholder="Search restaurants or cuisines...",
                                   label_visibility="collapsed")
        with col_filter:
            cuisine_f = st.selectbox("", ["All Cuisines", "Fast Food", "Desi", "Chinese", "Tea Cafe"],
                                     label_visibility="collapsed")

        rows = db.get_all_restaurants()
        if search:
            rows = [r for r in rows if search.lower() in r["name"].lower()
                    or search.lower() in (r["cuisine"] or "").lower()]
        if cuisine_f != "All Cuisines":
            rows = [r for r in rows if r["cuisine"] == cuisine_f]

        if not rows:
            render_html(f'<div style="text-align:center;padding:4rem;color:{TEXT_MUTED};">No restaurants found.</div>')
            return

        cols = st.columns(2)
        for i, r in enumerate(rows):
            color = CUISINE_COLORS.get(r["cuisine"], PRIMARY)
            stars = int(r["rating"])
            with cols[i % 2]:
                open_color = "#15803D" if r.get("is_open") else "#BE123C"
                open_label = "● Open" if r.get("is_open") else "● Closed"
                render_html(f"""
                <div class="zd-rest-card">
                    <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:0.6rem;">
                        <div>
                            <div style="font-family:'Space Grotesk',sans-serif;
                                        font-size:1.2rem;font-weight:800;color:{TEXT};">{r['name']}</div>
                            <div style="font-size:0.78rem;color:{color};font-weight:700;
                                        text-transform:uppercase;letter-spacing:0.06em;margin-top:2px;">{r['cuisine']}</div>
                        </div>
                        <div style="text-align:right;">
                            <div style="font-size:0.85rem;color:#F59E0B;font-weight:700;">
                                {"★" * stars}{"☆" * (5-stars)}
                            </div>
                            <div style="font-size:0.72rem;color:{TEXT_MUTED};margin-top:1px;">{r['rating']}/5</div>
                            <div style="font-size:0.72rem;color:{open_color};font-weight:600;margin-top:2px;">{open_label}</div>
                        </div>
                    </div>
                    <div style="font-size:0.82rem;color:{TEXT_MUTED};line-height:1.5;margin-bottom:0.5rem;">{(r.get('description') or '')[:100]}</div>
                    <div style="font-size:0.75rem;color:{TEXT_DIM};">{r.get('address') or ''}</div>
                </div>
                """)
                if st.button("View Menu", key=f"rest_{r['id']}",
                             use_container_width=True, type="primary"):
                    st.session_state.selected_restaurant = r["id"]
                    st.session_state.cust_page = "menu"
                    st.rerun()


def _menu_page(db, user):
    rid = st.session_state.get("selected_restaurant")
    if not rid:
        st.session_state.cust_page = "home"
        st.rerun()

    rest = db.get_restaurant_by_id(rid)
    if not rest:
        st.session_state.cust_page = "home"
        st.rerun()

    cart = st.session_state.cart
    color = CUISINE_COLORS.get(rest["cuisine"], PRIMARY)

    _, content, _ = st.columns([0.1, 11, 0.1])
    with content:
        col_back, col_info = st.columns([1, 5])
        with col_back:
            st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
            if st.button("← Back", key="back_home"):
                st.session_state.cust_page = "home"
                st.session_state.selected_restaurant = None
                st.rerun()
        with col_info:
            render_html(f"""
            <div style="padding:1.5rem 0 1rem;">
                <div style="font-family:'Space Grotesk',sans-serif;font-size:2rem;
                            font-weight:800;color:{TEXT};letter-spacing:-0.02em;">{rest['name']}</div>
                <div style="font-size:0.78rem;color:{color};font-weight:700;
                            text-transform:uppercase;letter-spacing:0.06em;margin-top:2px;">
                    {rest['cuisine']} &nbsp;·&nbsp; {rest.get('address','') }
                </div>
            </div>
            """)

        if not cart.is_empty() and cart.restaurant_id != rid:
            render_html(f"""
            <div style="background:#FFF7ED;border:1.5px solid #FED7AA;border-radius:10px;
                        padding:0.8rem 1rem;margin-bottom:1rem;font-size:0.85rem;color:#C2410C;">
                Your cart has items from <b>{cart.restaurant_name}</b>.
                Adding items here will clear your current cart.
            </div>
            """)

        # Show per-city delivery info if city already selected
        selected_city = st.session_state.get("checkout_city", "")
        if selected_city:
            city_cfg = db.get_city_delivery_settings(selected_city)
            if city_cfg:
                render_html(f"""
                <div style="background:{PRIMARY_LIGHT};border:1.5px solid #A7F3D0;border-radius:10px;
                            padding:0.7rem 1.2rem;margin-bottom:1.2rem;font-size:0.83rem;color:{PRIMARY_DARK};font-weight:500;
                            display:flex;gap:1.5rem;flex-wrap:wrap;align-items:center;">
                    <span><b>{selected_city}</b></span>
                    <span><b>{city_cfg['delivery_time_min']}–{city_cfg['delivery_time_max']} min</b> delivery</span>
                    <span>Free delivery above <b>Rs. {float(city_cfg['free_delivery_above']):,.0f}</b></span>
                    <span>Delivery fee: <b>Rs. {float(city_cfg['delivery_charge']):,.0f}</b></span>
                </div>
                """)
            else:
                render_html(f"""
                <div style="background:{PRIMARY_LIGHT};border:1.5px solid #A7F3D0;border-radius:10px;
                            padding:0.7rem 1rem;margin-bottom:1.2rem;font-size:0.82rem;color:{PRIMARY_DARK};font-weight:500;">
                    Free delivery on orders above Rs. {FREE_DELIVERY_THRESHOLD:,.0f} &nbsp;·&nbsp;
                    Rs. {DELIVERY_CHARGE} delivery otherwise
                </div>
                """)
        else:
            render_html(f"""
            <div style="background:{PRIMARY_LIGHT};border:1.5px solid #A7F3D0;border-radius:10px;
                        padding:0.7rem 1rem;margin-bottom:1.2rem;font-size:0.82rem;color:{PRIMARY_DARK};font-weight:500;">
                Free delivery on orders above Rs. {FREE_DELIVERY_THRESHOLD:,.0f} &nbsp;·&nbsp;
                Rs. {DELIVERY_CHARGE} delivery otherwise
            </div>
            """)

        notify = st.empty()

        items = db.get_menu(rid)
        categories: dict[str, list] = {}
        for item in items:
            categories.setdefault(item["category"] or "Other", []).append(item)

        for category, cat_items in categories.items():
            render_html(f'<div style="font-size:0.75rem;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;color:{TEXT_DIM};margin:1.4rem 0 0.6rem;">{category}</div>')
            with st.container(border=True):
                for item in cat_items:
                    c1, c2 = st.columns([5, 1])
                    with c1:
                        render_html(f"""
                        <div style="padding:0.5rem 0;">
                            <div style="font-weight:600;color:{TEXT};font-size:0.92rem;">{item['name']}</div>
                            <div style="color:{TEXT_MUTED};font-size:0.8rem;margin-top:2px;line-height:1.4;">{item.get('description') or ''}</div>
                            <div style="color:{PRIMARY};font-weight:700;font-size:0.9rem;margin-top:5px;">Rs. {float(item['price']):,.0f}</div>
                        </div>
                        """)
                    with c2:
                        st.markdown("<div style='height:0.6rem'></div>", unsafe_allow_html=True)
                        if st.button("Add", key=f"add_{item['id']}_{rid}",
                                     use_container_width=True, type="primary"):
                            cart.add_item(item["id"], item["name"], float(item["price"]), rid, rest["name"])
                            notify.success(f"Added {item['name']} to cart")
                            st.rerun()

        if not cart.is_empty() and cart.restaurant_id == rid:
            st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
            render_html(f"""
            <div style="background:{PRIMARY_LIGHT};border:1.5px solid {PRIMARY};border-radius:12px;
                        padding:1rem 1.4rem;display:flex;justify-content:space-between;align-items:center;">
                <div>
                    <div style="font-size:0.78rem;color:{TEXT_MUTED};">{cart.item_count} items in cart</div>
                    <div style="font-size:1.1rem;font-weight:700;color:{TEXT};">Rs. {cart.total:,.0f}</div>
                </div>
            </div>
            """)
            if st.button("Go to Cart →", use_container_width=True, type="primary"):
                st.session_state.cust_page = "cart"
                st.rerun()


def _cart_page(db, user):
    _, content, _ = st.columns([0.1, 11, 0.1])
    with content:
        page_header("Your Cart")

        cart = st.session_state.cart
        if cart.is_empty():
            render_html(f"""
            <div style="text-align:center;padding:5rem 2rem;">
                <div style="font-size:3rem;margin-bottom:1rem;"></div>
                <div style="font-family:'Space Grotesk',sans-serif;font-size:1.5rem;font-weight:700;color:{TEXT};">Cart is empty</div>
                <div style="font-size:0.88rem;color:{TEXT_MUTED};margin-top:0.5rem;">Browse restaurants to add items</div>
            </div>
            """)
            if st.button("Browse Restaurants", type="primary"):
                st.session_state.cust_page = "home"
                st.rerun()
            return

        col_cart, col_summary = st.columns([3, 2])

        with col_cart:
            render_html(f'<div style="font-size:0.78rem;font-weight:700;letter-spacing:0.08em;text-transform:uppercase;color:{TEXT_DIM};margin-bottom:0.8rem;">From {cart.restaurant_name}</div>')
            with st.container(border=True):
                for item_id, item in list(cart.items.items()):
                    c1, c2, c3, c4 = st.columns([4, 1, 1, 1])
                    with c1:
                        render_html(f"""
                        <div style="padding:4px 0;">
                            <div style="font-weight:600;color:{TEXT};font-size:0.9rem;">{item.name}</div>
                            <div style="color:{TEXT_MUTED};font-size:0.78rem;">Rs. {item.price:,.0f} each</div>
                        </div>
                        """)
                    with c2:
                        if st.button("−", key=f"dec_{item_id}", use_container_width=True):
                            cart.remove_item(item_id); st.rerun()
                    with c3:
                        render_html(f'<div style="text-align:center;padding:0.5rem;font-weight:700;color:{TEXT};">{item.quantity}</div>')
                    with c4:
                        if st.button("+", key=f"inc_{item_id}", use_container_width=True):
                            cart.add_item(item_id, item.name, item.price, cart.restaurant_id, cart.restaurant_name)
                            st.rerun()

            if st.button("Clear Cart", use_container_width=True):
                cart.clear(); st.rerun()

        with col_summary:
            render_html(f'<div style="font-size:0.78rem;font-weight:700;letter-spacing:0.08em;text-transform:uppercase;color:{TEXT_DIM};margin-bottom:0.8rem;">Order Summary</div>')
            with st.container(border=True):
                for item in cart.items.values():
                    render_html(f"""
                    <div style="display:flex;justify-content:space-between;padding:4px 0;font-size:0.85rem;">
                        <span style="color:{TEXT_MUTED};">{item.name} × {item.quantity}</span>
                        <span style="color:{TEXT};">Rs. {item.subtotal:,.0f}</span>
                    </div>
                    """)
                delivery_color = "#15803D" if cart.delivery_charge == 0 else TEXT_MUTED
                delivery_label = "Free" if cart.delivery_charge == 0 else f"Rs. {cart.delivery_charge:,.0f}"
                render_html(f"""
                <div style="height:1px;background:{BORDER};margin:0.8rem 0;"></div>
                <div style="display:flex;justify-content:space-between;font-size:0.85rem;padding:3px 0;">
                    <span style="color:{TEXT_MUTED};">Subtotal</span>
                    <span style="color:{TEXT};">Rs. {cart.subtotal:,.0f}</span>
                </div>
                <div style="display:flex;justify-content:space-between;font-size:0.85rem;padding:3px 0;">
                    <span style="color:{TEXT_MUTED};">Delivery</span>
                    <span style="color:{delivery_color};">{delivery_label}</span>
                </div>
                <div style="height:1px;background:{BORDER};margin:0.8rem 0;"></div>
                <div style="display:flex;justify-content:space-between;font-size:1rem;font-weight:700;">
                    <span style="color:{TEXT};font-family:'Space Grotesk',sans-serif;font-size:1.1rem;">Total</span>
                    <span style="color:{PRIMARY};font-family:'Space Grotesk',sans-serif;font-size:1.3rem;">Rs. {cart.total:,.0f}</span>
                </div>
                """)

            if cart.subtotal < FREE_DELIVERY_THRESHOLD:
                remaining = FREE_DELIVERY_THRESHOLD - cart.subtotal
                render_html(f'<div style="font-size:0.75rem;color:{TEXT_MUTED};margin-top:0.5rem;text-align:center;">Add Rs. {remaining:,.0f} more for free delivery</div>')

            st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
            if st.button("Proceed to Checkout →", use_container_width=True, type="primary"):
                st.session_state.show_checkout = True
                st.rerun()

        if st.session_state.get("show_checkout"):
            st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
            render_html(f'<div style="font-family:\'Space Grotesk\',sans-serif;font-size:1.5rem;font-weight:800;color:{TEXT};margin-bottom:0.3rem;">Delivery Details</div>')
            render_html(f'<div style="font-size:0.85rem;color:{TEXT_MUTED};margin-bottom:1.2rem;">Fill in your delivery info below</div>')

            # ── City picker OUTSIDE the form so branch list updates instantly ──
            active_cities = db.get_all_active_cities()
            all_cities = active_cities if active_cities else PAKISTAN_CITIES
            prev_city = st.session_state.get("checkout_city", all_cities[0] if all_cities else "Lahore")
            city_idx = all_cities.index(prev_city) if prev_city in all_cities else 0

            c_city = st.selectbox("City*", all_cities, index=city_idx, key="checkout_city_selector")

            # Persist immediately — triggers rerun so branch list and delivery banner react
            if c_city != st.session_state.get("checkout_city"):
                st.session_state.checkout_city = c_city
                st.rerun()

            # ── Branch selector driven by the live city value ──
            branches_in_city = db.get_branches_by_city(cart.restaurant_id, c_city) if cart.restaurant_id else []
            selected_branch_id = None
            if branches_in_city:
                branch_labels = [f"{b['address']} ({b['city']})" for b in branches_in_city]
                branch_choice = st.selectbox(
                    f"Nearest Branch in {c_city}",
                    branch_labels,
                    key="checkout_branch_selector",
                    help="Your order will be prepared at this branch",
                )
                chosen_idx = branch_labels.index(branch_choice)
                selected_branch_id = branches_in_city[chosen_idx]["id"]
            else:
                render_html(
                    f'<div style="font-size:0.8rem;color:{TEXT_MUTED};margin-bottom:0.6rem;padding:0.5rem 0.8rem;'
                    f'background:#FFF7ED;border:1px solid #FED7AA;border-radius:8px;">'
                    f'⚠️ No branches found in <b>{c_city}</b> — order will be fulfilled from the nearest available branch.</div>'
                )

            with st.form("checkout_form"):
                c1, c2 = st.columns(2)
                with c1:
                    c_name    = st.text_input("Full Name*", placeholder="Recipient name")
                    c_email   = st.text_input("Email Address*", placeholder="your@email.com")
                    c_phone   = st.text_input("Phone Number*", placeholder="03XX-XXXXXXX")
                with c2:
                    c_country = st.text_input("Country*", value="Pakistan", placeholder="Country")
                    # City shown as read-only — changed via the selector above
                    st.text_input("City", value=c_city, disabled=True,
                                  help="Change city using the selector above the form")
                    c_address = st.text_input("Street Address*", placeholder="Full delivery address")

                notes = st.text_area("Special Instructions (optional)", placeholder="Any notes for the restaurant...", height=70)

                # Fetch delivery settings for chosen city
                city_cfg = db.get_city_delivery_settings(c_city)
                if city_cfg:
                    dcharge      = float(city_cfg["delivery_charge"])
                    free_above   = float(city_cfg["free_delivery_above"])
                    dtime_label  = f"{city_cfg['delivery_time_min']}–{city_cfg['delivery_time_max']} min"
                    act_delivery = 0 if cart.subtotal >= free_above else dcharge
                    act_total    = cart.subtotal + act_delivery
                    free_note    = "Free delivery!" if act_delivery == 0 else f"Rs. {act_delivery:,.0f} delivery fee"
                else:
                    dcharge     = DELIVERY_CHARGE
                    free_above  = FREE_DELIVERY_THRESHOLD
                    dtime_label = "30–45 min"
                    act_delivery = 0 if cart.subtotal >= free_above else dcharge
                    act_total   = cart.subtotal + act_delivery
                    free_note   = "Free delivery!" if act_delivery == 0 else f"Rs. {act_delivery:,.0f} delivery fee"

                render_html(f"""
                <div style="background:{PRIMARY_LIGHT};border:1.5px solid #A7F3D0;border-radius:14px;
                            padding:1rem 1.3rem;margin:1rem 0;font-size:0.85rem;">
                    <div style="display:grid;grid-template-columns:1fr 1fr;gap:0.5rem 1.5rem;">
                        <div><span style="color:{TEXT_MUTED};">Subtotal</span>
                             <b style="float:right;color:{TEXT};">Rs. {cart.subtotal:,.0f}</b></div>
                        <div><span style="color:{TEXT_MUTED};">Delivery</span>
                             <b style="float:right;color:{'#16A34A' if act_delivery==0 else TEXT};">{free_note}</b></div>
                        <div><span style="color:{TEXT_MUTED};">Est. Time</span>
                             <b style="float:right;color:{PRIMARY};">{dtime_label}</b></div>
                        <div><span style="color:{TEXT_MUTED};">Payment</span>
                             <b style="float:right;color:{TEXT};">Cash on Delivery</b></div>
                    </div>
                    <div style="border-top:1px solid rgba(13,148,136,0.2);margin-top:0.8rem;padding-top:0.8rem;
                                display:flex;justify-content:space-between;align-items:center;">
                        <span style="font-size:1rem;font-weight:700;color:{TEXT};">Total</span>
                        <span style="font-family:'Space Grotesk',sans-serif;font-size:1.4rem;
                                     font-weight:700;color:{PRIMARY};">Rs. {act_total:,.0f}</span>
                    </div>
                </div>
                """)

                if st.form_submit_button("Place Order Now", use_container_width=True):
                    if not all([c_name, c_email, c_phone, c_country, c_city, c_address]):
                        st.error("Please fill all required fields.")
                    else:
                        st.session_state.checkout_city = c_city
                        oid = db.create_order(
                            cart.restaurant_id, selected_branch_id,
                            c_name, c_email, c_phone,
                            c_country, c_city, c_address,
                            cart.subtotal, act_delivery, act_total,
                            dtime_label, notes, cart.to_order_items()
                        )
                        cart.clear()
                        st.session_state.show_checkout = False
                        st.session_state.last_order_id = oid
                        st.session_state.cust_page = "orders"
                        st.success(f"Order #{oid} placed! Estimated delivery: {dtime_label}")
                        st.balloons()
                        st.rerun()


def _orders_page(db, user):
    _, content, _ = st.columns([0.1, 11, 0.1])
    with content:
        page_header("My Orders", "Track your past and current orders")

        all_orders = db.get_all_orders()
        customer_email = user.get("email", "")
        customer_orders = [o for o in all_orders if o.get("customer_email", "").lower() == customer_email.lower()]

        if not customer_orders:
            render_html(f"""
            <div style="text-align:center;padding:4rem;">
                <div style="font-size:3rem;margin-bottom:1rem;"></div>
                <div style="font-family:'Space Grotesk',sans-serif;font-size:1.5rem;font-weight:700;color:{TEXT};">No orders yet</div>
                <div style="font-size:0.88rem;color:{TEXT_MUTED};margin-top:0.5rem;">Your orders will appear here after checkout</div>
            </div>
            """)
            if st.button("Browse Restaurants", type="primary"):
                st.session_state.cust_page = "home"
                st.rerun()
            return

        for row in customer_orders:
            order = Order(row)
            with st.expander(f"Order #{order.id}  —  {order.restaurant_name}  —  Rs. {order.total:,.0f}"):
                c1, c2 = st.columns(2)
                with c1:
                    render_html(f"""
                    {badge(order.status)}
                    <div style="margin-top:0.8rem;">
                        <div style="font-size:0.82rem;color:{TEXT_MUTED};">Placed: {order.created_at[:16]}</div>
                        <div style="font-size:0.82rem;color:{TEXT_MUTED};margin-top:3px;">City: {order.customer_city}</div>
                        <div style="font-size:0.82rem;color:{TEXT_MUTED};margin-top:3px;">Address: {order.customer_address}</div>
                        {f'<div style="font-size:0.82rem;color:{PRIMARY};font-weight:600;margin-top:3px;">Est. Delivery: {order.estimated_delivery_time}</div>' if order.estimated_delivery_time else ''}
                        {f'<div style="font-size:0.78rem;color:{TEXT_DIM};margin-top:2px;">Branch: {order.branch_city} — {order.branch_address}</div>' if order.branch_address else ''}
                    </div>
                    """)
                with c2:
                    items = db.get_order_items(order.id)
                    for it in items:
                        render_html(f'<div style="font-size:0.82rem;color:{TEXT_MUTED};padding:2px 0;">{it["item_name"]} × {it["quantity"]} — Rs. {float(it["price"])*it["quantity"]:,.0f}</div>')
                    render_html(f"""
                    <div style="margin-top:0.8rem;padding-top:0.8rem;border-top:1px solid {BORDER};">
                        <div style="display:flex;justify-content:space-between;font-size:0.85rem;">
                            <span style="color:{TEXT_MUTED};">Subtotal</span>
                            <span>Rs. {order.subtotal:,.0f}</span>
                        </div>
                        <div style="display:flex;justify-content:space-between;font-size:0.85rem;margin-top:2px;">
                            <span style="color:{TEXT_MUTED};">Delivery</span>
                            <span>{"Free" if order.delivery_charge == 0 else f"Rs. {order.delivery_charge:,.0f}"}</span>
                        </div>
                        <div style="display:flex;justify-content:space-between;font-size:0.95rem;font-weight:700;margin-top:6px;">
                            <span>Total</span>
                            <span style="color:{PRIMARY};">Rs. {order.total:,.0f}</span>
                        </div>
                    </div>
                    """)

                if order.can_cancel():
                    if st.button(f"Cancel Order", key=f"cx_{order.id}"):
                        db.update_order_status(order.id, "cancelled")
                        st.success("Order cancelled.")
                        st.rerun()

                if order.status == "delivered" and not db.has_reviewed(order.id):
                    st.markdown("<hr>", unsafe_allow_html=True)
                    render_html(f'<div style="font-size:0.8rem;color:{TEXT_MUTED};margin-bottom:0.5rem;">Leave a Review</div>')
                    with st.form(f"rev_{order.id}"):
                        rating  = st.slider("Rating", 1, 5, 5)
                        comment = st.text_area("Comment (optional)", height=60)
                        if st.form_submit_button("Submit Review"):
                            db.add_review(order.id, order.restaurant_id, order.customer_name, rating, comment)
                            st.success("Thank you for your review!")
                            st.rerun()
                elif order.status == "delivered" and db.has_reviewed(order.id):
                    render_html(f'<div style="font-size:0.78rem;color:#15803D;margin-top:0.5rem;">✓ Reviewed</div>')
