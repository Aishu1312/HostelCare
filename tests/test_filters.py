"""
Covers Testing Checklist items 10-13, 16 and HARD BUG 2 / MEDIUM BUG 2/3:
category filter, status filter, combined filter, multiple complaints,
resolved-vs-pending isolation, and exact (non-substring) category matching.
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.complaint_service import filter_complaints, search_complaints
from utils.constants import (
    FILTER_ALL_CATEGORY,
    FILTER_ALL_STATUS,
    STATUS_APPROVED,
    STATUS_PENDING,
    STATUS_RESOLVED,
)

SAMPLE_COMPLAINTS = [
    {"complaint_id": "CMP-1", "room_number": "201", "category": "Electrical", "status": STATUS_PENDING},
    {"complaint_id": "CMP-2", "room_number": "305", "category": "Plumbing", "status": STATUS_APPROVED},
    {"complaint_id": "CMP-3", "room_number": "112", "category": "Cleaning", "status": STATUS_RESOLVED},
    {"complaint_id": "CMP-4", "room_number": "201", "category": "Electrical", "status": STATUS_RESOLVED},
]


def test_no_filter_returns_all():
    result = filter_complaints(SAMPLE_COMPLAINTS, FILTER_ALL_CATEGORY, FILTER_ALL_STATUS)
    assert len(result) == 4


def test_category_filter_only():
    result = filter_complaints(SAMPLE_COMPLAINTS, "Electrical", FILTER_ALL_STATUS)
    assert len(result) == 2
    assert all(c["category"] == "Electrical" for c in result)


def test_category_filter_does_not_substring_match():
    # "Plumbing" must not accidentally match "Electrical" or vice versa.
    result = filter_complaints(SAMPLE_COMPLAINTS, "Plumbing", FILTER_ALL_STATUS)
    assert len(result) == 1
    assert result[0]["complaint_id"] == "CMP-2"


def test_status_filter_only():
    result = filter_complaints(SAMPLE_COMPLAINTS, FILTER_ALL_CATEGORY, STATUS_RESOLVED)
    assert len(result) == 2
    assert all(c["status"] == STATUS_RESOLVED for c in result)


def test_resolved_never_appears_under_pending_filter():
    result = filter_complaints(SAMPLE_COMPLAINTS, FILTER_ALL_CATEGORY, STATUS_PENDING)
    assert all(c["status"] != STATUS_RESOLVED for c in result)
    assert len(result) == 1
    assert result[0]["complaint_id"] == "CMP-1"


def test_combined_filter_uses_logical_and():
    # Electrical AND Resolved -> only CMP-4, not CMP-1 (Electrical/Pending)
    # and not CMP-3 (Cleaning/Resolved).
    result = filter_complaints(SAMPLE_COMPLAINTS, "Electrical", STATUS_RESOLVED)
    assert len(result) == 1
    assert result[0]["complaint_id"] == "CMP-4"


def test_combined_filter_no_matches():
    result = filter_complaints(SAMPLE_COMPLAINTS, "Security", STATUS_PENDING)
    assert result == []


def test_search_is_case_insensitive_on_id_and_room():
    result = search_complaints(SAMPLE_COMPLAINTS, "cmp-3")
    assert len(result) == 1
    assert result[0]["complaint_id"] == "CMP-3"

    result = search_complaints(SAMPLE_COMPLAINTS, "201")
    assert len(result) == 2


def test_empty_search_returns_all():
    result = search_complaints(SAMPLE_COMPLAINTS, "")
    assert len(result) == 4
