"""
GreenScore Report Service
Owned by Person 2 (Backend, Database, and GreenPoints)
Handles report submission, retrieval, duplicate checks, status transitions, and review history.
"""

import uuid
from database import get_db, get_reports, get_dashboard_stats
from points import award_points
from constants import (
    ROLE_ADMIN,
    STATUS_SUBMITTED,
    STATUS_UNDER_REVIEW,
    STATUS_VERIFIED,
    STATUS_REJECTED,
    STATUS_RESOLVED,
    POINTS_FOR_VERIFICATION,
    POINTS_FOR_RESOLUTION,
    ACTION_VERIFIED,
    ACTION_RESOLVED,
    ISSUE_TYPES,
    DUPLICATE_WINDOW_MINUTES,
)


class ReportError(Exception):
    """Custom exception raised for invalid report operations."""
    pass


# Allowed status transitions strictly adhering to the state machine
VALID_TRANSITIONS = {
    STATUS_SUBMITTED: [STATUS_UNDER_REVIEW],
    STATUS_UNDER_REVIEW: [STATUS_VERIFIED, STATUS_REJECTED],
    STATUS_VERIFIED: [STATUS_RESOLVED],
    STATUS_REJECTED: [],
    STATUS_RESOLVED: [],
}


def create_report(user_id, bin_id, issue_type, description):
    """
    Save a new report after validating user, bin, issue type, and duplicate rules.
    Blocks duplicate submissions for the same bin and issue type within the duplicate window.
    Returns the generated report_id.
    """
    if not description or not description.strip():
        raise ReportError("Report description cannot be empty.")

    if issue_type not in ISSUE_TYPES:
        raise ReportError(f"Invalid issue type '{issue_type}'. Must be one of: {', '.join(ISSUE_TYPES)}")

    with get_db() as conn:
        # Validate user exists
        user = conn.execute("SELECT id, role FROM users WHERE id = ?", (user_id,)).fetchone()
        if not user:
            raise ReportError(f"User '{user_id}' does not exist.")

        # Validate bin exists and is active
        bin_record = conn.execute("SELECT id, active FROM bins WHERE id = ?", (bin_id,)).fetchone()
        if not bin_record:
            raise ReportError(f"Bin '{bin_id}' does not exist.")
        if not bin_record["active"]:
            raise ReportError(f"Bin '{bin_id}' is currently inactive.")

        # Check for duplicate reports for this bin & issue within the configured window
        duplicate = conn.execute("""
            SELECT id, created_at FROM reports
            WHERE bin_id = ?
              AND issue_type = ?
              AND status IN (?, ?)
              AND created_at >= datetime('now', ?)
        """, (
            bin_id,
            issue_type,
            STATUS_SUBMITTED,
            STATUS_UNDER_REVIEW,
            f"-{DUPLICATE_WINDOW_MINUTES} minutes",
        )).fetchone()

        if duplicate:
            raise ReportError(
                f"A report for bin '{bin_id}' with issue '{issue_type}' was submitted recently "
                f"({duplicate['id']}) and is currently pending review."
            )

        report_id = f"REP-{uuid.uuid4().hex[:8].upper()}"

        conn.execute("""
            INSERT INTO reports (
                id, user_id, bin_id, issue_type, description, status
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            report_id,
            user_id,
            bin_id,
            issue_type,
            description.strip(),
            STATUS_SUBMITTED,
        ))

    return report_id


def transition_report(report_id, admin_id, new_status, note=""):
    """
    Validates and executes a report status transition inside a single transaction.
    - Ensures only an admin can perform transitions.
    - Validates that the transition follows the defined workflow.
    - Awards GreenPoints on verification and resolution.
    - Records an audit log entry in report_history.
    """
    with get_db() as conn:
        # Validate admin identity
        admin = conn.execute("SELECT id, role FROM users WHERE id = ?", (admin_id,)).fetchone()
        if not admin or admin["role"] != ROLE_ADMIN:
            raise ReportError("Only administrators can transition report status.")

        # Fetch current report
        report = conn.execute("SELECT * FROM reports WHERE id = ?", (report_id,)).fetchone()
        if not report:
            raise ReportError(f"Report '{report_id}' not found.")

        old_status = report["status"]

        allowed = VALID_TRANSITIONS.get(old_status, [])
        if new_status not in allowed:
            raise ReportError(
                f"Invalid status transition from '{old_status}' to '{new_status}'. "
                f"Allowed transitions: {allowed if allowed else 'None (terminal state)'}."
            )

        # Award GreenPoints within the same transaction if applicable
        if new_status == STATUS_VERIFIED:
            award_points(conn, report["user_id"], report_id, ACTION_VERIFIED, POINTS_FOR_VERIFICATION)
        elif new_status == STATUS_RESOLVED:
            award_points(conn, report["user_id"], report_id, ACTION_RESOLVED, POINTS_FOR_RESOLUTION)

        # Update report status and timestamp markers
        conn.execute("""
            UPDATE reports
            SET status = ?,
                reviewer_id = ?,
                admin_note = ?,
                reviewed_at = CASE
                    WHEN ? IN ('Verified', 'Rejected')
                    THEN datetime('now')
                    ELSE reviewed_at
                END,
                resolved_at = CASE
                    WHEN ? = 'Resolved'
                    THEN datetime('now')
                    ELSE resolved_at
                END
            WHERE id = ?
        """, (
            new_status,
            admin_id,
            note.strip() if note else "",
            new_status,
            new_status,
            report_id,
        ))

        # Insert audit trail into report_history
        conn.execute("""
            INSERT INTO report_history (
                report_id, admin_id,
                old_status, new_status, note
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            report_id,
            admin_id,
            old_status,
            new_status,
            note.strip() if note else "",
        ))

    return True


def get_report_by_id(report_id):
    """Retrieve full details of a single report including bin information."""
    with get_db() as conn:
        row = conn.execute("""
            SELECT r.*, b.location AS bin_location, b.waste_category AS bin_waste_category
            FROM reports r
            LEFT JOIN bins b ON r.bin_id = b.id
            WHERE r.id = ?
        """, (report_id,)).fetchone()
        return dict(row) if row else None


def get_report_history(report_id):
    """Get status change audit trail for a specific report."""
    with get_db() as conn:
        rows = conn.execute("""
            SELECT rh.*, u.name AS admin_name
            FROM report_history rh
            LEFT JOIN users u ON rh.admin_id = u.id
            WHERE rh.report_id = ?
            ORDER BY rh.changed_at ASC, rh.id ASC
        """, (report_id,)).fetchall()
        return [dict(row) for row in rows]
