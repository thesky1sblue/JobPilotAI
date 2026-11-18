import axios from "axios";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export const api = axios.create({
  baseURL: API_BASE,
  timeout: 120000,
  headers: { "Content-Type": "application/json" },
});

// Types
export interface OverviewStats {
  total_jobs_discovered: number;
  new_today: number;
  strong_matches: number;
  applications_prepared: number;
  pending_approvals: number;
  applications_submitted: number;
}

export interface Job {
  id: string;
  title: string;
  company: string;
  location: string;
  location_type: string;
  source: string;
  employment_type: string;
  posted_at: string | null;
  discovered_at: string;
  application_url: string | null;
  salary_min: number | null;
  salary_max: number | null;
  match_score: number | null;
  classification: "strong" | "good" | "review" | "low" | null;
}

export interface JobDetail extends Omit<Job, "company"> {
  description: string;
  company: { id: string; name: string; careers_url: string } | string;
  required_skills: string[];
  preferred_skills: string[];
  education_requirement: string;
  deadline: string | null;
  match: {
    overall_score: number;
    classification: string;
    matched_skills: string[];
    missing_skills: string[];
    explanation: string;
    is_eligible: boolean;
  } | null;
}

export interface Company {
  id: string;
  name: string;
  domain: string;
  careers_url: string;
  ats_platform: string;
  ats_identifier: string;
  location: string;
  industry: string;
  is_verified: boolean;
  last_discovered_at: string | null;
}

export interface Application {
  id: string;
  job_id: string;
  job_title?: string;
  company_name?: string;
  match_score?: number | null;
  portal_url?: string | null;
  status: string;
  is_ready: boolean;
  submitted_at: string | null;
  created_at: string;
}

export interface CandidateProfile {
  id: string;
  full_name: string;
  email: string;
  phone: string | null;
  location: string | null;
  linkedin_url: string | null;
  github_url: string | null;
  experience_years: number;
  facts: Array<{ id: string; type: string; data: Record<string, unknown>; verified: boolean }>;
}

export interface Preferences {
  target_roles: string[];
  preferred_locations: string[];
  work_types: string[];
  experience_level: string;
  experience_years: number;
  discovery_morning: string;
  discovery_evening: string;
  discovery_timezone: string;
  llm_provider: string;
}

// API functions
export const getOverviewStats = () => api.get<OverviewStats>("/jobs/stats/overview").then(r => r.data);
export const getJobs = (params?: Record<string, unknown>) => api.get<{ total: number; jobs: Job[] }>("/jobs/", { params }).then(r => r.data);
export const getJob = (id: string) => api.get<JobDetail>(`/jobs/${id}`).then(r => r.data);
export const triggerDiscovery = () =>
  api.post<{ message?: string; new_jobs: number; companies_scanned?: number; errors?: string[] }>("/jobs/discover").then(r => r.data);
export const getCompanies = () => api.get<Company[]>("/companies/").then(r => r.data);
export const seedCompanies = () => api.post<{ message: string; seeded: number }>("/companies/seed").then(r => r.data);
export const getProfile = () => api.get<CandidateProfile>("/candidate/profile").then(r => r.data);
export const getPreferences = () => api.get<Preferences>("/candidate/preferences").then(r => r.data);
export const updatePreferences = (data: Partial<Preferences>) => api.put("/candidate/preferences", data).then(r => r.data);
export const getApplications = (status?: string) => api.get<Application[]>("/applications/", { params: status ? { status } : {} }).then(r => r.data);
export const approveApplication = (id: string, notes?: string) => api.post(`/applications/${id}/approve`, null, { params: notes ? { notes } : {} }).then(r => r.data);
export const rejectApplication = (id: string, notes?: string) => api.post(`/applications/${id}/reject`, null, { params: notes ? { notes } : {} }).then(r => r.data);
export const uploadResume = (file: File) => {
  const form = new FormData();
  form.append("file", file);
  return api.post<{ message: string; version: number }>("/candidate/upload-resume", form, { headers: { "Content-Type": "multipart/form-data" } }).then(r => r.data);
};

export const prepareApplication = (jobId: string) =>
  api.post<{ status: string; application_id: string; message: string }>(`/applications/prepare/${jobId}`).then(r => r.data);

export const batchPrepareApplications = (minScore: number = 80.0, limit: number = 25) =>
  api.post<{ status: string; prepared_count: number; applications: Array<{ application_id: string; job_title: string; company: string; match_score: number }> }>(
    "/applications/batch-prepare",
    null,
    { params: { min_score: minScore, limit } }
  ).then(r => r.data);

