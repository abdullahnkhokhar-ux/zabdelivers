import streamlit as st

# ── Premium Teal & Slate Palette ───────────────────────────
PRIMARY       = "#0D9488"   # Teal-600
PRIMARY_DARK  = "#0F766E"   # Teal-700
PRIMARY_LIGHT = "#CCFBF1"   # Teal-100
PRIMARY_GLOW  = "rgba(13,148,136,0.15)"
BG            = "#F0F4F8"
SURFACE       = "#FFFFFF"
SURFACE2      = "#F1F5F9"
SURFACE3      = "#E8EFF7"
BORDER        = "#D1DBE8"
BORDER_FOCUS  = "#0D9488"
TEXT          = "#0F172A"
TEXT_MUTED    = "#475569"
TEXT_DIM      = "#94A3B8"
SHADOW        = "rgba(15,23,42,0.10)"
SHADOW_MD     = "rgba(15,23,42,0.15)"
ACCENT        = "#F59E0B"
SUCCESS       = "#10B981"
DANGER        = "#EF4444"

CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:ital,wght@0,300;0,400;0,500;0,600;0,700;0,800;1,400&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&display=swap');

/* ── Reset & Base ── */
*, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
html, body, [class*="css"] {{
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    background: {BG} !important;
    color: {TEXT} !important;
    -webkit-font-smoothing: antialiased !important;
}}
.stApp {{ background: {BG} !important; }}
#MainMenu, footer, header {{ visibility: hidden !important; }}
[data-testid="stToolbar"], .stDeployButton {{ display: none !important; }}
.block-container {{ padding: 0 !important; max-width: 100% !important; }}
[data-testid="stSidebar"] {{ display: none !important; width: 0 !important; }}
[data-testid="collapsedControl"] {{ display: none !important; }}

