import os
import uuid
import pytest
import pytest_asyncio
from httpx import AsyncClient
from datetime import datetime

from app.workflows.checkpoint_saver import SqliteDurableSaver
from app.services.approval_service import ApprovalService
from app.services.browser_manager import BrowserManager, FIELD_LOCATOR_PATTERNS
from app.services.gmail_service import GmailService
from app.services.observability_service import ObservabilityService
from app.models.applications import Application, Approval
from app.models.jobs import Job, Company
from app.models.candidate import CandidateProfile
from app.models.browser import BrowserSession
from app.models.observability import AgentTrace
from app.models.gmail import GmailMessage

# ---------------------------------------------------------------------------
# 1. SQLITE DURABLE SAVER TESTS (PERSISTENT CHECKPOINTS & RESUMPTION)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_sqlite_durable_saver(tmp_path):
    db_file = str(tmp_path / "checkpoints_test.db")
    saver = SqliteDurableSaver(db_path=db_file)

    config = {"configurable": {"thread_id": "thread-audit-1", "checkpoint_ns": ""}}
    checkpoint = {
        "v": 1,
        "id": "cp-1",
        "ts": "2026-11-18T00:00:00Z",
        "channel_values": {"stage": "human_approval", "candidate_name": "Akash Nandy"},
        "channel_versions": {"stage": 1},
        "versions_seen": {},
    }
    metadata = {"source": "input", "step": 1, "writes": {}}

    # Put checkpoint
    next_config = await saver.aput(config, checkpoint, metadata, {})
    assert next_config["configurable"]["checkpoint_id"] == "cp-1"

    # Get tuple
    retrieved = await saver.aget_tuple(config)
    assert retrieved is not None
    assert retrieved.checkpoint["id"] == "cp-1"
    assert retrieved.checkpoint["channel_values"]["stage"] == "human_approval"
    assert retrieved.checkpoint["channel_values"]["candidate_name"] == "Akash Nandy"

    # Simulate process restart by instantiating new saver with same db file
    restarted_saver = SqliteDurableSaver(db_path=db_file)
    resumed_tuple = await restarted_saver.aget_tuple(config)
    assert resumed_tuple is not None
    assert resumed_tuple.checkpoint["id"] == "cp-1"
    assert resumed_tuple.checkpoint["channel_values"]["stage"] == "human_approval"

# ---------------------------------------------------------------------------
# 2. APPROVAL SERVICE TESTS (HASHING, INTEGRITY & INVALIDATION)
# ---------------------------------------------------------------------------

def test_approval_payload_hash_and_invalidation():
    service = ApprovalService()

    applicant = {"full_name": "Akash Nandy", "email": "akashnandy01@gmail.com", "phone": "+91 9330136009"}
    job = {"title": "AI Engineer", "company": "Tech Corp", "application_url": "https://techcorp.com/apply"}
    answers = {"Why work here?": "I love agentic systems.", "Years of Python?": "2"}
    resume = "Akash_Resume_v2.pdf"
    cover_letter = "Dear Hiring Manager..."

    # Canonical hash
    hash1 = service.compute_payload_hash(applicant, job, answers, resume, cover_letter)
    assert isinstance(hash1, str)
    assert len(hash1) == 64  # SHA256 length

    # Verify identical inputs produce same hash
    hash2 = service.compute_payload_hash(applicant, job, answers, resume, cover_letter)
    assert hash1 == hash2

    # Verification passes when status is approved and hash matches
    valid, err = service.verify_approval_integrity(hash1, hash1, "approved")
    assert valid is True
    assert err is None

    # Mutate answers - verify invalidation / tamper detection
    mutated_answers = answers.copy()
    mutated_answers["Why work here?"] = "Tampered response"
    mutated_hash = service.compute_payload_hash(applicant, job, mutated_answers, resume, cover_letter)
    assert mutated_hash != hash1

    valid_tampered, err_tampered = service.verify_approval_integrity(mutated_hash, hash1, "approved")
    assert valid_tampered is False
    assert "Payload mutation detected" in err_tampered

    # Unapproved status check
    valid_pending, err_pending = service.verify_approval_integrity(hash1, hash1, "pending")
    assert valid_pending is False
    assert "not 'approved'" in err_pending

# ---------------------------------------------------------------------------
# 3. BROWSER MANAGER TESTS (ATS DETECTION & LOCATORS)
# ---------------------------------------------------------------------------