export const batchSubmitApplications = () =>
  api.post<{ status: string; submitted_count: number; message: string }>("/applications/batch-submit").then(r => r.data);

export interface SubmissionReceipt {
  application_id: string;
  submission_id: string;
  job_title: string;
  company_name: string;
  company_domain: string;
  recipient_name: string;
  recipient_email: string;
  submitted_at: string;
  email_subject: string;
  email_body: string;
  resume_url: string;
  cover_letter_url: string | null;
}

export const getSubmissionReceipts = () =>
  api.get<SubmissionReceipt[]>("/applications/receipts").then(r => r.data);

// ==========================================
// RELEASE 2 TYPES & APIS
// ==========================================

export interface ApprovalItem {
  id: string;
  application_id: string;
  status: "pending" | "approved" | "rejected" | "changes_requested" | "saved_for_later" | "submitted";
  payload_hash: string;
  is_valid: boolean;
  job: {
    id: string;
    title: string;
    company: string;
    location: string;
    portal_url: string;
    score: number;
  };
  applicant: {
    name: string;
    email: string;
    phone: string;
  };
  answers: Record<string, string>;
  resume_url: string | null;
  cover_letter_url: string | null;
  created_at: string;
  reviewed_at?: string | null;
  reviewer_notes?: string | null;
}

export const getApprovals = (status?: string) =>
  api.get<ApprovalItem[]>("/approvals/", { params: status ? { status } : {} }).then(r => r.data);

export const getApprovalDetail = (id: string) =>
  api.get<ApprovalItem>(`/approvals/${id}`).then(r => r.data);

export const submitApprovalDecision = (id: string, decision: "approve" | "reject" | "request_changes" | "save_for_later", reviewerNotes?: string) =>
  api.post(`/approvals/${id}/decision`, { decision, reviewer_notes: reviewerNotes }).then(r => r.data);

export const executeApprovedSubmission = (id: string) =>
  api.post<{ status: string; application_id: string; message: string; browser_session_id?: string; screenshot_url?: string }>(`/approvals/${id}/submit`).then(r => r.data);

export interface ObservabilityMetrics {
  total_traces: number;
  total_tokens: number;
  prompt_tokens: number;
  completion_tokens: number;
  estimated_cost_usd: number;
  avg_latency_ms: number;
  by_agent: Record<string, { count: number; tokens: number; cost_usd: number }>;
  by_model: Record<string, { count: number; tokens: number; cost_usd: number }>;
}

export interface AgentTraceItem {
  id: string;
  agent_name: string;
  workflow_run_id: string | null;
  model_provider: string;
  model_name: string;
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
  cost_usd: number;
  latency_ms: number;
  status: string;
  created_at: string;
}

export const getObservabilityMetrics = () =>
  api.get<ObservabilityMetrics>("/observability/metrics").then(r => r.data);

export const getAgentTraces = (limit: number = 50, agentName?: string) =>
  api.get<AgentTraceItem[]>("/observability/traces", { params: { limit, ...(agentName ? { agent_name: agentName } : {}) } }).then(r => r.data);

export interface GmailRecruitmentMessage {
  id: string;
  message_id: string;
  sender: string;
  recipient: string;
  subject: string;
  snippet: string;
  received_at: string;
  classification: "interview" | "assessment" | "acknowledgement" | "rejection" | "other";
  confidence_score: number;
  company_domain: string | null;
  deadline: string | null;
  action_required: boolean;
  suggested_action: string | null;
  application_id: string | null;
}

export const getGmailMessages = (classification?: string, limit: number = 50) =>
  api.get<GmailRecruitmentMessage[]>("/gmail/messages", { params: { limit, ...(classification ? { classification } : {}) } }).then(r => r.data);

export const syncGmailMessages = () =>
  api.post<{ status: string; processed_count: number; matched_count: number }>("/gmail/sync").then(r => r.data);

export interface BrowserSessionItem {
  id: string;
  workflow_run_id: string | null;
  application_id: string | null;
  portal_url: string;
  ats_type: string;
  is_headful: boolean;
  field_mappings: Record<string, string>;
  pre_submit_screenshot: string | null;
  post_submit_screenshot: string | null;
  anti_bot_detected: boolean;
  success: boolean;
  error_message: string | null;
  created_at: string;
}

export const getBrowserSessions = (limit: number = 25) =>
  api.get<BrowserSessionItem[]>("/browser/sessions", { params: { limit } }).then(r => r.data);
