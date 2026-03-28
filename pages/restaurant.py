import streamlit as st
import pandas as pd
from models.order import Order
from utils.theme import inject_css, badge, render_html, render_navbar, render_nav_buttons, page_header, PRIMARY, PRIMARY_DARK, PRIMARY_LIGHT, BORDER, TEXT_MUTED, TEXT, TEXT_DIM, SURFACE2
from database.db_manager import PAKISTAN_CITIES

try:
    import plotly.graph_objects as go
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False


def show_restaurant_page(db):
    inject_css()
    user = st.session_state.user

    rest = db.get_restaurant_by_owner(user["id"])
    if not rest:
        st.warning("No restaurant linked to your account. Contact admin.")
        return

    render_navbar(user)

    page = st.session_state.get("rest_page", "orders")
    nav_items = [
        ("orders",   "Orders"),
        ("menu",     "Menu"),
        ("branches", "Branches"),
        ("reviews",  "Reviews"),
        ("stats",    "Stats"),
    ]
    st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
    cols = render_nav_buttons(nav_items, page, "rest_page")
    with cols[-1]:
        if st.button("Sign Out", key="so_rest", use_container_width=True):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()

    st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
    st.divider()

    _, content, _ = st.columns([0.1, 11, 0.1])
    with content:
        if page == "orders":
            _orders(db, rest)
        elif page == "menu":
            _menu(db, rest)
        elif page == "branches":
            _branches(db, rest)
        elif page == "reviews":
            _reviews(db, rest)
        elif page == "stats":
            _stats(db, rest)


def _orders(db, rest):
    col1, col2 = st.columns([5, 1])
    with col1:
        page_header("Incoming Orders",
                    f"{rest['name']} · {rest['cuisine']} · {'● Open' if rest['is_open'] else '● Closed'}")
    with col2:
        st.markdown("<div style='height:2rem'></div>", unsafe_allow_html=True)
        if st.button("Refresh", use_container_width=True):
            st.rerun()

    rows  = db.get_orders_by_restaurant(rest["id"])
    active = [r for r in rows if r["status"] not in ("delivered", "cancelled")]
    past   = [r for r in rows if r["status"] in ("delivered", "cancelled")]

    NEXT = {
        "confirmed": "Confirm Order",
        "preparing": "Start Preparing",
        "ready":     "Mark Ready",
        "picked_up": "Mark Picked Up",
        "delivered": "Mark Delivered",
    }

    if active:
        render_html(f'<div style="font-size:0.75rem;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;color:{TEXT_DIM};margin-bottom:0.8rem;">Active ({len(active)})</div>')
        for row in active:
            order = Order(row)
            items = db.get_order_items(order.id)
            with st.container(border=True):
                c1, c2, c3 = st.columns([3, 2, 2])
                with c1:
                    render_html(f"""
                    <div style="font-family:'Space Grotesk',sans-serif;font-weight:700;
                                color:{TEXT};font-size:1.1rem;">Order #{order.id}</div>
                    <div style="font-size:0.82rem;color:{TEXT_MUTED};margin-top:2px;">{order.customer_name}</div>
                    <div style="font-size:0.78rem;color:{TEXT_MUTED};margin-top:2px;">{order.customer_city} · {order.customer_phone}</div>
                    """)
                    for it in items:
                        render_html(f'<div style="font-size:0.78rem;color:{TEXT_MUTED};margin-top:1px;">{it["item_name"]} × {it["quantity"]}</div>')
                with c2:
                    render_html(f"""
                    <div style="font-family:'Space Grotesk',sans-serif;font-size:1.3rem;
                                font-weight:800;color:{PRIMARY};">Rs. {order.total:,.0f}</div>
                    <div style="font-size:0.75rem;color:{TEXT_MUTED};margin-top:2px;">{order.created_at[11:16]}</div>
                    """)
                with c3:
                    render_html(badge(order.status))

                if order.notes:
                    render_html(f'<div style="font-size:0.78rem;color:{TEXT_MUTED};margin-top:6px;font-style:italic;">Note: {order.notes}</div>')

                nxt = order.next_status()
                if nxt:
                    bc1, bc2 = st.columns([3, 1])
                    with bc1:
                        if st.button(NEXT.get(nxt, nxt), key=f"adv_{order.id}",
                                     use_container_width=True, type="primary"):
                            db.update_order_status(order.id, nxt)
                            st.rerun()
                    with bc2:
                        if order.status == "pending":
                            if st.button("Cancel", key=f"cxl_{order.id}", use_container_width=True):
                                db.update_order_status(order.id, "cancelled")
                                st.rerun()
    else:
        render_html(f'<div style="text-align:center;padding:2rem;color:{TEXT_MUTED};">No active orders right now.</div>')

    if past:
        render_html(f'<div style="font-size:0.75rem;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;color:{TEXT_DIM};margin:1.5rem 0 0.8rem;">Completed ({len(past)})</div>')
        for row in past[:10]:
            order = Order(row)
            with st.container(border=True):
                c1, c2, c3 = st.columns([3, 2, 2])
                with c1:
                    render_html(f'<div style="font-weight:600;color:{TEXT};">#{order.id} — {order.customer_name}</div>')
                with c2:
                    render_html(f'<div style="color:{PRIMARY};font-weight:700;">Rs. {order.total:,.0f}</div>')
                with c3:
                    render_html(badge(order.status))