/* ── Scrollbar ── */
::-webkit-scrollbar {{ width: 6px; height: 6px; }}
::-webkit-scrollbar-track {{ background: {SURFACE2}; border-radius: 10px; }}
::-webkit-scrollbar-thumb {{ background: #CBD5E1; border-radius: 10px; }}
::-webkit-scrollbar-thumb:hover {{ background: {PRIMARY}; }}

/* ── Navbar ── */
.zd-navbar {{
    background: {SURFACE};
    border-bottom: 1.5px solid {BORDER};
    padding: 0 2.5rem;
    height: 68px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    box-shadow: 0 2px 16px {SHADOW};
}}
.zd-brand {{
    font-family: 'Space Grotesk', sans-serif;
    font-size: 1.55rem;
    font-weight: 700;
    color: {TEXT};
    letter-spacing: -0.03em;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}}
.zd-brand span {{ color: {PRIMARY}; }}
.zd-brand-dot {{
    width: 10px; height: 10px;
    background: {PRIMARY};
    border-radius: 50%;
    display: inline-block;
    margin-right: 2px;
    box-shadow: 0 0 8px rgba(13,148,136,0.5);
}}
.zd-user-chip {{
    background: {PRIMARY_LIGHT};
    color: {PRIMARY_DARK};
    border-radius: 50px;
    padding: 0.4rem 1.1rem;
    font-size: 0.82rem;
    font-weight: 700;
    border: 1.5px solid rgba(13,148,136,0.2);
}}

/* ── Page Container ── */
.zd-page {{ max-width: 1280px; margin: 0 auto; padding: 2rem 2.5rem 4rem; }}
.zd-page-title {{
    font-family: 'Space Grotesk', sans-serif;
    font-size: 2.1rem;
    font-weight: 700;
    color: {TEXT};
    letter-spacing: -0.03em;
    margin-bottom: 0.25rem;
    line-height: 1.1;
}}
.zd-page-sub {{
    font-size: 0.88rem;
    color: {TEXT_MUTED};
    margin-bottom: 2rem;
    font-weight: 400;
}}

/* ── Buttons ── */
.stButton > button {{
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-weight: 600 !important;
    border-radius: 10px !important;
    transition: all 0.18s ease !important;
    font-size: 0.875rem !important;
}}
.stButton > button[kind="primary"] {{
    background: linear-gradient(135deg, {PRIMARY} 0%, {PRIMARY_DARK} 100%) !important;
    color: #fff !important;
    border: none !important;
    box-shadow: 0 2px 10px rgba(13,148,136,0.30) !important;
}}
.stButton > button[kind="primary"]:hover {{
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 20px rgba(13,148,136,0.40) !important;
}}
.stButton > button[kind="secondary"], .stButton > button:not([kind]) {{
    background: {SURFACE} !important;
    color: {TEXT} !important;
    border: 1.5px solid {BORDER} !important;
    box-shadow: 0 1px 4px {SHADOW} !important;
}}
.stButton > button[kind="secondary"]:hover, .stButton > button:not([kind]):hover {{
    background: {SURFACE2} !important;
    border-color: {PRIMARY} !important;
    color: {PRIMARY} !important;
    transform: translateY(-1px) !important;
}}

[data-testid="stFormSubmitButton"] button {{
    background: linear-gradient(135deg, {PRIMARY} 0%, {PRIMARY_DARK} 100%) !important;
    color: #fff !important;
    border: none !important;
    border-radius: 10px !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-weight: 700 !important;
    font-size: 0.95rem !important;
    width: 100% !important;
    padding: 0.75rem !important;
    box-shadow: 0 4px 14px rgba(13,148,136,0.30) !important;
    transition: all 0.18s !important;
}}
[data-testid="stFormSubmitButton"] button:hover {{
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 24px rgba(13,148,136,0.40) !important;
}}

/* ════════════════════════════════════════════════════════════
   INPUT PLACEHOLDER FIX — ALL TEXT INPUTS
   ════════════════════════════════════════════════════════════ */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stNumberInput > div > div > input {{
    background: {SURFACE} !important;
    border: 1.5px solid {BORDER} !important;
    border-radius: 10px !important;
    color: {TEXT} !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-size: 0.9rem !important;
    padding: 0.65rem 0.9rem !important;
    transition: border-color 0.15s, box-shadow 0.15s !important;
}}
.stTextInput > div > div > input::placeholder {{
    color: #64748B !important;
    opacity: 1 !important;
    font-style: italic !important;
}}
.stTextArea > div > div > textarea::placeholder {{
    color: #64748B !important;
    opacity: 1 !important;
    font-style: italic !important;
}}
.stNumberInput > div > div > input::placeholder {{
    color: #64748B !important;
    opacity: 1 !important;
    font-style: italic !important;
}}
.stTextInput > div > div > input::-webkit-input-placeholder,
.stTextArea > div > div > textarea::-webkit-input-placeholder {{
    color: #64748B !important;
    opacity: 1 !important;
}}
.stTextInput > div > div > input::-moz-placeholder,
.stTextArea > div > div > textarea::-moz-placeholder {{
    color: #64748B !important;
    opacity: 1 !important;
}}
.stTextInput > div > div > input:-ms-input-placeholder,
.stTextArea > div > div > textarea:-ms-input-placeholder {{
    color: #64748B !important;
    opacity: 1 !important;
}}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus,
.stNumberInput > div > div > input:focus {{
    border-color: {PRIMARY} !important;
    box-shadow: 0 0 0 3px rgba(13,148,136,0.14) !important;
    outline: none !important;
}}
.stTextInput label, .stTextArea label, .stSelectbox label, .stNumberInput label {{
    color: {TEXT_MUTED} !important;
    font-size: 0.76rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.07em !important;
    text-transform: uppercase !important;
    margin-bottom: 0.3rem !important;
}}

/* ── Selectbox ── */
.stSelectbox > div > div {{
    background: {SURFACE} !important;
    border: 1.5px solid {BORDER} !important;
    border-radius: 10px !important;
    color: {TEXT} !important;
}}
[data-baseweb="select"] > div {{ color: {TEXT} !important; }}
[data-baseweb="popover"] [role="option"] {{
    color: {TEXT} !important;
    background: {SURFACE} !important;
}}
[data-baseweb="popover"] [role="option"]:hover {{
    background: {PRIMARY_LIGHT} !important;
    color: {PRIMARY_DARK} !important;
}}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {{
    background: {SURFACE2} !important;
    border-radius: 12px !important;
    padding: 5px !important;
    border: 1.5px solid {BORDER} !important;
    gap: 2px !important;
}}
.stTabs [data-baseweb="tab"] {{
    background: transparent !important;
    border-radius: 9px !important;
    color: {TEXT_MUTED} !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-size: 0.88rem !important;
    font-weight: 600 !important;
    padding: 0.5rem 1.3rem !important;
    transition: all 0.2s !important;
    border: none !important;
}}
.stTabs [aria-selected="true"] {{
    background: linear-gradient(135deg, {PRIMARY} 0%, {PRIMARY_DARK} 100%) !important;
    color: #fff !important;
    box-shadow: 0 3px 10px rgba(13,148,136,0.28) !important;
}}

/* ── Cards / Containers ── */
[data-testid="stVerticalBlockBorderWrapper"] {{
    background: {SURFACE} !important;
    border: 1.5px solid {BORDER} !important;
    border-radius: 16px !important;
    box-shadow: 0 2px 8px {SHADOW} !important;
    transition: all 0.2s !important;
}}
[data-testid="stVerticalBlockBorderWrapper"]:hover {{
    border-color: rgba(13,148,136,0.30) !important;
    box-shadow: 0 6px 20px {SHADOW_MD} !important;
}}

/* ── Metrics ── */
[data-testid="stMetric"] {{
    background: {SURFACE} !important;
    border: 1.5px solid {BORDER} !important;
    border-radius: 16px !important;
    padding: 1.4rem 1.6rem !important;
    box-shadow: 0 2px 8px {SHADOW} !important;
    transition: all 0.2s !important;
    border-top: 3px solid {PRIMARY} !important;
}}
[data-testid="stMetric"]:hover {{
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 24px {SHADOW_MD} !important;
}}
[data-testid="stMetricLabel"] {{
    color: {TEXT_MUTED} !important;
    font-size: 0.72rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.09em !important;
    font-weight: 700 !important;
}}
[data-testid="stMetricValue"] {{
    color: {TEXT} !important;
    font-family: 'Space Grotesk', sans-serif !important;
    font-size: 2rem !important;
    font-weight: 700 !important;
    letter-spacing: -0.02em !important;
}}

/* ── Expander ── */
[data-testid="stExpander"] {{
    background: {SURFACE} !important;
    border: 1.5px solid {BORDER} !important;
    border-radius: 14px !important;
    box-shadow: 0 1px 6px {SHADOW} !important;
    overflow: hidden !important;
}}
[data-testid="stExpander"] summary {{
    color: {TEXT} !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-weight: 600 !important;
    padding: 0.9rem 1.1rem !important;
}}
[data-testid="stExpander"] summary:hover {{
    background: {SURFACE2} !important;
}}

/* ── Dataframe ── */
[data-testid="stDataFrame"] {{
    border-radius: 14px !important;
    overflow: hidden !important;
    border: 1.5px solid {BORDER} !important;
    box-shadow: 0 2px 8px {SHADOW} !important;
}}

/* ── Vega/Altair charts ── */
[data-testid="stVegaLiteChart"] {{
    background: {SURFACE} !important;
    border-radius: 14px !important;
    padding: 0.5rem !important;
    border: 1.5px solid {BORDER} !important;
    box-shadow: 0 2px 8px {SHADOW} !important;
    overflow: hidden !important;
}}
[data-testid="stVegaLiteChart"] > div {{ background: {SURFACE} !important; }}
.vega-embed {{ background: {SURFACE} !important; }}

/* ── Radio ── */
.stRadio label {{
    background: {SURFACE} !important;
    border: 1.5px solid {BORDER} !important;
    border-radius: 10px !important;
    color: {TEXT_MUTED} !important;
    font-size: 0.88rem !important;
    font-weight: 500 !important;
    padding: 0.5rem 1rem !important;
    transition: all 0.15s !important;
    cursor: pointer !important;
}}
.stRadio label:hover {{
    border-color: {PRIMARY} !important;
    color: {PRIMARY} !important;
    background: {PRIMARY_LIGHT} !important;
}}

/* ── Misc ── */
.stAlert {{ border-radius: 12px !important; }}
hr {{ border-color: {BORDER} !important; margin: 0.5rem 0 !important; }}
.stCaption {{ color: {TEXT_MUTED} !important; }}

/* ── Section label ── */
.zd-section-label {{
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 0.7rem;
    font-weight: 800;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: {TEXT_DIM};
    margin-bottom: 0.7rem;
    display: flex;
    align-items: center;
    gap: 0.6rem;
}}
.zd-section-label::after {{
    content: '';
    flex: 1;
    height: 1px;
    background: {BORDER};
}}

/* ── Status Badges ── */
.zd-badge {{
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 4px 12px;
    border-radius: 50px;
    font-size: 0.70rem;
    font-weight: 800;
    letter-spacing: 0.07em;
    text-transform: uppercase;
    font-family: 'Plus Jakarta Sans', sans-serif;
}}
.zd-badge-pending   {{ background:#FFF7ED; color:#C2410C; border:1.5px solid #FED7AA; }}
.zd-badge-confirmed {{ background:#EFF6FF; color:#1D4ED8; border:1.5px solid #BFDBFE; }}
.zd-badge-preparing {{ background:#F5F3FF; color:#7C3AED; border:1.5px solid #DDD6FE; }}
.zd-badge-ready     {{ background:#F0FDF4; color:#15803D; border:1.5px solid #BBF7D0; }}
.zd-badge-picked_up {{ background:#ECFDF5; color:#0F766E; border:1.5px solid #A7F3D0; }}
.zd-badge-delivered {{ background:#F0FDF4; color:#166534; border:1.5px solid #BBF7D0; }}
.zd-badge-cancelled {{ background:#FFF1F2; color:#BE123C; border:1.5px solid #FECDD3; }}

/* ── Custom Cards ── */
.zd-card {{
    background: {SURFACE};
    border: 1.5px solid {BORDER};
    border-radius: 16px;
    padding: 1.4rem 1.6rem;
    margin-bottom: 0.9rem;
    box-shadow: 0 2px 8px {SHADOW};
    transition: all 0.2s;
}}
.zd-card:hover {{
    border-color: rgba(13,148,136,0.3);
    box-shadow: 0 6px 20px {SHADOW_MD};
    transform: translateY(-2px);
}}
.zd-rest-card {{
    background: {SURFACE};
    border: 1.5px solid {BORDER};
    border-left: 4px solid {PRIMARY};
    border-radius: 16px;
    padding: 1.5rem 1.7rem;
    margin-bottom: 1rem;
    cursor: pointer;
    box-shadow: 0 2px 8px {SHADOW};
    transition: all 0.22s;
}}
.zd-rest-card:hover {{
    border-color: {PRIMARY};
    box-shadow: 0 8px 28px rgba(13,148,136,0.15);
    transform: translateY(-3px);
}}
.zd-menu-item {{
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    padding: 0.9rem 0;
    border-bottom: 1px solid {SURFACE3};
}}
.zd-menu-item:last-child {{ border-bottom: none; }}
.zd-cart-row {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.6rem 0;
    border-bottom: 1px solid {SURFACE3};
}}
.zd-cart-row:last-child {{ border-bottom: none; }}
.zd-auth-card {{
    background: {SURFACE};
    border: 1.5px solid {BORDER};
    border-radius: 22px;
    padding: 2.5rem;
    box-shadow: 0 8px 40px {SHADOW};
}}

/* ── Hide press-enter instruction ── */
[data-testid="InputInstructions"] {{ display: none !important; }}

/* ── Remove ghost form container ── */
[data-testid="stForm"] {{
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 0 !important;
}}
.stTabs [data-baseweb="tab-panel"] {{ padding-top: 0 !important; }}
.zd-auth-card [data-testid="stVerticalBlockBorderWrapper"] {{
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 0 !important;
}}

/* ════════════════════════════════════════════════════════════
   BUTTONS — CENTERED WITH PROPER PADDING
   ════════════════════════════════════════════════════════════ */
.stButton > button {{
    margin: 0 4px !important;
    padding: 0.55rem 1.2rem !important;
    min-height: 42px !important;
}}
[data-testid="stFormSubmitButton"] button {{
    margin: 0.5rem 0 0 !important;
    padding: 0.8rem 1.5rem !important;
    min-height: 48px !important;
}}
[data-testid="stHorizontalBlock"] > div [data-testid="stButton"] {{
    display: flex !important;
    justify-content: center !important;
    align-items: center !important;
}}
[data-testid="stButton"] > button {{
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    text-align: center !important;
    white-space: nowrap !important;
}}

/* ════════════════════════════════════════════════════════════
   MOBILE RESPONSIVE — 768px and below
   ════════════════════════════════════════════════════════════ */
@media (max-width: 768px) {{

    /* Navbar — smaller and tighter on mobile */
    .zd-navbar {{
        padding: 0 1rem !important;
        height: 56px !important;
    }}
    .zd-brand {{
        font-size: 1.15rem !important;
    }}
    .zd-brand-dot {{
        width: 8px !important;
        height: 8px !important;
    }}
    .zd-user-chip {{
        font-size: 0.72rem !important;
        padding: 0.3rem 0.7rem !important;
    }}

    /* Page container — less padding on mobile */
    .zd-page {{
        padding: 1rem 0.8rem 3rem !important;
    }}

    /* Page title smaller */
    .zd-page-title {{
        font-size: 1.4rem !important;
    }}
    .zd-page-sub {{
        font-size: 0.82rem !important;
        margin-bottom: 1.2rem !important;
    }}

    /* Nav buttons — smaller font and padding */
    .stButton > button {{
        font-size: 0.75rem !important;
        padding: 0.4rem 0.5rem !important;
        min-height: 38px !important;
        margin: 0 2px !important;
    }}

    /* Stack columns on mobile — make Streamlit columns full width */
    [data-testid="stHorizontalBlock"] {{
        flex-wrap: wrap !important;
        gap: 0.5rem !important;
    }}
    [data-testid="stHorizontalBlock"] > div {{
        min-width: 100% !important;
        flex: 1 1 100% !important;
    }}

    /* Cards — reduce padding */
    .zd-card {{
        padding: 1rem 1rem !important;
        border-radius: 12px !important;
    }}
    .zd-rest-card {{
        padding: 1rem 1.1rem !important;
        border-radius: 12px !important;
    }}

    /* Auth card — smaller padding */
    .zd-auth-card {{
        padding: 1.4rem 1.1rem !important;
        border-radius: 16px !important;
    }}

    /* Metrics — smaller value text */
    [data-testid="stMetricValue"] {{
        font-size: 1.4rem !important;
    }}
    [data-testid="stMetric"] {{
        padding: 1rem 1.1rem !important;
    }}

    /* Tabs — smaller text */
    .stTabs [data-baseweb="tab"] {{
        font-size: 0.78rem !important;
        padding: 0.4rem 0.7rem !important;
    }}

    /* Inputs — comfortable touch size */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stNumberInput > div > div > input {{
        font-size: 1rem !important;
        padding: 0.75rem 0.9rem !important;
        min-height: 48px !important;
    }}

    /* Selectbox touch-friendly */
    .stSelectbox > div > div {{
        min-height: 48px !important;
        font-size: 1rem !important;
    }}

    /* Form submit button — big and easy to tap */
    [data-testid="stFormSubmitButton"] button {{
        min-height: 52px !important;
        font-size: 1rem !important;
    }}

    /* Dataframe — allow horizontal scroll */
    [data-testid="stDataFrame"] {{
        overflow-x: auto !important;
    }}

    /* Expander — full width */
    [data-testid="stExpander"] {{
        border-radius: 10px !important;
    }}

    /* Menu item — stack on small screens */
    .zd-menu-item {{
        flex-direction: column !important;
        gap: 0.4rem !important;
        padding: 0.8rem 0 !important;
    }}

    /* Cart row — stack on small screens */
    .zd-cart-row {{
        flex-direction: column !important;
        align-items: flex-start !important;
        gap: 0.3rem !important;
    }}

    /* Section label smaller */
    .zd-section-label {{
        font-size: 0.65rem !important;
    }}

    /* Badge smaller */
    .zd-badge {{
        font-size: 0.62rem !important;
        padding: 3px 9px !important;
    }}

    /* Hide hover effects on touch devices */
    .zd-card:hover,
    .zd-rest-card:hover,
    [data-testid="stMetric"]:hover {{
        transform: none !important;
    }}
}}

/* ════════════════════════════════════════════════════════════
   VERY SMALL SCREENS — 480px and below (phones)
   ════════════════════════════════════════════════════════════ */
@media (max-width: 480px) {{

    .zd-navbar {{
        padding: 0 0.75rem !important;
        height: 52px !important;
    }}
    .zd-brand {{
        font-size: 1rem !important;
    }}
    .zd-page {{
        padding: 0.75rem 0.6rem 2.5rem !important;
    }}
    .zd-page-title {{
        font-size: 1.2rem !important;
    }}
    .stButton > button {{
        font-size: 0.7rem !important;
        padding: 0.35rem 0.4rem !important;
        min-height: 36px !important;
    }}
    [data-testid="stMetricValue"] {{
        font-size: 1.2rem !important;
    }}
    .zd-auth-card {{
        padding: 1.1rem 0.9rem !important;
    }}
}}
</style>
"""


def inject_css():
    st.markdown(CSS, unsafe_allow_html=True)


def render_navbar(user=None):
    user_chip = (
        f'<div class="zd-user-chip">👤 {user["name"].split()[0]}</div>'
        if user else ""
    )
    st.markdown(f"""
    <div class="zd-navbar">
        <div class="zd-brand">
            <span class="zd-brand-dot"></span>ZAB<span>DELIVERS</span>
        </div>
        {user_chip}
    </div>
    """, unsafe_allow_html=True)


def render_nav_buttons(nav_items, active_page, page_key, extra_cols=None):
    """Render centered nav pills as Streamlit buttons in a row."""
    n = len(nav_items)
    pad = max(1, (8 - n) // 2)
    col_widths = [pad]
    for _ in range(n):
        col_widths += [0.1, 1]
    col_widths += [0.1, 1]
    cols_raw = st.columns(col_widths)
    btn_cols = [cols_raw[1 + 1 + i*2] for i in range(n)]
    signout_col = cols_raw[-1]
    for i, (key, label) in enumerate(nav_items):
        active = (active_page == key)
        with btn_cols[i]:
            if st.button(label, key=f"nav_{page_key}_{key}", use_container_width=True,
                         type="primary" if active else "secondary"):
                st.session_state[page_key] = key
                if page_key == "cust_page":
                    st.session_state.selected_restaurant = None
                st.rerun()
    return btn_cols + [signout_col]


def badge(status):
    icons = {
        "pending":   "🕐",
        "confirmed": "✅",
        "preparing": "🍳",
        "ready":     "📦",
        "picked_up": "🛵",
        "delivered": "🎉",
        "cancelled": "✕",
    }
    labels = {
        "pending":   "Pending",
        "confirmed": "Confirmed",
        "preparing": "Preparing",
        "ready":     "Ready",
        "picked_up": "Out for Delivery",
        "delivered": "Delivered",
        "cancelled": "Cancelled",
    }
    icon = icons.get(status, "")
    return f'<span class="zd-badge zd-badge-{status}">{icon} {labels.get(status, status)}</span>'


def section_label(text):
    return f'<div class="zd-section-label">{text}</div>'


def render_html(html: str):
    st.markdown(html, unsafe_allow_html=True)


def page_header(title, subtitle=None):
    sub = f'<div class="zd-page-sub">{subtitle}</div>' if subtitle else ""
    render_html(f'<div class="zd-page-title">{title}</div>{sub}')
