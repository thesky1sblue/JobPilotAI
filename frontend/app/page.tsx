"use client";
import { useEffect, useState } from "react";
import { TopBar } from "@/components/layout/TopBar";
import { StatCard } from "@/components/ui/StatCard";
import { getOverviewStats, getJobs, OverviewStats, Job } from "@/lib/api";
import { formatScore, classificationColor, formatDate } from "@/lib/utils";
import { AlertCircle, TrendingUp } from "lucide-react";

export default function OverviewPage() {
  const [stats, setStats] = useState<OverviewStats | null>(null);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
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
    load();
  }, []);

  return (
    <div className="flex flex-col h-full">
      <TopBar title="Overview" subtitle="JobPilot AI — Recruitment Intelligence Platform" />
      <div className="flex-1 overflow-auto p-6 space-y-6">
        {error && (
          <div className="flex items-center gap-2 p-3 bg-danger/10 border border-danger/20 rounded text-danger text-xs">
            <AlertCircle size={14} /> {error}
          </div>
        )}

        {/* Stats grid */}
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
          <StatCard label="Jobs Discovered" value={stats?.total_jobs_discovered ?? "—"} color="text-text" />
          <StatCard label="New Today" value={stats?.new_today ?? "—"} color="text-accent" />
          <StatCard label="Strong Matches" value={stats?.strong_matches ?? "—"} color="text-success" />
          <StatCard label="Prepared" value={stats?.applications_prepared ?? "—"} color="text-warning" />
          <StatCard label="Pending Approval" value={stats?.pending_approvals ?? "—"} color="text-warning" />
          <StatCard label="Submitted" value={stats?.applications_submitted ?? "—"} color="text-success" />
        </div>

        {/* Recent Jobs */}
        <div>
          <div className="flex items-center gap-2 mb-3">
            <TrendingUp size={14} className="text-accent" />
            <h2 className="text-xs font-semibold text-text uppercase tracking-wider">Recent Discoveries</h2>
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
                  <tr className="border-b border-border">
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

        {/* Quick start guide if no data */}
        {!loading && stats?.total_jobs_discovered === 0 && (
          <div className="bg-surface border border-border rounded-lg p-6">
            <h3 className="text-sm font-semibold text-text mb-4">Quick Start</h3>
            <ol className="space-y-2 text-xs text-text-muted">
              <li className="flex gap-2"><span className="text-accent font-mono">1.</span> Upload your resume in <a href="/resume" className="text-accent hover:underline">Resume Studio</a></li>
              <li className="flex gap-2"><span className="text-accent font-mono">2.</span> Configure your job preferences in <a href="/settings" className="text-accent hover:underline">Settings</a></li>
              <li className="flex gap-2"><span className="text-accent font-mono">3.</span> Seed the company watchlist in <a href="/companies" className="text-accent hover:underline">Companies</a></li>
              <li className="flex gap-2"><span className="text-accent font-mono">4.</span> Click <strong className="text-text">Run Discovery</strong> in the top bar</li>
              <li className="flex gap-2"><span className="text-accent font-mono">5.</span> Review matches in <a href="/matches" className="text-accent hover:underline">Match Intelligence</a></li>
            </ol>
          </div>
        )}
      </div>
    </div>
  );
}