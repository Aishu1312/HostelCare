"""
SQLite data-access layer.

Replaces FirebaseService to run locally with SQLite.
Maintains the same interface: returns (success: bool, result_or_error) tuple.
"""

import sqlite3
import uuid
from utils.helpers import get_current_utc_datetime


class SQLiteService:
    def __init__(self, conn):
        self.conn = conn

    def is_connected(self) -> bool:
        return self.conn is not None

    def create_complaint(self, room_number: str, category: str, description: str):
        """Writes a new complaint. Returns (success, complaint_dict | error_str)."""
        if not self.is_connected():
            return False, "Database is not connected."

        try:
            now = get_current_utc_datetime()
            complaint_id = f"CMP-{str(uuid.uuid4())[:8].upper()}"

            complaint_data = {
                "complaint_id": complaint_id,
                "room_number": room_number.strip(),
                "category": category.strip(),
                "description": description.strip(),
                "status": "Pending",
                "created_at": now.isoformat(),
                "updated_at": now.isoformat(),
            }

            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO complaints 
                (complaint_id, room_number, category, description, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                complaint_data["complaint_id"],
                complaint_data["room_number"],
                complaint_data["category"],
                complaint_data["description"],
                complaint_data["status"],
                complaint_data["created_at"],
                complaint_data["updated_at"]
            ))
            self.conn.commit()

            return True, complaint_data

        except Exception as exc:
            return False, f"Failed to save complaint: {exc}"

    def get_all_complaints(self):
        """Returns (success, list_of_complaint_dicts | error_str)."""
        if not self.is_connected():
            return False, "Database is not connected."

        try:
            cursor = self.conn.cursor()
            # Order by created_at DESC (simulating Firestore behavior)
            cursor.execute('SELECT * FROM complaints ORDER BY created_at DESC')
            rows = cursor.fetchall()
            
            complaints = []
            for row in rows:
                complaints.append(dict(row))

            return True, complaints

        except Exception as exc:
            return False, f"Failed to load complaints: {exc}"

    def update_complaint_status(self, complaint_id: str, new_status: str):
        """
        Updates the status of a specific complaint.
        Returns (success, updated_complaint_dict | error_str).
        """
        if not self.is_connected():
            return False, "Database is not connected."

        if not complaint_id:
            return False, "A valid complaint ID is required."

        try:
            cursor = self.conn.cursor()
            
            # Check if exists
            cursor.execute('SELECT * FROM complaints WHERE complaint_id = ?', (complaint_id,))
            existing = cursor.fetchone()
            if not existing:
                return False, f"Complaint {complaint_id} was not found."

            now = get_current_utc_datetime().isoformat()
            
            cursor.execute('''
                UPDATE complaints
                SET status = ?, updated_at = ?
                WHERE complaint_id = ?
            ''', (new_status, now, complaint_id))
            self.conn.commit()

            # Verify and return updated
            cursor.execute('SELECT * FROM complaints WHERE complaint_id = ?', (complaint_id,))
            updated = cursor.fetchone()
            
            if not updated or updated["status"] != new_status:
                return False, "Status update could not be verified."

            return True, dict(updated)

        except Exception as exc:
            return False, f"Failed to update complaint: {exc}"
