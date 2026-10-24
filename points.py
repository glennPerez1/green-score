"""
GreenScore GreenPoints System
Owned by Person 2 (Backend, Database, and GreenPoints)
"""

from database import get_db
from constants import ACTION_VERIFIED, ACTION_RESOLVED


def award_points(conn, user_id, report_id, action, points=5):
    """
    Insert a reward within the caller's transaction.
    Duplicate report/action rewards are ignored thanks to UNIQUE(report_id, action).
    Returns True if reward was inserted, False if it was already rewarded.
    """
    if action not in {ACTION_VERIFIED, ACTION_RESOLVED}:
        raise ValueError(f"Invalid points action: {action}. Must be '{ACTION_VERIFIED}' or '{ACTION_RESOLVED}'.")
    if points <= 0:
        raise ValueError("Points must be positive.")

    cursor = conn.execute("""
        INSERT OR IGNORE INTO points_ledger (
            user_id, report_id, action, points
        )
        VALUES (?, ?, ?, ?)
    """, (user_id, report_id, action, points))
    return cursor.rowcount == 1


def get_points_balance(user_id):
    """Calculate a student's total earned points."""
    with get_db() as conn:
        row = conn.execute("""
            SELECT COALESCE(SUM(points), 0) AS balance
            FROM points_ledger
            WHERE user_id = ?
        """, (user_id,)).fetchone()
        return int(row["balance"]) if row else 0


def get_points_ledger(user_id):
    """Get all GreenPoints transactions for a student in descending chronological order."""
    with get_db() as conn:
        rows = conn.execute("""
            SELECT id, user_id, report_id, action, points, created_at
            FROM points_ledger
            WHERE user_id = ?
            ORDER BY created_at DESC, id DESC
        """, (user_id,)).fetchall()
        return [dict(row) for row in rows]
