import os
import sqlite3
from contextlib import contextmanager

DB_PATH = os.getenv("DB_PATH", "greenscore.db")


@contextmanager
def get_db(db_path=None):
    """Open a database connection and manage transactions."""
    path = db_path or os.getenv("DB_PATH", DB_PATH)
    conn = sqlite3.connect(path, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db(db_path=None):
    """Create all GreenScore database tables."""
    with get_db(db_path) as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                role TEXT NOT NULL
                    CHECK(role IN ('student', 'admin')),
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS bins (
                id TEXT PRIMARY KEY,
                location TEXT NOT NULL,
                waste_category TEXT NOT NULL,
                active INTEGER NOT NULL DEFAULT 1
            );

            CREATE TABLE IF NOT EXISTS reports (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL REFERENCES users(id),
                bin_id TEXT NOT NULL REFERENCES bins(id),
                issue_type TEXT NOT NULL,
                description TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Submitted'
                    CHECK(status IN ('Submitted', 'Under Review', 'Verified', 'Rejected', 'Resolved')),
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                reviewed_at TEXT,
                resolved_at TEXT,
                reviewer_id TEXT REFERENCES users(id),
                admin_note TEXT DEFAULT ''
            );

            CREATE TABLE IF NOT EXISTS points_ledger (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL REFERENCES users(id),
                report_id TEXT NOT NULL REFERENCES reports(id),
                action TEXT NOT NULL
                    CHECK(action IN ('verified', 'resolved')),
                points INTEGER NOT NULL
                    CHECK(points > 0),
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                UNIQUE(report_id, action)
            );

            CREATE TABLE IF NOT EXISTS report_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                report_id TEXT NOT NULL REFERENCES reports(id),
                admin_id TEXT NOT NULL REFERENCES users(id),
                old_status TEXT NOT NULL,
                new_status TEXT NOT NULL,
                note TEXT DEFAULT '',
                changed_at TEXT NOT NULL DEFAULT (datetime('now'))
            );
        """)


def get_bins(active_only=True):
    """Fetch all bins, optionally filtering by active status."""
    with get_db() as conn:
        if active_only:
            rows = conn.execute("SELECT * FROM bins WHERE active = 1 ORDER BY id").fetchall()
        else:
            rows = conn.execute("SELECT * FROM bins ORDER BY id").fetchall()
        return [dict(row) for row in rows]


def get_reports(user_id=None, status=None):
    """
    Retrieve reports from the database.
    Can filter by user_id (for students) and/or status (for admin/dashboard).
    Returns a list of dicts.
    """
    query = """
        SELECT r.*, b.location AS bin_location, b.waste_category AS bin_waste_category
        FROM reports r
        LEFT JOIN bins b ON r.bin_id = b.id
        WHERE 1=1
    """
    params = []
    if user_id:
        query += " AND r.user_id = ?"
        params.append(user_id)
    if status:
        query += " AND r.status = ?"
        params.append(status)
    query += " ORDER BY r.created_at DESC"

    with get_db() as conn:
        rows = conn.execute(query, params).fetchall()
        return [dict(row) for row in rows]


def get_dashboard_stats():
    """Get status counts for the admin dashboard."""
    with get_db() as conn:
        rows = conn.execute("""
            SELECT status, COUNT(*) AS total
            FROM reports
            GROUP BY status
        """).fetchall()
    stats = {row["status"]: row["total"] for row in rows}
    return {
        "total": sum(stats.values()),
        "submitted": stats.get("Submitted", 0),
        "under_review": stats.get("Under Review", 0),
        "verified": stats.get("Verified", 0),
        "resolved": stats.get("Resolved", 0),
        "rejected": stats.get("Rejected", 0),
    }


def add_bin(bin_id, location, waste_category):
    """Register a new campus waste bin."""
    with get_db() as conn:
        conn.execute("""
            INSERT INTO bins (id, location, waste_category, active)
            VALUES (?, ?, ?, 1)
        """, (bin_id.strip(), location.strip(), waste_category.strip()))
    return True


def toggle_bin_status(bin_id, active):
    """Activate or deactivate an existing campus waste bin."""
    with get_db() as conn:
        conn.execute("""
            UPDATE bins
            SET active = ?
            WHERE id = ?
        """, (1 if active else 0, bin_id))
    return True


if __name__ == "__main__":
    init_db()
    print("GreenScore database initialized successfully.")
