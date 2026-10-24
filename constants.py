"""
GreenScore Shared Constants
Owned by Person 2 (Backend, Database, and GreenPoints)
"""

# User Roles
ROLE_STUDENT = "student"
ROLE_ADMIN = "admin"

# Report Statuses
STATUS_SUBMITTED = "Submitted"
STATUS_UNDER_REVIEW = "Under Review"
STATUS_VERIFIED = "Verified"
STATUS_REJECTED = "Rejected"
STATUS_RESOLVED = "Resolved"

ALL_STATUSES = [
    STATUS_SUBMITTED,
    STATUS_UNDER_REVIEW,
    STATUS_VERIFIED,
    STATUS_REJECTED,
    STATUS_RESOLVED,
]

# GreenPoints Reward Policy
POINTS_FOR_VERIFICATION = 5
POINTS_FOR_RESOLUTION = 5

ACTION_VERIFIED = "verified"
ACTION_RESOLVED = "resolved"

# Standard Issue Categories
ISSUE_TYPES = [
    "Overflowing bin",
    "Incorrect segregation",
    "Damaged bin",
    "Missed collection",
    "Other waste issue",
]

# Duplicate report detection window (in minutes)
DUPLICATE_WINDOW_MINUTES = 15
