"use client";
import { useEffect, useState } from "react";
import { TopBar } from "@/components/layout/TopBar";
import { getJobs, getJob, Job, JobDetail } from "@/lib/api";
import { ScoreBar } from "@/components/ui/ScoreBar";
import { classificationBg, formatDate, cn } from "@/lib/utils";

export default function MatchesPage() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [selected, setSelected] = useState<JobDetail | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getJobs({ page: 1, page_size: 50, min_score: 55 }).then(r => {
      setJobs(r.jobs);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, []);

  const handleSelect = async (job: Job) => {
    const detail = await getJob(job.id);
    setSelected(detail);
  };

  return (
    <div className="flex flex-col h-full">
      <TopBar title="Match Intelligence" subtitle="Compatibility analysis for discovered opportunities" />
      <div className="flex flex-1 overflow-hidden">
        {/* Job list */}
        <div className="w-80 border-r border-border overflow-auto">
          {loading ? (
            <div className="p-6 text-center text-text-muted text-xs">Loading...</div>
          ) : jobs.length === 0 ? (
            <div className="p-6 text-center text-text-muted text-xs">No matches yet. Run discovery first.</div>
          ) : (
            <div>
              {jobs.map(job => (
                <button key={job.id} onClick={() => handleSelect(job)}
                  className={cn(
                    "w-full text-left p-4 border-b border-border/50 hover:bg-surface-2 transition-colors",
                    selected?.id === job.id && "bg-surface-2 border-l-2 border-l-accent"
                  )}>
                  <div className="flex items-start justify-between gap-2">
                    <div className="min-w-0">
                      <div className="text-xs font-medium text-text truncate">{job.title}</div>
                      <div className="text-[11px] text-text-muted mt-0.5">{job.company}</div>
                    </div>
                    {job.match_score != null && (
                      <span className={cn("text-[10px] font-mono font-bold flex-shrink-0 px-1.5 py-0.5 rounded border", classificationBg(job.classification))}>
                        {job.match_score.toFixed(0)}%
                      </span>
                    )}
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Detail panel */}
        <div className="flex-1 overflow-auto p-6">
          {!selected ? (
            <div className="flex items-center justify-center h-full text-text-muted text-xs">
              Select a job to view match analysis
            </div>
          ) : (
            <div className="space-y-6 max-w-2xl">
              <div>
                <h2 className="text-lg font-semibold text-text">{selected.title}</h2>
                <p className="text-sm text-text-muted mt-1">{typeof selected.company === "object" ? (selected.company as { name: string }).name : selected.company}</p>
              </div>

              {selected.match && (
                <>
                  <div className="bg-surface border border-border rounded-lg p-4">
                    <div className="flex items-center justify-between mb-4">
                      <span className="text-xs font-semibold text-text uppercase tracking-wider">Overall Match</span>
                      <span className={cn("text-2xl font-bold font-mono", classificationBg(selected.match.classification), "px-3 py-1 rounded border")}>
                        {selected.match.overall_score.toFixed(0)}%
                      </span>
                    </div>
                    <div className="space-y-3">
                      <ScoreBar score={selected.match.overall_score} label="Overall" />
                    </div>
                  </div>

                  <div className="bg-surface border border-border rounded-lg p-4">
                    <h3 className="text-xs font-semibold text-text uppercase tracking-wider mb-3">Analysis</h3>
                    <p className="text-xs text-text-muted leading-relaxed">{selected.match.explanation}</p>
                    
                    {selected.match.matched_skills.length > 0 && (
                      <div className="mt-4">
                        <div className="text-[10px] text-text-muted uppercase tracking-wider mb-2">Matched Skills</div>
                        <div className="flex flex-wrap gap-1.5">
                          {selected.match.matched_skills.map(s => (
                            <span key={s} className="px-2 py-0.5 bg-success/10 text-success border border-success/20 rounded text-[10px] font-mono">{s}</span>
                          ))}
                        </div>
                      </div>
                    )}
                    
                    {selected.match.missing_skills.length > 0 && (
                      <div className="mt-3">
                        <div className="text-[10px] text-text-muted uppercase tracking-wider mb-2">Skills to Develop</div>
                        <div className="flex flex-wrap gap-1.5">
                          {selected.match.missing_skills.map(s => (
                            <span key={s} className="px-2 py-0.5 bg-warning/10 text-warning border border-warning/20 rounded text-[10px] font-mono">{s}</span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </>
              )}

              <div className="bg-surface border border-border rounded-lg p-4">
                <h3 className="text-xs font-semibold text-text uppercase tracking-wider mb-3">Job Details</h3>
                <div className="space-y-2 text-xs">
                  <div className="flex gap-2"><span className="text-text-muted w-24">Location</span><span className="text-text">{selected.location || "—"}</span></div>
                  <div className="flex gap-2"><span className="text-text-muted w-24">Type</span><span className="text-text">{selected.employment_type || "—"}</span></div>
                  <div className="flex gap-2"><span className="text-text-muted w-24">Posted</span><span className="text-text">{formatDate(selected.posted_at)}</span></div>
                </div>
                {selected.application_url && (
                  <a href={selected.application_url} target="_blank" rel="noopener noreferrer"
                    className="mt-4 inline-flex items-center gap-1.5 px-3 py-1.5 bg-accent text-background rounded text-xs font-medium hover:bg-accent-hover transition-colors">
                    Apply Now →
                  </a>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}