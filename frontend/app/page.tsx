"use client";
import { useEffect, useState } from "react";
import { TopBar } from "@/components/layout/TopBar";
import { StatCard } from "@/components/ui/StatCard";
import { getOverviewStats, getJobs, batchPrepareApplications, batchSubmitApplications, OverviewStats, Job } from "@/lib/api";
import { formatScore, classificationColor, formatDate } from "@/lib/utils";
import { AlertCircle, TrendingUp, Zap, Send, CheckCircle2, Loader2 } from "lucide-react";

export default function OverviewPage() {
  const [stats, setStats] = useState<OverviewStats | null>(null);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Batch Apply State
  const [threshold, setThreshold] = useState<number>(80.0);
  const [batchLimit, setBatchLimit] = useState<number>(25);
  const [isPreparing, setIsPreparing] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [batchMessage, setBatchMessage] = useState<{ text: string; isError: boolean } | null>(null);

  const load = async () => {
    try {
      const [s, j] = await Promise.all([getOverviewStats(), getJobs({ page: 1, page_size: 8 })]);
      setStats(s);
      setJobs(j.jobs);
    } catch {
      setError("Could not connect to backend. Is it running on port 8000?");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const handleBatchPrepare = async () => {
    setIsPreparing(true);
    setBatchMessage(null);
    try {
      const res = await batchPrepareApplications(threshold, batchLimit);
      setBatchMessage({
        text: `Successfully prepared ${res.prepared_count} applications (Score ≥ ${threshold}%) with tailored resumes & cover letters! Review in Queue.`,
        isError: false,
      });
      await load();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to prepare batch applications";
      setBatchMessage({ text: msg, isError: true });
    } finally {
      setIsPreparing(false);
    }
  };

  const handleBatchSubmit = async () => {
    setIsSubmitting(true);
    setBatchMessage(null);
    try {
      const res = await batchSubmitApplications();
      setBatchMessage({
        text: res.message || `Successfully submitted ${res.submitted_count} applications!`,
        isError: false,
      });
      await load();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to submit batch applications";
      setBatchMessage({ text: msg, isError: true });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="flex flex-col h-full">
      <TopBar title="Overview" subtitle="JobPilot AI — Recruitment Intelligence Platform" />
      <div className="flex-1 overflow-auto p-6 space-y-6">
        {error && (
          <div className="flex items-center gap-2 p-3 bg-danger/10 border border-danger/20 rounded text-danger text-xs">
            <AlertCircle size={14} /> {error}
          </div>
        )}

        {/* 1-Click Batch Automation Banner */}
        <div className="bg-gradient-to-r from-surface to-surface-2 border border-accent/30 rounded-lg p-5 shadow-lg">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
              <div className="flex items-center gap-2 text-accent font-semibold text-sm">
                <Zap size={16} className="text-warning fill-warning" />
                <span>1-Click Autonomous Batch Application Engine</span>
              </div>
              <p className="text-xs text-text-muted mt-1 max-w-xl">
                Automatically generate tailored ATS resumes, personalized cover letters, and auto-map form answers for all vacancies matching your profile above the threshold score.
              </p>
            </div>

            <div className="flex flex-wrap items-center gap-3">
              <div className="flex items-center gap-2 bg-surface-2 border border-border px-2.5 py-1.5 rounded text-xs">
                <span className="text-[11px] text-text-muted uppercase tracking-wider">Score:</span>
                <select
                  value={threshold}
                  onChange={(e) => setThreshold(Number(e.target.value))}
                  className="bg-transparent text-text font-mono font-bold focus:outline-none cursor-pointer"
                >
                  <option value={80}>≥ 80% (Strong)</option>
                  <option value={85}>≥ 85% (Very High)</option>
                  <option value={90}>≥ 90% (Elite)</option>
                </select>
              </div>

              <div className="flex items-center gap-2 bg-surface-2 border border-border px-2.5 py-1.5 rounded text-xs">
                <span className="text-[11px] text-text-muted uppercase tracking-wider">Batch:</span>
                <select
                  value={batchLimit}
                  onChange={(e) => setBatchLimit(Number(e.target.value))}
                  className="bg-transparent text-text font-mono font-bold focus:outline-none cursor-pointer"
                >
                  <option value={10}>10 jobs</option>
                  <option value={25}>25 jobs</option>
                  <option value={50}>50 jobs</option>
                </select>
              </div>

              <button
                onClick={handleBatchPrepare}
                disabled={isPreparing || isSubmitting}
                className="flex items-center gap-1.5 px-3.5 py-2 bg-accent text-background font-semibold text-xs rounded hover:bg-accent-hover transition-all disabled:opacity-50 shadow"
              >
                {isPreparing ? <Loader2 size={13} className="animate-spin" /> : <Zap size={13} />}
                {isPreparing ? "Preparing Documents..." : `Prepare All (≥${threshold}%)`}
              </button>

              <button
                onClick={handleBatchSubmit}
                disabled={isSubmitting || isPreparing || (stats?.pending_approvals ?? 0) === 0}
                className="flex items-center gap-1.5 px-3.5 py-2 bg-success/20 text-success border border-success/30 font-semibold text-xs rounded hover:bg-success/30 transition-all disabled:opacity-40"
              >
                {isSubmitting ? <Loader2 size={13} className="animate-spin" /> : <Send size={13} />}
                {isSubmitting ? "Submitting..." : `Submit All (${stats?.pending_approvals ?? 0})`}
              </button>
            </div>
          </div>

          {batchMessage && (
            <div className={`mt-3 flex items-center gap-2 p-2.5 rounded text-xs border ${
              batchMessage.isError ? "bg-danger/10 border-danger/20 text-danger" : "bg-success/10 border-success/20 text-success"
            }`}>
              {batchMessage.isError ? <AlertCircle size={14} /> : <CheckCircle2 size={14} />}
              <span>{batchMessage.text}</span>
            </div>
          )}
        </div>

        {/* Stats grid */}
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
          <StatCard label="Jobs Discovered" value={stats?.total_jobs_discovered ?? "—"} color="text-text" />
          <StatCard label="New Today" value={stats?.new_today ?? "—"} color="text-accent" />
          <StatCard label="Strong Matches (≥80%)" value={stats?.strong_matches ?? "—"} color="text-success" />
          <StatCard label="Prepared" value={stats?.applications_prepared ?? "—"} color="text-warning" />
          <StatCard label="Pending Approval" value={stats?.pending_approvals ?? "—"} color="text-warning" />
          <StatCard label="Submitted" value={stats?.applications_submitted ?? "—"} color="text-success" />
        </div>

        {/* Recent Jobs */}
        <div>
          <div className="flex items-center gap-2 mb-3">
            <TrendingUp size={14} className="text-accent" />
            <h2 className="text-xs font-semibold text-text uppercase tracking-wider">Top Match Opportunities</h2>
          </div>
          <div className="bg-surface border border-border rounded-lg overflow-hidden">
            {loading ? (
              <div className="p-8 text-center text-text-muted text-xs">Loading...</div>
            ) : jobs.length === 0 ? (
              <div className="p-8 text-center text-text-muted text-xs">
                No jobs discovered yet. Click &ldquo;Run Discovery&rdquo; to start.
              </div>
            ) : (
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b border-border bg-surface-2">
                    <th className="text-left p-3 text-text-muted font-medium uppercase tracking-wider text-[10px]">Company / Role</th>
                    <th className="text-left p-3 text-text-muted font-medium uppercase tracking-wider text-[10px]">Location</th>
                    <th className="text-left p-3 text-text-muted font-medium uppercase tracking-wider text-[10px]">Source</th>
                    <th className="text-right p-3 text-text-muted font-medium uppercase tracking-wider text-[10px]">Match</th>
                    <th className="text-right p-3 text-text-muted font-medium uppercase tracking-wider text-[10px]">Discovered</th>
                  </tr>
                </thead>
                <tbody>
                  {jobs.map((job) => (
                    <tr key={job.id} className="border-b border-border/50 hover:bg-surface-2 transition-colors">
                      <td className="p-3">
                        <div className="font-medium text-text">{job.title}</div>
                        <div className="text-text-muted text-[11px]">{job.company}</div>
                      </td>
                      <td className="p-3 text-text-muted">{job.location || "—"}</td>
                      <td className="p-3">
                        <span className="font-mono text-[10px] text-text-muted uppercase">{job.source}</span>
                      </td>
                      <td className="p-3 text-right">
                        {job.match_score != null ? (
                          <span className={`font-mono font-bold ${classificationColor(job.classification)}`}>
                            {formatScore(job.match_score)}
                          </span>
                        ) : <span className="text-text-muted">—</span>}
                      </td>
                      <td className="p-3 text-right text-text-muted font-mono">{formatDate(job.discovered_at)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
