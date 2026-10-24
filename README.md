# 🌱 GreenScore — Campus Waste Management & GreenPoints

[![Python](https://img.shields.io/badge/Python-3.12-brightgreen.svg)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.66-FF4B4B.svg)](https://streamlit.io)
[![Plotly](https://img.shields.io/badge/Plotly-7.0-blue.svg)](https://plotly.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> A campus sustainability and waste-management MVP that connects student crowdsourced reporting with administrative oversight and reward incentives.

---

## 📌 Project Overview

**GreenScore** simplifies campus waste management by giving students an easy way to report issues at waste bins (overflowing bins, incorrect segregation, damaged bins, or missed collections) using physical or simulated **QR codes**. 

Campus administrators oversee incoming issues, transition reports through an auditable verification and resolution lifecycle, and reward students with **GreenPoints**. Real-time dashboards and analytics display campus hotspots, issue frequency, and sustainability metrics.

---

## 🔑 Hackathon Demo Credentials

For live evaluation, testing, and judge demonstrations:

### 🛡️ Administrator Portal
*Access via the **`🛡️ Admin Access`** tab:*
- **Admin PIN:** `admin123` *(displayed on-screen for evaluator convenience)*
- **User ID:** `ADM-001`
- **Email:** `admin@greenscore.edu`
- **Capabilities:** Review queue, report verification (+5 pts), issue resolution (+5 pts), rejection, audit logs, hotspot analytics, and bin QR management.

### 🎓 Pre-Configured Student Profiles
*Access via the **`🎓 Student Login`** tab (log in using Student ID or Email + PIN `1234`):*

| Student Name | Student ID | Email | PIN | Department | Hostel (Bhawan) | Initial Badge |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Gagandeep Singh** | `STU-001` | `gagan@gmail.com` | **`1234`** | Mechanical Engineering | Vigyan Bhawan | Eco Champion 🌟 |
| **Ronak Das** | `STU-002` | `ronak@gmail.com` | **`1234`** | Mechanical Engineering | Vigyan Bhawan | Active Scout 🌿 |
| **Sameer Raj** | `STU-003` | `sameer@gmail.com` | **`1234`** | Mechanical Engineering | Jawahar Bhawan | Green Contributor 🌱 |

### ✨ Self-Registration for New Students
*Access via the **`✨ New Student Sign Up`** tab:*
- Register with any **Full Name**, **Student ID**, and **Email Address** (**unrestricted email domains** — not limited to `@iitr.ac.in`).
- Set a personal 4-digit security PIN.
- Instant automatic authentication into their personalized reporting dashboard.

---

## 🚀 Key User Journeys

### 1. 🔐 Role-Based Authentication Gateway (`app.py`)
- **Gated Admin Access:** Protected by the Admin Security PIN (`admin123`). Unauthorized students cannot access or manipulate the review queue.
- **Student Authentication:** Secure PIN verification for existing and newly registered accounts.
- **Unrestricted Email Domain:** Any valid email domain can be used to create accounts.
- **Session Isolation & Sign Out:** Dedicated user profile card and one-click session sign out in the sidebar.

### 2. 🎓 Students (`student_ui.py`)
- **QR Code Scanning & Preselection:** Mobile camera scan or simulation link (`/?bin_id=BIN-001`) automatically routes to the student reporting portal with the target bin pre-selected.
- **Issue Submission:** Pick from standardized categories (*Overflowing bin*, *Incorrect segregation*, *Damaged bin*, *Missed collection*, *Other waste issue*), provide context, and submit.
- **Duplicate Report Guard:** Prevents duplicate reports for the same bin and same issue type until the active report is resolved.
- **Optional Photo Proof:** Attach real-time photographs or simulated camera uploads as visual evidence.
- **My Reports History:** Track report progress through visual lifecycle bars (`Submitted` → `Under Review` → `Verified` → `Resolved`).
- **GreenPoints Wallet & Ledger:** View live points balance and inspect a detailed transaction ledger for all earned rewards.

### 3. 🛡️ Campus Administrators (`dashboard.py` & `analytics.py`)
- **Operations Dashboard:** Live KPI metrics for Total Reports, Submitted, Under Review, Verified, Resolved, and Total GreenPoints Awarded.
- **Report Review Queue:** Filter reports by status, category, or bin. Inspect descriptions, uploaded photo proof, and timestamps.
- **Status Transition Workflow:** Move reports through strictly enforced states:
  - `Submitted` ➔ `Under Review`
  - `Under Review` ➔ `Verified` (+5 pts awarded) OR `Rejected` (0 pts)
  - `Verified` ➔ `Resolved` (+5 pts awarded)
- **Audit History Trail:** Inspect who changed report statuses, when, and read administrator notes.
- **Interactive Visual Analytics:** Rich Plotly charts for status distributions, category frequency, campus hotspot bins, and daily submission timelines.
- **Bins Directory & QR Tag Generator:** Inspect all registered bins and generate high-resolution QR tags.

### 4. 🌱 GreenPoints Reward Policy (`points.py`)
- **+5 GreenPoints** when an administrator verifies a report on-site.
- **+5 GreenPoints** when the waste issue is completely resolved.
- **0 Points** for pending, unverified, or rejected reports.
- **Duplicate Protection:** Unique constraints (`report_id`, `action`) prevent duplicate points allocations even if actions are repeated.

---

## 👥 Team Ownership & Structure

Our team coordinated through a shared [`CONTRACT.md`](file:///home/p1k4-chu/user/project/green-score/CONTRACT.md):

| Team Member | Domain | Owned Modules |
|---|---|---|
| **Person 1** | Student Experience & QR Codes | `student_ui.py`, `qr_utils.py` |
| **Person 2** | Database, Services, & GreenPoints | `database.py`, `report_service.py`, `points.py`, `seed_data.py`, `constants.py`, `test_backend.py` |
| **Person 3** | App Entry, Admin Dashboard, Analytics, Deployment | `app.py`, `dashboard.py`, `analytics.py`, `requirements.txt`, `README.md` |

---

## 🛠️ Technology Stack

- **Runtime:** Python `3.12.14` (Compatible with Python `3.12.10+`)
- **Application Framework:** Streamlit `1.66.1`
- **Database:** SQLite with foreign keys and ACID transactions
- **Visualizations:** Plotly `7.0.0` & Pandas `3.1.0`
- **QR Generation:** `qrcode 8.2` with `Pillow 13.0.0`
- **Hosting & Deployment:** Render Cloud Platform

---

## 💻 Local Setup & Execution

### Option A: Using Conda (Recommended)

If the `green_score` conda environment is available:

```bash
conda activate green_score
streamlit run app.py
```

### Option B: Using Virtual Environment

```bash
# 1. Clone repository
git clone https://github.com/glennPerez1/green-score.git
cd green-score

# 2. Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run application
streamlit run app.py
```

Access the app in your browser at `http://localhost:8501`.

---

## 🧪 Running Backend & Integration Tests

The test suite validates database initialization, report creation, duplicate submission rejection, non-admin security guards, illegal status transition guards, GreenPoints reward logic, duplicate reward prevention, and dashboard metrics:

```bash
python test_backend.py
```

Expected output:
```text
============================================================
Starting GreenScore Backend Tests...
============================================================
[Test 1] Initializing database and running seed_data()...
PASS: Database initialized and seeded with 4 users and 6 bins.
...
ALL BACKEND TESTS PASSED SUCCESSFULLY! (13/13)
============================================================
```

---

## ☁️ Deployment on Render

### Render Configuration

1. **Create Web Service:** Connect your GitHub repository to [Render](https://render.com).
2. **Environment:** `Python 3`
3. **Build Command:**
   ```bash
   pip install -r requirements.txt
   ```
4. **Start Command:**
   ```bash
   streamlit run app.py --server.port $PORT --server.address 0.0.0.0
   ```
5. **Environment Variables:**
   - `PORT`: (Set automatically by Render)
   - `APP_BASE_URL`: Live service URL (`https://green-score-9orq.onrender.com`) used when generating QR codes.
   - `DB_PATH`: Path to SQLite database (defaults to `greenscore.db`).

### ⚠️ Database Persistence on Render & Trade-Offs

| Strategy | Advantages | Limitations | Recommended Use |
|---|---|---|---|
| **Render Free Tier (Default SQLite)** | Zero infrastructure cost; boots instantly; auto-seeded on launch via `ensure_database_ready()`. | Ephemeral filesystem: database resets on spin-down or new deployment. | Hackathon demo and judge evaluations. |
| **Render Paid Web Service + Persistent Disk** | Preserves SQLite records permanently across container restarts by setting `DB_PATH=/var/data/greenscore.db`. | Requires Render paid tier ($7/mo instance + $0.25/GB disk). | Campus pilot deployment. |
| **Managed PostgreSQL (Supabase / Render Postgres)** | Multi-instance concurrency, backups, and permanent persistence. | Requires minor DB connection adapter refactoring. | Full campus production. |

---

## 📱 QR Code Simulation

To test QR code handling without a physical camera:
1. Open the student portal or access `https://green-score-9orq.onrender.com/?bin_id=BIN-002` (or `http://localhost:8501/?bin_id=BIN-002` locally).
2. The application automatically switches into Student Reporting mode with **BIN-002 (Block A - First Floor)** pre-selected.
3. Or visit the **Demo QR Bins** tab in the student portal and click **"Simulate Scan"** on any bin.

---

## 🔒 Shared Contract Principles

- Report statuses follow the strict workflow: `Submitted` ➔ `Under Review` ➔ `Verified` ➔ `Resolved` (or `Rejected`).
- All functions strictly adhere to the contracts defined in [`CONTRACT.md`](file:///home/p1k4-chu/user/project/green-score/CONTRACT.md).
- Single source of truth for database schema and reward rules in backend services.
