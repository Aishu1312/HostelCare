"""
Firebase initialization.

Reads credentials from Streamlit secrets (st.secrets), never from a
hardcoded file or literal in source control. Returns None (instead of
raising) when secrets are missing/invalid so the rest of the app can show
a friendly error instead of crashing — see services/firebase_service.py.
"""

import json

import streamlit as st

try:
    import firebase_admin
    from firebase_admin import credentials, firestore
except ImportError:  # pragma: no cover - exercised only if dependency missing
    firebase_admin = None
    credentials = None
    firestore = None


@st.cache_resource(show_spinner=False)
def get_firestore_client():
    """
    Initializes (once, cached) and returns a Firestore client, or None if
    initialization fails for any reason. Callers MUST check for None and
    degrade gracefully rather than crashing the app.
    """
    if firebase_admin is None:
        return None

    try:
        if not firebase_admin._apps:
            if "firebase" not in st.secrets:
                return None

            service_account_info = dict(st.secrets["firebase"])

            # Streamlit secrets store multi-line private keys with escaped
            # newlines; restore real newlines before use.
            if "private_key" in service_account_info:
                service_account_info["private_key"] = service_account_info[
                    "private_key"
                ].replace("\\n", "\n")

            cred = credentials.Certificate(service_account_info)
            firebase_admin.initialize_app(cred)

        return firestore.client()

    except (KeyError, ValueError, json.JSONDecodeError, Exception):
        # Broad catch is intentional here: any credential/config problem
        # must degrade to "database unavailable", never a stack trace
        # shown to the user.
        return None
