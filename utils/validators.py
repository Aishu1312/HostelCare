"""
Input validation for complaint submissions.

Every validator returns (is_valid: bool, error_message: str | None).
`validate_complaint_data` aggregates all field validators and is the single
entry point services/complaint_service.py should call before ever writing
to Firebase. Invalid input must never reach the database.
"""

from utils.constants import (
    CATEGORY_OPTIONS,
    MAX_DESCRIPTION_LENGTH,
    MAX_ROOM_NUMBER_LENGTH,
    MIN_DESCRIPTION_LENGTH,
    MIN_ROOM_NUMBER_LENGTH,
)


def validate_room_number(room_number: str):
    if room_number is None:
        return False, "Room number is required."

    cleaned = room_number.strip()

    if len(cleaned) == 0:
        return False, "Room number cannot be empty."

    if len(cleaned) > MAX_ROOM_NUMBER_LENGTH:
        return False, f"Room number cannot exceed {MAX_ROOM_NUMBER_LENGTH} characters."

    if len(cleaned) < MIN_ROOM_NUMBER_LENGTH:
        return False, "Room number cannot be empty."

    # Room numbers are typically alphanumeric (e.g. "201", "A-305").
    if not all(ch.isalnum() or ch in "-/ " for ch in cleaned):
        return False, "Room number contains invalid characters."

    return True, None


def validate_category(category: str):
    if category is None:
        return False, "Category is required."

    cleaned = category.strip()

    if len(cleaned) == 0:
        return False, "Category cannot be empty."

    if cleaned not in CATEGORY_OPTIONS:
        return False, "Category must be one of the approved categories."

    return True, None


def validate_description(description: str):
    if description is None:
        return False, "Description is required."

    cleaned = description.strip()

    if len(cleaned) == 0:
        return False, "Description cannot be empty."

    if len(cleaned) < MIN_DESCRIPTION_LENGTH:
        return False, f"Description must be at least {MIN_DESCRIPTION_LENGTH} characters."

    if len(cleaned) > MAX_DESCRIPTION_LENGTH:
        return False, f"Description cannot exceed {MAX_DESCRIPTION_LENGTH} characters."

    return True, None


def validate_complaint_data(room_number: str, category: str, description: str):
    """
    Aggregates all field validators.

    Returns (is_valid: bool, errors: list[str]).
    `errors` is empty when is_valid is True.
    """
    errors = []

    room_valid, room_error = validate_room_number(room_number)
    if not room_valid:
        errors.append(room_error)

    category_valid, category_error = validate_category(category)
    if not category_valid:
        errors.append(category_error)

    description_valid, description_error = validate_description(description)
    if not description_valid:
        errors.append(description_error)

    return len(errors) == 0, errors
