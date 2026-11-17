# JobPilot AI — REST API Documentation

The backend service is built with FastAPI and runs on port `8000`.
All endpoints are namespaced under `/api/v1`.

## Health Check
- `GET /health`
  - Returns backend service health status and version.

---

## Candidate & Resume Endpoints (`/api/v1/candidate`)

### Upload Resume
- **POST** `/api/v1/candidate/upload-resume`
- **Request**: Multipart form-data with `file` (.pdf or .docx, max 10MB).
- **Response**: Extracted candidate text preview, candidate ID, and resume version.

### Candidate Profile
- **GET** `/api/v1/candidate/profile`
  - Returns the verified candidate profile, contact details, experience, and structured facts.
- **PUT** `/api/v1/candidate/profile`
  - Updates profile fields (name, phone, location, links).

### Job Preferences
- **GET** `/api/v1/candidate/preferences`
  - Returns target job titles, preferred locations, work types, and schedule.
- **PUT** `/api/v1/candidate/preferences`
  - Updates candidate search preferences and discovery frequency.

### Resumes List
- **GET** `/api/v1/candidate/resumes`
  - Returns all uploaded and generated resume versions with metadata.

---

## Job Discovery & Matching Endpoints (`/api/v1/jobs`)

### List Discovered Jobs
- **GET** `/api/v1/jobs/`
  - **Query Parameters**:
    - `page` (int, default 1)
    - `page_size` (int, default 20)
    - `min_score` (float, e.g. 70.0)
    - `location` (string)
    - `source` (e.g. `greenhouse`, `lever`)
    - `classification` (`strong`, `good`, `review`, `low`)
    - `search` (keyword)
  - **Response**: Paginated list of jobs with match score and classification.

### Job Details
- **GET** `/api/v1/jobs/{job_id}`
  - Returns complete job details, description, company details, required skills, and matching breakdown.

### Overview KPI Stats
- **GET** `/api/v1/jobs/stats/overview`
  - Returns total jobs discovered, new today, strong matches, applications prepared, pending approvals, and submitted count.

### Trigger Discovery Run
- **POST** `/api/v1/jobs/discover`
  - Initiates immediate scan of all watchlisted companies across active ATS connectors.

---

## Application Queue & Approvals (`/api/v1/applications`)

### List Applications
- **GET** `/api/v1/applications/`
  - **Query Parameters**: `status` (e.g. `pending_approval`, `submitted`)
  - Returns list of applications and current lifecycle stage.

### Application Details
- **GET** `/api/v1/applications/{application_id}`
  - Returns full application package, tailored resume, cover letter, prepared form answers, and validation results.

### Approve Application
- **POST** `/api/v1/applications/{application_id}/approve`
  - Explicit user approval required to transition application from `pending_approval` to `approved`.

### Reject Application
- **POST** `/api/v1/applications/{application_id}/reject`
  - Rejects application with optional reviewer notes.

---

## Company Watchlist (`/api/v1/companies`)

### List Companies
- **GET** `/api/v1/companies/`
  - Returns watchlisted companies, ATS platform type, careers URL, and last discovery timestamp.

### Seed Watchlist
- **POST** `/api/v1/companies/seed`
  - Populates initial 50-company watchlist into the database.

### Add Company
- **POST** `/api/v1/companies/`
  - Adds a new company to the watchlist with automatic ATS detection.

---

## Settings (`/api/v1/settings`)

### Get Current Configuration
- **GET** `/api/v1/settings/`
  - Returns LLM provider, discovery schedules, timezone, and environment info.