def test_browser_ats_detection():
    manager = BrowserManager()

    assert manager.detect_ats_type("https://jobs.lever.co/netflix/12345") == "lever"
    assert manager.detect_ats_type("https://boards.greenhouse.io/stripe/jobs/6789") == "greenhouse"
    assert manager.detect_ats_type("https://amazon.wd5.myworkdayjobs.com/Amazon_Jobs/job/123") == "workday"
    assert manager.detect_ats_type("https://startup.com/careers/apply") == "custom"

def test_browser_field_selectors():
    assert "first_name" in FIELD_LOCATOR_PATTERNS
    assert "email" in FIELD_LOCATOR_PATTERNS
    assert len(FIELD_LOCATOR_PATTERNS["first_name"]) > 0
    assert len(FIELD_LOCATOR_PATTERNS["email"]) > 0

# ---------------------------------------------------------------------------
# 4. GMAIL SERVICE TESTS (CLASSIFICATION & DEADLINE EXTRACTION)
# ---------------------------------------------------------------------------

def test_gmail_classification_and_deadlines():
    service = GmailService()

    # Interview invitation
    cat, conf, act_req, summary = service.classify_email(
        "Invitation to Interview with Razorpay",
        "Hi Akash, We would like to schedule a technical round for the AI Engineer role."
    )
    assert cat == "interview"
    assert act_req is True
    assert conf >= 0.9

    # Assessment
    cat_ass, conf_ass, act_ass, summary_ass = service.classify_email(
        "HackerRank Assessment - Swiggy SDE",
        "Please complete the online coding test by Friday."
    )
    assert cat_ass == "assessment"
    assert act_ass is True

    # Acknowledgement
    cat_ack, conf_ack, act_ack, summary_ack = service.classify_email(
        "Thank you for applying to Zepto",
        "We have received your application for the Python Developer position."
    )
    assert cat_ack == "acknowledgement"
    assert act_ack is False

    # Rejection
    cat_rej, conf_rej, act_rej, summary_rej = service.classify_email(
        "Update on your application",
        "Thank you for your interest. Unfortunately, we have decided not moving forward at this time."
    )
    assert cat_rej == "rejection"
    assert act_rej is False

    # Deadline parsing
    deadline = service.extract_deadline("Please submit your assessment before 2026-11-25.")
    assert deadline is not None
    assert deadline.year == 2026
    assert deadline.month == 11
    assert deadline.day == 25

# ---------------------------------------------------------------------------
# 5. OBSERVABILITY SERVICE TESTS (COST CALCULATION & PII SCRUBBING)
# ---------------------------------------------------------------------------

def test_observability_costs_and_pii_scrubber():
    # Cost calculation for Gemini 1.5 Flash
    cost_flash = ObservabilityService.calculate_cost("gemini-1.5-flash", prompt_tokens=1000, completion_tokens=1000)
    assert cost_flash > 0

    # Cost calculation for Gemini 1.5 Pro
    cost_pro = ObservabilityService.calculate_cost("gemini-1.5-pro", prompt_tokens=1000, completion_tokens=1000)
    assert cost_pro > cost_flash

    # PII scrubber tests
    text_with_pii = "Contact Akash at akashnandy01@gmail.com or call 933-013-6009. secret_key: AIzaSyDZTqXsRltG7NTPg50ajTu89RBR"
    scrubbed = ObservabilityService.scrub_pii(text_with_pii)

    assert "akashnandy01@gmail.com" not in scrubbed
    assert "[REDACTED_EMAIL]" in scrubbed
    assert "933-013-6009" not in scrubbed
    assert "[REDACTED_PHONE]" in scrubbed
    assert "[REDACTED_SECRET]" in scrubbed

