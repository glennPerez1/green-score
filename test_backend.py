"""
GreenScore Backend Test Suite
Owned by Person 2 (Backend, Database, and GreenPoints)
Verifies database integrity, report workflow, duplicate rejection, points ledger, and dashboard statistics.
"""

import os
import sys

# Use an isolated test database by default to ensure clean test assertions
TEST_DB = "greenscore_test.db"
os.environ["DB_PATH"] = TEST_DB

# Remove any existing test db before starting
if os.path.exists(TEST_DB):
    try:
        os.remove(TEST_DB)
    except OSError:
        pass

from database import init_db, get_db, get_bins
from seed_data import seed_data
from report_service import (
    create_report,
    transition_report,
    get_reports,
    get_report_by_id,
    get_report_history,
    get_dashboard_stats,
    ReportError,
)
from points import (
    award_points,
    get_points_balance,
    get_points_ledger,
)
from constants import (
    STATUS_SUBMITTED,
    STATUS_UNDER_REVIEW,
    STATUS_VERIFIED,
    STATUS_RESOLVED,
    STATUS_REJECTED,
)


def run_tests():
    print("=" * 60)
    print("Starting GreenScore Backend Tests...")
    print("=" * 60)

    # 1. Test Database Initialization and Seed Data
    print("\n[Test 1] Initializing database and running seed_data()...")
    seed_data()
    bins = get_bins()
    assert len(bins) == 6, f"Expected 6 bins, got {len(bins)}"
    with get_db() as conn:
        user_count = conn.execute("SELECT COUNT(*) AS c FROM users").fetchone()["c"]
        assert user_count == 3, f"Expected 3 users, got {user_count}"
    print("PASS: Database initialized and seeded with 3 users and 6 bins.")

    # 2. Test Report Creation
    print("\n[Test 2] Creating a new student report...")
    initial_balance = get_points_balance("STU-001")
    report_id = create_report(
        user_id="STU-001",
        bin_id="BIN-001",
        issue_type="Overflowing bin",
        description="The bin is overflowing onto the ground.",
    )
    assert report_id.startswith("REP-"), f"Invalid report_id format: {report_id}"
    print(f"PASS: Created report {report_id}")

    # 3. Test Student Visibility
    print("\n[Test 3] Verifying student report retrieval...")
    student_reports = get_reports(user_id="STU-001")
    assert any(r["id"] == report_id for r in student_reports), "Created report not found in student's reports"
    print("PASS: Report appears in student report history.")

    # 4. Test Duplicate Report Prevention
    print("\n[Test 4] Testing duplicate submission prevention...")
    duplicate_blocked = False
    try:
        create_report(
            user_id="STU-001",
            bin_id="BIN-001",
            issue_type="Overflowing bin",
            description="Another student reporting same full bin.",
        )
    except ReportError as e:
        duplicate_blocked = True
        print(f"Caught expected duplicate error: {e}")
    assert duplicate_blocked, "Duplicate report was not blocked!"
    print("PASS: Duplicate report submission within window was successfully blocked.")

    # 5. Test Non-Admin Transition Guard
    print("\n[Test 5] Ensuring students cannot transition report status...")
    student_blocked = False
    try:
        transition_report(report_id, "STU-001", STATUS_UNDER_REVIEW, "Student trying to review")
    except ReportError as e:
        student_blocked = True
    assert student_blocked, "Non-admin was allowed to transition report!"
    print("PASS: Non-admin users cannot transition reports.")

    # 6. Test Invalid Transition (Direct Submitted -> Resolved)
    print("\n[Test 6] Testing invalid transition protection (Submitted -> Resolved)...")
    invalid_transition_blocked = False
    try:
        transition_report(report_id, "ADM-001", STATUS_RESOLVED, "Skipping review")
    except ReportError as e:
        invalid_transition_blocked = True
    assert invalid_transition_blocked, "Invalid transition directly to Resolved was not blocked!"
    print("PASS: Invalid transition directly to Resolved was blocked.")

    # 7. Test Valid Workflow: Submitted -> Under Review
    print("\n[Test 7] Transitioning: Submitted -> Under Review...")
    assert transition_report(report_id, "ADM-001", STATUS_UNDER_REVIEW, "Review initiated.")
    rep = get_report_by_id(report_id)
    assert rep["status"] == STATUS_UNDER_REVIEW
    assert get_points_balance("STU-001") == initial_balance, "Points awarded prematurely!"
    print("PASS: Moved to Under Review. No premature points awarded.")

    # 8. Test Valid Workflow: Under Review -> Verified (Awards +5 points)
    print("\n[Test 8] Transitioning: Under Review -> Verified (+5 points)...")
    assert transition_report(report_id, "ADM-001", STATUS_VERIFIED, "Issue verified by campus staff.")
    rep = get_report_by_id(report_id)
    assert rep["status"] == STATUS_VERIFIED
    assert rep["reviewed_at"] is not None
    verified_balance = get_points_balance("STU-001")
    assert verified_balance == initial_balance + 5, f"Expected {initial_balance + 5}, got {verified_balance}"
    print(f"PASS: Moved to Verified. Student earned 5 GreenPoints. Balance: {verified_balance}")

    # 9. Test Valid Workflow: Verified -> Resolved (Awards +5 points)
    print("\n[Test 9] Transitioning: Verified -> Resolved (+5 points)...")
    assert transition_report(report_id, "ADM-001", STATUS_RESOLVED, "Bin has been emptied and cleaned.")
    rep = get_report_by_id(report_id)
    assert rep["status"] == STATUS_RESOLVED
    assert rep["resolved_at"] is not None
    resolved_balance = get_points_balance("STU-001")
    assert resolved_balance == initial_balance + 10, f"Expected {initial_balance + 10}, got {resolved_balance}"
    print(f"PASS: Moved to Resolved. Total GreenPoints earned: {resolved_balance}")

    # 10. Test Duplicate Reward Protection in Points Ledger
    print("\n[Test 10] Testing duplicate reward protection...")
    with get_db() as conn:
        # Attempt to insert verified points a second time for same report
        second_reward = award_points(conn, "STU-001", report_id, "verified", 5)
        assert not second_reward, "Duplicate reward was wrongly recorded!"
    assert get_points_balance("STU-001") == resolved_balance
    print("PASS: Duplicate GreenPoints reward was strictly prevented.")

    # 11. Test Report History / Audit Trail
    print("\n[Test 11] Checking audit log history...")
    history = get_report_history(report_id)
    assert len(history) == 3, f"Expected 3 history records, got {len(history)}"
    assert history[0]["old_status"] == STATUS_SUBMITTED and history[0]["new_status"] == STATUS_UNDER_REVIEW
    assert history[1]["old_status"] == STATUS_UNDER_REVIEW and history[1]["new_status"] == STATUS_VERIFIED
    assert history[2]["old_status"] == STATUS_VERIFIED and history[2]["new_status"] == STATUS_RESOLVED
    print("PASS: Audit trail correctly logs all 3 status transitions.")

    # 12. Test Rejection Workflow
    print("\n[Test 12] Testing rejection workflow (Under Review -> Rejected, 0 points)...")
    rep_reject = create_report("STU-002", "BIN-002", "Damaged bin", "Scratched sticker")
    transition_report(rep_reject, "ADM-001", STATUS_UNDER_REVIEW, "Checking damage")
    transition_report(rep_reject, "ADM-001", STATUS_REJECTED, "Cosmetic only, not damaged.")
    assert get_points_balance("STU-002") == 0, "Rejected report awarded points!"
    print("PASS: Rejected report successfully transitions and awards 0 points.")

    # 13. Test Dashboard Statistics
    print("\n[Test 13] Checking get_dashboard_stats()...")
    stats = get_dashboard_stats()
    assert stats["total"] >= 2
    assert "submitted" in stats and "verified" in stats and "resolved" in stats and "rejected" in stats
    print(f"PASS: Dashboard stats calculated: {stats}")

    print("\n" + "=" * 60)
    print("ALL BACKEND TESTS PASSED SUCCESSFULLY! (13/13)")
    print("=" * 60)


if __name__ == "__main__":
    try:
        run_tests()
    finally:
        # Clean up test database file
        if os.path.exists(TEST_DB):
            try:
                os.remove(TEST_DB)
            except OSError:
                pass
