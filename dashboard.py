"""
GreenScore Administrator Dashboard
Owned by Person 3 (Application, Analytics, and Deployment)
Provides oversight of campus waste management, report verification workflows,
audit trails, and real-time sustainability analytics.
"""

from typing import Dict, Any, List, Optional
import pandas as pd
import streamlit as st

import datetime
import os
from database import get_db, get_reports, get_bins, get_dashboard_stats, add_bin, toggle_bin_status
from report_service import transition_report, get_report_by_id, get_report_history, ReportError
from points import get_points_balance
from constants import (
    ROLE_ADMIN,
    STATUS_SUBMITTED,
    STATUS_UNDER_REVIEW,
    STATUS_VERIFIED,
    STATUS_REJECTED,
    STATUS_RESOLVED,
    ALL_STATUSES,
    ISSUE_TYPES,
)
import analytics
import qr_utils


# ==============================================================================
# ADMIN STYLING
# ==============================================================================
def _inject_admin_theme():
    """Inject styling tailored for the administrative dashboard."""
    st.markdown(
        """
        <style>
        .admin-header {
            background: linear-gradient(90deg, #1b4332 0%, #2d6a4f 100%);
            color: #ffffff;
            border-radius: 10px;
            padding: 16px 24px;
            margin-bottom: 20px;
            box-shadow: 0 4px 12px rgba(27, 67, 50, 0.2);
        }
        .admin-metric-card {
            background-color: #ffffff;
            border-radius: 10px;
            padding: 14px 16px;
            border-left: 5px solid #2d6a4f;
            box-shadow: 0 2px 6px rgba(0,0,0,0.06);
            margin-bottom: 12px;
        }
        .badge-status {
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 0.8rem;
            font-weight: 600;
        }
        .status-submitted { background: #e9ecef; color: #495057; }
        .status-under-review { background: #fef3c7; color: #92400e; }
        .status-verified { background: #d1fae5; color: #065f46; }
        .status-resolved { background: #dbeafe; color: #1e40af; }
        .status-rejected { background: #fee2e2; color: #991b1b; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _get_total_points_awarded() -> int:
    """Retrieve total GreenPoints awarded across all campus reports."""
    try:
        with get_db() as conn:
            row = conn.execute("SELECT COALESCE(SUM(points), 0) AS total FROM points_ledger").fetchone()
            return int(row["total"]) if row else 0
    except Exception:
        return 0


def _get_all_ledger_records() -> List[Dict[str, Any]]:
    """Retrieve all GreenPoints ledger transactions with student names."""
    try:
        with get_db() as conn:
            rows = conn.execute("""
                SELECT pl.id, pl.user_id, pl.report_id, pl.action, pl.points, pl.created_at,
                       u.name AS student_name
                FROM points_ledger pl
                LEFT JOIN users u ON pl.user_id = u.id
                ORDER BY pl.created_at DESC, pl.id DESC
            """).fetchall()
            return [dict(r) for r in rows]
    except Exception:
        return []


def render_dashboard() -> None:
    """Main rendering entry point for Administrator Dashboard."""
    _inject_admin_theme()

    # Admin Session / Profile in Sidebar
    with st.sidebar:
        st.markdown("### 🛡️ Admin Profile")
        admin_id = "ADM-001"
        st.markdown(
            f"""
            <div style="background:#f0fdf4; border:1px solid #bbf7d0; border-radius:8px; padding:12px; margin-bottom:12px;">
                <div style="font-weight:700; color:#1b4332;">Campus Sanitation HQ</div>
                <div style="font-size:0.85rem; color:#555;">Operator ID: <code>{admin_id}</code></div>
                <div style="font-size:0.8rem; color:#16a34a; font-weight:600; margin-top:4px;">● System Active</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button("🔄 Refresh Data", use_container_width=True):
            st.rerun()

    # Header Banner
    st.markdown(
        """
        <div class="admin-header">
            <h2 style="margin:0; font-weight:800;">🌿 GreenScore Operations Dashboard</h2>
            <p style="margin:4px 0 0 0; opacity:0.9; font-size:0.95rem;">
                Campus waste-management command center: monitor reports, perform on-site reviews, and verify GreenPoints rewards.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # --------------------------------------------------------------------------
    # TOP KPI METRICS
    # --------------------------------------------------------------------------
    stats = get_dashboard_stats()
    total_pts = _get_total_points_awarded()
    all_reports = get_reports()

    m1, m2, m3, m4, m5, m6 = st.columns(6)
    m1.metric("Total Reports", stats.get("total", 0))
    m2.metric("Submitted", stats.get("submitted", 0), help="New reports waiting for review")
    m3.metric("Under Review", stats.get("under_review", 0), help="Currently being checked by staff")
    m4.metric("Verified", stats.get("verified", 0), help="Confirmed issues (earned +5 pts)")
    m5.metric("Resolved", stats.get("resolved", 0), help="Waste cleaned/cleared (earned +5 pts)")
    m6.metric("GreenPoints Awarded", f"{total_pts} 🌱", help="Total points granted to campus students")

    st.markdown("---")

    # --------------------------------------------------------------------------
    # DASHBOARD TABS
    # --------------------------------------------------------------------------
    tab_reports, tab_analytics, tab_points, tab_bins = st.tabs([
        "📋 Report Review Queue",
        "📊 Visual Analytics & Trends",
        "🌱 GreenPoints Ledger",
        "📍 Campus Bins Directory",
    ])

    # ==========================================================================
    # TAB 1: REPORT REVIEW QUEUE & STATUS TRANSITION
    # ==========================================================================
    with tab_reports:
        st.markdown("### 🔍 Campus Waste Report Queue")

        # Filters
        f_col1, f_col2, f_col3 = st.columns([1, 1, 1])
        with f_col1:
            status_filter = st.selectbox(
                "Filter by Status",
                ["All Statuses"] + ALL_STATUSES,
                index=0,
            )
        with f_col2:
            issue_filter = st.selectbox(
                "Filter by Issue Category",
                ["All Categories"] + ISSUE_TYPES,
                index=0,
            )
        with f_col3:
            all_bins_data = get_bins(active_only=False)
            bin_filter_opts = ["All Bins"] + [b["id"] for b in all_bins_data]
            bin_filter = st.selectbox(
                "Filter by Bin ID",
                bin_filter_opts,
                index=0,
            )

        # Apply filtering
        filtered_reports = all_reports
        if status_filter != "All Statuses":
            filtered_reports = [r for r in filtered_reports if r.get("status") == status_filter]
        if issue_filter != "All Categories":
            filtered_reports = [r for r in filtered_reports if r.get("issue_type") == issue_filter]
        if bin_filter != "All Bins":
            filtered_reports = [r for r in filtered_reports if r.get("bin_id") == bin_filter]

        st.caption(f"Showing **{len(filtered_reports)}** of **{len(all_reports)}** total campus reports.")

        # Reports Summary Table
        if not filtered_reports:
            st.info("No reports match the selected filters.")
        else:
            table_rows = []
            for r in filtered_reports:
                table_rows.append({
                    "Report ID": r.get("id"),
                    "Status": r.get("status"),
                    "Bin ID": r.get("bin_id"),
                    "Location": r.get("bin_location", "Campus"),
                    "Category": r.get("issue_type"),
                    "Reported By": r.get("user_id"),
                    "Date": r.get("created_at"),
                    "Admin Note": r.get("admin_note", "") or "-",
                })
            df_table = pd.DataFrame(table_rows)
            st.dataframe(df_table, use_container_width=True, hide_index=True)

            csv_bytes = df_table.to_csv(index=False).encode("utf-8")
            st.download_button(
                label=f"📥 Download Filtered Reports ({len(df_table)} rows) as CSV",
                data=csv_bytes,
                file_name=f"greenscore_reports_{datetime.date.today().isoformat()}.csv",
                mime="text/csv",
                use_container_width=True,
            )

        st.markdown("---")

        # Report Action & Review Center
        st.markdown("### ⚙️ Action & Workflow Panel")
        st.markdown("Select a report below to inspect its details, transition its status, and award GreenPoints.")

        if not all_reports:
            st.info("No reports available to review. Once students submit reports, they will appear here.")
        else:
            # Build dropdown choices for reports
            report_choices = [
                f"{r['id']} — {r.get('issue_type')} @ {r.get('bin_id')} [{r.get('status')}]"
                for r in all_reports
            ]
            selected_report_str = st.selectbox(
                "Select Report to Review / Transition",
                report_choices,
                index=0,
            )
            selected_rep_id = selected_report_str.split(" — ")[0].strip()
            rep_details = get_report_by_id(selected_rep_id)

            if rep_details:
                current_status = rep_details.get("status")

                col_det1, col_det2 = st.columns([1, 1])

                with col_det1:
                    st.markdown(
                        f"""
                        <div style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:8px; padding:16px;">
                            <h4 style="margin-top:0; color:#1e293b;">📄 Report Details: <code>{rep_details['id']}</code></h4>
                            <p><strong>Bin:</strong> {rep_details.get('bin_id')} — <em>{rep_details.get('bin_location', 'N/A')}</em> ({rep_details.get('bin_waste_category', 'General')})</p>
                            <p><strong>Issue Category:</strong> {rep_details.get('issue_type')}</p>
                            <p><strong>Description:</strong> {rep_details.get('description')}</p>
                            <p><strong>Reported By:</strong> <code>{rep_details.get('user_id')}</code> at {rep_details.get('created_at')}</p>
                            <p><strong>Current Status:</strong> <span style="font-weight:700; color:#1b4332;">{current_status}</span></p>
                            <p><strong>Reviewed At:</strong> {rep_details.get('reviewed_at') or 'Not yet reviewed'}</p>
                            <p><strong>Resolved At:</strong> {rep_details.get('resolved_at') or 'Not yet resolved'}</p>
                            <p><strong>Current Admin Note:</strong> {rep_details.get('admin_note') or 'None'}</p>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                    # Check for attached photo proof
                    photo_proof = None
                    for ext_c in [".png", ".jpg", ".jpeg"]:
                        cand_p = os.path.join("uploads", f"{rep_details['id']}{ext_c}")
                        if os.path.exists(cand_p):
                            photo_proof = cand_p
                            break
                    if photo_proof:
                        st.image(photo_proof, caption=f"📸 Attached Photo Proof for #{rep_details['id']}", width=260)

                with col_det2:
                    st.markdown(
                        f"""
                        <div style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:8px; padding:16px;">
                            <h4 style="margin-top:0; color:#1e293b;">⚡ Status Transition Controls</h4>
                            <p style="font-size:0.85rem; color:#64748b;">
                                Workflow: <code>Submitted</code> → <code>Under Review</code> → <code>Verified</code> or <code>Rejected</code> → <code>Resolved</code>
                            </p>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                    admin_note_input = st.text_input(
                        "Admin Note / Remarks (Optional)",
                        placeholder="e.g. Verified by campus patrol; cleaning crew dispatched.",
                        key=f"note_{selected_rep_id}",
                    )

                    # Dynamic transition controls strictly adhering to the Contract state machine
                    if current_status == STATUS_SUBMITTED:
                        st.info("Status: **Submitted**. Move this report into review to investigate.")
                        if st.button("🚀 Start Review (Move to Under Review)", type="primary", use_container_width=True):
                            try:
                                transition_report(selected_rep_id, admin_id, STATUS_UNDER_REVIEW, admin_note_input)
                                st.success(f"Report {selected_rep_id} moved to **Under Review**!")
                                st.rerun()
                            except ReportError as err:
                                st.error(f"Transition error: {err}")

                    elif current_status == STATUS_UNDER_REVIEW:
                        st.warning("Status: **Under Review**. Choose whether to verify or reject the report.")
                        btn_col1, btn_col2 = st.columns(2)
                        with btn_col1:
                            if st.button("✅ Verify Issue (+5 pts)", type="primary", use_container_width=True):
                                try:
                                    transition_report(selected_rep_id, admin_id, STATUS_VERIFIED, admin_note_input)
                                    st.success(f"Report {selected_rep_id} verified! Awarded +5 GreenPoints to student.")
                                    st.rerun()
                                except ReportError as err:
                                    st.error(f"Transition error: {err}")
                        with btn_col2:
                            if st.button("❌ Reject Issue (0 pts)", use_container_width=True):
                                try:
                                    transition_report(selected_rep_id, admin_id, STATUS_REJECTED, admin_note_input)
                                    st.warning(f"Report {selected_rep_id} rejected. No GreenPoints awarded.")
                                    st.rerun()
                                except ReportError as err:
                                    st.error(f"Transition error: {err}")

                    elif current_status == STATUS_VERIFIED:
                        st.success("Status: **Verified**. When physical waste cleanup is finished, mark as resolved.")
                        if st.button("🎉 Mark as Resolved (+5 pts)", type="primary", use_container_width=True):
                            try:
                                transition_report(selected_rep_id, admin_id, STATUS_RESOLVED, admin_note_input)
                                st.balloons()
                                st.success(f"Report {selected_rep_id} marked as Resolved! Awarded +5 GreenPoints.")
                                st.rerun()
                            except ReportError as err:
                                st.error(f"Transition error: {err}")

                    elif current_status == STATUS_RESOLVED:
                        st.info("✅ **Report Resolved**. Full lifecycle complete (+10 total GreenPoints awarded).")

                    elif current_status == STATUS_REJECTED:
                        st.error("❌ **Report Rejected**. Terminal status (0 GreenPoints awarded).")

                # Audit History Trail
                history = get_report_history(selected_rep_id)
                with st.expander(f"📜 Audit Trail History for {selected_rep_id} ({len(history)} events)"):
                    if not history:
                        st.caption("No transitions logged yet for this report.")
                    else:
                        for entry in history:
                            note_text = f" (Note: {entry['note']})" if entry.get('note') else ""
                            admin_label = entry.get('admin_name') or entry.get('admin_id')
                            st.markdown(
                                f"- **{entry.get('changed_at')}**: Changed from `'{entry.get('old_status')}'` "
                                f"to **`'{entry.get('new_status')}'`** by `{admin_label}`.{note_text}"
                            )

    # ==========================================================================
    # TAB 2: VISUAL ANALYTICS & TRENDS
    # ==========================================================================
    with tab_analytics:
        st.markdown("### 📊 Campus Waste & Sustainability Analytics")
        st.caption("Real-time visual insights generated from verified database records.")

        row1_col1, row1_col2 = st.columns(2)
        with row1_col1:
            st.markdown("#### 🍩 Report Status Distribution")
            fig_status = analytics.plot_status_breakdown(all_reports)
            st.plotly_chart(fig_status, use_container_width=True, key="chart_status_breakdown")

        with row1_col2:
            st.markdown("#### 📊 Waste Issues by Category")
            fig_issues = analytics.plot_issues_by_category(all_reports)
            st.plotly_chart(fig_issues, use_container_width=True, key="chart_issues_category")

        row2_col1, row2_col2 = st.columns(2)
        with row2_col1:
            st.markdown("#### 📍 Top Campus Bin Activity Hotspots")
            fig_bins = analytics.plot_reports_by_bin(all_reports)
            st.plotly_chart(fig_bins, use_container_width=True, key="chart_bins_activity")

        with row2_col2:
            st.markdown("#### 📅 Report Submissions Timeline")
            fig_timeline = analytics.plot_activity_timeline(all_reports)
            st.plotly_chart(fig_timeline, use_container_width=True, key="chart_activity_timeline")

    # ==========================================================================
    # TAB 3: GREENPOINTS LEDGER & IMPACT
    # ==========================================================================
    with tab_points:
        st.markdown("### 🌱 Campus GreenPoints Reward Ledger")
        st.caption("Full audit record of student rewards earned for verified reports and cleanups.")

        ledger_records = _get_all_ledger_records()

        col_lp_left, col_lp_right = st.columns([1, 1])
        with col_lp_left:
            st.markdown(
                f"""
                <div class="admin-metric-card">
                    <div style="font-size:0.9rem; color:#2d6a4f; font-weight:700; text-transform:uppercase;">
                        Total GreenPoints Distributed
                    </div>
                    <div style="font-size:2.8rem; font-weight:800; color:#1b4332; margin:6px 0;">
                        {total_pts} 🌱
                    </div>
                    <div style="font-size:0.85rem; color:#555;">
                        Granted across {len(ledger_records)} reward transactions.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with col_lp_right:
            st.markdown("#### 🎯 Points Allocation Breakdown")
            fig_pts = analytics.plot_points_distribution(ledger_records)
            st.plotly_chart(fig_pts, use_container_width=True, key="chart_points_distribution")

        st.markdown("#### 📜 Transaction History Log")
        if not ledger_records:
            st.info("No points awarded yet. Verify or resolve submitted reports to distribute GreenPoints!")
        else:
            table_ledger = []
            for item in ledger_records:
                table_ledger.append({
                    "Ledger ID": item.get("id"),
                    "Student ID": item.get("user_id"),
                    "Student Name": item.get("student_name") or "-",
                    "Report ID": item.get("report_id"),
                    "Action Type": item.get("action", "").title(),
                    "Points Granted": f"+{item.get('points')} 🌱",
                    "Timestamp": item.get("created_at"),
                })
            df_ledger = pd.DataFrame(table_ledger)
            st.dataframe(df_ledger, use_container_width=True, hide_index=True)

    # ==========================================================================
    # TAB 4: CAMPUS BINS DIRECTORY & QR PREVIEW
    # ==========================================================================
    with tab_bins:
        st.markdown("### 📍 Campus Waste Bins Directory")
        st.caption("Registered campus bins equipped with QR codes.")

        bins = get_bins(active_only=False)
        if bins:
            df_bins = pd.DataFrame(bins)
            st.dataframe(df_bins, use_container_width=True, hide_index=True)

            st.markdown("#### 🖨️ QR Code Tag Inspection")
            st.caption("Administrators can preview or print QR labels for physical bin placement.")
            selected_bin_for_qr = st.selectbox(
                "Select Bin to Inspect QR Tag",
                [f"{b['id']} — {b['location']} ({b.get('waste_category', 'General')})" for b in bins],
            )
            inspect_bin_id = selected_bin_for_qr.split(" — ")[0].strip()

            lan_ip = qr_utils.get_local_ip()
            default_host = os.getenv("APP_BASE_URL", f"http://{lan_ip}:8501")

            q_col1, q_col2 = st.columns([1, 2])
            with q_col1:
                qr_img = qr_utils.generate_bin_qr(inspect_bin_id, base_url=default_host)
                st.image(qr_img, caption=f"QR for {inspect_bin_id}", width=200)
            with q_col2:
                target_url = qr_utils.get_bin_direct_url(inspect_bin_id, base_url=default_host)
                st.markdown(f"**Target Routing URL:** `{target_url}`")
                st.markdown(
                    "📱 **Scannable from Phone:** As long as your phone is connected to the same Wi-Fi, "
                    "scanning this QR with your camera will directly open GreenScore and preselect the bin."
                )

            st.markdown("---")
            col_add, col_toggle = st.columns([1, 1])

            with col_add:
                st.markdown("#### ➕ Add New Campus Bin")
                new_bid = st.text_input("New Bin ID", placeholder="e.g. BIN-007")
                new_loc = st.text_input("Campus Location", placeholder="e.g. Main Auditorium Lawn")
                new_cat = st.selectbox("Waste Category", ["General", "Recyclable", "Organic", "E-Waste / Hazardous"])
                if st.button("➕ Register Bin", type="primary", use_container_width=True):
                    if not new_bid.strip() or not new_loc.strip():
                        st.error("Please provide both Bin ID and Location.")
                    elif any(b["id"].upper() == new_bid.strip().upper() for b in bins):
                        st.error(f"Bin ID '{new_bid.strip()}' already exists.")
                    else:
                        try:
                            add_bin(new_bid.strip(), new_loc.strip(), new_cat)
                            st.success(f"Bin {new_bid.strip()} successfully registered!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error registering bin: {e}")

            with col_toggle:
                st.markdown("#### ⚙️ Activate / Deactivate Bins")
                for b in bins:
                    is_active = bool(b.get("active", 1))
                    icon = "🟢 Active" if is_active else "🔴 Inactive"
                    btn_text = "Deactivate" if is_active else "Activate"
                    st.write(f"**{b['id']}** — {b['location']} ({icon})")
                    if st.button(f"{btn_text} {b['id']}", key=f"t_{b['id']}"):
                        toggle_bin_status(b["id"], not is_active)
                        st.rerun()


if __name__ == "__main__":
    st.set_page_config(
        page_title="GreenScore — Admin Dashboard",
        page_icon="🌿",
        layout="wide",
    )
    render_dashboard()
