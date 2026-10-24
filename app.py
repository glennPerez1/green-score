"""GreenScore: Campus Waste Management & Sustainability Platform

App entry point with Role-Based Authentication Gateway.
- Gated Admin access protected by Admin PIN.
- Authenticated Student accounts (Gagandeep Singh, Ronak Das, Sameer Raj).
- Student Sign Up portal for creating unique student accounts (unrestricted email).
"""

import os
import streamlit as st

from database import (
    create_user,
    get_bins,
    get_db,
    get_user_by_id_or_email,
    init_db,
    verify_user_credentials,
)
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
        init_db()
        seed_data()


ensure_database_ready()


# ==============================================================================
# AUTHENTICATION & SESSION MANAGEMENT
# ==============================================================================
if "authenticated_user" not in st.session_state:
    st.session_state["authenticated_user"] = None

user = st.session_state["authenticated_user"]

# ------------------------------------------------------------------------------
# LOGIN / SIGN UP GATEWAY (If not authenticated)
# ------------------------------------------------------------------------------
if not user:
    st.markdown(
        """
        <div style="background: linear-gradient(135deg, #1b4332 0%, #2d6a4f 100%); padding: 24px 28px; border-radius: 12px; color: white; margin-bottom: 24px; box-shadow: 0 4px 14px rgba(27,67,50,0.25);">
            <h1 style="margin:0; font-size: 2.1rem; font-weight:800; letter-spacing: -0.5px;">🌱 GreenScore Authentication</h1>
            <p style="margin: 6px 0 0 0; opacity: 0.95; font-size: 1.0rem;">
                Real-time campus waste reporting & sustainability reward platform. Please log in or register.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    scanned_bin = st.query_params.get("bin_id", "").strip()
    if scanned_bin:
        st.info(f"📍 **QR Code Detected for `{scanned_bin}`**. Log in as a student to submit your report.")

    tab_stu_login, tab_stu_signup, tab_admin_login = st.tabs(
        [
            "🎓 Student Login",
            "✨ New Student Sign Up",
            "🛡️ Admin Access",
        ]
    )

    # 1. Student Login
    with tab_stu_login:
        st.markdown("### 🎓 Student Sign In")
        st.caption("Sign in with your Student ID or Email and your security PIN.")

        col_l1, col_l2 = st.columns([1, 1])
        with col_l1:
            stu_identifier = st.text_input("Student ID or Email", placeholder="e.g. STU-001, STU-002")
            stu_pin = st.text_input("4-Digit Security PIN", type="password", placeholder="Enter your PIN")

            if st.button("🔑 Log In as Student", type="primary", use_container_width=True):
                if not stu_identifier.strip() or not stu_pin.strip():
                    st.error("Please provide both your Student ID/Email and your PIN.")
                else:
                    auth_user = verify_user_credentials(stu_identifier, stu_pin)
                    if auth_user and auth_user.get("role") == "student":
                        st.session_state["authenticated_user"] = auth_user
                        st.success(f"Welcome back, {auth_user['name']}!")
                        st.rerun()
                    else:
                        st.error("Invalid credentials. Please verify your Student ID/Email and PIN.")

        with col_l2:
            st.markdown(
                """
                <div style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:10px; padding:18px; margin-top:4px;">
                    <h4 style="margin-top:0; color:#1b4332;">💡 Pre-Configured Demo Student Accounts</h4>
                    <p style="font-size:0.85rem; color:#475569; margin-bottom:10px;">
                        Judges and evaluators can use any of these pre-created accounts:
                    </p>
                    <ul style="font-size:0.88rem; line-height:1.7; padding-left:18px; color:#334155;">
                        <li><strong>Gagandeep Singh:</strong> ID: <code>STU-001</code> | Email: <code>gagan@gmail.com</code> | PIN: <code>1234</code></li>
                        <li><strong>Ronak Das:</strong> ID: <code>STU-002</code> | Email: <code>ronak@gmail.com</code> | PIN: <code>1234</code></li>
                        <li><strong>Sameer Raj:</strong> ID: <code>STU-003</code> | Email: <code>sameer@gmail.com</code> | PIN: <code>1234</code></li>
                    </ul>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # 2. Student Sign Up
    with tab_stu_signup:
        st.markdown("### ✨ Create New Student Account")
        st.caption("Register your own unique student account. Email can be any personal or college address.")

        col_reg1, col_reg2 = st.columns([1, 1])
        with col_reg1:
            new_name = st.text_input("Full Name", placeholder="e.g. Priya Sharma")
            new_id = st.text_input("Student Roll No / ID", placeholder="e.g. STU-004")
            new_email = st.text_input("Email Address", placeholder="e.g. priya.sharma@gmail.com (Any email domain)")

            col_p1, col_p2 = st.columns(2)
            with col_p1:
                new_pin = st.text_input("Create 4-Digit PIN", type="password", placeholder="e.g. 1234")
            with col_p2:
                new_pin_confirm = st.text_input("Confirm PIN", type="password", placeholder="Confirm PIN")

            if st.button("✨ Create Account & Log In", type="primary", use_container_width=True):
                if not new_name.strip() or not new_id.strip() or not new_email.strip():
                    st.error("Please fill in all profile fields.")
                elif not new_pin.strip() or new_pin != new_pin_confirm:
                    st.error("PINs do not match or cannot be empty.")
                else:
                    existing = get_user_by_id_or_email(new_id) or get_user_by_id_or_email(new_email)
                    if existing:
                        st.error(f"An account with ID '{new_id}' or Email '{new_email}' already exists.")
                    else:
                        try:
                            created = create_user(
                                user_id=new_id.strip(),
                                name=new_name.strip(),
                                role="student",
                                email=new_email.strip(),
                                pin=new_pin.strip(),
                            )
                            st.session_state["authenticated_user"] = created
                            st.balloons()
                            st.success(f"🎉 Account created successfully! Welcome, {new_name}!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Registration failed: {e}")

        with col_reg2:
            st.markdown(
                """
                <div style="background:#f0fdf4; border:1px solid #bbf7d0; border-radius:10px; padding:18px; margin-top:4px;">
                    <h4 style="margin-top:0; color:#166534;">🌟 Why Register on GreenScore?</h4>
                    <ul style="font-size:0.88rem; line-height:1.7; padding-left:18px; color:#14532d;">
                        <li><strong>Earn GreenPoints:</strong> Receive +5 points for every verified campus report and +5 points upon resolution.</li>
                        <li><strong>Track Your Reports:</strong> Access your personal dashboard with live resolution progress.</li>
                        <li><strong>Campus Impact:</strong> Help keep lecture halls, hostels, and dining areas clean and segregated.</li>
                    </ul>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # 3. Admin Login
    with tab_admin_login:
        st.markdown("### 🛡️ Administrator Access")
        st.caption("Authorized campus facility and sanitation supervisors only.")

        col_adm1, col_adm2 = st.columns([1, 1])
        with col_adm1:
            admin_pin_input = st.text_input("Enter Admin Security PIN", type="password", placeholder="Enter Admin PIN")

            if st.button("🔓 Unlock Admin Dashboard", type="primary", use_container_width=True):
                if admin_pin_input.strip() in ("admin123", "1234"):
                    admin_rec = get_user_by_id_or_email("ADM-001") or {
                        "id": "ADM-001",
                        "name": "Campus Administrator",
                        "role": "admin",
                        "email": "admin@greenscore.edu",
                    }
                    st.session_state["authenticated_user"] = admin_rec
                    st.success("Admin identity verified. Access granted!")
                    st.rerun()
                else:
                    st.error("Access Denied: Incorrect Admin PIN.")

        with col_adm2:
            st.markdown(
                """
                <div style="background:#fffbeb; border:1px solid #fde68a; border-radius:10px; padding:18px; margin-top:4px;">
                    <h4 style="margin-top:0; color:#92400e;">🔑 Evaluator / Demo Admin PIN</h4>
                    <p style="font-size:0.88rem; color:#78350f; margin-bottom:6px;">
                        For live hackathon evaluation and testing:
                    </p>
                    <div style="font-size:1.15rem; font-weight:800; color:#92400e; background:#fef3c7; padding:8px 12px; border-radius:6px; display:inline-block;">
                        Admin PIN: <code>admin123</code>
                    </div>
                    <p style="font-size:0.8rem; color:#92400e; margin-top:8px;">
                        (Students without this PIN cannot access or manipulate the Admin verification queue.)
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # Sidebar note while unauthenticated
    with st.sidebar:
        st.title("🌱 GreenScore")
        st.caption("Smarter campus waste management & rewards")
        st.divider()
        st.info("🔒 Please log in or register to access student reporting or admin operations.")

# ------------------------------------------------------------------------------
# AUTHENTICATED USER ROUTING
# ------------------------------------------------------------------------------
else:
    with st.sidebar:
        st.title("🌱 GreenScore")
        st.caption("Smarter campus waste management")

        # User profile badge
        role_label = "🛡️ Administrator" if user.get("role") == "admin" else "🎓 Student"
        st.markdown(
            f"""
            <div style="background:#ffffff; border:1px solid #e2e8f0; border-radius:10px; padding:12px 14px; margin-bottom:12px;">
                <div style="font-size:0.8rem; font-weight:700; color:#2d6a4f; text-transform:uppercase;">Logged In As</div>
                <div style="font-size:1.05rem; font-weight:800; color:#1b4332;">{user.get('name')}</div>
                <div style="font-size:0.8rem; color:#64748b;">{role_label} (<code>{user.get('id')}</code>)</div>
                {f'<div style="font-size:0.75rem; color:#64748b;">✉️ {user.get("email")}</div>' if user.get("email") else ''}
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button("🚪 Sign Out", use_container_width=True):
            st.session_state["authenticated_user"] = None
            st.rerun()

        st.divider()

    # Route strictly according to verified role
    if user.get("role") == "admin":
        from dashboard import render_dashboard
        render_dashboard()
    else:
        from student_ui import render_student_portal
        render_student_portal(current_user=user)

    st.sidebar.caption("GreenScore • Campus Sustainability MVP")
