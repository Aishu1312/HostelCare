"""
SQLite database initialization and configuration.
"""

import sqlite3
import streamlit as st

DB_NAME = "hostelcare.db"

def init_db():
    """Initialize the SQLite database and create the complaints table if it doesn't exist."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS complaints (
            complaint_id TEXT PRIMARY KEY,
            room_number TEXT NOT NULL,
            category TEXT NOT NULL,
            description TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TIMESTAMP NOT NULL,
            updated_at TIMESTAMP NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

@st.cache_resource(show_spinner=False)
def get_db_connection():
    """
    Returns a cached SQLite connection.
    """
    init_db()
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn
