"""
GreenScore Seed Data Initialization
Owned by Person 2 (Backend, Database, and GreenPoints)
"""

from database import init_db, get_db


def seed_data():
    """Seed initial demo users, campus bins, and optional initial demo reports."""
    init_db()

    users = [
        ("STU-001", "Demo Student", "student"),
        ("STU-002", "Demo Student 2", "student"),
        ("ADM-001", "Demo Administrator", "admin"),
    ]

    bins = [
        ("BIN-001", "Block A - Ground Floor", "General"),
        ("BIN-002", "Block A - First Floor", "Recyclable"),
        ("BIN-003", "Block B - Ground Floor", "General"),
        ("BIN-004", "Main Canteen", "Organic"),
        ("BIN-005", "Library Entrance", "Recyclable"),
        ("BIN-006", "Hostel Entrance", "General"),
    ]

    sample_reports = [
        (
            "REP-DEMO-001",
            "STU-001",
            "BIN-001",
            "Overflowing bin",
            "Bin is completely full and trash is overflowing onto the floor.",
            "Submitted",
        ),
        (
            "REP-DEMO-002",
            "STU-002",
            "BIN-004",
            "Incorrect segregation",
            "Plastic bottles disposed in organic waste bin.",
            "Under Review",
        ),
    ]

    with get_db() as conn:
        conn.executemany("""
            INSERT OR IGNORE INTO users (id, name, role)
            VALUES (?, ?, ?)
        """, users)

        conn.executemany("""
            INSERT OR IGNORE INTO bins (id, location, waste_category)
            VALUES (?, ?, ?)
        """, bins)


if __name__ == "__main__":
    seed_data()
    print("GreenScore demo data is ready.")
