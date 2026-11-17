"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { TopBar } from "@/components/layout/TopBar";
import { getJobs, getJob, batchPrepareApplications, prepareApplication, Job, JobDetail } from "@/lib/api";
import { ScoreBar } from "@/components/ui/ScoreBar";
import { classificationBg, formatDate, cn } from "@/lib/utils";
import { Sparkles, CheckCircle2, ArrowRight, Loader2, Send } from "lucide-react";

export default function MatchesPage() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [selected, setSelected] = useState<JobDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [batchLoading, setBatchLoading] = useState(false);
  const [batchResult, setBatchResult] = useState<string | null>(null);
  const [singlePreparing, setSinglePreparing] = useState(false);
  const [singleMessage, setSingleMessage] = useState<string | null>(null);

  useEffect(() => {
    getJobs({ page: 1, page_size: 100, min_score: 55 })
      .then(r => {
        setJobs(r.jobs);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  const handleSelect = async (job: Job) => {
    setSingleMessage(null);
    const detail = await getJob(job.id);
    setSelected(detail);
  };

  const handleBatchPrepare = async () => {
    setBatchLoading(true);
    setBatchResult(null);
    try {
      const res = await batchPrepareApplications(80.0, 25);
      setBatchResult(`Successfully prepared ${res.prepared_count} applications! Jump to Queue to review.`);
    } catch (e: any) {
      setBatchResult("Batch preparation failed: " + (e?.response?.data?.detail || e.message));
    } finally {
      setBatchLoading(false);
    }
  };

  const handlePrepareSingle = async (jobId: string) => {
    setSinglePreparing(true);
    setSingleMessage(null);
    try {
      const res = await prepareApplication(jobId);
      setSingleMessage(res.message);
    } catch (e: any) {
      setSingleMessage("Error: " + (e?.response?.data?.detail || e.message));
    } finally {
      setSinglePreparing(false);
    }
  };

  const strongMatchesCount = jobs.filter(j => (j.match_score ?? 0) >= 80).length;

  return (
    <div className="flex flex-col h-full">
      <TopBar title="Match Intelligence" subtitle="Compatibility analysis & grounded application generator" />

      {/* Action Strip */}
      <div className="bg-surface-2 border-b border-border px-6 py-3 flex items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <span className="text-xs font-semibold text-text flex items-center gap-1.5">
            <Sparkles size={14} className="text-accent" />
            <span>High-Compatibility Matches (≥80%):</span>
            <span className="px-1.5 py-0.2 rounded font-mono font-bold text-accent bg-accent/10 border border-accent/20">
              {strongMatchesCount}
            </span>
          </span>
          {batchResult && (
            <span className="text-xs text-success flex items-center gap-1">
              <CheckCircle2 size={13} /> {batchResult}
            </span>
          )}
        </div>

        <div className="flex items-center gap-2">
          <Link
            href="/queue"
            className="flex items-center gap-1 px-3 py-1.5 bg-surface text-text-muted hover:text-text border border-border rounded text-xs transition-colors"
          >
            Go to Queue <ArrowRight size={12} />
          </Link>
          <button
            onClick={handleBatchPrepare}
            disabled={batchLoading}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-accent hover:bg-accent-hover text-background font-medium rounded text-xs transition-colors shadow-sm disabled:opacity-50"
          >
            {batchLoading ? (
              <>
                <Loader2 size={13} className="animate-spin" />
                Preparing Documents...
              </>
            ) : (
              <>
                <Sparkles size={13} />
                Batch Prepare Top Matches (≥80%)
              </>
            )}
          </button>
        </div>
      </div>

      <div className="flex flex-1 overflow-hidden">
        {/* Job list */}
        <div className="w-80 border-r border-border overflow-auto">
          {loading ? (
            <div className="p-6 text-center text-text-muted text-xs">Loading matches...</div>
          ) : jobs.length === 0 ? (
            <div className="p-6 text-center text-text-muted text-xs">No matches yet. Run discovery first.</div>
          ) : (
            <div>
              {jobs.map(job => (
                <button
                  key={job.id}
                  onClick={() => handleSelect(job)}
                  className={cn(
                    "w-full text-left p-4 border-b border-border/50 hover:bg-surface-2 transition-colors",
                    selected?.id === job.id && "bg-surface-2 border-l-2 border-l-accent"
                  )}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="min-w-0">
                      <div className="text-xs font-medium text-text truncate">{job.title}</div>
                      <div className="text-[11px] text-text-muted mt-0.5">{job.company}</div>
                    </div>
                    {job.match_score != null && (
                      <span
                        className={cn(
                          "text-[10px] font-mono font-bold flex-shrink-0 px-1.5 py-0.5 rounded border",
                          classificationBg(job.classification)
                        )}
                      >
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
              Select a job from the list to view match breakdown and generate applications
            </div>
          ) : (
            <div className="space-y-6 max-w-2xl">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <h2 className="text-lg font-semibold text-text">{selected.title}</h2>
                  <p className="text-sm text-text-muted mt-1">
                    {typeof selected.company === "object" ? (selected.company as { name: string }).name : selected.company}
                  </p>
                </div>
                <button
                  onClick={() => handlePrepareSingle(selected.id)}
                  disabled={singlePreparing}
                  className="flex items-center gap-1.5 px-3 py-1.5 bg-accent hover:bg-accent-hover text-background font-medium rounded text-xs transition-colors shadow-sm disabled:opacity-50"
                >
                  {singlePreparing ? (
                    <>
                      <Loader2 size={13} className="animate-spin" />
                      Generating...
                    </>
                  ) : (
                    <>
                      <Send size={13} />
                      Prepare Application
                    </>
                  )}
                </button>
              </div>

              {singleMessage && (
                <div className="p-3 bg-surface border border-accent/30 rounded-lg text-xs text-text flex items-center justify-between">
                  <span>{singleMessage}</span>
                  <Link href="/queue" className="text-accent underline text-[11px] ml-2">
                    View in Queue →
                  </Link>
                </div>
              )}

              {selected.match && (
                <>
                  <div className="bg-surface border border-border rounded-lg p-4">
                    <div className="flex items-center justify-between mb-4">
                      <span className="text-xs font-semibold text-text uppercase tracking-wider">Overall Compatibility</span>
                      <span
                        className={cn(
                          "text-2xl font-bold font-mono",
                          classificationBg(selected.match.classification),
                          "px-3 py-1 rounded border"
                        )}
                      >
                        {selected.match.overall_score.toFixed(0)}%
                      </span>
                    </div>
                    <div className="space-y-3">
                      <ScoreBar score={selected.match.overall_score} label="Weighted Compatibility Score" />
                    </div>
                  </div>

                  <div className="bg-surface border border-border rounded-lg p-4">
                    <h3 className="text-xs font-semibold text-text uppercase tracking-wider mb-3">Ground-Truth Match Reasoning</h3>
                    <p className="text-xs text-text-muted leading-relaxed">{selected.match.explanation}</p>

                    {selected.match.matched_skills.length > 0 && (
                      <div className="mt-4">
                        <div className="text-[10px] text-text-muted uppercase tracking-wider mb-2">Verified Matched Skills</div>
                        <div className="flex flex-wrap gap-1.5">
                          {selected.match.matched_skills.map(s => (
                            <span
                              key={s}
                              className="px-2 py-0.5 bg-success/10 text-success border border-success/20 rounded text-[10px] font-mono"
                            >
                              {s}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {selected.match.missing_skills.length > 0 && (
                      <div className="mt-3">
                        <div className="text-[10px] text-text-muted uppercase tracking-wider mb-2">Skills to Develop</div>
                        <div className="flex flex-wrap gap-1.5">
                          {selected.match.missing_skills.map(s => (
                            <span
                              key={s}
                              className="px-2 py-0.5 bg-warning/10 text-warning border border-warning/20 rounded text-[10px] font-mono"
                            >
                              {s}
                            </span>
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
                  <div className="flex gap-2">
                    <span className="text-text-muted w-24">Location</span>
                    <span className="text-text">{selected.location || "—"}</span>
                  </div>
                  <div className="flex gap-2">
                    <span className="text-text-muted w-24">Type</span>
                    <span className="text-text">{selected.employment_type || "—"}</span>
                  </div>
                  <div className="flex gap-2">
                    <span className="text-text-muted w-24">Posted</span>
                    <span className="text-text">{formatDate(selected.posted_at)}</span>
                  </div>
                </div>
                {selected.application_url && (
                  <a
                    href={selected.application_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="mt-4 inline-flex items-center gap-1.5 px-3 py-1.5 bg-surface-2 text-text border border-border hover:bg-surface rounded text-xs font-medium transition-colors"
                  >
                    External Job Board ↗
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
