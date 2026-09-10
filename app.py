"""
HostelCare — Hostel Complaint Registration Portal
Web Warfare 2K26 — Round 2 — Problem Statement 3

Built with Streamlit + Firebase (Firestore). No third-party AI APIs are
called by this application at runtime — it is a standard CRUD portal.
"""

import time

import pandas as pd
import altair as alt
import streamlit as st

from config.db_config import get_db_connection
from services.complaint_service import (
    filter_complaints,
    get_dashboard_stats,
    search_complaints,
    submit_complaint,
    update_status,
)
from services.sqlite_service import SQLiteService
from utils.constants import (
    APP_TITLE,
    CATEGORY_FILTER_OPTIONS,
    CATEGORY_OPTIONS,
    DUPLICATE_SUBMISSION_COOLDOWN_SECONDS,
    STATUS_BADGE_COLORS,
    STATUS_FILTER_OPTIONS,
    STATUS_ICONS,
    STATUS_OPTIONS,
)
from utils.helpers import format_timestamp

# -----------------------------------------------------------------------
# Page config + light theming
# -----------------------------------------------------------------------
st.set_page_config(
    page_title=APP_TITLE,
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=Playfair+Display:wght@600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'DM Sans', sans-serif;
        font-size: 15px;
    }

    /* ── Animations ── */
    @keyframes fadeSlideUp {
        from { opacity: 0; transform: translateY(12px); }
        to { opacity: 1; transform: translateY(0); }
    }
    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }

    /* ── Background ── */
    .stApp {
        background-color: #f9f7f4;
        animation: fadeIn 0.5s ease-out forwards;
    }

    /* ── Sidebar ── */
    [data-testid="stSidebar"] {
        background-color: #ffffff !important;
        border-right: 1px solid #ece9e3;
        backdrop-filter: none;
    }
    [data-testid="stSidebar"] * { color: #3d3730 !important; }
    [data-testid="stSidebar"] hr { border-color: #ece9e3; }

    /* Sidebar radio options */
    [data-testid="stSidebar"] .stRadio > div {
        gap: 2px;
    }
    [data-testid="stSidebar"] .stRadio label {
        padding: 9px 14px;
        border-radius: 8px;
        font-size: 14px;
        font-weight: 500;
        color: #6b6560 !important;
        transition: background 0.15s ease, color 0.15s ease;
        cursor: pointer;
    }
    [data-testid="stSidebar"] .stRadio label:hover {
        background: #f4f1ed;
        color: #1a1714 !important;
    }

    /* ── Main content ── */
    .block-container {
        background: transparent;
        padding: 1.5rem 2rem !important;
        max-width: 1100px;
        animation: fadeSlideUp 0.4s ease-out forwards;
    }

    /* ── Typography ── */
    h1 {
        font-family: 'Playfair Display', serif !important;
        font-size: 32px !important;
        font-weight: 700 !important;
        color: #1a1714 !important;
        letter-spacing: -0.3px;
        margin-bottom: 4px !important;
    }
    h2, h3 {
        font-family: 'DM Sans', sans-serif !important;
        font-weight: 600 !important;
        color: #2d2925 !important;
    }
    p, label, span, div { color: #4a4540 !important; }
    .stCaption, small { color: #9c958d !important; font-size: 13px !important; }

    /* ── KPI Cards ── */
    .kpi-card {
        background: #ffffff;
        border: 1px solid #ece9e3;
        border-radius: 12px;
        padding: 24px 22px;
        transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
        cursor: default;
        animation: fadeSlideUp 0.5s ease-out forwards;
    }
    .kpi-card:hover {
        box-shadow: 0 8px 24px rgba(0,0,0,0.04);
        transform: translateY(-3px);
        border-color: #d4cfc8;
    }
    .kpi-icon { font-size: 20px; margin-bottom: 14px; display: block; opacity: 0.8; }
    .kpi-label {
        font-size: 11px; font-weight: 600;
        color: #9c958d !important; text-transform: uppercase;
        letter-spacing: 0.1em; margin: 0 0 8px 0;
    }
    .kpi-value {
        font-family: 'Playfair Display', serif;
        font-size: 38px; font-weight: 700;
        color: #1a1714 !important;
        margin: 0; line-height: 1;
    }

    /* ── Complaint cards ── */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: #ffffff !important;
        border: 1px solid #ece9e3 !important;
        border-radius: 12px !important;
        box-shadow: none !important;
        transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
        animation: fadeSlideUp 0.4s ease-out forwards;
    }
    div[data-testid="stVerticalBlockBorderWrapper"]:hover {
        box-shadow: 0 6px 16px rgba(0,0,0,0.03) !important;
        border-color: #d4cfc8 !important;
        transform: translateY(-1px);
    }

    /* ── Status badges ── */
    .status-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 6px;
        font-size: 12px; font-weight: 600;
        letter-spacing: 0.02em;
        color: #fff;
    }

    /* ── Buttons ── */
    .stButton > button {
        font-family: 'DM Sans', sans-serif !important;
        font-weight: 500 !important;
        font-size: 14px !important;
        border-radius: 8px !important;
        border: 1px solid #d4cfc8 !important;
        color: #3d3730 !important;
        background: #ffffff !important;
        padding: 0.45rem 1.1rem !important;
        transition: all 0.2s cubic-bezier(0.25, 0.8, 0.25, 1) !important;
    }
    .stButton > button:hover {
        border-color: #b0a89e !important;
        background: #f4f1ed !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.03) !important;
        transform: translateY(-1px) !important;
    }
    .stButton > button:active {
        transform: translateY(0) !important;
    }
    .stButton > button[kind="primary"] {
        background: #1a1714 !important;
        color: #f9f7f4 !important;
        border-color: #1a1714 !important;
    }
    .stButton > button[kind="primary"]:hover {
        background: #2d2925 !important;
        border-color: #2d2925 !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1) !important;
    }

    /* ── Inputs ── */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div {
        background: #ffffff !important;
        border: 1px solid #d4cfc8 !important;
        border-radius: 8px !important;
        color: #1a1714 !important;
        font-family: 'DM Sans', sans-serif !important;
        transition: border-color 0.2s ease, box-shadow 0.2s ease, transform 0.2s ease;
    }
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus,
    .stSelectbox > div > div:focus-within {
        border-color: #1a1714 !important;
        box-shadow: 0 0 0 3px rgba(26,23,20,0.06) !important;
        transform: translateY(-1px);
    }

    /* ── Dataframe ── */
    .stDataFrame { border-radius: 10px; border: 1px solid #ece9e3; overflow: hidden; }

    /* ── Login page ── */
    .login-card {
        background: #ffffff;
        border: 1px solid #ece9e3;
        border-radius: 16px;
        padding: 44px 40px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.04);
        text-align: center;
        animation: fadeSlideUp 0.6s cubic-bezier(0.25, 0.8, 0.25, 1) forwards;
    }
    .login-logo { font-size: 36px; margin-bottom: 16px; display: block; }
    .login-title {
        font-family: 'Playfair Display', serif;
        font-size: 26px; font-weight: 700;
        color: #1a1714 !important;
        margin: 0 0 6px 0;
    }
    .login-sub {
        font-size: 14px;
        color: #9c958d !important;
        margin: 0 0 28px 0;
    }
    .role-hint { display: flex; gap: 8px; margin-top: 16px; justify-content: center; flex-wrap: wrap; }
    .role-pill {
        background: #f4f1ed;
        border: 1px solid #ece9e3;
        border-radius: 6px; padding: 5px 12px;
        font-size: 12px; font-weight: 500;
        color: #6b6560 !important;
        font-family: 'DM Mono', monospace;
    }

    /* ── Divider ── */
    hr { border: none; border-top: 1px solid #ece9e3; }
    </style>
    """,
    unsafe_allow_html=True,
)


db_conn = get_db_connection()
db_service = SQLiteService(db_conn)

# -----------------------------------------------------------------------
# Authentication Gate
# -----------------------------------------------------------------------
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
    st.session_state["role"] = None

if not st.session_state["logged_in"]:
    # Hide sidebar on login page
    st.markdown("<style>[data-testid='stSidebar']{display:none}</style>", unsafe_allow_html=True)
    
    _, mid, _ = st.columns([1, 1.2, 1])
    with mid:
        st.markdown("""
        <div class="login-card">
            <span class="login-logo">🏠</span>
            <p class="login-title">HostelCare</p>
            <p class="login-sub">Hostel Complaint Management Portal</p>
        </div>
        """, unsafe_allow_html=True)
        
        with st.container(border=False):
            st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
            username = st.text_input("Username", placeholder="Enter your username", key="login_username")
            password = st.text_input("Password", type="password", placeholder="Enter your password", key="login_password")
            st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
            
            if st.button("Continue", type="primary", use_container_width=True):
                u = username.strip().lower()
                p = password.strip()
                if u == "admin" and p == "password":
                    st.session_state["logged_in"] = True
                    st.session_state["role"] = "admin"
                    st.toast("Welcome back, Admin! 👑", icon="✅")
                    st.rerun()
                elif u == "student" and p == "password":
                    st.session_state["logged_in"] = True
                    st.session_state["role"] = "student"
                    st.toast("Welcome! 🎓", icon="✅")
                    st.rerun()
                else:
                    st.error(f"Invalid credentials. Use **admin/password** or **student/password**")
            
            st.markdown("""
            <div style='margin-top:18px; text-align:center;'>
                <p style='font-size:12px; color:#9c958d; margin-bottom:8px;'>Demo accounts</p>
                <div class='role-hint'>
                    <span class='role-pill'>admin / password</span>
                    <span class='role-pill'>student / password</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    st.stop()


def load_complaints():
    """Fetches fresh complaint data from SQLite."""
    if not db_service.is_connected():
        return None, "⚠️ Unable to connect to the database."
    success, result = db_service.get_all_complaints()
    if not success:
        return None, f"⚠️ {result}"
    return result, None


def render_status_badge(status: str) -> str:
    color = STATUS_BADGE_COLORS.get(status, "#64748B")
    icon = STATUS_ICONS.get(status, "")
    return f'<span class="status-badge" style="background-color:{color};">{icon} {status}</span>'


# -----------------------------------------------------------------------
# Sidebar navigation
# -----------------------------------------------------------------------
with st.sidebar:
    st.markdown("""
    <div style='padding: 24px 4px 20px 4px;'>
        <div style='font-size: 13px; font-weight: 600; color: #9c958d; letter-spacing: 0.12em; text-transform: uppercase; margin-bottom: 4px;'>HostelCare</div>
        <div style='font-family: Playfair Display, serif; font-size: 20px; font-weight: 700; color: #1a1714;'>Complaint Portal</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Admin sees Dashboard, All Complaints, Admin Panel, About
    # Student sees Dashboard, Submit Complaint, All Complaints, About
    if st.session_state["role"] == "admin":
        nav_options = ["🏠  Dashboard", "📋  All Complaints", "🔧  Admin Panel", "ℹ️  About"]
    else:
        nav_options = ["🏠  Dashboard", "📝  Submit Complaint", "📋  All Complaints", "ℹ️  About"]
    
    page = st.radio(
        "Navigate",
        options=nav_options,
        label_visibility="collapsed",
    )
    
    st.divider()
    
    role_icon = "👑" if st.session_state["role"] == "admin" else "🎓"
    role_label = st.session_state["role"].capitalize()
    st.markdown(f"""
    <div style='padding: 10px 12px; background: #f4f1ed; border-radius: 8px; border: 1px solid #ece9e3;'>
        <div style='font-size: 11px; color: #9c958d; margin-bottom: 2px; font-weight: 500; text-transform: uppercase; letter-spacing: 0.08em;'>Signed in as</div>
        <div style='font-size: 14px; font-weight: 600; color: #1a1714;'>{role_icon} {role_label}</div>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("Sign out", use_container_width=True):
        st.session_state["logged_in"] = False
        st.session_state["role"] = None
        st.rerun()

if not db_service.is_connected():
    st.sidebar.warning("Database not connected.")

# =========================================================================
# DASHBOARD
# =========================================================================
if page == "🏠  Dashboard":
    st.markdown("<h1>Dashboard</h1>", unsafe_allow_html=True)
    st.caption("Live overview of all complaints in the system.")
    st.divider()

    complaints, error = load_complaints()

    if error:
        st.error(error)
    else:
        stats = get_dashboard_stats(complaints)

        col1, col2, col3, col4 = st.columns(4)
        kpi_cells = [
            (col1, "Total", stats["total"], "📋"),
            (col2, "Pending", stats["Pending"], "⏳"),
            (col3, "Approved", stats.get("Approved", 0), "✅"),
            (col4, "Resolved", stats["Resolved"], "🎉"),
        ]
        for col, label, value, icon in kpi_cells:
            with col:
                st.markdown(
                    f"""
                    <div class="kpi-card">
                        <span class="kpi-icon">{icon}</span>
                        <p class="kpi-label">{label}</p>
                        <p class="kpi-value">{value}</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        st.markdown("<div style='margin: 16px 0 8px 0'></div>", unsafe_allow_html=True)
        if complaints:
            dash_col1, dash_col2 = st.columns([3, 2])
            with dash_col1:
                st.subheader("Most Recent Complaints")
                recent = complaints[:5]
                for c in recent:
                    with st.container(border=True):
                        left, right = st.columns([4, 1])
                        with left:
                            st.markdown(f"**{c.get('complaint_id')}** — Room {c.get('room_number')} · {c.get('category')}")
                            st.caption(c.get("description", "")[:120])
                        with right:
                            st.markdown(render_status_badge(c.get("status", "")), unsafe_allow_html=True)
            
            with dash_col2:
                st.subheader("Complaints by Category")
                df_cat = pd.DataFrame(complaints)
                if not df_cat.empty:
                    chart = alt.Chart(df_cat).mark_arc(innerRadius=50).encode(
                        theta=alt.Theta("count()", type="quantitative"),
                        color=alt.Color("category:N", legend=alt.Legend(title="Category", orient="bottom")),
                        tooltip=["category:N", "count()"]
                    ).properties(height=350)
                    st.altair_chart(chart, use_container_width=True)
        else:
            st.info("No complaints have been submitted yet.")

# =========================================================================
# SUBMIT COMPLAINT
# =========================================================================
elif page == "📝  Submit Complaint":
    st.markdown("<h1>Submit a Complaint</h1>", unsafe_allow_html=True)
    st.caption("Describe your issue below. Our team will review it promptly.")
    st.divider()

    with st.form("complaint_form", clear_on_submit=True):
        room_number = st.text_input("Room Number", placeholder="e.g. 201")
        col_cat, col_empty = st.columns([1, 1])
        with col_cat:
            category = st.selectbox("Category", options=CATEGORY_OPTIONS)
        description = st.text_area(
            "Description",
            placeholder="Describe the issue in detail — the more specific, the faster we can act.",
            max_chars=500,
            height=120,
        )
        submitted = st.form_submit_button("Submit", type="primary")

    if submitted:
        # Duplicate-submission guard: block only rapid repeats of the exact
        # same complaint within a short cooldown window.
        last = st.session_state.get("last_submission")
        fingerprint = (room_number.strip(), category, description.strip())
        now = time.time()

        is_duplicate = (
            last is not None
            and last["fingerprint"] == fingerprint
            and (now - last["time"]) < DUPLICATE_SUBMISSION_COOLDOWN_SECONDS
        )

        if is_duplicate:
            st.warning("This complaint was just submitted. Please wait a moment before resubmitting.")
        elif not db_service.is_connected():
            st.error("⚠️ Unable to connect to the database.")
        else:
            success, payload = submit_complaint(db_service, room_number, category, description)

            if not success:
                for err in payload:
                    st.error(err)
            else:
                st.session_state["last_submission"] = {"fingerprint": fingerprint, "time": now}
                st.toast("Complaint submitted!", icon="✅")
                st.success(f"✓ Submitted — Complaint ID: **{payload['complaint_id']}** · Status: {payload['status']}")

# =========================================================================
# COMPLAINTS LIST
# =========================================================================
elif page == "📋  All Complaints":
    st.markdown("<h1>All Complaints</h1>", unsafe_allow_html=True)
    st.divider()

    complaints, error = load_complaints()

    if error:
        st.error(error)
    else:
        filter_col1, filter_col2, filter_col3 = st.columns([1, 1, 2])
        with filter_col1:
            category_filter = st.selectbox("Category", options=CATEGORY_FILTER_OPTIONS)
        with filter_col2:
            status_filter = st.selectbox("Status", options=STATUS_FILTER_OPTIONS)
        with filter_col3:
            search_query = st.text_input("Search by Complaint ID or Room Number", placeholder="e.g. CMP-1024 or 201")

        filtered = filter_complaints(complaints, category_filter, status_filter)
        filtered = search_complaints(filtered, search_query)

        st.caption(f"Showing {len(filtered)} of {len(complaints)} complaints.")

        if not filtered:
            st.info("No complaints match the selected filters.")
        else:
            df = pd.DataFrame(filtered)
            df['created_at'] = df['created_at'].apply(format_timestamp)
            
            # Select and reorder
            df = df[['complaint_id', 'room_number', 'category', 'status', 'description', 'created_at']]
            
            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "complaint_id": st.column_config.TextColumn("ID", width="small"),
                    "room_number": st.column_config.TextColumn("Room", width="small"),
                    "category": st.column_config.TextColumn("Category", width="medium"),
                    "status": st.column_config.TextColumn("Status", width="small"),
                    "description": st.column_config.TextColumn("Description", width="large"),
                    "created_at": st.column_config.TextColumn("Timestamp", width="medium"),
                }
            )

# =========================================================================
# ADMIN PANEL
# =========================================================================
elif page == "🔧  Admin Panel":
    # Hard role guard — defensive in case nav labels ever drift
    if st.session_state.get("role") != "admin":
        st.error("🚫 Access denied. This page is for administrators only.")
        st.stop()

    st.markdown("<h1>Admin Panel</h1>", unsafe_allow_html=True)
    st.caption("Review and update the status of complaints.")
    st.divider()

    complaints, error = load_complaints()

    if error:
        st.error(error)
    elif not complaints:
        st.info("No complaints to manage yet.")
    else:
        admin_col1, admin_col2 = st.columns([1, 1])
        with admin_col1:
            admin_category_filter = st.selectbox("Filter by Category", options=CATEGORY_FILTER_OPTIONS, key="admin_cat")
        with admin_col2:
            admin_status_filter = st.selectbox("Filter by Status", options=STATUS_FILTER_OPTIONS, key="admin_status")

        visible = filter_complaints(complaints, admin_category_filter, admin_status_filter)

        if not visible:
            st.info("No complaints match the selected filters.")
        else:
            options = {
                f"{c['complaint_id']} — Room {c['room_number']} · {c['category']} · {c['status']}": c
                for c in visible
            }
            selected_label = st.selectbox("Select Complaint", options=list(options.keys()))
            selected_complaint = options[selected_label]

            with st.container(border=True):
                c1, c2 = st.columns([1, 1])
                with c1:
                    st.markdown(f"**ID:** {selected_complaint['complaint_id']}")
                    st.markdown(f"**Room:** {selected_complaint['room_number']}")
                    st.markdown(f"**Category:** {selected_complaint['category']}")
                with c2:
                    st.markdown(f"**Status:** {render_status_badge(selected_complaint['status'])}", unsafe_allow_html=True)
                    st.markdown(f"**Submitted:** {format_timestamp(selected_complaint.get('created_at'))}")
                st.markdown(f"**Description:** {selected_complaint['description']}")

            new_status = st.selectbox(
                "Update Status To",
                options=STATUS_OPTIONS,
                index=STATUS_OPTIONS.index(selected_complaint["status"])
                if selected_complaint["status"] in STATUS_OPTIONS
                else 0,
            )

            if st.button("Update Status", type="primary"):
                success, payload = update_status(
                    db_service, selected_complaint["complaint_id"], new_status
                )
                if not success:
                    st.error(f"⚠️ {payload}")
                else:
                    st.toast("Status updated!", icon="✅")
                    st.rerun()

# =========================================================================
# ABOUT
# =========================================================================
else:
    st.markdown("<h1>About HostelCare</h1>", unsafe_allow_html=True)
    st.divider()
    st.markdown(
        """
        **HostelCare** is a hostel maintenance complaint registration portal
        built for **Web Warfare 2K26 — Round 2, Problem Statement 3**.

        **Core features**
        - Students submit complaints with room number, category, and description.
        - Every complaint is timestamped and assigned a unique, immutable ID.
        - Complaints can be filtered by category and status, and searched by ID or room number.
        - Admins review complaints and update their status: **Pending → Approved → Resolved**.

        **Technology stack**
        - [Streamlit](https://streamlit.io) — UI framework
        - [SQLite](https://sqlite.org) — local relational database
        - [Altair](https://altair-viz.github.io) — dashboard charts
        - [DM Sans + Playfair Display](https://fonts.google.com) — typography

        *This application does not call any third-party AI service at runtime.*
        """
    )