# ---------------------------------------------------------------------------
# 6. API ENDPOINTS INTEGRATION TESTS
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_release2_api_endpoints(client: AsyncClient, db_session):
    # Seed Company & Job
    company = Company(
        id=uuid.uuid4(),
        name="Zerodha",
        domain="zerodha.com",
        careers_url="https://zerodha.com/careers",
        location="Bangalore",
        industry="Fintech",
        ats_platform="lever"
    )
    db_session.add(company)
    await db_session.flush()

    job = Job(
        id=uuid.uuid4(),
        company_id=company.id,
        title="Software Engineer - Backend",
        description="Looking for Python, FastAPI, and Postgres backend engineer.",
        location="Bangalore",
        location_type="hybrid",
        source="lever",
        source_id="zerodha-01",
        application_url="https://jobs.lever.co/zerodha/01"
    )
    db_session.add(job)
    await db_session.flush()

    # Seed Candidate Profile
    candidate = CandidateProfile(
        id=uuid.uuid4(),
        full_name="Akash Nandy",
        email="akashnandy01@gmail.com",
        phone="+91 9330136009",
        location="Bangalore",
        experience_years=1.0
    )
    db_session.add(candidate)
    await db_session.flush()

    # Seed Application & Approval
    app_id = uuid.uuid4()
    app = Application(
        id=app_id,
        job_id=job.id,
        candidate_id=candidate.id,
        status="pending_approval",
        is_ready=True
    )
    db_session.add(app)
    await db_session.flush()

    approval_hash = ApprovalService.compute_payload_hash(
        {"full_name": candidate.full_name, "email": candidate.email, "phone": candidate.phone},
        {"title": job.title, "company": company.name, "application_url": job.application_url},
        {"notice_period": "Immediate"},
        "Akash_Resume.pdf",
        "Cover letter..."
    )

    approval = Approval(
        id=uuid.uuid4(),
        application_id=app_id,
        status="pending"
    )
    db_session.add(approval)

    # Seed Observability Trace
    trace = AgentTrace(
        id=uuid.uuid4(),
        agent_name="matching_agent",
        step_name="evaluate_match",
        model_provider="google",
        model_name="gemini-1.5-flash",
        prompt_tokens=450,
        completion_tokens=120,
        total_tokens=570,
        estimated_cost_usd=0.00007,
        duration_ms=310.0,
        status="success"
    )
    db_session.add(trace)

    # Seed Gmail Message
    gmail_msg = GmailMessage(
        id=uuid.uuid4(),
        message_id="msg-audit-100",
        thread_id="th-100",
        sender="careers@zerodha.com",
        recipient="akashnandy01@gmail.com",
        subject="Application Received: Software Engineer",
        snippet="We have received your application and will review it shortly.",
        received_at=datetime.utcnow(),
        classification="acknowledgement",
        confidence_score=0.98,
        action_required=False,
        linked_company_id=company.id,
        linked_application_id=app_id
    )
    db_session.add(gmail_msg)

    # Seed Browser Session
    browser_session = BrowserSession(
        id=uuid.uuid4(),
        application_id=app_id,
        portal_url=job.application_url,
        portal_type="lever",
        staged_answers={"full_name": "Akash Nandy", "email": "akashnandy01@gmail.com"},
        submission_success=True,
        status="submitted"
    )
    db_session.add(browser_session)
    await db_session.commit()

    # 1. Test GET /api/v1/approvals/
    res_approvals = await client.get("/api/v1/approvals/")
    assert res_approvals.status_code == 200
    approvals_data = res_approvals.json()
    assert len(approvals_data) >= 1
    item = approvals_data[0]
    assert item["job"]["title"] == "Software Engineer - Backend"
    assert item["job"]["company"] == "Zerodha"
    assert item["is_valid"] is True

    # 2. Test POST /api/v1/approvals/{id}/decision -> approve
    approval_id = item["id"]
    res_dec = await client.post(f"/api/v1/approvals/{approval_id}/decision", json={"decision": "approve", "reviewer_notes": "All verified"})
    assert res_dec.status_code == 200
    assert res_dec.json()["status"] == "success"
    assert res_dec.json()["decision"] == "approve"

    # 3. Test GET /api/v1/observability/metrics
    res_metrics = await client.get("/api/v1/observability/metrics")
    assert res_metrics.status_code == 200
    metrics_data = res_metrics.json()
    assert metrics_data["total_traces"] >= 1
    assert "matching_agent" in metrics_data["by_agent"]

    # 4. Test GET /api/v1/observability/traces
    res_traces = await client.get("/api/v1/observability/traces")
    assert res_traces.status_code == 200
    traces_data = res_traces.json()
    assert len(traces_data) >= 1
    assert traces_data[0]["agent_name"] == "matching_agent"

    # 5. Test GET /api/v1/gmail/messages
    res_gmail = await client.get("/api/v1/gmail/messages")
    assert res_gmail.status_code == 200
    gmail_data = res_gmail.json()
    assert len(gmail_data) >= 1
    assert gmail_data[0]["classification"] == "acknowledgement"

    # 6. Test GET /api/v1/browser/sessions
    res_browser = await client.get("/api/v1/browser/sessions")
    assert res_browser.status_code == 200
    browser_data = res_browser.json()
    assert len(browser_data) >= 1
    assert browser_data[0]["ats_type"] == "lever"
