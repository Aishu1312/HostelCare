"""
Business logic layer sitting between the Streamlit UI and SQLiteService.

The filtering and stats functions here are pure (no Firebase, no
Streamlit) so they can be unit tested directly against plain dicts/lists —
see tests/test_filters.py and tests/test_status.py.
"""

from utils.constants import (
    FILTER_ALL_CATEGORY,
    FILTER_ALL_STATUS,
    STATUS_APPROVED,
    STATUS_OPTIONS,
    STATUS_PENDING,
    STATUS_RESOLVED,
)
from utils.helpers import normalize, normalize_for_search
from utils.validators import validate_complaint_data


def submit_complaint(db_service, room_number: str, category: str, description: str):
    """
    Validates then persists a new complaint.

    Returns (success: bool, payload) where payload is either the created
    complaint dict or a list of validation/database error strings.
    """
    is_valid, errors = validate_complaint_data(room_number, category, description)
    if not is_valid:
        return False, errors

    success, result = db_service.create_complaint(room_number, category, description)
    if not success:
        return False, [result]

    return True, result


def update_status(db_service, complaint_id: str, new_status: str):
    """Validates the target status against the canonical list, then delegates
    to SQLiteService. Returns (success, payload)."""
    if new_status not in STATUS_OPTIONS:
        return False, f"'{new_status}' is not a recognized status."

    success, result = db_service.update_complaint_status(complaint_id, new_status)
    if not success:
        return False, result

    return True, result


def filter_complaints(complaints: list, category_filter: str, status_filter: str):
    """
    Applies category and status filters with logical AND semantics
    (HARD BUG 2 prevention). Uses exact, normalized equality — never
    substring matching (MEDIUM BUG 2 / MEDIUM BUG 3 prevention).
    """
    category_active = category_filter != FILTER_ALL_CATEGORY
    status_active = status_filter != FILTER_ALL_STATUS

    result = []
    for complaint in complaints:
        if category_active and normalize(complaint.get("category")) != normalize(category_filter):
            continue
        if status_active and normalize(complaint.get("status")) != normalize(status_filter):
            continue
        result.append(complaint)

    return result


def search_complaints(complaints: list, query: str):
    """Case-insensitive search over complaint ID and room number."""
    query = normalize_for_search(query)
    if not query:
        return complaints

    result = []
    for complaint in complaints:
        complaint_id = normalize_for_search(complaint.get("complaint_id", ""))
        room_number = normalize_for_search(complaint.get("room_number", ""))
        if query in complaint_id or query in room_number:
            result.append(complaint)

    return result


def get_dashboard_stats(complaints: list) -> dict:
    """Computes KPI counts dynamically from live complaint data — never
    hardcoded (dashboard requirement)."""
    stats = {
        "total": len(complaints),
        STATUS_PENDING: 0,
        STATUS_APPROVED: 0,
        STATUS_RESOLVED: 0,
    }

    for complaint in complaints:
        status = complaint.get("status")
        if status in stats:
            stats[status] += 1

    return stats