def _menu(db, rest):
    page_header("Menu Management")

    with st.expander("Add New Item"):
        with st.form("add_item_form"):
            c1, c2 = st.columns(2)
            with c1:
                new_name = st.text_input("Item Name*")
                new_cat  = st.selectbox("Category", ["Burgers","Fried Chicken","Karahi","Nihari & Haleem",
                                                      "Biryani & Rice","Bread","Soups","Noodles","Rice",
                                                      "Mains","Dim Sum","Chai & Kahwa","Snacks",
                                                      "Desserts","Drinks","Cold Drinks","Deals","Sides","Other"])
            with c2:
                new_price = st.number_input("Price (Rs.)*", min_value=0.0, step=5.0, format="%.0f")
                new_desc  = st.text_input("Description")
            if st.form_submit_button("Add Item", use_container_width=True):
                if new_name and new_price > 0:
                    db.add_menu_item(rest["id"], new_name, new_desc, new_price, new_cat)
                    st.success(f"'{new_name}' added to menu.")
                    st.rerun()
                else:
                    st.error("Name and price are required.")

    all_items = db.get_all_menu(rest["id"])
    cats: dict = {}
    for item in all_items:
        cats.setdefault(item["category"] or "Other", []).append(item)

    for category, cat_items in cats.items():
        render_html(f'<div style="font-size:0.75rem;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;color:{TEXT_DIM};margin:1.4rem 0 0.6rem;">{category}</div>')
        with st.container(border=True):
            for item in cat_items:
                c1, c2, c3, c4, c5 = st.columns([3, 2, 1, 1, 1])
                with c1:
                    render_html(f"""
                    <div style="font-weight:600;color:{TEXT};font-size:0.9rem;">{item['name']}</div>
                    <div style="color:{TEXT_MUTED};font-size:0.78rem;">{item.get('description') or ''}</div>
                    """)
                with c2:
                    new_p = st.number_input("", value=float(item["price"]),
                                             step=5.0, format="%.0f",
                                             key=f"price_{item['id']}",
                                             label_visibility="collapsed")
                    if new_p != float(item["price"]):
                        if st.button("Save", key=f"saveprice_{item['id']}"):
                            db.update_menu_item_price(item["id"], new_p)
                            st.success("Price updated.")
                            st.rerun()
                with c3:
                    avail_color = "#15803D" if item["available"] else "#BE123C"
                    render_html(f'<div style="text-align:center;padding:0.5rem;font-size:0.82rem;font-weight:600;color:{avail_color};">{"On" if item["available"] else "Off"}</div>')
                with c4:
                    lbl = "Disable" if item["available"] else "Enable"
                    if st.button(lbl, key=f"tog_{item['id']}", use_container_width=True):
                        db.toggle_item_availability(item["id"])
                        st.rerun()
                with c5:
                    if st.button("Delete", key=f"del_{item['id']}", use_container_width=True):
                        db.delete_menu_item(item["id"])
                        st.rerun()


