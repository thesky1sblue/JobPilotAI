"use client";
import { useEffect, useState } from "react";
import { TopBar } from "@/components/layout/TopBar";
import { getJobs, Job } from "@/lib/api";
import { formatScore, classificationBg, formatDate, formatSalary } from "@/lib/utils";
import { Search, ExternalLink } from "lucide-react";
import { cn } from "@/lib/utils";

export default function DiscoveryPage() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [classification, setClassification] = useState("");
  const [page, setPage] = useState(1);

  const load = async () => {
    setLoading(true);
    try {
      const r = await getJobs({ page, page_size: 25, search: search || undefined, classification: classification || undefined });
      setJobs(r.jobs);
      setTotal(r.total);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, [page, classification]);

  return (
    <div className="flex flex-col h-full">
      <TopBar title="Job Discovery" subtitle={`${total} jobs discovered`} />
      <div className="flex-1 overflow-auto p-6">
        {/* Filters */}
        <div className="flex gap-3 mb-4">
          <div className="relative flex-1 max-w-xs">
            <Search size={12} className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted" />
            <input
              className="w-full pl-8 pr-3 py-2 bg-surface border border-border rounded text-xs text-text placeholder-text-muted focus:outline-none focus:border-accent"
              placeholder="Search jobs..."
              value={search}
              onChange={e => setSearch(e.target.value)}
              onKeyDown={e => e.key === "Enter" && load()}
            />
          </div>
          <select
            className="bg-surface border border-border rounded px-3 py-2 text-xs text-text focus:outline-none focus:border-accent"
            value={classification}
            onChange={e => { setClassification(e.target.value); setPage(1); }}
          >
            <option value="">All matches</option>
            <option value="strong">Strong (85+)</option>
            <option value="good">Good (70+)</option>
            <option value="review">Review (55+)</option>
            <option value="low">Low priority</option>
          </select>
        </div>

        {/* Table */}
        <div className="bg-surface border border-border rounded-lg overflow-hidden">
          {loading ? (
            <div className="p-12 text-center text-text-muted text-xs">Loading jobs...</div>
          ) : jobs.length === 0 ? (
            <div className="p-12 text-center text-text-muted text-xs">No jobs found. Run discovery to fetch jobs.</div>
          ) : (
            <>
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b border-border bg-surface-2">
                    <th className="text-left p-3 text-text-muted font-medium uppercase tracking-wider text-[10px]">Role</th>
                    <th className="text-left p-3 text-text-muted font-medium uppercase tracking-wider text-[10px]">Company</th>
                    <th className="text-left p-3 text-text-muted font-medium uppercase tracking-wider text-[10px]">Location</th>
                    <th className="text-left p-3 text-text-muted font-medium uppercase tracking-wider text-[10px]">Salary</th>
                    <th className="text-left p-3 text-text-muted font-medium uppercase tracking-wider text-[10px]">Source</th>
                    <th className="text-right p-3 text-text-muted font-medium uppercase tracking-wider text-[10px]">Match</th>
                    <th className="text-right p-3 text-text-muted font-medium uppercase tracking-wider text-[10px]">Date</th>
                    <th className="p-3"></th>
                  </tr>
                </thead>
                <tbody>
                  {jobs.map(job => (
                    <tr key={job.id} className="border-b border-border/50 hover:bg-surface-2 transition-colors">
                      <td className="p-3 font-medium text-text max-w-xs">
                        <div className="truncate">{job.title}</div>
                      </td>
                      <td className="p-3 text-text-muted">{job.company}</td>
                      <td className="p-3 text-text-muted">
                        <div className="truncate max-w-[120px]">{job.location || "—"}</div>
                        {job.location_type && (
                          <span className="text-[10px] font-mono text-text-muted uppercase">{job.location_type}</span>
                        )}
                      </td>
                      <td className="p-3 font-mono text-text-muted text-[11px]">{formatSalary(job.salary_min, job.salary_max)}</td>
                      <td className="p-3">
                        <span className="font-mono text-[10px] text-text-muted uppercase bg-surface-2 px-1.5 py-0.5 rounded">{job.source}</span>
                      </td>
                      <td className="p-3 text-right">
                        {job.match_score != null ? (
                          <div className="flex items-center justify-end gap-2">
                            <span className={cn("text-[10px] font-medium border px-1.5 py-0.5 rounded uppercase", classificationBg(job.classification))}>
                              {job.classification}
                            </span>
                            <span className="font-mono font-bold text-text">{formatScore(job.match_score)}</span>
                          </div>
                        ) : <span className="text-text-muted">—</span>}
                      </td>
                      <td className="p-3 text-right font-mono text-text-muted text-[11px]">{formatDate(job.discovered_at)}</td>
                      <td className="p-3">
                        {job.application_url && (
                          <a href={job.application_url} target="_blank" rel="noopener noreferrer" className="text-accent hover:text-accent-hover">
                            <ExternalLink size={12} />
                          </a>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {/* Pagination */}
              <div className="flex items-center justify-between p-3 border-t border-border">
                <span className="text-[11px] text-text-muted font-mono">{total} total</span>
                <div className="flex gap-2">
                  <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1}
                    className="px-2 py-1 text-[11px] bg-surface-2 border border-border rounded text-text-muted hover:text-text disabled:opacity-30">Prev</button>
                  <span className="px-2 py-1 text-[11px] text-text-muted font-mono">p.{page}</span>
                  <button onClick={() => setPage(p => p + 1)} disabled={jobs.length < 25}
                    className="px-2 py-1 text-[11px] bg-surface-2 border border-border rounded text-text-muted hover:text-text disabled:opacity-30">Next</button>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}