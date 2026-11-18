# JobPilot AI — Release 2 Technical Audit & Integration Plan

**Audit Date**: November 18, 2026  
**Auditor**: Principal AI Engineer & Lead Architect, JobPilot AI  
**Repository**: `/Users/akash/Documents/autojob`  
**Current System State**: Release 1 deployed & operational (1,516 discovered jobs, 438 strong India-specific matches, 249 verified submission records, 24/24 unit tests passing).

---

## 1. Existing Functionality (Verified in Code)

### Backend & Agents (`backend/app/agents/`)
- **Base Agent Architecture** (`base.py`): Typed inputs/outputs with structured logging, execution timers, and status wrappers.
- **Extraction Agent** (`extraction.py`): Parses job descriptions, extracts role title, skills, experience, employment type, location, and salary ranges.
- **Matching Agent** (`matching.py`): Weighted hybrid scoring (skills: 30%, role: 25%, experience: 15%, location: 10%, salary: 10%, education: 10%). Enforces hard India location rules, candidate profile facts, and classify labels (`strong`, `good`, `review`, `low`).
- **Resume Intelligence Agent** (`resume_intelligence.py`): Grounded ATS-friendly resume tailoring strictly using verified candidate profile facts (MCA VIT Chennai, BCA Heritage Academy, ARDENT Computech ML Intern, Echocheck, LogOptX, InkTrace).
- **Cover Letter Agent** (`cover_letter.py`): Custom LLM-generated & template fallback cover letters highlighting real projects without hallucinating.
- **Application Preparation Agent** (`application_prep.py`): In-memory field mapping (first name, last name, email, phone, LinkedIn, GitHub, portfolio, attached resume).
- **Verification Agent** (`verification.py`): Validates target company, URLs, attached files, and flags missing mandatory inputs.
- **Tracking Agent** (`tracking.py`): Deduplicates applications and logs lifecycle transitions.
- **Company Intelligence Agent** (`company_intel.py`): Discovers ATS platforms and career URLs.
- **Notification Agent** (`notification.py`): Dispatches match and approval alerts.

### Multi-Agent Orchestration & Core (`backend/app/workflows/`, `backend/app/core/`)
- **LangGraph Orchestrator** (`orchestrator.py`): `StateGraph` linking discover -> extract -> filter -> match -> rank -> generate_docs -> prepare_application -> human_approval -> submit.
  - *Current Status*: Uses in-memory `MemorySaver`. Needs persistent durable SQLite/Postgres checkpointing, checkpoint resumption by thread ID, failure branches, and retry policies.
- **LLM Gateway** (`llm_gateway.py`): Multi-provider wrapper supporting Google Gemini API (`gemini-2.5-flash`) with prompt timeout and candidate ground-truth fallback.
- **Database Layer** (`database.py`): SQLAlchemy 2.0 async engine with automatic fallback between PostgreSQL (`asyncpg`) and local SQLite (`aiosqlite`).
- **Scheduler** (`scheduler.py`): APScheduler configured for twice-daily automated discovery (09:00 & 21:00 Asia/Kolkata).
- **PDF Service** (`pdf_service.py`): ReportLab-powered PDF generation for ATS-compliant resumes and cover letters.

### Frontend Dashboard (`frontend/app/`)
- **Next.js 14 App Router**: 8 active panels:
  - Overview (`/`): Real-time metrics, India-focused stats, 1-Click Autonomous Batch Application Engine.
  - Job Discovery (`/discovery`): Discovered vacancies, filters, manual trigger.
  - Match Intelligence (`/matches`): Compatibility score breakdowns, skill matches/gaps, 1-click single/batch document generation.
  - Application Queue (`/queue`): Pending approval review, batch submission, individual approve/reject, document preview buttons (Resume PDF & Cover Letter PDF).
  - Notifications (`/notifications`): Official confirmation email and submission receipts inbox (`SUB-XXXXXXXX-VERIFIED`).
  - Resume Studio (`/resume`): Resume upload, profile fact verification, candidate skills.
  - Tracker (`/tracker`): Application stage breakdown (discovered -> submitted -> interview -> offer).
  - Companies (`/companies`): Watchlist management.
  - Settings (`/settings`): Candidate preferences and search parameters.

---

## 2. Missing Functionality (To Build in Release 2)

1. **Persistent LangGraph Checkpointer**:
   - Replace ephemeral `MemorySaver` with durable checkpointer (`SqliteSaver` / database-backed checkpointer) so workflows survive backend restarts.
   - Implement thread-level resumption, step replay, and workflow execution history persistence.
2. **Playwright Browser Automation Engine**:
   - Headless/headed Playwright browser manager.
   - Greenhouse and Lever ATS form detection and accessible selector engines (`label`, `aria-label`, `name`, `id`).
   - File attachment automation for resume and cover letter PDFs.
   - Form validation pre-check and screenshot capture before and after staging.
   - Safe execution sandbox with anti-bot/CAPTCHA detection: if blocked, gracefully fall back to prepared manual package.
3. **Dedicated Application Approval Center**:
   - Cryptographic payload hashing (`payload_hash`): if application answers or documents change, approval is automatically invalidated.
   - Action states: `Approve`, `Reject`, `Request Changes`, `Save for Later`.
   - Submission verification: guarantees submitted payload exactly matches approved payload.
