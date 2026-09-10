"""
Single source of truth for every constant used across the application.

CRITICAL RULE (AI-QUIRK BUG PREVENTION):
Every layer of the app (UI, Firebase writes, filters, admin updates,
validation, tests) MUST import these constants instead of re-typing
string literals. Never write "in_progress", "pending", etc. anywhere
else in the codebase.
"""

# ---------------------------------------------------------------------------
# Canonical status values
# ---------------------------------------------------------------------------
STATUS_PENDING = "Pending"
STATUS_APPROVED = "Approved"
STATUS_RESOLVED = "Resolved"

# Ordered so the admin panel can present a logical Pending -> In Progress ->
# Resolved progression.
STATUS_OPTIONS = [STATUS_PENDING, STATUS_APPROVED, STATUS_RESOLVED]

# Icon + color kept alongside status text so the UI never relies on color
# alone (accessibility requirement).
STATUS_ICONS = {
    STATUS_PENDING: "🟡",
    STATUS_APPROVED: "🔵",
    STATUS_RESOLVED: "🟢",
}

STATUS_BADGE_COLORS = {
    STATUS_PENDING: "#F59E0B",      # warning
    STATUS_APPROVED: "#2563EB",  # primary
    STATUS_RESOLVED: "#16A34A",     # success
}

# ---------------------------------------------------------------------------
# Canonical category values
# ---------------------------------------------------------------------------
CATEGORY_ELECTRICAL = "Electrical"
CATEGORY_PLUMBING = "Plumbing"
CATEGORY_CLEANING = "Cleaning"
CATEGORY_FURNITURE = "Furniture"
CATEGORY_INTERNET = "Internet/Wi-Fi"
CATEGORY_WATER_SUPPLY = "Water Supply"
CATEGORY_SECURITY = "Security"
CATEGORY_OTHER = "Other"

CATEGORY_OPTIONS = [
    CATEGORY_ELECTRICAL,
    CATEGORY_PLUMBING,
    CATEGORY_CLEANING,
    CATEGORY_FURNITURE,
    CATEGORY_INTERNET,
    CATEGORY_WATER_SUPPLY,
    CATEGORY_SECURITY,
    CATEGORY_OTHER,
]

# ---------------------------------------------------------------------------
# Filter sentinel values
# ---------------------------------------------------------------------------
FILTER_ALL_CATEGORY = "All Categories"
FILTER_ALL_STATUS = "All Statuses"

CATEGORY_FILTER_OPTIONS = [FILTER_ALL_CATEGORY] + CATEGORY_OPTIONS
STATUS_FILTER_OPTIONS = [FILTER_ALL_STATUS] + STATUS_OPTIONS

# ---------------------------------------------------------------------------
# Validation limits
# ---------------------------------------------------------------------------
MIN_ROOM_NUMBER_LENGTH = 1
MAX_ROOM_NUMBER_LENGTH = 10
MIN_DESCRIPTION_LENGTH = 10
MAX_DESCRIPTION_LENGTH = 500

# ---------------------------------------------------------------------------
# Firestore collection name
# ---------------------------------------------------------------------------
COMPLAINTS_COLLECTION = "complaints"

# ---------------------------------------------------------------------------
# Timestamp display format
# ---------------------------------------------------------------------------
TIMESTAMP_DISPLAY_FORMAT = "%d %b %Y, %I:%M %p"

# ---------------------------------------------------------------------------
# Misc UI
# ---------------------------------------------------------------------------
APP_TITLE = "HostelCare — Complaint Registration Portal"
DUPLICATE_SUBMISSION_COOLDOWN_SECONDS = 5
