"""LangGraph multi-agent workflow orchestrator for JobPilot AI."""
from typing import TypedDict, List, Dict, Any, Optional
import structlog
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from app.agents.extraction import ExtractionAgent
from app.agents.matching import MatchingAgent
from app.agents.resume_intelligence import ResumeIntelligenceAgent
from app.agents.cover_letter import CoverLetterAgent

logger = structlog.get_logger()

# 1. Typed State Schemas
class DiscoveryState(TypedDict, total=False):
    companies: List[Dict[str, Any]]
    raw_jobs: List[Dict[str, Any]]

class MatchingState(TypedDict, total=False):
    extracted_jobs: List[Dict[str, Any]]
    filtered_jobs: List[Dict[str, Any]]
    matched_jobs: List[Dict[str, Any]]
    ranked_jobs: List[Dict[str, Any]]

class ApplicationState(TypedDict, total=False):
    target_job: Optional[Dict[str, Any]]
    tailored_resume: Optional[Dict[str, Any]]
    cover_letter: Optional[Dict[str, Any]]
    prepared_application: Optional[Dict[str, Any]]
    approval_status: str  # "pending", "approved", "rejected"
    submission_result: Optional[Dict[str, Any]]

class OrchestratorState(TypedDict, total=False):
    candidate: Dict[str, Any]
    candidate_facts: List[Dict[str, Any]]
    preferences: Dict[str, Any]
    companies: List[Dict[str, Any]]
    raw_jobs: List[Dict[str, Any]]
    extracted_jobs: List[Dict[str, Any]]
    filtered_jobs: List[Dict[str, Any]]
    matched_jobs: List[Dict[str, Any]]
    ranked_jobs: List[Dict[str, Any]]
    target_job: Optional[Dict[str, Any]]
    tailored_resume: Optional[Dict[str, Any]]
    cover_letter: Optional[Dict[str, Any]]
    prepared_application: Optional[Dict[str, Any]]
    approval_status: str
    submission_result: Optional[Dict[str, Any]]
    status_messages: List[str]

# Agent instances
extractor = ExtractionAgent()
matcher = MatchingAgent()
resume_agent = ResumeIntelligenceAgent()
cover_letter_agent = CoverLetterAgent()

# 2. Workflow Node Functions
async def node_discover(state: OrchestratorState) -> Dict[str, Any]:
    messages = list(state.get("status_messages", []))
    messages.append("Step 1: Discovering jobs from ATS connectors...")
    raw_jobs = list(state.get("raw_jobs", []))
    # If raw_jobs provided in state, keep them; else default mock discovery for workflow
    if not raw_jobs:
        raw_jobs = [
            {
                "title": "Junior Python / AI Engineer",
                "company": "Swiggy",
                "description": "Looking for entry-level engineer skilled in Python, Machine Learning, and APIs.",
                "location": "Bangalore",
                "source": "lever",
                "source_id": "swiggy-001",
                "application_url": "https://jobs.lever.co/swiggy/001",
            }
        ]
    return {"raw_jobs": raw_jobs, "status_messages": messages}

async def node_extract(state: OrchestratorState) -> Dict[str, Any]:
    messages = list(state.get("status_messages", []))
    messages.append("Step 2: Extracting requirements & skills...")
    extracted_jobs = []
    for raw in state.get("raw_jobs", []):
        res = await extractor.run({"raw_job": raw})
        if res["status"] == "success":
            data = res["data"]
            data["company"] = raw.get("company", "Company")
            extracted_jobs.append(data)
    return {"extracted_jobs": extracted_jobs, "status_messages": messages}

async def node_filter(state: OrchestratorState) -> Dict[str, Any]:
    messages = list(state.get("status_messages", []))
    messages.append("Step 3: Filtering jobs based on preferences & experience...")
    preferences = state.get("preferences", {})
    exp_max = preferences.get("experience_years", 2.0)
    filtered = []
    for job in state.get("extracted_jobs", []):
        min_exp = job.get("experience_min")
        if min_exp is None or min_exp <= (exp_max + 1):
            filtered.append(job)
    return {"filtered_jobs": filtered, "status_messages": messages}

async def node_match(state: OrchestratorState) -> Dict[str, Any]:
    messages = list(state.get("status_messages", []))
    messages.append("Step 4: Computing multi-criteria match scores...")
    matched = []
    candidate_facts = state.get("candidate_facts", [])
    preferences = state.get("preferences", {})
    for job in state.get("filtered_jobs", []):
        res = await matcher.run({
            "job": job,
            "candidate_facts": candidate_facts,
            "preferences": preferences,
        })
        if res["status"] == "success":
            matched_entry = dict(job)
            matched_entry["match_details"] = res["data"]
            matched_entry["overall_score"] = res["data"]["overall_score"]
            matched.append(matched_entry)
    return {"matched_jobs": matched, "status_messages": messages}