def _reviews(db, rest):
    page_header("Customer Reviews")

    reviews = db.get_reviews_by_restaurant(rest["id"])
    if not reviews:
        render_html(f'<div style="text-align:center;padding:3rem;color:{TEXT_MUTED};">No reviews yet.</div>')
        return

    avg = sum(r["rating"] for r in reviews) / len(reviews)
    c1, c2 = st.columns(2)
    c1.metric("Average Rating", f"{avg:.1f} / 5.0")
    c2.metric("Total Reviews", len(reviews))

    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
    for r in reviews:
        with st.container(border=True):
            render_html(f"""
            <div style="display:flex;justify-content:space-between;align-items:flex-start;">
                <div>
                    <div style="font-weight:600;color:{TEXT};">{r['customer_name']}</div>
                    <div style="color:#F59E0B;font-size:0.9rem;margin-top:2px;">
                        {"★" * r['rating']}{"☆" * (5 - r['rating'])}
                    </div>
                </div>
                <div style="color:{TEXT_MUTED};font-size:0.75rem;">{str(r['created_at'])[:10]}</div>
            </div>
            """)
            if r.get("comment"):
                render_html(f'<div style="color:{TEXT_MUTED};font-size:0.85rem;margin-top:0.6rem;line-height:1.5;">{r["comment"]}</div>')


