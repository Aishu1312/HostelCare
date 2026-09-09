"""
Firestore data-access layer.

Every public method returns a (success: bool, result_or_error) tuple and
NEVER lets a Firestore/network exception escape to the caller. This is
what makes "Firebase unavailable" a friendly warning instead of a crash
(EASY/MEDIUM bug-hunt requirement).

Firestore's own auto-generated document ID is used as the complaint's
unique, immutable identifier (HARD BUG 1 prevention) — never a list index,
row number, category, or room number.
"""

from utils.constants import COMPLAINTS_COLLECTION
from utils.helpers import get_current_utc_datetime


class FirebaseService:
    def __init__(self, client):
        # client may be None if Firebase failed to initialize; every method
        # below checks for that before touching Firestore.
        self.client = client

    def is_connected(self) -> bool:
        return self.client is not None

    def create_complaint(self, room_number: str, category: str, description: str):
        """Writes a new complaint. Returns (success, complaint_dict | error_str)."""
        if not self.is_connected():
            return False, "Database is not connected."

        try:
            now = get_current_utc_datetime()
            doc_ref = self.client.collection(COMPLAINTS_COLLECTION).document()

            complaint_data = {
                "room_number": room_number.strip(),
                "category": category.strip(),
                "description": description.strip(),
                "status": "Pending",
                "created_at": now,
                "updated_at": now,
            }

            doc_ref.set(complaint_data)

            # Verify the write succeeded by reading it back (EASY BUG 2
            # prevention: never assume a write succeeded silently).
            written = doc_ref.get()
            if not written.exists:
                return False, "Write verification failed. Please try again."

            result = written.to_dict()
            result["complaint_id"] = doc_ref.id
            return True, result

        except Exception as exc:
            return False, f"Failed to save complaint: {exc}"

    def get_all_complaints(self):
        """Returns (success, list_of_complaint_dicts | error_str)."""
        if not self.is_connected():
            return False, "Database is not connected."

        try:
            docs = (
                self.client.collection(COMPLAINTS_COLLECTION)
                .order_by("created_at", direction="DESCENDING")
                .stream()
            )

            complaints = []
            for doc in docs:
                data = doc.to_dict()
                data["complaint_id"] = doc.id
                complaints.append(data)

            return True, complaints

        except Exception as exc:
            return False, f"Failed to load complaints: {exc}"

    def update_complaint_status(self, complaint_id: str, new_status: str):
        """
        Updates ONLY the complaint matching complaint_id (the Firestore
        document ID). Firestore document references are scoped to a single
        document, so this can never accidentally touch another complaint
        (HARD BUG 1 prevention).

        Returns (success, updated_complaint_dict | error_str).
        """
        if not self.is_connected():
            return False, "Database is not connected."

        if not complaint_id:
            return False, "A valid complaint ID is required."

        try:
            doc_ref = self.client.collection(COMPLAINTS_COLLECTION).document(
                complaint_id
            )

            existing = doc_ref.get()
            if not existing.exists:
                return False, f"Complaint {complaint_id} was not found."

            doc_ref.update(
                {
                    "status": new_status,
                    "updated_at": get_current_utc_datetime(),
                }
            )

            # Verify the update actually took effect before reporting success.
            updated = doc_ref.get()
            updated_data = updated.to_dict()

            if updated_data.get("status") != new_status:
                return False, "Status update could not be verified."

            updated_data["complaint_id"] = complaint_id
            return True, updated_data

        except Exception as exc:
            return False, f"Failed to update complaint: {exc}"
