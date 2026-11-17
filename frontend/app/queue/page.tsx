"use client";
import { useEffect, useState } from "react";
import { TopBar } from "@/components/layout/TopBar";
import { getApplications, approveApplication, rejectApplication, batchSubmitApplications, Application } from "@/lib/api";
import { statusColor, formatDate } from "@/lib/utils";
import { CheckCircle, XCircle, Send, CheckCheck, ExternalLink, Loader2 } from "lucide-react";

export default function QueuePage() {
  const [apps, setApps] = useState<Application[]>([]);
  const [loading, setLoading] = useState(true);
  const [submittingBatch, setSubmittingBatch] = useState(false);
  const [batchMessage, setBatchMessage] = useState<string | null>(null);

  const load = async () => {
    setLoading(true);
    try {
      setApps(await getApplications());
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const handleApprove = async (id: string) => {
    await approveApplication(id);
    await load();
  };

  const handleReject = async (id: string) => {
    await rejectApplication(id);
    await load();
  };

  const handleBatchSubmit = async () => {
    setSubmittingBatch(true);
    setBatchMessage(null);
    try {
      const res = await batchSubmitApplications();
      setBatchMessage(res.message);
      await load();
    } catch (e: any) {
      setBatchMessage("Batch submission failed: " + (e?.response?.data?.detail || e.message));
    } finally {
      setSubmittingBatch(false);
    }
  };

  const pending = apps.filter(a => a.status === "pending_approval");
  const others = apps.filter(a => a.status !== "pending_approval");

  return (
    <div className="flex flex-col h-full">
      <TopBar title="Application Queue" subtitle={`${pending.length} pending your explicit approval`} />
      <div className="flex-1 overflow-auto p-6 space-y-6">
        {batchMessage && (
          <div className="p-3 bg-accent/10 border border-accent/30 rounded-lg text-xs text-accent flex items-center justify-between">
            <span>{batchMessage}</span>
            <button onClick={() => setBatchMessage(null)} className="text-text-muted hover:text-text text-[11px]">✕</button>
          </div>
        )}

        {pending.length > 0 && (
          <div>
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-xs font-semibold text-text uppercase tracking-wider flex items-center gap-2">
                <span>Pending Your Approval</span>
                <span className="px-1.5 py-0.5 bg-warning/20 text-warning rounded-full text-[10px] font-mono">
                  {pending.length}
                </span>
              </h2>
              <button
                onClick={handleBatchSubmit}
                disabled={submittingBatch}
                className="flex items-center gap-1.5 px-3 py-1.5 bg-accent hover:bg-accent-hover text-background font-medium rounded-lg text-xs transition-colors shadow-sm disabled:opacity-50"
              >
                {submittingBatch ? (
                  <>
                    <Loader2 size={13} className="animate-spin" />
                    Submitting All...
                  </>
                ) : (
                  <>
                    <CheckCheck size={13} />
                    Approve & Submit All ({pending.length})
                  </>
                )}
              </button>
            </div>

            <div className="bg-surface border border-warning/30 rounded-lg overflow-hidden shadow-sm">
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b border-border bg-surface-2">
                    <th className="text-left p-3 text-text-muted font-medium text-[10px] uppercase">Opportunity</th>
                    <th className="text-left p-3 text-text-muted font-medium text-[10px] uppercase">Company</th>
                    <th className="text-left p-3 text-text-muted font-medium text-[10px] uppercase">Match</th>
                    <th className="text-left p-3 text-text-muted font-medium text-[10px] uppercase">Documents</th>
                    <th className="text-left p-3 text-text-muted font-medium text-[10px] uppercase">Prepared</th>
                    <th className="text-right p-3 text-text-muted font-medium text-[10px] uppercase">Decision</th>
                  </tr>
                </thead>
                <tbody>
                  {pending.map(a => (
                    <tr key={a.id} className="border-b border-border/50 hover:bg-surface-2 transition-colors">
                      <td className="p-3">
                        <div className="font-medium text-text">{a.job_title || "Software Engineering Role"}</div>
                        <div className="font-mono text-text-muted text-[10px] mt-0.5">{a.id.slice(0, 8)}...</div>
                      </td>
                      <td className="p-3 text-text-muted font-medium">{a.company_name || "Enterprise"}</td>
                      <td className="p-3">
                        {a.match_score != null ? (
                          <span className="px-1.5 py-0.5 rounded font-mono font-bold text-[10px] bg-accent/10 text-accent border border-accent/20">
                            {a.match_score.toFixed(0)}%
                          </span>
                        ) : (
                          <span className="text-text-muted">—</span>
                        )}
                      </td>
                      <td className="p-3">
                        <div className="flex items-center gap-1.5">
                          <a
                            href={`http://localhost:8000/api/v1/applications/${a.id}/resume`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="px-2 py-0.5 bg-surface border border-border hover:border-accent/50 text-[10px] text-text rounded"
                            title="View Attached Resume PDF"
                          >
                            Resume
                          </a>
                          <a
                            href={`http://localhost:8000/api/v1/applications/${a.id}/cover-letter`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="px-2 py-0.5 bg-surface border border-border hover:border-accent/50 text-[10px] text-accent rounded"
                            title="View Generated Cover Letter PDF"
                          >
                            Cover Letter
                          </a>
                        </div>
                      </td>
                      <td className="p-3 font-mono text-text-muted">{formatDate(a.created_at)}</td>
                      <td className="p-3 text-right">
                        <div className="flex items-center justify-end gap-2">
                          {a.portal_url && (
                            <a
                              href={a.portal_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="p-1 text-text-muted hover:text-text rounded border border-border"
                              title="Inspect Job Portal"
                            >
                              <ExternalLink size={12} />
                            </a>
                          )}
                          <button
                            onClick={() => handleApprove(a.id)}
                            className="flex items-center gap-1 px-2.5 py-1 bg-success/10 text-success border border-success/30 rounded text-[11px] font-medium hover:bg-success/20 transition-colors"
                          >
                            <CheckCircle size={12} /> Approve & Submit
                          </button>
                          <button
                            onClick={() => handleReject(a.id)}
                            className="flex items-center gap-1 px-2.5 py-1 bg-danger/10 text-danger border border-danger/30 rounded text-[11px] font-medium hover:bg-danger/20 transition-colors"
                          >
                            <XCircle size={12} /> Reject
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        <div>
          <h2 className="text-xs font-semibold text-text uppercase tracking-wider mb-3">All Application History ({apps.length})</h2>
          <div className="bg-surface border border-border rounded-lg overflow-hidden shadow-sm">
            {loading ? (
              <div className="p-12 text-center text-text-muted text-xs">Loading application records...</div>
            ) : apps.length === 0 ? (
              <div className="p-12 text-center text-text-muted text-xs">No applications yet. Use Batch Apply on Dashboard or Matches to get started.</div>
            ) : (
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b border-border bg-surface-2">
                    <th className="text-left p-3 text-text-muted font-medium text-[10px] uppercase">Opportunity</th>
                    <th className="text-left p-3 text-text-muted font-medium text-[10px] uppercase">Company</th>
                    <th className="text-left p-3 text-text-muted font-medium text-[10px] uppercase">Status</th>
                    <th className="text-left p-3 text-text-muted font-medium text-[10px] uppercase">Score</th>
                    <th className="text-left p-3 text-text-muted font-medium text-[10px] uppercase">Documents</th>
                    <th className="text-left p-3 text-text-muted font-medium text-[10px] uppercase">Submitted At</th>
                    <th className="text-left p-3 text-text-muted font-medium text-[10px] uppercase">Created</th>
                  </tr>
                </thead>
                <tbody>
                  {apps.map(a => (
                    <tr key={a.id} className="border-b border-border/50 hover:bg-surface-2 transition-colors">
                      <td className="p-3">
                        <div className="font-medium text-text">{a.job_title || "Job Opportunity"}</div>
                        <div className="font-mono text-text-muted text-[10px]">{a.id.slice(0, 8)}...</div>
                      </td>
                      <td className="p-3 text-text-muted">{a.company_name || "—"}</td>
                      <td className="p-3">
                        <span className={statusColor(a.status)}>
                          {a.status === "submitted" ? "✓ Submitted" : a.status.replace(/_/g, " ")}
                        </span>
                      </td>
                      <td className="p-3 font-mono">
                        {a.match_score != null ? `${a.match_score.toFixed(0)}%` : "—"}
                      </td>
                      <td className="p-3">
                        <div className="flex items-center gap-1.5">
                          <a
                            href={`http://localhost:8000/api/v1/applications/${a.id}/resume`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="px-1.5 py-0.5 bg-surface border border-border hover:border-accent/50 text-[10px] text-text rounded"
                            title="View Attached Resume"
                          >
                            Resume
                          </a>
                          <a
                            href={`http://localhost:8000/api/v1/applications/${a.id}/cover-letter`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="px-1.5 py-0.5 bg-surface border border-border hover:border-accent/50 text-[10px] text-accent rounded"
                            title="View Generated Cover Letter"
                          >
                            Cover Letter
                          </a>
                        </div>
                      </td>
                      <td className="p-3 font-mono text-text-muted">{formatDate(a.submitted_at)}</td>
                      <td className="p-3 font-mono text-text-muted">{formatDate(a.created_at)}</td>
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
