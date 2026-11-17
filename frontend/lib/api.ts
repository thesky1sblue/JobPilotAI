import axios from "axios";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export const api = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
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
export const triggerDiscovery = () => api.post<{ message: string; new_jobs: number }>("/jobs/discover").then(r => r.data);
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