"""Student Experience and QR Integration Portal for GreenScore.

Person 1: Student Experience & QR integration.
Exports `render_student_portal()` (and alias `render_student_ui`) for Person 3's app.py.
Resilient fallback provided when backend modules are not yet loaded.
Finalized with GreenPoints ledger, responsive styling, and QR demo triggers.
"""

import datetime
import os
from typing import Any, Dict, List, Optional
import pandas as pd
import streamlit as st

import qr_utils

# ==============================================================================
# BACKEND IMPORT WITH FAILSAFE MOCK FALLBACK (Shared Contract Person 2)
# ==============================================================================
try:
    # Backend modules are authored by Person 2 and will resolve once Person 2 merges.
    # type: ignore comments prevent IDE linters from showing red squiggles before Person 2 commits.
    from database import get_bins  # type: ignore
    from report_service import create_report, get_reports  # type: ignore
    from points import get_points_balance, get_points_ledger  # type: ignore
    from constants import (  # type: ignore
        ISSUE_TYPES,
        STATUS_SUBMITTED,
        STATUS_UNDER_REVIEW,
        STATUS_VERIFIED,
        STATUS_REJECTED,
        STATUS_RESOLVED,
        POINTS_FOR_VERIFICATION,
        POINTS_FOR_RESOLUTION,
    )
    BACKEND_AVAILABLE = True
