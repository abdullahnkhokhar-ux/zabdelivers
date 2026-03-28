import streamlit as st
import pandas as pd
from models.order import Order
from utils.theme import (
    inject_css, badge, render_html, render_navbar,
    render_nav_buttons, page_header,
    PRIMARY, PRIMARY_LIGHT, PRIMARY_DARK,
    BORDER, TEXT_MUTED, TEXT, SURFACE2, TEXT_DIM, SURFACE, BG
)
from database.db_manager import PAKISTAN_CITIES

try:
    import plotly.graph_objects as go
    import plotly.express as px
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False


def _make_bar_chart(categories, values, title="", color=PRIMARY):
    """Create a light-theme Plotly bar chart."""
    fig = go.Figure(go.Bar(
        x=categories,
        y=values,
        marker=dict(
            color=color,
            line=dict(color=PRIMARY_DARK, width=0),
        ),
        text=values,
        textposition="outside",
        textfont=dict(size=12, color=TEXT, family="Plus Jakarta Sans"),
    ))
    fig.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(family="Plus Jakarta Sans", color=TEXT, size=12),
        title=dict(text=title, font=dict(size=14, color=TEXT, family="Plus Jakarta Sans"), x=0),
        margin=dict(l=10, r=10, t=30 if title else 10, b=10),
        xaxis=dict(
            showgrid=False, showline=False, tickfont=dict(color=TEXT_MUTED, size=11),
            tickangle=-30 if len(categories) > 5 else 0,
        ),
        yaxis=dict(
            showgrid=True, gridcolor="#E2E8F0", showline=False,
            tickfont=dict(color=TEXT_MUTED, size=11),
            zeroline=False,
        ),
        showlegend=False,
        height=280,
    )
    return fig


def show_admin_page(db):
    inject_css()
    user = st.session_state.user
    render_navbar(user)

    page = st.session_state.get("admin_page", "dashboard")
    nav_items = [
        ("dashboard",   "Dashboard"),
        ("orders",      "All Orders"),
        ("customers",   "Customers"),
        ("restaurants", "Restaurants"),
        ("branches",    "Branches"),
        ("delivery",    "Delivery"),
    ]
    st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
    cols = render_nav_buttons(nav_items, page, "admin_page")
    with cols[-1]:
        if st.button("Sign Out", key="so_admin", use_container_width=True):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()

    st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
    st.divider()

    _, content, _ = st.columns([0.1, 11, 0.1])
    with content:
        if page == "dashboard":
            _dashboard(db)
        elif page == "orders":
            _all_orders(db)
        elif page == "customers":
            _customers(db)
        elif page == "restaurants":
            _restaurants(db)
        elif page == "branches":
            _branches(db)
        elif page == "delivery":
            _delivery_settings(db)


