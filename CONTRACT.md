
# GreenScore Shared Contract

## 1. Project Overview

GreenScore is a campus waste management application built using Python and Streamlit. Students can report waste-related issues using bin QR codes, track report statuses, and earn GreenPoints. Administrators can review reports and view analytics.

## 2. Technology Stack

- Python: 3.12.10
- Frontend and application: Streamlit
- Data processing: Pandas
- Charts: Plotly
- QR code generation: qrcode and Pillow
- Database: SQLite initially, unless the team agrees otherwise
- Deployment: Render
- Dependencies: requirements.txt

All team members must use Python 3.12.10 and install dependencies using:

```bash
python -m pip install -r requirements.txt
```

## 3. Naming Conventions

Use these names consistently across shared functions, database columns, and modules.

| Meaning | Standard name |
|---|---|
| Student/user ID | user_id |
| Admin ID | admin_id |
| Bin ID | bin_id |
| Report ID | report_id |
| Issue category | issue_type |
| Issue description | description |
| Report status | status |
| Creation timestamp | created_at |
| Review timestamp | reviewed_at |
| Resolution timestamp | resolved_at |
| Reviewer ID in database | reviewer_id |
| Admin note | admin_note |
| Points balance | points_balance |
| Bin location | location |
| Waste category of bin | waste_category |

The users table uses `id` as its primary key. Other tables reference that value through `user_id`, `admin_id`, or other appropriate foreign keys.

Use snake_case for Python functions, variables, and database columns.

## 4. Shared Report Statuses

Use these exact status values:

- Submitted
- Under Review
- Verified
- Rejected
- Resolved

Do not introduce alternative status names such as Pending or Completed without team agreement.

Expected workflow:

Submitted → Under Review → Verified → Resolved

A report may instead be rejected after review.

Only verified reports may be resolved. Rejected reports cannot earn GreenPoints.

## 5. Shared Constants

Person 2 owns `constants.py`.

It must define:

```python
ROLE_STUDENT = "student"
ROLE_ADMIN = "admin"

STATUS_SUBMITTED = "Submitted"
STATUS_UNDER_REVIEW = "Under Review"
STATUS_VERIFIED = "Verified"
STATUS_REJECTED = "Rejected"
STATUS_RESOLVED = "Resolved"

POINTS_FOR_VERIFICATION = 5
POINTS_FOR_RESOLUTION = 5

ISSUE_TYPES = [
    "Overflowing bin",
    "Incorrect segregation",
    "Damaged bin",
    "Missed collection",
    "Other waste issue",
]
```

Use these constants instead of duplicating status strings and reward values across modules.

## 6. Database Schema Ownership

Person 2 is the sole owner of database schema changes and database initialization.

### users

- id
- name
- role
- created_at

### bins

- id
- location
- waste_category
- active

### reports

- id
- user_id
- bin_id
- issue_type
- description
- status
- created_at
- reviewed_at
- resolved_at
- reviewer_id
- admin_note

### points_ledger

- id
- user_id
- report_id
- action
- points
- created_at

Use primary keys, foreign keys, and appropriate uniqueness constraints.

All report and points data must be stored through the shared backend functions. Do not create a second database or duplicate business logic in the UI.

If a new column or table is needed, discuss it with the team and let Person 2 implement the change.

## 7. Shared Backend Function Signatures

Person 2 owns the implementations of these functions.

In `database.py`:

```python
def init_db():
    ...

def get_bins(active_only=True):
    ...

def get_reports(user_id=None, status=None):
    ...

def get_dashboard_stats():
    ...
```

In `report_service.py`:

```python
def create_report(
    user_id,
    bin_id,
    issue_type,
    description
):
    ...

def transition_report(
    report_id,
    admin_id,
    new_status,
    note=""
):
    ...
```

In `points.py`:

```python
def get_points_balance(user_id):
    ...

def get_points_ledger(user_id):
    ...
```

The signatures above are shared contracts, not implementations. Replace the placeholder bodies with real code.

Person 1 and Person 3 must import and call these functions rather than implementing competing versions.

Do not change function names, parameter names, or return formats without informing the team.

## 8. GreenPoints Business Rules

- Award 5 points when a report is verified.
- Award an additional 5 points when the verified report is resolved.
- Rejected reports earn zero points.
- Submitted reports earn no points.
- Each qualifying reward can be awarded only once per report and action.
- Store reward transactions in `points_ledger`.
- Calculate the balance from the ledger or a consistent backend-maintained balance.
- Reward updates and report status changes must be handled safely to prevent duplicate awards.

## 9. File Ownership

### Person 1: Student Interface

- `student_ui.py`
- `qr_utils.py`

Responsibilities:
- Student reporting interface
- Bin selection
- QR code generation and handling
- Report history
- GreenPoints display

Required interface:

```python
def render_student_ui():
    ...
```

### Person 2: Backend

- `database.py`
- `seed_data.py`
- `report_service.py`
- `points.py`
- `constants.py`
- `test_backend.py`

Responsibilities:
- Database schema and initialization
- Seed data
- Report creation and retrieval
- Status transitions
- GreenPoints ledger and reward logic
- Backend tests

### Person 3: Application, Analytics and Deployment

- `app.py`
- `dashboard.py`
- `analytics.py`
- `requirements.txt`
- `CONTRACT.md`
- `README.md`

Responsibilities:
- Application entry point and navigation
- Admin dashboard
- Analytics and charts
- Integration of shared modules
- Dependency management
- Render deployment
- End-to-end testing

## 10. Integration Rules

- Each person edits their assigned files.
- All modules must use the shared names and function signatures.
- UI modules must not contain independent database or reward logic.
- Dashboard metrics must use stored data after integration.
- Temporary demo data must be clearly identified as simulated.
- Imports must use the actual agreed module and function names.
- Test the application after integrating each major module.
- Resolve interface changes through team discussion.

## 11. GitHub Rules

- Use one shared GitHub repository.
- Keep `main` in a working state.
- Use separate feature branches when practical:
  - `feature/student-ui`
  - `feature/backend`
  - `feature/dashboard`
- Commit small, working changes frequently.
- Pull the latest changes before starting integration.
- Do not commit `.venv/`, `.env`, credentials, secrets, or database files.
- Add appropriate exclusions to `.gitignore`.

## 12. Deployment Rules

- The deployed entry point is `app.py`.
- Render must use Python 3.12.10 where supported.
- Install dependencies from `requirements.txt`.
- Bind Streamlit to Render's supplied port and `0.0.0.0`.
- Use the configured live application URL when generating production QR codes.
- Keep credentials in environment variables, not source code.
- Choose and configure a persistent database strategy before promising data persistence.
- Test the complete report lifecycle on the deployed application.

## 13. Definition of Done

The MVP is ready when:

1. A student can submit a report against a registered bin.
2. The report is stored and appears in the student's report history.
3. An admin can review, verify, reject, and resolve eligible reports.
4. GreenPoints are awarded according to the agreed rules without duplicates.
5. Dashboard metrics and charts reflect stored records.
6. QR codes open the correct bin reporting page.
7. The application runs locally using the agreed Python environment.
8. The deployed Render application passes an end-to-end test.
9. All three team members can integrate their modules using the shared contract.

Any changes to this contract must be communicated to all team members before implementation.