except ImportError:
    BACKEND_AVAILABLE = False

    # Contract status values and rules
    STATUS_SUBMITTED = "Submitted"
    STATUS_UNDER_REVIEW = "Under Review"
    STATUS_VERIFIED = "Verified"
    STATUS_REJECTED = "Rejected"
    STATUS_RESOLVED = "Resolved"

    POINTS_FOR_VERIFICATION = 5
    POINTS_FOR_RESOLUTION = 5

    ISSUE_TYPES = [
        "Overflowing bin",
        "Incorrect segregation",
        "Damaged bin",
        "Missed collection",
        "Other waste issue",
    ]

    # Pre-seeded mock database records for standalone resilience
    INITIAL_MOCK_BINS = [
        {"id": "BIN-001", "location": "Library North Entrance", "waste_category": "Recyclables", "active": 1},
        {"id": "BIN-002", "location": "Student Activity Center (SAC) Courtyard", "waste_category": "Organic", "active": 1},
        {"id": "BIN-003", "location": "Hostel Block 4 Food Court", "waste_category": "General Waste", "active": 1},
        {"id": "BIN-004", "location": "Science & Tech Complex Hub", "waste_category": "E-Waste / Hazardous", "active": 1},
        {"id": "BIN-005", "location": "Sports Arena Pavilion", "waste_category": "Recyclables", "active": 1},
        {"id": "BIN-006", "location": "Main Administration Lawn", "waste_category": "Organic", "active": 1},
    ]

    INITIAL_MOCK_REPORTS = [
        {
            "id": "REP-2026-001",
            "user_id": "STU-001",
            "bin_id": "BIN-001",
            "issue_type": "Overflowing bin",
            "description": "Cardboard and plastic containers overflowing onto the pavement steps.",
            "status": STATUS_RESOLVED,
            "created_at": "2026-10-22 09:30:00",
            "reviewed_at": "2026-10-22 10:15:00",
            "resolved_at": "2026-10-22 12:45:00",
            "reviewer_id": "ADM-001",
            "admin_note": "Emptied and sanitized by campus sanitation crew.",
        },
        {
            "id": "REP-2026-002",
            "user_id": "STU-001",
            "bin_id": "BIN-002",
            "issue_type": "Incorrect segregation",
            "description": "Plastic beverage bottles dumped inside green organic compost container.",
            "status": STATUS_VERIFIED,
            "created_at": "2026-10-23 11:20:00",
            "reviewed_at": "2026-10-23 12:00:00",
            "resolved_at": None,
            "reviewer_id": "ADM-001",
            "admin_note": "Inspection confirmed. Re-sorting scheduled.",
        },
        {
            "id": "REP-2026-003",
            "user_id": "STU-002",
            "bin_id": "BIN-003",
            "issue_type": "Damaged bin",
            "description": "Foot pedal is broken and the lid remains jammed open, attracting birds.",
            "status": STATUS_UNDER_REVIEW,
            "created_at": "2026-10-23 15:40:00",
            "reviewed_at": None,
            "resolved_at": None,
            "reviewer_id": None,
            "admin_note": "",
        },
        {
            "id": "REP-2026-004",
            "user_id": "STU-001",
            "bin_id": "BIN-004",
            "issue_type": "Missed collection",
            "description": "Scheduled morning collection was missed; bin is almost full.",
            "status": STATUS_SUBMITTED,
            "created_at": "2026-10-24 08:50:00",
            "reviewed_at": None,
            "resolved_at": None,
            "reviewer_id": None,
            "admin_note": "",
        },
    ]

    INITIAL_MOCK_LEDGER = [
        {
            "id": "LEDG-001",
            "user_id": "STU-001",
            "report_id": "REP-2026-001",
            "action": "report_verified",
            "points": POINTS_FOR_VERIFICATION,
            "created_at": "2026-10-22 10:15:00",
        },
        {
            "id": "LEDG-002",
            "user_id": "STU-001",
            "report_id": "REP-2026-001",
            "action": "report_resolved",
            "points": POINTS_FOR_RESOLUTION,
            "created_at": "2026-10-22 12:45:00",
        },
        {
            "id": "LEDG-003",
            "user_id": "STU-001",
            "report_id": "REP-2026-002",
            "action": "report_verified",
            "points": POINTS_FOR_VERIFICATION,
            "created_at": "2026-10-23 12:00:00",
        },
        {
            "id": "LEDG-004",
            "user_id": "STU-002",
            "report_id": "REP-2026-003",
            "action": "report_verified",
            "points": POINTS_FOR_VERIFICATION,
            "created_at": "2026-10-23 16:30:00",
        },
    ]

    def _ensure_mock_state():
        if "mock_bins" not in st.session_state:
            st.session_state.mock_bins = list(INITIAL_MOCK_BINS)
        if "mock_reports" not in st.session_state:
            st.session_state.mock_reports = list(INITIAL_MOCK_REPORTS)
        if "mock_ledger" not in st.session_state:
            st.session_state.mock_ledger = list(INITIAL_MOCK_LEDGER)

    def get_bins(active_only: bool = True) -> List[Dict[str, Any]]:
        _ensure_mock_state()
        bins = st.session_state.mock_bins
        if active_only:
            return [b for b in bins if b.get("active", 1)]
        return bins

    def create_report(user_id: str, bin_id: str, issue_type: str, description: str) -> str:
        _ensure_mock_state()
        report_counter = len(st.session_state.mock_reports) + 1
        new_report_id = f"REP-2026-{report_counter:03d}"
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        new_report = {
            "id": new_report_id,
            "user_id": user_id,
            "bin_id": bin_id,
            "issue_type": issue_type,
            "description": description,
            "status": STATUS_SUBMITTED,
            "created_at": now_str,
            "reviewed_at": None,
            "resolved_at": None,
            "reviewer_id": None,
            "admin_note": "",
        }
        st.session_state.mock_reports.insert(0, new_report)
        return new_report_id

    def get_reports(user_id: Optional[str] = None, status: Optional[str] = None) -> List[Dict[str, Any]]:
        _ensure_mock_state()
        reports = st.session_state.mock_reports
        if user_id:
            reports = [r for r in reports if r.get("user_id") == user_id]
        if status:
            reports = [r for r in reports if r.get("status") == status]
        return reports

    def get_points_ledger(user_id: str) -> List[Dict[str, Any]]:
        _ensure_mock_state()
        ledger = st.session_state.mock_ledger
        return [entry for entry in ledger if entry.get("user_id") == user_id]

    def get_points_balance(user_id: str) -> int:
        ledger = get_points_ledger(user_id)
        return sum(entry.get("points", 0) for entry in ledger)


# ==============================================================================
# DEMO STUDENTS ROSTER
# ==============================================================================
DEMO_STUDENTS = {
    "STU-001": {
        "name": "Aarav Sharma",
        "department": "Computer Science & Engineering",
        "hall": "Ganga Bhawan",
        "badge": "Eco Champion 🌟",
    },
    "STU-002": {
        "name": "Priya Patel",
        "department": "Environmental Engineering",
        "hall": "Sarojini Bhawan",
        "badge": "Active Scout 🌿",
    },
    "STU-003": {
        "name": "Rohan Verma",
        "department": "Mechanical Engineering",
        "hall": "Govind Bhawan",
        "badge": "Green Contributor 🌱",
    },
}