async def node_rank(state: OrchestratorState) -> Dict[str, Any]:
    messages = list(state.get("status_messages", []))
    messages.append("Step 5: Ranking opportunities by match score...")
    matched = list(state.get("matched_jobs", []))
    ranked = sorted(matched, key=lambda x: x.get("overall_score", 0), reverse=True)
    target = ranked[0] if ranked else None
    return {"ranked_jobs": ranked, "target_job": target, "status_messages": messages}

async def node_generate_docs(state: OrchestratorState) -> Dict[str, Any]:
    messages = list(state.get("status_messages", []))
    messages.append("Step 6: Generating tailored resume & cover letter...")
    target = state.get("target_job")
    candidate = state.get("candidate", {})
    facts = state.get("candidate_facts", [])
    tailored_resume = None
    cover_letter = None
    if target:
        r_res = await resume_agent.run({
            "candidate": candidate,
            "candidate_facts": facts,
            "job": target,
        })
        if r_res["status"] == "success":
            tailored_resume = r_res["data"]

        cl_res = await cover_letter_agent.run({
            "candidate": candidate,
            "candidate_facts": facts,
            "job": target,
        })
        if cl_res["status"] == "success":
            cover_letter = cl_res["data"]

    return {
        "tailored_resume": tailored_resume,
        "cover_letter": cover_letter,
        "status_messages": messages,
    }

async def node_prepare_application(state: OrchestratorState) -> Dict[str, Any]:
    messages = list(state.get("status_messages", []))
    messages.append("Step 7: Validating and packaging application...")
    target = state.get("target_job", {})
    candidate = state.get("candidate", {})
    resume = state.get("tailored_resume", {})
    cl = state.get("cover_letter", {})

    prepared = {
        "candidate_name": candidate.get("full_name"),
        "candidate_email": candidate.get("email"),
        "candidate_phone": candidate.get("phone"),
        "job_title": target.get("title") if target else None,
        "company": target.get("company") if target else None,
        "application_url": target.get("application_url") if target else None,
        "resume_path": resume.get("pdf_path") if resume else None,
        "cover_letter_path": cl.get("pdf_path") if cl else None,
        "is_ready_for_review": True,
    }
    return {
        "prepared_application": prepared,
        "approval_status": "pending_approval",
        "status_messages": messages,
    }

async def node_human_approval(state: OrchestratorState) -> Dict[str, Any]:
    messages = list(state.get("status_messages", []))
    messages.append("Step 8: Human-in-the-loop approval gate reached.")
    return {"status_messages": messages}

async def node_submit(state: OrchestratorState) -> Dict[str, Any]:
    messages = list(state.get("status_messages", []))
    approval = state.get("approval_status")
    if approval != "approved":
        messages.append("Submission halted: Application has not been approved.")
        return {
            "submission_result": {"status": "halted", "reason": "Requires human approval"},
            "status_messages": messages,
        }
    messages.append("Step 9: Submitting verified application to employer portal...")
    target = state.get("target_job", {})
    result = {
        "status": "submitted",
        "job_title": target.get("title"),
        "company": target.get("company"),
        "portal_url": target.get("application_url"),
        "confirmation_code": f"APP-{target.get('source_id', 'AUTO')}-CONFIRMED",
    }
    return {"submission_result": result, "status_messages": messages}

def should_submit(state: OrchestratorState) -> str:
    if state.get("approval_status") == "approved":
        return "submit"
    return END

# 3. Build StateGraph with Checkpointer
def build_jobpilot_workflow():
    workflow = StateGraph(OrchestratorState)

    workflow.add_node("discover", node_discover)
    workflow.add_node("extract", node_extract)
    workflow.add_node("filter", node_filter)
    workflow.add_node("match", node_match)
    workflow.add_node("rank", node_rank)
    workflow.add_node("generate_docs", node_generate_docs)
    workflow.add_node("prepare_application", node_prepare_application)
    workflow.add_node("human_approval", node_human_approval)
    workflow.add_node("submit", node_submit)

    workflow.add_edge(START, "discover")
    workflow.add_edge("discover", "extract")
    workflow.add_edge("extract", "filter")
    workflow.add_edge("filter", "match")
    workflow.add_edge("match", "rank")
    workflow.add_edge("rank", "generate_docs")
    workflow.add_edge("generate_docs", "prepare_application")
    workflow.add_edge("prepare_application", "human_approval")

    # Conditional edge or interrupt before submit
    workflow.add_conditional_edges("human_approval", should_submit, ["submit", END])
    workflow.add_edge("submit", END)

    checkpointer = MemorySaver()
    compiled_app = workflow.compile(
        checkpointer=checkpointer,
        interrupt_before=["submit"],
    )
    return compiled_app

jobpilot_workflow = build_jobpilot_workflow()
