"""
HostelCare — Hostel Complaint Registration Portal
Web Warfare 2K26 — Round 2 — Problem Statement 3

Built with Streamlit + Firebase (Firestore). No third-party AI APIs are
called by this application at runtime — it is a standard CRUD portal.
"""

import time

import streamlit as st

from config.firebase_config import get_firestore_client
from services.complaint_service import (
    filter_complaints,
    get_dashboard_stats,
    search_complaints,
    submit_complaint,
    update_status,
)
from services.firebase_service import FirebaseService
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
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

    .kpi-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 18px 20px;
        text-align: left;
    }
    .kpi-value { font-size: 32px; font-weight: 700; color: #0F172A; margin: 0; }
    .kpi-label { font-size: 13px; font-weight: 600; color: #64748B; text-transform: uppercase;
                 letter-spacing: 0.04em; margin: 0 0 4px 0; }

    .status-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 999px;
        font-size: 13px;
        font-weight: 600;
        color: #FFFFFF;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------------------------------------------------------
# Firebase wiring (fault-tolerant)
# -----------------------------------------------------------------------
firestore_client = get_firestore_client()
firebase_service = FirebaseService(firestore_client)


def load_complaints():
    """Fetches fresh complaint data from Firestore. Fresh data is prioritized
    over caching per the reliability requirement — every page re-fetches on
    render rather than trusting a stale in-memory copy."""
    if not firebase_service.is_connected():
        return None, "⚠️ Unable to connect to the database. Please check your Firebase configuration."

    success, result = firebase_service.get_all_complaints()
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
st.sidebar.title("🏠 HostelCare")
st.sidebar.caption("Hostel Complaint Registration Portal")

page = st.sidebar.radio(
    "Navigate",
    options=["🏠 Dashboard", "📝 Submit Complaint", "📋 Complaints", "🔧 Admin Panel", "ℹ️ About"],
    label_visibility="collapsed",
)

if not firebase_service.is_connected():
    st.sidebar.warning("Database not connected. Add Firebase credentials to Streamlit secrets.")

# =========================================================================
# DASHBOARD
# =========================================================================
if page == "🏠 Dashboard":
    st.title("Dashboard")
    st.caption("A live overview of every complaint currently in the system.")

    complaints, error = load_complaints()

    if error:
        st.error(error)
    else:
        stats = get_dashboard_stats(complaints)

        col1, col2, col3, col4 = st.columns(4)
        kpi_cells = [
            (col1, "Total", stats["total"]),
            (col2, "Pending", stats["Pending"]),
            (col3, "In Progress", stats["In Progress"]),
            (col4, "Resolved", stats["Resolved"]),
        ]
        for col, label, value in kpi_cells:
            with col:
                st.markdown(
                    f"""
                    <div class="kpi-card">
                        <p class="kpi-label">{label}</p>
                        <p class="kpi-value">{value}</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        st.write("")
        if complaints:
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
        else:
            st.info("No complaints have been submitted yet.")

# =========================================================================
# SUBMIT COMPLAINT
# =========================================================================
elif page == "📝 Submit Complaint":
    st.title("Submit a Complaint")
    st.caption("Fill in the details below. All fields are required.")

    with st.form("complaint_form", clear_on_submit=True):
        room_number = st.text_input("Room Number", placeholder="e.g. 201")
        category = st.selectbox("Complaint Category", options=CATEGORY_OPTIONS)
        description = st.text_area(
            "Complaint Description",
            placeholder="Describe the issue in detail...",
            max_chars=500,
            height=140,
        )
        submitted = st.form_submit_button("Submit Complaint", type="primary")

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
        elif not firebase_service.is_connected():
            st.error("⚠️ Unable to connect to the database. Please check your Firebase configuration.")
        else:
            success, payload = submit_complaint(firebase_service, room_number, category, description)

            if not success:
                for err in payload:
                    st.error(err)
            else:
                st.session_state["last_submission"] = {"fingerprint": fingerprint, "time": now}
                st.success("✅ Complaint submitted successfully!")
                st.markdown(
                    f"""
                    **Complaint ID:** {payload['complaint_id']}
                    **Status:** {payload['status']}
                    **Submitted:** {format_timestamp(payload['created_at'])}
                    """
                )

# =========================================================================
# COMPLAINTS LIST
# =========================================================================
elif page == "📋 Complaints":
    st.title("All Complaints")

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
            header = st.columns([1.3, 0.8, 1.2, 3, 1.3, 1.7])
            for col, label in zip(header, ["ID", "Room", "Category", "Description", "Status", "Timestamp"]):
                col.markdown(f"**{label}**")

            for c in filtered:
                row = st.columns([1.3, 0.8, 1.2, 3, 1.3, 1.7])
                row[0].write(c.get("complaint_id", ""))
                row[1].write(c.get("room_number", ""))
                row[2].write(c.get("category", ""))
                row[3].write(c.get("description", ""))
                row[4].markdown(render_status_badge(c.get("status", "")), unsafe_allow_html=True)
                row[5].write(format_timestamp(c.get("created_at")))

# =========================================================================
# ADMIN PANEL
# =========================================================================
elif page == "🔧 Admin Panel":
    st.title("Admin Panel")
    st.caption("Update the status of an individual complaint. Updates affect only the selected complaint.")

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

            st.write("")
            with st.container(border=True):
                st.markdown(f"**Complaint ID:** {selected_complaint['complaint_id']}")
                st.markdown(f"**Room:** {selected_complaint['room_number']}")
                st.markdown(f"**Category:** {selected_complaint['category']}")
                st.markdown(f"**Description:** {selected_complaint['description']}")
                st.markdown(f"**Current Status:** {render_status_badge(selected_complaint['status'])}", unsafe_allow_html=True)
                st.markdown(f"**Submitted:** {format_timestamp(selected_complaint.get('created_at'))}")

            new_status = st.selectbox(
                "Update Status To",
                options=STATUS_OPTIONS,
                index=STATUS_OPTIONS.index(selected_complaint["status"])
                if selected_complaint["status"] in STATUS_OPTIONS
                else 0,
            )

            if st.button("Update Status", type="primary"):
                success, payload = update_status(
                    firebase_service, selected_complaint["complaint_id"], new_status
                )
                if not success:
                    st.error(f"⚠️ {payload}")
                else:
                    st.success("✅ Status updated successfully.")
                    st.rerun()

# =========================================================================
# ABOUT
# =========================================================================
else:
    st.title("About HostelCare")
    st.markdown(
        """
        HostelCare is a hostel maintenance complaint registration portal
        built for **Web Warfare 2K26 — Round 2, Problem Statement 3**.

        **Core features**
        - Students submit complaints with room number, category, and description.
        - Every complaint is timestamped and assigned a unique, immutable ID by Firestore.
        - Complaints can be filtered by category and status (individually or combined),
          and searched by ID or room number.
        - Admins move complaints through **Pending → In Progress → Resolved**,
          with updates scoped to exactly one complaint.

        **Technology stack**
        - Streamlit (UI)
        - Firebase Firestore (database)
        - Google Fonts (Inter)

        This application does not call any third-party AI service at runtime.
        """
    )