# ==============================================================================
# CUSTOM STYLING (GreenScore Theme)
# ==============================================================================
def _inject_student_theme():
    """Inject modern, responsive CSS styling for the student portal."""
    st.markdown(
        """
        <style>
        /* Card Containers */
        .gs-card {
            background: linear-gradient(135deg, rgba(27, 67, 50, 0.04) 0%, rgba(45, 106, 79, 0.08) 100%);
            border: 1px solid rgba(45, 106, 79, 0.2);
            border-radius: 12px;
            padding: 18px 22px;
            margin-bottom: 16px;
        }
        .gs-banner {
            background: linear-gradient(90deg, #1b4332 0%, #2d6a4f 100%);
            color: #ffffff;
            border-radius: 10px;
            padding: 14px 20px;
            margin-bottom: 20px;
            box-shadow: 0 4px 12px rgba(27, 67, 50, 0.25);
        }
        .gs-metric-box {
            background: #ffffff;
            border-left: 5px solid #2d6a4f;
            border-radius: 8px;
            padding: 14px 18px;
            box-shadow: 0 2px 6px rgba(0,0,0,0.06);
            margin-bottom: 12px;
        }
        .gs-status-badge {
            display: inline-block;
            padding: 4px 10px;
            border-radius: 20px;
            font-size: 0.82rem;
            font-weight: 600;
        }
        .gs-status-submitted { background-color: #e9ecef; color: #495057; }
        .gs-status-under-review { background-color: #fff3cd; color: #856404; }
        .gs-status-verified { background-color: #d1e7dd; color: #0f5132; }
        .gs-status-resolved { background-color: #cfe2ff; color: #084298; }
        .gs-status-rejected { background-color: #f8d7da; color: #842029; }
        
        .gs-qr-card {
            border: 1px solid #d8f3dc;
            border-radius: 12px;
            padding: 14px;
            background: #ffffff;
            text-align: center;
            box-shadow: 0 2px 8px rgba(0,0,0,0.04);
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }
        .gs-qr-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 14px rgba(27, 67, 50, 0.15);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


# ==============================================================================
# MAIN EXPORT FUNCTION: render_student_portal
# ==============================================================================
def render_student_portal() -> None:
    """Render the complete student portal interface.

    Consumed by Person 3 in app.py or run standalone.
    """
    _inject_student_theme()

    # --------------------------------------------------------------------------
    # SIDEBAR: Student Account Switcher & Profile
    # --------------------------------------------------------------------------
    with st.sidebar:
        st.markdown("### 🎓 Student Profile")
        student_choices = [f"{uid}: {info['name']}" for uid, info in DEMO_STUDENTS.items()]
        selected_student_str = st.selectbox(
            "Active Student Account",
            student_choices,
            index=0,
            help="Simulate switching between different campus student reporters.",
        )
        active_user_id = selected_student_str.split(":")[0].strip()
        student_info = DEMO_STUDENTS[active_user_id]

        # Live balance for sidebar
        user_balance = get_points_balance(active_user_id)

        st.markdown(
            f"""
            <div class="gs-card">
                <div style="font-size:1.15rem; font-weight:700; color:#1b4332;">{student_info['name']}</div>
                <div style="font-size:0.85rem; color:#555;">ID: <code>{active_user_id}</code></div>
                <div style="font-size:0.82rem; color:#666; margin-top:4px;">🏛 {student_info['department']}</div>
                <div style="font-size:0.82rem; color:#666;">🏠 {student_info['hall']}</div>
                <hr style="margin: 8px 0; border: none; border-top: 1px solid #cce3de;" />
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <span style="font-size:0.85rem; font-weight:600; color:#2d6a4f;">GreenPoints</span>
                    <span style="font-size:1.25rem; font-weight:800; color:#1b4332;">{user_balance} 🌱</span>
                </div>
                <div style="margin-top:6px; font-size:0.8rem; font-weight:600; color:#40916c;">
                    {student_info['badge']}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if not BACKEND_AVAILABLE:
            st.info("ℹ️ Running in **Resilient Mock Mode** (Independent UI Preview).")
        else:
            st.success("⚡ Connected to **Live Backend**.")

    # --------------------------------------------------------------------------
    # URL QUERY PARAMETER DETECTION (?bin_id=...)
    # --------------------------------------------------------------------------
    # Streamlit 1.66.1 supports st.query_params
    query_params = st.query_params
    scanned_bin_id = query_params.get("bin_id", "").strip()

    # Load available bins
    all_bins = get_bins(active_only=True)
    if not all_bins:
        all_bins = INITIAL_MOCK_BINS

    matched_bin = next((b for b in all_bins if b["id"].upper() == scanned_bin_id.upper()), None)

    # --------------------------------------------------------------------------
    # HEADER BANNER & DETECTED QR BADGE
    # --------------------------------------------------------------------------
    st.markdown(
        """
        <div class="gs-banner">
            <h2 style="margin:0; font-weight:800; letter-spacing: -0.5px;">🌱 GreenScore Student Portal</h2>
            <p style="margin:4px 0 0 0; opacity:0.9; font-size:0.95rem;">
                Scan smart bin QR codes across campus, report waste issues instantly, and earn GreenPoints rewards.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if scanned_bin_id:
        col_badge, col_clear = st.columns([4, 1])
        with col_badge:
            if matched_bin:
                st.success(
                    f"📷 **QR Code Scanned & Verified:** Preselected **{matched_bin['id']}** — "
                    f"*{matched_bin['location']}* ({matched_bin.get('waste_category', 'General')})"
                )
            else:
                st.warning(
                    f"📷 **QR Code Detected:** `{scanned_bin_id}` (Not in registered bin database. "
                    "You may choose another bin below.)"
                )
        with col_clear:
            if st.button("✖ Clear Scan", use_container_width=True, help="Reset scanned QR parameter"):
                if "bin_id" in st.query_params:
                    del st.query_params["bin_id"]
                st.rerun()

    # --------------------------------------------------------------------------
    # NAVIGATION TABS
    # --------------------------------------------------------------------------
    tab1, tab2, tab3, tab4 = st.tabs(
        [
            "📢 Report Waste Issue",
            "📋 My Reports",
            "🌱 GreenPoints & Ledger",
            "📱 Demo QR Bins",
        ]
    )

    # ==========================================================================
    # TAB 1: REPORT WASTE ISSUE
    # ==========================================================================
    with tab1:
        st.markdown("### 📝 Submit a Waste Issue Report")
        st.markdown(
            "Help keep our campus clean and sustainable. Reports verified and resolved by campus teams earn GreenPoints!"
        )

        with st.container():
            # Bin selection dropdown
            bin_options = [
                f"{b['id']} — {b['location']} [{b.get('waste_category', 'Standard')}]"
                for b in all_bins
            ]
            
            # Compute preselection index if scanned
            default_bin_index = 0
            if matched_bin:
                for idx, b in enumerate(all_bins):
                    if b["id"].upper() == matched_bin["id"].upper():
                        default_bin_index = idx
                        break

            col_form_left, col_form_right = st.columns([1, 1])
            with col_form_left:
                selected_bin_str = st.selectbox(
                    "Select Campus Waste Bin",
                    bin_options,
                    index=default_bin_index,
                    help="Bins marked with QR tags across campus buildings and grounds.",
                )
                selected_bin_id = all_bins[bin_options.index(selected_bin_str)]["id"]
                selected_bin_obj = next(b for b in all_bins if b["id"] == selected_bin_id)

            with col_form_right:
                selected_issue_type = st.selectbox(
                    "Issue Category",
                    ISSUE_TYPES,
                    index=0,
                    help="Select the issue type matching the bin condition.",
                )

            # Live check for existing active report for same bin + same issue type
            existing_all = get_reports()
            active_duplicate = next(
                (
                    r for r in existing_all
                    if r.get("bin_id") == selected_bin_id
                    and r.get("issue_type") == selected_issue_type
                    and r.get("status") not in (STATUS_RESOLVED, STATUS_REJECTED)
                ),
                None,
            )

            if active_duplicate:
                st.warning(
                    f"🔒 **Duplicate Guard Active**: Report `#{active_duplicate.get('id')}` for **{selected_issue_type}** "
                    f"at `{selected_bin_id}` is already in progress (Status: **{active_duplicate.get('status')}**).\n\n"
                    f"To prevent duplicate reports, submissions for this issue are locked until the issue is marked as **Resolved**."
                )

            # Details & description
            st.markdown(
                f"**Target Bin Details:** `{selected_bin_obj['id']}` located at "
                f"**{selected_bin_obj['location']}** (Category: *{selected_bin_obj.get('waste_category', 'General')}*)"
            )

            description_input = st.text_area(
                "Describe the Waste Issue (Required)",
                placeholder="e.g. Bin is completely overflowing, bags stacked on ground, lid hinge damaged...",
                help="Provide clear, non-empty context for the sanitation and maintenance crew.",
                height=120,
            )

            # Optional photo proof uploader
            col_photo, col_preview = st.columns([1, 1])
            with col_photo:
                uploaded_photo = st.file_uploader(
                    "📷 Attach Photo Proof (Optional)",
                    type=["png", "jpg", "jpeg"],
                    help="Upload a photo of the bin issue to help maintenance verify and resolve faster.",
                )
            with col_preview:
                if uploaded_photo:
                    st.image(uploaded_photo, caption="📸 Attached Proof Preview", width=220)

            # Verification checkpoint info
            st.caption("🔒 Verified reports earn **+5 GreenPoints**; resolved reports earn an additional **+5 GreenPoints**.")

            submit_disabled = active_duplicate is not None
            if st.button("🚀 Submit Waste Report", type="primary", use_container_width=True, disabled=submit_disabled):
                cleaned_desc = description_input.strip()
                if not cleaned_desc:
                    st.error("⚠️ Validation Error: Description cannot be empty. Please provide specific details.")
                else:
                    try:
                        new_rep_id = create_report(
                            user_id=active_user_id,
                            bin_id=selected_bin_id,
                            issue_type=selected_issue_type,
                            description=cleaned_desc,
                        )
                        # Save photo proof if attached
                        if uploaded_photo:
                            os.makedirs("uploads", exist_ok=True)
                            ext = os.path.splitext(uploaded_photo.name)[1].lower() or ".jpg"
                            photo_path = os.path.join("uploads", f"{new_rep_id}{ext}")
                            with open(photo_path, "wb") as f_out:
                                f_out.write(uploaded_photo.getbuffer())

                        st.balloons()
                        st.success(
                            f"🎉 **Report Submitted Successfully!** Reference ID: `{new_rep_id}`\n\n"
                            f"Reported issue: **{selected_issue_type}** for bin **{selected_bin_id}**."
                        )
                        st.info("Your report is now **Submitted**. Check the **My Reports** tab to monitor its lifecycle.")
                    except Exception as err:
                        st.error(f"⚠️ Report Submission Failed: {err}")

    # ==========================================================================
    # TAB 2: MY REPORTS
    # ==========================================================================
    with tab2:
        st.markdown(f"### 📋 Report History for {student_info['name']}")
        user_reports = get_reports(user_id=active_user_id)

        # Summary statistics
        total_reps = len(user_reports)
        verified_count = sum(1 for r in user_reports if r.get("status") in (STATUS_VERIFIED, STATUS_RESOLVED))
        resolved_count = sum(1 for r in user_reports if r.get("status") == STATUS_RESOLVED)
        under_review_count = sum(1 for r in user_reports if r.get("status") in (STATUS_SUBMITTED, STATUS_UNDER_REVIEW))

        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        col_m1.metric("Total Submitted", total_reps)
        col_m2.metric("Under Review", under_review_count)
        col_m3.metric("Verified", verified_count)
        col_m4.metric("Resolved", resolved_count)

        if not user_reports:
            st.info("You haven't submitted any waste reports yet. Use the **Report Waste Issue** tab to report an issue!")
        else:
            # Filter bar
            filter_status = st.selectbox(
                "Filter by Status",
                ["All Statuses", STATUS_SUBMITTED, STATUS_UNDER_REVIEW, STATUS_VERIFIED, STATUS_RESOLVED, STATUS_REJECTED],
                index=0,
            )

            displayed_reports = user_reports
            if filter_status != "All Statuses":
                displayed_reports = [r for r in user_reports if r.get("status") == filter_status]

            # Tabular view with DataFrame
            table_rows = []
            for r in displayed_reports:
                table_rows.append(
                    {
                        "Report ID": r.get("id"),
                        "Bin ID": r.get("bin_id"),
                        "Issue Category": r.get("issue_type"),
                        "Description": r.get("description"),
                        "Status": r.get("status"),
                        "Reported At": r.get("created_at"),
                        "Admin Remark": r.get("admin_note", "") or "-",
                    }
                )

            df_reports = pd.DataFrame(table_rows)
            st.dataframe(df_reports, use_container_width=True, hide_index=True)

            # Detailed Card breakdown
            st.markdown("#### 🔍 Report Lifecycle Breakdown")
            for rep in displayed_reports:
                status_val = rep.get("status", STATUS_SUBMITTED)
                with st.expander(f"📦 #{rep.get('id')} — {rep.get('issue_type')} at {rep.get('bin_id')} ({status_val})"):
                    st.write(f"**Description:** {rep.get('description')}")
                    st.write(f"**Submitted Date:** {rep.get('created_at')}")
                    if rep.get("admin_note"):
                        st.info(f"**Admin Remarks:** {rep.get('admin_note')}")

                    # Check for attached photo proof
                    photo_found = None
                    for ext_c in [".png", ".jpg", ".jpeg"]:
                        cand = os.path.join("uploads", f"{rep.get('id')}{ext_c}")
                        if os.path.exists(cand):
                            photo_found = cand
                            break
                    if photo_found:
                        st.image(photo_found, caption=f"📸 Attached Proof for #{rep.get('id')}", width=280)
                    
                    # Visual status progress bar
                    status_order = [STATUS_SUBMITTED, STATUS_UNDER_REVIEW, STATUS_VERIFIED, STATUS_RESOLVED]
                    if status_val == STATUS_REJECTED:
                        st.error("❌ This report was marked as **Rejected** upon review. (No GreenPoints awarded)")
                    elif status_val in status_order:
                        step_idx = status_order.index(status_val) + 1
                        st.progress(step_idx / 4, text=f"Lifecycle: {status_val} (Step {step_idx} of 4)")

    # ==========================================================================
    # TAB 3: GREENPOINTS & LEDGER
    # ==========================================================================
    with tab3:
        st.markdown(f"### 🌱 GreenPoints Wallet & Rewards: {student_info['name']}")

        balance = get_points_balance(active_user_id)
        ledger_entries = get_points_ledger(active_user_id)

        # Tier calculation
        if balance < 15:
            tier_name = "Bronze Reporter"
            tier_icon = "🥉"
            next_tier = "Silver Scout (15 pts)"
            pts_needed = 15 - balance
            prog_ratio = max(0.0, min(1.0, balance / 15.0))
        elif balance < 30:
            tier_name = "Silver Scout"
            tier_icon = "🥈"
            next_tier = "Gold Champion (30 pts)"
            pts_needed = 30 - balance
            prog_ratio = max(0.0, min(1.0, (balance - 15) / 15.0))
        elif balance < 50:
            tier_name = "Gold Champion"
            tier_icon = "🥇"
            next_tier = "Platinum Eco Hero (50 pts)"
            pts_needed = 50 - balance
            prog_ratio = max(0.0, min(1.0, (balance - 30) / 20.0))
        else:
            tier_name = "Platinum Eco Hero"
            tier_icon = "👑"
            next_tier = "Maximum Tier Achieved!"
            pts_needed = 0
            prog_ratio = 1.0

        col_wallet, col_rules = st.columns([1, 1])

        with col_wallet:
            st.markdown(
                f"""
                <div class="gs-card" style="text-align:center; padding: 24px 20px;">
                    <div style="font-size:0.9rem; text-transform:uppercase; letter-spacing:1px; color:#2d6a4f; font-weight:700;">
                        Current Available Balance
                    </div>
                    <div style="font-size:3.2rem; font-weight:800; color:#1b4332; margin:8px 0;">
                        {balance} <span style="font-size:2rem;">🌱</span>
                    </div>
                    <div style="font-size:1rem; color:#2d6a4f; font-weight:700;">
                        {tier_icon} {tier_name}
                    </div>
                    <div style="font-size:0.8rem; color:#666; margin-top:6px;">
                        Redeemable for cafeteria discounts, campus printing credits, and eco-merchandise.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if pts_needed > 0:
                st.progress(prog_ratio, text=f"Tier Progress: {pts_needed} 🌱 more to reach {next_tier}")
            else:
                st.progress(1.0, text=f"👑 {next_tier}")

        with col_rules:
            st.markdown(
                """
                <div class="gs-card">
                    <h4 style="margin-top:0; color:#1b4332;">📜 How GreenPoints Are Earned</h4>
                    <ul style="padding-left:18px; font-size:0.9rem; color:#333; line-height:1.6;">
                        <li><strong>+5 Points:</strong> Awarded when maintenance verifies a legitimate report.</li>
                        <li><strong>+5 Points:</strong> Awarded once the issue is completely resolved on-site.</li>
                        <li><strong>0 Points:</strong> Submitted reports pending review or rejected reports.</li>
                        <li><strong>Duplicate Guard:</strong> Each milestone can only be rewarded once per report.</li>
                    </ul>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("#### 📜 Transaction History Ledger")
        if not ledger_entries:
            st.info("No GreenPoints transactions recorded yet. Submit reports to begin accumulating points!")
        else:
            ledger_rows = []
            for item in ledger_entries:
                ledger_rows.append(
                    {
                        "Transaction ID": item.get("id"),
                        "Report Reference": item.get("report_id"),
                        "Action Type": item.get("action", "").replace("_", " ").title(),
                        "Points Earned": f"+{item.get('points', 0)} 🌱",
                        "Timestamp": item.get("created_at"),
                    }
                )
            df_ledger = pd.DataFrame(ledger_rows)
            st.dataframe(df_ledger, use_container_width=True, hide_index=True)

    # ==========================================================================
    # TAB 4: DEMO QR BINS (Judges & Evaluation)
    # ==========================================================================
    with tab4:
        st.markdown("### 📱 Campus Bin QR Code Showcase")
        st.markdown(
            "Every waste bin on campus has a physical scannable QR code encoded with its direct URL. "
            "Scan any QR code below using your mobile camera, or click **Simulate Scan** to test real-time URL detection!"
        )

        # Cleanly determine base URL without technical clutter on the student page
        app_base_url = os.getenv("APP_BASE_URL", "https://green-score-9orq.onrender.com").rstrip("/")

        # 3-column responsive grid
        cols = st.columns(3)
        for i, bin_item in enumerate(all_bins):
            col_target = cols[i % 3]
            bin_id = bin_item["id"]
            bin_loc = bin_item["location"]
            bin_cat = bin_item.get("waste_category", "Standard")

            # Generate QR image
            qr_image = qr_utils.generate_bin_qr(bin_id=bin_id, base_url=app_base_url)
            direct_url = qr_utils.get_bin_direct_url(bin_id=bin_id, base_url=app_base_url)

            with col_target:
                st.markdown(
                    f"""
                    <div class="gs-qr-card">
                        <div style="font-weight:700; color:#1b4332; font-size:1.05rem;">{bin_id}</div>
                        <div style="font-size:0.85rem; color:#444; height:38px; margin-top:2px;">{bin_loc}</div>
                        <div style="font-size:0.78rem; font-weight:600; color:#2d6a4f; margin-bottom:8px;">🏷️ {bin_cat}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                st.image(qr_image, caption=f"QR for {bin_id}", use_container_width=True)

                if st.button(f"📲 Simulate Scan {bin_id}", key=f"sim_scan_{bin_id}", use_container_width=True):
                    st.query_params["bin_id"] = bin_id
                    st.rerun()

                st.markdown(
                    f"<div style='text-align:center; font-size:0.75rem;'><a href='{direct_url}' target='_blank'>Direct Link</a></div>",
                    unsafe_allow_html=True,
                )
                st.markdown("<br/>", unsafe_allow_html=True)


# Backwards compatibility alias for CONTRACT.md
render_student_ui = render_student_portal


# ==============================================================================
# MAIN STANDALONE EXECUTION BLOCK
# ==============================================================================
if __name__ == "__main__":
    st.set_page_config(
        page_title="GreenScore — Student Experience",
        page_icon="🌱",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    render_student_portal()