def _stats(db, rest):
    page_header("Statistics", f"Performance overview for {rest['name']}")

    rows = db.get_orders_by_restaurant(rest["id"])
    total     = len(rows)
    revenue   = sum(float(r["total"]) for r in rows if r["status"] == "delivered")
    active    = sum(1 for r in rows if r["status"] in ("pending","confirmed","preparing","ready"))
    delivered = sum(1 for r in rows if r["status"] == "delivered")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Orders", total)
    c2.metric("Revenue (Rs.)", f"{revenue:,.0f}")
    c3.metric("Active Now", active)
    c4.metric("Delivered", delivered)

    if rows:
        df = pd.DataFrame(rows)
        df["created_at"] = pd.to_datetime(df["created_at"])
        st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            render_html(f'<div style="font-size:0.75rem;font-weight:700;letter-spacing:0.08em;text-transform:uppercase;color:{TEXT_DIM};margin-bottom:0.5rem;">Orders by Status</div>')
            sc = df["status"].value_counts().reset_index()
            sc.columns = ["Status", "Count"]
            if HAS_PLOTLY:
                STATUS_COLORS = {
                    "pending": "#F97316", "confirmed": "#3B82F6",
                    "preparing": "#8B5CF6", "ready": "#10B981",
                    "picked_up": "#0D9488", "delivered": "#16A34A",
                    "cancelled": "#EF4444",
                }
                colors = [STATUS_COLORS.get(s, PRIMARY) for s in sc["Status"].tolist()]
                fig = go.Figure(go.Bar(
                    x=sc["Status"], y=sc["Count"],
                    marker=dict(color=colors),
                    text=sc["Count"], textposition="outside",
                    textfont=dict(size=12, color=TEXT),
                ))
                fig.update_layout(
                    plot_bgcolor="white", paper_bgcolor="white",
                    font=dict(family="Plus Jakarta Sans", color=TEXT, size=12),
                    margin=dict(l=10, r=10, t=10, b=10),
                    xaxis=dict(showgrid=False, showline=False, tickfont=dict(color=TEXT_MUTED, size=11)),
                    yaxis=dict(showgrid=True, gridcolor="#E2E8F0", showline=False, tickfont=dict(color=TEXT_MUTED)),
                    showlegend=False, height=260,
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.bar_chart(sc.set_index("Status"))
        with col2:
            render_html(f'<div style="font-size:0.75rem;font-weight:700;letter-spacing:0.08em;text-transform:uppercase;color:{TEXT_DIM};margin-bottom:0.5rem;">Recent Orders</div>')
            display = df[["id", "customer_name", "total", "status"]].head(10)
            st.dataframe(display, use_container_width=True, hide_index=True)


def _branches(db, rest):
    page_header("My Branches", f"City-wise branches for {rest['name']}")

    branches = db.get_branches_by_restaurant(rest["id"])

    # Show delivery info per city
    cities_with_branch = list({b["city"] for b in branches})
    if cities_with_branch:
        render_html(f'<div class="zd-section-label">Delivery Info by City</div>')
        city_cols = st.columns(min(len(cities_with_branch), 3))
        for i, city in enumerate(sorted(cities_with_branch)):
            cfg = db.get_city_delivery_settings(city)
            with city_cols[i % 3]:
                if cfg:
                    render_html(f"""
                    <div style="background:#F0FDF4;border:1.5px solid #BBF7D0;border-radius:14px;
                                padding:1rem 1.2rem;margin-bottom:0.8rem;">
                        <div style="font-family:'Space Grotesk',sans-serif;font-weight:700;
                                    color:{TEXT};font-size:1rem;">📍 {city}</div>
                        <div style="font-size:0.82rem;color:{TEXT_MUTED};margin-top:6px;">
                            {cfg['delivery_time_min']}–{cfg['delivery_time_max']} min
                        </div>
                        <div style="font-size:0.82rem;color:{TEXT_MUTED};margin-top:2px;">
                            Rs. {float(cfg['delivery_charge']):,.0f} delivery
                        </div>
                        <div style="font-size:0.82rem;color:{PRIMARY};font-weight:600;margin-top:2px;">
                            Free above Rs. {float(cfg['free_delivery_above']):,.0f}
                        </div>
                    </div>
                    """)
                else:
                    render_html(f"""
                    <div style="background:#F1F5F9;border:1.5px solid {BORDER};border-radius:14px;
                                padding:1rem 1.2rem;margin-bottom:0.8rem;">
                        <div style="font-weight:700;color:{TEXT};">📍 {city}</div>
                        <div style="font-size:0.8rem;color:{TEXT_MUTED};margin-top:4px;">
                            No delivery settings configured by admin yet.
                        </div>
                    </div>
                    """)

    # Add branch
    with st.expander("Add a New Branch"):
        with st.form("add_branch_rest_form"):
            c1, c2 = st.columns(2)
            with c1:
                city    = st.selectbox("City*", PAKISTAN_CITIES)
                address = st.text_input("Branch Address*", placeholder="Full street address")
            with c2:
                phone = st.text_input("Branch Phone", placeholder="e.g. 042-XXXXXXX")
            if st.form_submit_button("Add Branch", use_container_width=True):
                if city and address:
                    db.add_branch(rest["id"], city, address, phone)
                    st.success(f"Branch added in {city}!")
                    st.rerun()
                else:
                    st.error("City and address are required.")

    st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
    render_html(f'<div class="zd-section-label">All Branches ({len(branches)})</div>')

    if not branches:
        render_html(f'<div style="text-align:center;padding:3rem;color:{TEXT_MUTED};">No branches added yet. Add your first branch above.</div>')
        return

    # Group by city
    by_city: dict = {}
    for b in branches:
        by_city.setdefault(b["city"], []).append(b)

    for city, city_branches in sorted(by_city.items()):
        render_html(f'<div style="font-size:0.75rem;font-weight:800;letter-spacing:0.08em;text-transform:uppercase;color:{TEXT_DIM};margin:1rem 0 0.5rem;">📍 {city}</div>')
        for b in city_branches:
            with st.container(border=True):
                c1, c2, c3 = st.columns([5, 1, 1])
                with c1:
                    open_c = "#16A34A" if b["is_open"] else "#DC2626"
                    render_html(f"""
                    <div style="font-weight:600;color:{TEXT};">{b['address']}</div>
                    <div style="font-size:0.78rem;color:{TEXT_MUTED};margin-top:2px;">{b.get('phone') or 'No phone set'}</div>
                    <div style="font-size:0.75rem;color:{open_c};font-weight:700;margin-top:3px;">
                        {"● Open" if b['is_open'] else "● Closed"}
                    </div>
                    """)
                with c2:
                    lbl = "Close" if b["is_open"] else "Open"
                    if st.button(lbl, key=f"rtog_{b['id']}", use_container_width=True):
                        db.toggle_branch(b["id"])
                        st.rerun()
                with c3:
                    if st.button("Delete", key=f"rdel_{b['id']}", use_container_width=True):
                        db.delete_branch(b["id"])
                        st.rerun()