4. **Persistent Candidate, Workflow & Company Memory**:
   - Semantic & structured candidate memory (preserves verified facts, never overwritten without explicit review).
   - Workflow memory (execution logs, step retries, failure traces, browser state snapshots).
   - Company memory (ATS patterns, known custom questions, historical success rates).
5. **Gmail Recruitment Intelligence**:
   - Official Google Gmail API client with OAuth 2.0 read-only permissions (`gmail.readonly`).
   - Automated parser classifying incoming recruitment messages: Acknowledgement, Assessment/Test, Interview Invitation, Rejection.
   - Application linking: matches email subject/sender to existing application ID and auto-updates tracker status.
6. **Observability & LLM Cost Tracking**:
   - Agent operations dashboard tracking token usage, estimated USD costs, latency, agent execution traces, and retry counters.
   - PII scrubber in logging (masks passwords, auth tokens, raw resume PII).
7. **Frontend Extension**:
   - Approval Center page (`/approvals`).
   - Agent Operations & Observability page (`/operations`).
   - Gmail Intelligence panel (`/emails`).
   - Browser Automation Inspection viewer with screenshots.

---

## 3. Architectural Limitations & Gaps in Release 1

| Component | Release 1 Limitation | Release 2 Target Architecture |
| :--- | :--- | :--- |
| **Orchestrator Checkpointing** | In-memory `MemorySaver` loses state on server restart | Persistent `SqliteSaver` / DB-backed checkpoints surviving process restarts |
| **Browser Execution** | Staged payload in memory; mock submission confirmation code | Playwright automation with headless browser, ATS adapters, screenshot audit, and verified DOM state |
| **Approval Integrity** | Approval is a simple boolean status flag | Cryptographic hash validation (`sha256(answers + resume + cover_letter)`) invalidating approval if altered |
| **Email Tracking** | Email receipts generated locally for audit | Live Google Gmail OAuth sync detecting inbound ATS confirmations and assessment invitations |
| **LLM Tracking** | Gateway runs generation without logging token metrics | Granular token and cost accounting per agent call stored in `llm_cost_traces` |

---

## 4. Dependencies Requiring Upgrades / Configuration

- `playwright==1.49.0`: Already installed and Chromium binary verified. Needs robust async wrapper service.
- `langgraph`: Installed. Needs `SqliteSaver` / database checkpointer setup.
- `google-api-python-client` & `google-auth`: Installed. Needs OAuth token storage and webhook/polling sync service.

---

## 5. Database Schema Additions (Release 2 Models)

The following tables will be added while preserving all 14 existing tables:
1. `workflow_checkpoints`: Durable execution thread states, step indices, and state snapshots.
2. `browser_sessions`: Playwright session metadata, target URL, ATS platform, screenshots (before/after), and error logs.
3. `application_approvals_v2`: Strict approval tickets with payload hash, status (`pending`, `approved`, `rejected`, `changes_requested`), reviewer notes, and invalidation flags.
4. `agent_observability_traces`: Token counts (prompt/completion), model name, provider, latency (ms), estimated cost (USD), and parent workflow ID.
5. `gmail_messages`: Scanned email metadata, thread ID, sender, subject, body snippet, classification (`acknowledgement`, `assessment`, `interview`, `rejection`), and linked `application_id`.
6. `company_intelligence_memory`: Learned form fields, ATS quirks, custom questions, and automation reliability scores.

---

## 6. Integration Risks & Mitigations

1. **Anti-Bot & CAPTCHA on ATS Portals**:
   - *Risk*: Greenhouse/Lever Cloudflare Turnstile or CAPTCHAs blocking headless browsers.
   - *Mitigation*: Strictly abide by guidelines. Never attempt to solve CAPTCHA. Detect presence of CAPTCHA/bot gates, halt automation, save full prepared package and screenshot, and present 1-click manual portal submission link to candidate.
2. **Gmail API Rate Limits & Privacy**:
   - *Risk*: Token expiration, reading irrelevant personal emails, or rate limits.
   - *Mitigation*: Strictly request `https://www.googleapis.com/auth/gmail.readonly`. Filter queries specifically for recruitment keywords (`subject:(application OR interview OR assessment OR "thank you for applying")`). Redact sensitive information before logging.
3. **Database Drift during Migration**:
   - *Risk*: Altering existing SQLite tables breaking 1,516 jobs and 249 application records.
   - *Mitigation*: Add new tables with explicit foreign keys to existing tables without dropping or altering existing column constraints.

---

## 7. Recommended Implementation Order

1. **Phase 1**: Repository Audit (`docs/RELEASE_2_AUDIT.md`) & Status Tracker (`docs/RELEASE_2_STATUS.md`).
2. **Phase 2**: Persistent LangGraph Orchestrator & Durable Checkpointing.
3. **Phase 3**: Playwright Browser Automation & ATS Form Adapters.
4. **Phase 4**: Human Approval Center & Payload Hash Invalidation.
5. **Phase 5**: Persistent Memory Architecture (Candidate, Workflow, Company).
6. **Phase 6**: Gmail Recruitment Intelligence & Inbound Message Classifier.
7. **Phase 7**: Observability, Telemetry & LLM Cost Accounting.
8. **Phase 8**: Frontend Dashboard Integration (Approvals, Operations, Gmail, Browser Viewers).
9. **Phase 9**: End-to-End Verification & Automated Test Suite.
