"""
GreenScore: Campus Waste Management & Sustainability Platform
Owned by Person 3 (me: Application, Admin Dashboard, Integration, and Deployment)

App entry point connecting Student UI, Administrator Dashboard, and QR scanning workflows.
"""

import os
import streamlit as st

from database import init_db, get_bins, get_db
from seed_data import seed_data

# ==============================================================================
# STREAMLIT PAGE CONFIGURATION
# ==============================================================================
st.set_page_config(
    page_title="GreenScore — Campus Waste Management",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ==============================================================================
# AUTOMATIC DATABASE INITIALIZATION & RESILIENCE
# ==============================================================================
def ensure_database_ready():
    """Ensure database tables and initial seed data exist upon app launch."""
    try:
        bins = get_bins(active_only=False)
        if not bins:
            seed_data()
    except Exception:
        # If table does not exist or first boot on Render / local
        init_db()
        seed_data()

    # Ensure all demo students from student_ui roster exist in the users table
    try:
        with get_db() as conn:
            conn.execute("""
                INSERT OR IGNORE INTO users (id, name, role)
                VALUES ('STU-003', 'Rohan Verma', 'student')
            """)
    except Exception:
        pass


ensure_database_ready()


# ==============================================================================
# ROUTING & ROLE MANAGEMENT
# ==============================================================================
# Auto-detect QR scan parameter (?bin_id=...)
# If a student scans a bin QR code, default directly to the Student interface
scanned_bin = st.query_params.get("bin_id", "").strip()
default_role_index = 1 if scanned_bin else 0

st.sidebar.title("🌱 GreenScore")
st.sidebar.caption("Smarter campus waste management & GreenPoints")

role = st.sidebar.radio(
    "Active Interface Role",
    ["Admin Operations", "Student Experience"],
    index=default_role_index,
    help="Switch between Administrator oversight and Student reporting.",
)

# Route to corresponding sub-application
if role == "Admin Operations":
    from dashboard import render_dashboard
    render_dashboard()
else:
    from student_ui import render_student_ui
    render_student_ui()

# Sidebar Footer
st.sidebar.divider()
st.sidebar.caption("GreenScore • Campus Sustainability Hackathon MVP")
st.sidebar.caption("Tech: Python 3.12 | Streamlit | SQLite | Plotly")
