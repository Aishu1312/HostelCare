"""
Covers Testing Checklist items 1-4: empty room number, empty category,
empty description, and a valid complaint.
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.validators import validate_complaint_data


def test_empty_room_number_rejected():
    is_valid, errors = validate_complaint_data("", "Electrical", "The fan is not working at all.")
    assert is_valid is False
    assert any("room number" in e.lower() for e in errors)


def test_whitespace_only_room_number_rejected():
    is_valid, errors = validate_complaint_data("   ", "Electrical", "The fan is not working at all.")
    assert is_valid is False


def test_empty_category_rejected():
    is_valid, errors = validate_complaint_data("201", "", "The fan is not working at all.")
    assert is_valid is False
    assert any("category" in e.lower() for e in errors)


def test_invalid_category_rejected():
    is_valid, errors = validate_complaint_data("201", "Skydiving", "The fan is not working at all.")
    assert is_valid is False


def test_empty_description_rejected():
    is_valid, errors = validate_complaint_data("201", "Electrical", "")
    assert is_valid is False
    assert any("description" in e.lower() for e in errors)


def test_too_short_description_rejected():
    is_valid, errors = validate_complaint_data("201", "Electrical", "short")
    assert is_valid is False


def test_too_long_description_rejected():
    is_valid, errors = validate_complaint_data("201", "Electrical", "x" * 1000)
    assert is_valid is False


def test_valid_complaint_accepted():
    is_valid, errors = validate_complaint_data(
        "201", "Electrical", "The ceiling fan in room 201 makes a loud noise and needs repair."
    )
    assert is_valid is True
    assert errors == []


def test_none_values_rejected():
    is_valid, errors = validate_complaint_data(None, None, None)
    assert is_valid is False
    assert len(errors) == 3
