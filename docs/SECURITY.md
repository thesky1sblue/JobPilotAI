# JobPilot AI — Security Architecture & Guidelines

Security is a foundational engineering requirement for JobPilot AI. This document outlines the safeguards implemented across the system.

## 1. Secrets & Credentials Management
- Zero secrets committed to version control.
- All API keys (`GEMINI_API_KEY`, `ANTHROPIC_API_KEY`, `SECRET_KEY`) are managed strictly via `.env` and environment variables.
- Git ignores `.env`, sqlite test databases, credentials, and uploaded files.

## 2. File Upload Safeguards
- Allowed upload formats are strictly restricted to PDF (`application/pdf`) and Word (`application/vnd.openxmlformats-officedocument.wordprocessingml.document`).
- Strict file size limit enforced (10 MB default, configurable via `MAX_UPLOAD_SIZE_MB`).
- Resumes are stored under dedicated isolated upload directories with UUID-generated file paths to prevent directory traversal and overwrite attacks.

## 3. Ground Truth Factual Grounding (Anti-Hallucination)
- The candidate's verified resume is the single source of truth.
- The `ResumeIntelligenceAgent` and `CoverLetterAgent` are strictly forbidden from fabricating qualifications, degrees, companies, achievements, or employment dates.
- Verified candidate facts are stored separately from unverified extracted information.

## 4. Human-In-The-Loop Approval Gates
- The system **never** automatically submits an application without explicit user sign-off.
- The LangGraph orchestrator enforces a hard `interrupt_before=["submit"]` checkpoint.
- Submissions require manual approval via `/api/v1/applications/{id}/approve` from the dashboard UI.
- All approval decisions, rejections, and review notes are logged immutably in `approvals` and `application_events`.

## 5. Untrusted Data Defenses
- External job postings, ATS HTML pages, and career descriptions are treated as untrusted third-party data.
- System prompts isolate job descriptions within delimited contexts, defending against indirect prompt injection.
- Plaintext sanitization and regex extraction prevent script injection when parsing HTML.

## 6. Access Controls & Anti-Abuse
- Connectors only interact with publicly documented, permitted GET endpoints (e.g., Greenhouse Boards API, Lever Postings API).
- The system strictly adheres to platform terms: no CAPTCHA solving, no MFA bypassing, and no unauthorized account scraping.
- Rate limiting and backoff exponential delays are enforced on HTTP clients.
