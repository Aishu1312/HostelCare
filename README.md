# Hostel Complaint Registration Portal (HostelCare)

Built for **Web Warfare 2K26 — Round 2, Problem Statement 3**.

## Overview

HostelCare lets hostel students submit maintenance complaints and lets
admins move each complaint through a **Pending → In Progress → Resolved**
lifecycle. It is built with Streamlit and Firebase Firestore, using only
Google-technology infrastructure — no third-party AI APIs are called at
runtime.

## Problem Statement

> Hostel students log maintenance complaints and track their status.

The application satisfies all six official requirements:

1. **Complaint form** — Room Number, Category, Description, with full validation.
2. **Status field** — exactly one of `Pending`, `In Progress`, `Resolved`, using a single canonical constant set everywhere.
3. **List/table view** — auto-refreshing table of all complaints (ID, Room, Category, Description, Status, Timestamp).
4. **Filters** — by Category and Status, individually and combined (logical AND).
5. **Timestamp** — generated automatically server-side at creation; never user-entered.
6. **Admin status update** — updates exactly one complaint, identified by its immutable Firestore document ID.

## Features

- Dashboard with live KPI cards (Total / Pending / In Progress / Resolved), computed dynamically — never hardcoded.
- Complaint submission form with inline validation and a confirmation summary (ID, status, timestamp).
- Complaints table with category filter, status filter, and case-insensitive search by ID or room number.
- Admin panel to select a complaint and update its status, with immediate table refresh.
- Friendly error handling if Firebase is unreachable — the app never crashes or leaks credentials/stack traces.
- Duplicate-submission guard (short cooldown on identical resubmits, not a blanket lock).
- Accessible status display: color badge **and** text label **and** icon (never color alone).

## Technology Stack

| Layer       | Technology                          |
|-------------|--------------------------------------|
| UI          | Streamlit                            |
| Database    | Firebase Firestore (`firebase-admin`)|
| Fonts       | Google Fonts (Inter)                 |
| Language    | Python 3.10+                         |
| Testing     | pytest                               |

No OpenAI, ChatGPT, Claude, Anthropic, Copilot, Groq, or other non-Google
AI services are used or referenced by this application.

## Architecture

```
hostel-complaint-portal/
│
├── app.py                     # Streamlit UI: dashboard, form, list, admin, about
├── requirements.txt
├── README.md
├── .gitignore
├── .env.example
│
├── config/
│   └── firebase_config.py     # Cached, fault-tolerant Firestore client init
│
├── services/
│   ├── firebase_service.py    # All Firestore reads/writes; never raises
│   └── complaint_service.py   # Validation orchestration, filtering, stats
│
├── utils/
│   ├── validators.py          # Field-level input validation
│   ├── constants.py           # Single source of truth: statuses, categories
│   └── helpers.py             # Timestamp formatting, ID/search normalization
│
├── tests/
│   ├── test_validators.py
│   ├── test_filters.py
│   └── test_status.py
│
└── .streamlit/
    ├── config.toml
    └── secrets.toml.example
```

**Why this structure:** each layer has one job. `utils/constants.py` is the
single canonical source for status/category strings so the "in_progress"
vs "In Progress" bug class is structurally impossible — every other file
imports from it rather than typing literals. `services/firebase_service.py`
isolates all Firestore calls behind a `(success, result)` contract so the
UI layer never has to handle raw exceptions. `services/complaint_service.py`
holds pure, Firebase-free logic (filtering, search, stats) specifically so
it can be unit tested without a live database.

## Firebase Database Structure

Firestore collection `complaints`, one document per complaint. The
**Firestore document ID** is the complaint's unique, immutable identifier
— never a list index, row number, category, or room number.

```
complaints/
  {auto-generated document ID}/
    room_number:  string
    category:     string   # one of the canonical CATEGORY_OPTIONS
    description:  string
    status:       string   # one of "Pending" | "In Progress" | "Resolved"
    created_at:   timestamp
    updated_at:   timestamp
```

## Installation

```bash
git clone <your-repo-url>
cd hostel-complaint-portal
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Configuration

1. In the [Firebase Console](https://console.firebase.google.com/), create a project and enable **Firestore Database**.
2. Go to **Project Settings → Service Accounts → Generate new private key**. This downloads a JSON file — keep it private.
3. Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml`.
4. Fill in the `[firebase]` section using the values from the downloaded JSON file.
5. Confirm `.streamlit/secrets.toml` is listed in `.gitignore` (it is, by default) — never commit it.

## Running Locally

```bash
streamlit run app.py
```

The app opens at `http://localhost:8501`. If `.streamlit/secrets.toml` is
missing or invalid, the app still starts and shows a friendly "database
not connected" warning instead of crashing.

## Deployment

**Streamlit Community Cloud**

1. Push this repository to GitHub (real secrets excluded via `.gitignore`).
2. On [share.streamlit.io](https://share.streamlit.io), create a new app pointing at `app.py`.
3. In the app's **Settings → Secrets**, paste the contents of your local `.streamlit/secrets.toml`.
4. Deploy.

## Testing

```bash
pip install pytest
pytest tests/ -v
```

24 tests cover validation, filtering (including combined filters and
non-substring category matching), status canonicalization, and dashboard
stat computation. All pass against the current codebase.

## Bug Prevention

| # | Bug | Prevention |
|---|-----|------------|
| Easy 1 | Timestamp missing/wrong format | Timestamp generated server-side in `firebase_service.create_complaint`; never accepted from user input. |
| Easy 2 | New complaint not appearing | Write is read back and verified before "success" is reported; UI re-fetches from Firestore on every render (`st.rerun()` after mutations). |
| Easy 3 | Blank category allowed | `validators.validate_category` rejects empty/None and anything outside `CATEGORY_OPTIONS`. |
| Medium 1 | Status update not reflecting | `update_complaint_status` re-reads the document after writing and verifies the new value before reporting success; UI calls `st.rerun()`. |
| Medium 2 | Wrong category filtering (substring match) | `filter_complaints` uses exact normalized equality, never substring/`in` matching. |
| Medium 3 | Resolved shown under Pending | Same exact-equality filtering applies to status. |
| Hard 1 | Updating one complaint updates another | Firestore document ID (never index/room number) is the sole identifier for reads/updates. |
| Hard 2 | Combined filter fails | `filter_complaints` applies category and status conditions with logical AND; covered by `test_combined_filter_uses_logical_and`. |
| AI-Quirk | `"in_progress"` vs `"In Progress"` | All statuses come from `utils/constants.STATUS_OPTIONS`; nothing else in the codebase hardcodes a status string. |

## Known Limitations

- No authentication layer — the Admin Panel is reachable by anyone with the URL, matching the "don't add unreliable auth in the time limit" guidance in the brief.
- No pagination — the complaints table renders all matching rows; fine for a hackathon dataset, would need pagination at scale.
- No file/image attachments on complaints.

## Future Improvements

- Add lightweight admin authentication (e.g. a shared passcode) if time allows in a later round.
- Add pagination and sorting for large complaint volumes.
- Add email/notification hooks on status change.

## Team

_Add your team name and members here before submission._