def _dashboard(db):
    page_header("Dashboard", f"System overview · ZabDelivers · Admin: {st.session_state.user['name']}")

    s = db.get_admin_stats()
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Total Orders",   s["total_orders"])
    c2.metric("Total Revenue",  f"Rs. {s['total_revenue']:,.0f}")
    c3.metric("Customers",      s["total_customers"])
    c4.metric("Restaurants",    s["total_restaurants"])
    c5.metric("Branches",       s.get("total_branches", 0))
    c6.metric("Pending Orders", s["pending_orders"])

    st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)

    rows = db.get_all_orders()
    if rows:
        df = pd.DataFrame(rows)
        df["created_at"] = pd.to_datetime(df["created_at"])

        col1, col2 = st.columns(2)

        with col1:
            render_html(f'<div class="zd-section-label">Orders by Status</div>')
            sc = df["status"].value_counts().reset_index()
            sc.columns = ["Status", "Count"]

            if HAS_PLOTLY:
                STATUS_COLORS = {
                    "pending":   "#F97316",
                    "confirmed": "#3B82F6",
                    "preparing": "#8B5CF6",
                    "ready":     "#10B981",
                    "picked_up": "#0D9488",
                    "delivered": "#16A34A",
                    "cancelled": "#EF4444",
                }
                colors = [STATUS_COLORS.get(s, PRIMARY) for s in sc["Status"].tolist()]
                fig = go.Figure(go.Bar(
                    x=sc["Status"],
                    y=sc["Count"],
                    marker=dict(color=colors),
                    text=sc["Count"],
                    textposition="outside",
                    textfont=dict(size=12, color=TEXT),
                ))
                fig.update_layout(
                    plot_bgcolor="white", paper_bgcolor="white",
                    font=dict(family="Plus Jakarta Sans", color=TEXT, size=12),
                    margin=dict(l=10, r=10, t=10, b=10),
                    xaxis=dict(showgrid=False, showline=False, tickfont=dict(color=TEXT_MUTED, size=11)),
                    yaxis=dict(showgrid=True, gridcolor="#E2E8F0", showline=False, tickfont=dict(color=TEXT_MUTED)),
                    showlegend=False, height=280,
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.bar_chart(sc.set_index("Status"))

        with col2:
            render_html(f'<div class="zd-section-label">Revenue by Restaurant</div>')
            rev = db.get_revenue_by_restaurant()
            if rev:
                rev_df = pd.DataFrame(rev)
                if HAS_PLOTLY:
                    n = len(rev_df)
                    colors = [f"rgba(13,148,136,{0.4 + 0.6*i/(max(n-1,1))})" for i in range(n)]
                    fig2 = go.Figure(go.Bar(
                        x=rev_df["name"],
                        y=rev_df["revenue"].astype(float),
                        marker=dict(color=colors, line=dict(color=PRIMARY_DARK, width=0)),
                        text=[f"Rs. {v:,.0f}" for v in rev_df["revenue"].astype(float)],
                        textposition="outside",
                        textfont=dict(size=11, color=TEXT),
                    ))
                    fig2.update_layout(
                        plot_bgcolor="white", paper_bgcolor="white",
                        font=dict(family="Plus Jakarta Sans", color=TEXT, size=12),
                        margin=dict(l=10, r=10, t=10, b=10),
                        xaxis=dict(showgrid=False, showline=False,
                                   tickfont=dict(color=TEXT_MUTED, size=11),
                                   tickangle=-25 if len(rev_df) > 3 else 0),
                        yaxis=dict(showgrid=True, gridcolor="#E2E8F0", showline=False,
                                   tickfont=dict(color=TEXT_MUTED)),
                        showlegend=False, height=280,
                    )
                    st.plotly_chart(fig2, use_container_width=True)
                else:
                    st.bar_chart(rev_df.set_index("name")["revenue"])

        render_html(f'<div class="zd-section-label" style="margin-top:1.5rem;">Recent Orders</div>')
        display = df[["id", "customer_name", "restaurant_name", "total", "status", "created_at"]].head(20)
        st.dataframe(display, use_container_width=True, hide_index=True)


def _all_orders(db):
    page_header("All Orders", "View-only — order status is managed by each restaurant")

    col1, col2, col3 = st.columns([3, 2, 1])
    with col1:
        search = st.text_input("", placeholder="Search customer, restaurant...", label_visibility="collapsed")
    with col2:
        rows = db.get_all_orders()
        status_opts = ["All"] + sorted(list({r["status"] for r in rows}))
        status_f = st.selectbox("", status_opts, label_visibility="collapsed")
    with col3:
        if st.button("↻  Refresh", use_container_width=True):
            st.rerun()

    filtered = rows
    if status_f != "All":
        filtered = [r for r in filtered if r["status"] == status_f]
    if search:
        s = search.lower()
        filtered = [r for r in filtered if
                    s in r["customer_name"].lower() or
                    s in r.get("restaurant_name", "").lower() or
                    s in r["customer_email"].lower()]

    render_html(f'<div style="color:{TEXT_MUTED};font-size:0.82rem;margin:0.5rem 0 1rem;font-weight:600;">{len(filtered)} orders found</div>')

    # Info note
    render_html(f"""
    <div style="background:#EFF6FF;border:1.5px solid #BFDBFE;border-radius:12px;
                padding:0.8rem 1.2rem;margin-bottom:1.2rem;font-size:0.82rem;color:#1D4ED8;font-weight:600;">
        ℹ️ Order status is updated by the restaurant. Admins have view-only access here.
    </div>
    """)

    for row in filtered:
        order = Order(row)
        with st.expander(f"#{order.id}  ·  {order.customer_name}  ·  {order.restaurant_name}  ·  Rs. {order.total:,.0f}"):
            c1, c2 = st.columns(2)
            with c1:
                render_html(f"""
                {badge(order.status)}
                <div style="margin-top:0.9rem;">
                    <div style="font-size:0.82rem;color:{TEXT_MUTED};margin-top:4px;">
                        <b style="color:{TEXT};">Customer:</b> {order.customer_name}
                    </div>
                    <div style="font-size:0.82rem;color:{TEXT_MUTED};margin-top:3px;">
                        <b style="color:{TEXT};">Email:</b> {order.customer_email}
                    </div>
                    <div style="font-size:0.82rem;color:{TEXT_MUTED};margin-top:3px;">
                        <b style="color:{TEXT};">Phone:</b> {order.customer_phone}
                    </div>
                    <div style="font-size:0.82rem;color:{TEXT_MUTED};margin-top:3px;">
                        {order.customer_city}, {order.customer_country}
                    </div>
                    <div style="font-size:0.82rem;color:{TEXT_MUTED};margin-top:3px;">
                        <b style="color:{TEXT};">Address:</b> {order.customer_address}
                    </div>
                    <div style="font-size:0.75rem;color:{TEXT_DIM};margin-top:5px;">
                        Placed: {order.created_at[:16]}
                    </div>
                </div>
                """)
            with c2:
                items = db.get_order_items(order.id)
                render_html(f'<div class="zd-section-label">Items</div>')
                for it in items:
                    render_html(f'<div style="font-size:0.83rem;color:{TEXT_MUTED};padding:3px 0;">'
                                f'{it["item_name"]} × {it["quantity"]} &nbsp;—&nbsp; '
                                f'<b style="color:{TEXT};">Rs. {float(it["price"])*it["quantity"]:,.0f}</b></div>')
                render_html(f"""
                <div style="margin-top:0.9rem;padding-top:0.9rem;border-top:1.5px solid {BORDER};">
                    <div style="display:flex;justify-content:space-between;font-size:0.85rem;padding:2px 0;">
                        <span style="color:{TEXT_MUTED};">Subtotal</span>
                        <span style="color:{TEXT};">Rs. {order.subtotal:,.0f}</span>
                    </div>
                    <div style="display:flex;justify-content:space-between;font-size:0.85rem;padding:2px 0;">
                        <span style="color:{TEXT_MUTED};">Delivery</span>
                        <span style="color:{TEXT};">{"Free" if order.delivery_charge == 0 else f"Rs. {order.delivery_charge:,.0f}"}</span>
                    </div>
                    <div style="display:flex;justify-content:space-between;font-size:1rem;font-weight:700;
                                padding-top:8px;border-top:1px solid {BORDER};margin-top:4px;">
                        <span style="color:{TEXT};">Total</span>
                        <span style="color:{PRIMARY};font-family:'Space Grotesk',sans-serif;">Rs. {order.total:,.0f}</span>
                    </div>
                </div>
                """)
            # ── NO STATUS CHANGE BUTTONS HERE ──
            # Status is managed by the restaurant only


def _customers(db):
    page_header("All Customers")

    customers = db.get_all_customers()
    if not customers:
        render_html(f'<div style="text-align:center;padding:3rem;color:{TEXT_MUTED};">No customers yet.</div>')
        return

    c1, c2 = st.columns(2)
    c1.metric("Total Customers", len(customers))
    orders = db.get_all_orders()
    c2.metric("Orders Placed", len(orders))

    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
    df = pd.DataFrame(customers)
    display = df[["id", "name", "email", "phone", "created_at"]]
    display.columns = ["ID", "Name", "Email", "Phone", "Registered"]
    st.dataframe(display, use_container_width=True, hide_index=True)


def _restaurants(db):
    page_header("All Restaurants")

    rows = db.get_all_restaurants_admin()
    if not rows:
        render_html(f'<div style="text-align:center;padding:3rem;color:{TEXT_MUTED};">No restaurants yet.</div>')
        return

    c1, c2 = st.columns(2)
    c1.metric("Total Restaurants", len(rows))
    rev_data = db.get_revenue_by_restaurant()
    total_rev = sum(float(r["revenue"]) for r in rev_data)
    c2.metric("Total Revenue (Delivered)", f"Rs. {total_rev:,.0f}")

    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

    for row in rows:
        with st.container(border=True):
            c1, c2, c3 = st.columns([4, 2, 2])
            with c1:
                render_html(f"""
                <div style="font-family:'Space Grotesk',sans-serif;font-weight:700;
                            color:{TEXT};font-size:1.1rem;">{row['name']}</div>
                <div style="font-size:0.75rem;color:{PRIMARY};font-weight:700;
                            text-transform:uppercase;letter-spacing:0.06em;margin-top:2px;">
                    {row['cuisine']}
                </div>
                <div style="font-size:0.78rem;color:{TEXT_MUTED};margin-top:3px;">{row.get('address','')}</div>
                <div style="font-size:0.75rem;color:{TEXT_DIM};margin-top:2px;">Owner: {row.get('owner_email','')}</div>
                """)
            with c2:
                render_html(f"""
                <div style="color:#F59E0B;font-size:0.9rem;font-weight:700;">
                    {"★" * int(row['rating'])}{"☆" * (5-int(row['rating']))}
                </div>
                <div style="color:{TEXT_MUTED};font-size:0.78rem;margin-top:2px;">{row['phone']}</div>
                """)
            with c3:
                open_color = "#16A34A" if row["is_open"] else "#DC2626"
                open_bg = "#F0FDF4" if row["is_open"] else "#FFF1F2"
                render_html(f"""
                <div style="display:inline-block;background:{open_bg};color:{open_color};
                            border-radius:50px;padding:3px 12px;font-size:0.75rem;font-weight:700;">
                    {"● Open" if row["is_open"] else "● Closed"}
                </div>
                """)

    if rev_data:
        st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
        render_html(f'<div class="zd-section-label">Revenue by Restaurant</div>')

        if HAS_PLOTLY:
            rev_df = pd.DataFrame(rev_data)
            fig = go.Figure()
            fig.add_trace(go.Bar(
                name="Revenue (Rs.)",
                x=rev_df["name"],
                y=rev_df["revenue"].astype(float),
                marker_color=PRIMARY,
                text=[f"Rs. {v:,.0f}" for v in rev_df["revenue"].astype(float)],
                textposition="outside",
            ))
            fig.add_trace(go.Bar(
                name="Orders",
                x=rev_df["name"],
                y=rev_df["orders"],
                marker_color=PRIMARY_LIGHT,
                text=rev_df["orders"],
                textposition="outside",
            ))
            fig.update_layout(
                barmode="group",
                plot_bgcolor="white", paper_bgcolor="white",
                font=dict(family="Plus Jakarta Sans", color=TEXT, size=12),
                margin=dict(l=10, r=10, t=10, b=10),
                xaxis=dict(showgrid=False, showline=False, tickfont=dict(color=TEXT_MUTED, size=11)),
                yaxis=dict(showgrid=True, gridcolor="#E2E8F0", showline=False, tickfont=dict(color=TEXT_MUTED)),
                legend=dict(font=dict(color=TEXT), bgcolor="white"),
                height=300,
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            rev_df = pd.DataFrame(rev_data)
            st.bar_chart(rev_df.set_index("name")[["revenue", "orders"]])


def _branches(db):
    page_header("Restaurant Branches", "Manage city-wise branches for each restaurant")

    with st.expander("Add New Branch"):
        restaurants = db.get_all_restaurants_admin()
        rest_names  = [r["name"] for r in restaurants]
        with st.form("add_branch_form"):
            c1, c2 = st.columns(2)
            with c1:
                rest_choice = st.selectbox("Restaurant*", rest_names)
                city        = st.selectbox("City*", PAKISTAN_CITIES)
            with c2:
                address = st.text_input("Branch Address*", placeholder="Full address of this branch")
                phone   = st.text_input("Branch Phone", placeholder="e.g. 042-XXXXXXX")
            if st.form_submit_button("Add Branch", use_container_width=True):
                if rest_choice and city and address:
                    chosen_rest = next(r for r in restaurants if r["name"] == rest_choice)
                    db.add_branch(chosen_rest["id"], city, address, phone)
                    st.success(f"Branch added for {rest_choice} in {city}!")
                    st.rerun()
                else:
                    st.error("Please fill all required fields.")

    st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

    all_branches = db.get_all_branches_admin()
    if not all_branches:
        render_html(f'<div style="text-align:center;padding:3rem;color:{TEXT_MUTED};">No branches yet.</div>')
        return

    grouped: dict = {}
    for b in all_branches:
        grouped.setdefault(b["restaurant_name"], []).append(b)

    for rest_name, branches in grouped.items():
        render_html(f'<div class="zd-section-label">{rest_name} — {len(branches)} branch{"es" if len(branches)!=1 else ""}</div>')
        with st.container(border=True):
            for b in branches:
                c1, c2, c3, c4 = st.columns([3, 2, 1, 1])
                with c1:
                    render_html(f"""
                    <div style="font-weight:600;color:{TEXT};font-size:0.9rem;">{b['address']}</div>
                    <div style="font-size:0.75rem;color:{TEXT_MUTED};margin-top:2px;">{b.get('phone') or '—'}</div>
                    """)
                with c2:
                    open_color = "#16A34A" if b["is_open"] else "#DC2626"
                    open_bg    = "#F0FDF4" if b["is_open"] else "#FFF1F2"
                    render_html(f"""
                    <div style="display:inline-block;background:{open_bg};color:{open_color};
                                border-radius:50px;padding:3px 12px;font-size:0.75rem;font-weight:700;">
                        📍 {b['city']} &nbsp; {"● Open" if b['is_open'] else "● Closed"}
                    </div>
                    """)
                with c3:
                    lbl = "Disable" if b["is_open"] else "Enable"
                    if st.button(lbl, key=f"tog_br_{b['id']}", use_container_width=True):
                        db.toggle_branch(b["id"])
                        st.rerun()
                with c4:
                    if st.button("Delete", key=f"del_br_{b['id']}", use_container_width=True):
                        db.delete_branch(b["id"])
                        st.rerun()


def _delivery_settings(db):
    page_header("City Delivery Settings", "Set delivery time and charges per city — these reflect live in the app")

    all_settings = db.get_all_city_settings()
    existing_cities = {s["city"] for s in all_settings}

    with st.expander("Configure New City"):
        available_new = [c for c in PAKISTAN_CITIES if c not in existing_cities]
        if available_new:
            with st.form("add_city_form"):
                c1, c2, c3, c4, c5 = st.columns(5)
                with c1:
                    new_city = st.selectbox("City", available_new)
                with c2:
                    new_tmin = st.number_input("Min Time (min)", min_value=5, max_value=120, value=30, step=5)
                with c3:
                    new_tmax = st.number_input("Max Time (min)", min_value=10, max_value=180, value=45, step=5)
                with c4:
                    new_charge = st.number_input("Delivery Charge (Rs.)", min_value=0, value=100, step=10)
                with c5:
                    new_free = st.number_input("Free Above (Rs.)", min_value=0, value=1000, step=100)
                if st.form_submit_button("Save City", use_container_width=True):
                    db.update_city_delivery_settings(new_city, new_tmin, new_tmax, new_charge, new_free)
                    st.success(f"Settings saved for {new_city}!")
                    st.rerun()
        else:
            render_html(f'<div style="color:{TEXT_MUTED};font-size:0.85rem;padding:0.5rem;">All cities are already configured.</div>')

    st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
    render_html(f'<div class="zd-section-label">All City Settings</div>')

    if not all_settings:
        render_html(f'<div style="text-align:center;padding:2rem;color:{TEXT_MUTED};">No city settings configured yet.</div>')
        return

    for s in all_settings:
        with st.container(border=True):
            c1, c2, c3, c4, c5, c6, c7 = st.columns([2, 1.5, 1.5, 1.5, 1.5, 1, 1])
            with c1:
                is_on = bool(s["is_active"])
                bg_c  = PRIMARY_LIGHT if is_on else "#F1F5F9"
                tx_c  = PRIMARY_DARK  if is_on else TEXT_MUTED
                render_html(f"""
                <div style="font-family:'Space Grotesk',sans-serif;font-weight:700;
                            font-size:1.05rem;color:{TEXT};">{s['city']}</div>
                <div style="display:inline-block;background:{bg_c};color:{tx_c};
                            border-radius:50px;padding:2px 10px;font-size:0.7rem;font-weight:700;margin-top:4px;">
                    {"● Active" if is_on else "● Inactive"}
                </div>
                """)
            with c2:
                render_html(f"""
                <div style="font-size:0.7rem;color:{TEXT_MUTED};text-transform:uppercase;font-weight:700;">Delivery Time</div>
                <div style="font-size:1rem;font-weight:700;color:{PRIMARY};">
                    {s['delivery_time_min']}–{s['delivery_time_max']} min
                </div>
                """)
            with c3:
                render_html(f"""
                <div style="font-size:0.7rem;color:{TEXT_MUTED};text-transform:uppercase;font-weight:700;">Delivery Fee</div>
                <div style="font-size:1rem;font-weight:700;color:{TEXT};">Rs. {float(s['delivery_charge']):,.0f}</div>
                """)
            with c4:
                render_html(f"""
                <div style="font-size:0.7rem;color:{TEXT_MUTED};text-transform:uppercase;font-weight:700;">Free Above</div>
                <div style="font-size:1rem;font-weight:700;color:{TEXT};">Rs. {float(s['free_delivery_above']):,.0f}</div>
                """)
            with c5:
                new_tmin = st.number_input("Min", value=int(s["delivery_time_min"]),
                                            key=f"tmin_{s['city']}", min_value=5, step=5,
                                            label_visibility="collapsed")
                new_tmax = st.number_input("Max", value=int(s["delivery_time_max"]),
                                            key=f"tmax_{s['city']}", min_value=10, step=5,
                                            label_visibility="collapsed")
            with c6:
                new_charge = st.number_input("Fee", value=float(s["delivery_charge"]),
                                              key=f"fee_{s['city']}", min_value=0.0, step=10.0,
                                              label_visibility="collapsed")
                new_free   = st.number_input("Free", value=float(s["free_delivery_above"]),
                                              key=f"free_{s['city']}", min_value=0.0, step=100.0,
                                              label_visibility="collapsed")
            with c7:
                if st.button("Save", key=f"save_{s['city']}", use_container_width=True, type="primary"):
                    db.update_city_delivery_settings(
                        s["city"], new_tmin, new_tmax, new_charge, new_free
                    )
                    st.success(f"{s['city']} updated!")
                    st.rerun()
                toggle_lbl = "Disable" if s["is_active"] else "Enable"
                if st.button(toggle_lbl, key=f"tog_{s['city']}", use_container_width=True):
                    db.toggle_city_active(s["city"], 0 if s["is_active"] else 1)
                    st.rerun()
