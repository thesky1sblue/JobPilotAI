"use client";
import { useEffect, useState } from "react";
import { TopBar } from "@/components/layout/TopBar";
import { getSubmissionReceipts, SubmissionReceipt } from "@/lib/api";
import { formatDate } from "@/lib/utils";
import { Mail, CheckCircle, Copy, ExternalLink, FileText, Send, Building2 } from "lucide-react";

export default function NotificationsPage() {
  const [receipts, setReceipts] = useState<SubmissionReceipt[]>([]);
  const [selected, setSelected] = useState<SubmissionReceipt | null>(null);
  const [loading, setLoading] = useState(true);
  const [copiedId, setCopiedId] = useState<string | null>(null);

  useEffect(() => {
    getSubmissionReceipts()
      .then(data => {
        setReceipts(data);
        if (data.length > 0) setSelected(data[0]);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const handleCopy = (id: string) => {
    navigator.clipboard.writeText(id);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2500);
  };

  return (
    <div className="flex flex-col h-full">
      <TopBar
        title="Application Confirmations & Receipts"
        subtitle={`${receipts.length} verified submission receipts with confirmation IDs for akashnandy01@gmail.com`}
      />

      <div className="flex flex-1 overflow-hidden">
        {/* Receipt List */}
        <div className="w-88 border-r border-border overflow-auto bg-surface/50">
          <div className="p-3 border-b border-border bg-surface-2 text-xs font-semibold text-text uppercase tracking-wider flex items-center justify-between">
            <span className="flex items-center gap-1.5">
              <Mail size={13} className="text-accent" /> Submission Notices
            </span>
            <span className="px-1.5 py-0.5 rounded text-[10px] font-mono bg-accent/10 text-accent border border-accent/20">
              {receipts.length}
            </span>
          </div>

          {loading ? (
            <div className="p-8 text-center text-text-muted text-xs">Loading submission receipts...</div>
          ) : receipts.length === 0 ? (
            <div className="p-8 text-center text-text-muted text-xs">
              No applications submitted yet. Approve applications from the Queue to generate confirmation records.
            </div>
          ) : (
            <div>
              {receipts.map(r => (
                <button
                  key={r.application_id}
                  onClick={() => setSelected(r)}
                  className={`w-full text-left p-3.5 border-b border-border/50 hover:bg-surface-2 transition-colors ${
                    selected?.application_id === r.application_id ? "bg-surface-2 border-l-2 border-l-accent" : ""
                  }`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="min-w-0">
                      <div className="text-xs font-semibold text-text truncate">{r.company_name}</div>
                      <div className="text-[11px] text-text-muted truncate mt-0.5">{r.job_title}</div>
                    </div>
                    <span className="text-[10px] font-mono text-success flex items-center gap-1 shrink-0 bg-success/10 px-1.5 py-0.5 rounded border border-success/20">
                      <CheckCircle size={10} /> Logged
                    </span>
                  </div>
                  <div className="mt-2 flex items-center justify-between text-[10px] text-text-muted font-mono">
                    <span className="text-accent">{r.submission_id}</span>
                    <span>{formatDate(r.submitted_at)}</span>
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Email Receipt View */}
        <div className="flex-1 overflow-auto p-6 bg-surface">
          {!selected ? (
            <div className="flex items-center justify-center h-full text-text-muted text-xs">
              Select an application confirmation receipt from the left
            </div>
          ) : (
            <div className="max-w-2xl mx-auto space-y-6">
              {/* Receipt Header Card */}
              <div className="bg-surface-2 border border-border rounded-xl p-5 shadow-sm space-y-4">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <span className="text-[10px] uppercase tracking-wider font-semibold text-text-muted">
                      Official Application Confirmation
                    </span>
                    <h2 className="text-base font-bold text-text mt-0.5">{selected.email_subject}</h2>
                  </div>
                  <div className="text-right">
                    <span className="text-[10px] font-mono text-text-muted">Submission Reference</span>
                    <div className="flex items-center gap-1.5 mt-0.5">
                      <span className="px-2 py-1 bg-surface border border-accent/40 text-accent font-mono text-xs font-bold rounded">
                        {selected.submission_id}
                      </span>
                      <button
                        onClick={() => handleCopy(selected.submission_id)}
                        className="p-1 hover:bg-surface rounded text-text-muted hover:text-text border border-border"
                        title="Copy Submission ID"
                      >
                        <Copy size={12} />
                      </button>
                    </div>
                    {copiedId === selected.submission_id && (
                      <span className="text-[10px] text-success block mt-1 font-mono">Copied to clipboard!</span>
                    )}
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3 pt-3 border-t border-border text-xs">
                  <div>
                    <span className="text-text-muted block text-[10px] uppercase">Applicant</span>
                    <span className="text-text font-medium">{selected.recipient_name}</span>
                    <span className="text-text-muted block text-[11px] font-mono mt-0.5">{selected.recipient_email}</span>
                  </div>
                  <div>
                    <span className="text-text-muted block text-[10px] uppercase">Employer & Portal</span>
                    <span className="text-text font-medium flex items-center gap-1">
                      <Building2 size={12} /> {selected.company_name}
                    </span>
                    <span className="text-text-muted block text-[11px] mt-0.5">Submitted: {formatDate(selected.submitted_at)}</span>
                  </div>
                </div>
              </div>

              {/* Formatted Confirmation Email Body */}
              <div className="bg-surface border border-border rounded-xl p-6 shadow-sm">
                <div className="text-[10px] uppercase tracking-wider font-semibold text-text-muted mb-3 flex items-center gap-1.5">
                  <Mail size={12} className="text-accent" /> Registered Confirmation Notice
                </div>
                <div className="text-xs text-text leading-relaxed font-mono whitespace-pre-wrap bg-surface-2 p-4 rounded-lg border border-border">
                  {selected.email_body}
                </div>
              </div>

              {/* Submitted Assets */}
              <div className="bg-surface border border-border rounded-xl p-5 shadow-sm">
                <h3 className="text-xs font-semibold text-text uppercase tracking-wider mb-3">
                  Submitted Ground-Truth Assets
                </h3>
                <div className="flex items-center gap-3">
                  <a
                    href={selected.resume_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-2 px-3 py-2 bg-surface-2 hover:bg-surface text-text border border-border rounded-lg text-xs transition-colors"
                  >
                    <FileText size={14} className="text-accent" />
                    <span>View Submitted Resume PDF</span>
                    <ExternalLink size={11} className="text-text-muted" />
                  </a>

                  {selected.cover_letter_url && (
                    <a
                      href={selected.cover_letter_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center gap-2 px-3 py-2 bg-surface-2 hover:bg-surface text-accent border border-accent/30 rounded-lg text-xs transition-colors"
                    >
                      <FileText size={14} />
                      <span>View Custom Cover Letter PDF</span>
                      <ExternalLink size={11} className="text-accent/70" />
                    </a>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
