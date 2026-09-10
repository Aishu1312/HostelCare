"""
Covers Testing Checklist items 7-9, 17 and the AI-QUIRK BUG: canonical
status values are exact, single-source, and never aliased
(e.g. "in_progress" vs "In Progress").
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.complaint_service import get_dashboard_stats, update_status
from utils.constants import (
    STATUS_APPROVED,
    STATUS_OPTIONS,
    STATUS_PENDING,
    STATUS_RESOLVED,
)


def test_status_options_are_canonical_and_exact():
    assert STATUS_OPTIONS == ["Pending", "Approved", "Resolved"]
    # No lowercase/underscored aliases anywhere in the canonical list.
    for status in STATUS_OPTIONS:
        assert "_" not in status
        assert status[0].isupper()


def test_status_options_has_no_duplicates():
    assert len(STATUS_OPTIONS) == len(set(STATUS_OPTIONS))


class _FakeFirebaseService:
    """Minimal stand-in so update_status can be tested without Firestore."""

    def __init__(self):
        self.calls = []

    def update_complaint_status(self, complaint_id, new_status):
        self.calls.append((complaint_id, new_status))
        return True, {"complaint_id": complaint_id, "status": new_status}


def test_update_status_rejects_non_canonical_value():
    fake_service = _FakeFirebaseService()
    success, payload = update_status(fake_service, "CMP-1", "in_progress")
    assert success is False
    assert fake_service.calls == []  # Firebase must never be called with a bad value.


def test_update_status_accepts_canonical_value():
    fake_service = _FakeFirebaseService()
    success, payload = update_status(fake_service, "CMP-1", STATUS_APPROVED)
    assert success is True
    assert payload["status"] == STATUS_APPROVED
    assert fake_service.calls == [("CMP-1", STATUS_APPROVED)]


def test_dashboard_stats_computed_dynamically():
    complaints = [
        {"status": STATUS_PENDING},
        {"status": STATUS_PENDING},
        {"status": STATUS_APPROVED},
        {"status": STATUS_RESOLVED},
        {"status": STATUS_RESOLVED},
        {"status": STATUS_RESOLVED},
    ]
    stats = get_dashboard_stats(complaints)
    assert stats["total"] == 6
    assert stats[STATUS_PENDING] == 2
    assert stats[STATUS_APPROVED] == 1
    assert stats[STATUS_RESOLVED] == 3


def test_dashboard_stats_empty_list():
    stats = get_dashboard_stats([])
    assert stats["total"] == 0
    assert stats[STATUS_PENDING] == 0
