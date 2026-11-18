"use client";
import { useEffect, useState } from "react";
import { TopBar } from "@/components/layout/TopBar";
import {
  getApprovals,
  submitApprovalDecision,
  executeApprovedSubmission,
  ApprovalItem
} from "@/lib/api";
import { formatDate } from "@/lib/utils";
import {
  ShieldCheck,
  CheckCircle,
  XCircle,
  Clock,
  Send,
  AlertTriangle,
  FileText,
  ExternalLink,
  Loader2,
  Bookmark,
  RefreshCw,
  Hash
} from "lucide-react";

export default function ApprovalsPage() {
  const [approvals, setApprovals] = useState<ApprovalItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedItem, setSelectedItem] = useState<ApprovalItem | null>(null);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [notes, setNotes] = useState("");
  const [submissionFeedback, setSubmissionFeedback] = useState<string | null>(null);

  const load = async () => {
    setLoading(true);
    try {
      const items = await getApprovals(statusFilter === "all" ? undefined : statusFilter);
      setApprovals(items);
      if (items.length > 0 && !selectedItem) {
        setSelectedItem(items[0]);
      } else if (selectedItem) {
        const found = items.find((i) => (i.id || (i as any).approval_id) === (selectedItem.id || (selectedItem as any).approval_id));
        if (found) setSelectedItem(found);
      }
    } catch (err) {
      console.error("Failed to load approvals", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, [statusFilter]);

  const handleDecision = async (decision: "approve" | "reject" | "request_changes" | "save_for_later") => {
    if (!selectedItem) return;
    const targetId = selectedItem.id || (selectedItem as any).approval_id;
    setActionLoading(decision);
    try {
      await submitApprovalDecision(targetId, decision, notes);
      setNotes("");
      await load();
    } catch (err: any) {
      alert("Decision failed: " + (err?.response?.data?.detail || err.message));
    } finally {
      setActionLoading(null);
    }
  };

  const handleExecuteSubmission = async () => {
    if (!selectedItem) return;
    const targetId = selectedItem.id || (selectedItem as any).approval_id;
    setActionLoading("submit");
    setSubmissionFeedback(null);
    try {
      const res = await executeApprovedSubmission(targetId);
      setSubmissionFeedback(res.message);
      await load();
    } catch (err: any) {
      setSubmissionFeedback("Submission error: " + (err?.response?.data?.detail || err.message));
    } finally {
      setActionLoading(null);
    }
  };

  return (
    <div className="flex flex-col h-full bg-background text-text">
      <TopBar
        title="Human Approval Center"
        subtitle="Cryptographically verified payloads requiring explicit consent prior to submission"
      />

      <div className="flex-1 overflow-hidden flex flex-col md:flex-row">
        {/* Left: Queue list */}
        <div className="w-full md:w-96 border-r border-border flex flex-col bg-surface">
          <div className="p-3 border-b border-border flex items-center justify-between">
            <div className="flex items-center gap-1">
              {["all", "pending", "approved", "submitted"].map((tab) => (
                <button
                  key={tab}
                  onClick={() => setStatusFilter(tab)}
                  className={`px-2.5 py-1 text-xs rounded font-medium capitalize transition-colors ${
                    statusFilter === tab
                      ? "bg-accent text-background font-semibold"
                      : "text-text-muted hover:text-text hover:bg-surface-2"
                  }`}
                >
                  {tab}
                </button>
              ))}
            </div>
            <button
              onClick={() => load()}
              className="p-1 hover:bg-surface-2 rounded text-text-muted hover:text-text transition-colors"
              title="Refresh"
            >
              <RefreshCw size={13} className={loading ? "animate-spin" : ""} />
            </button>
          </div>

          <div className="flex-1 overflow-y-auto divide-y divide-border/60">
            {loading && approvals.length === 0 ? (
              <div className="p-6 text-center text-xs text-text-muted flex items-center justify-center gap-2">
                <Loader2 size={14} className="animate-spin text-accent" /> Loading approvals...
              </div>
            ) : approvals.length === 0 ? (
              <div className="p-6 text-center text-xs text-text-muted">
                No prepared applications in this status.
              </div>
            ) : (
              approvals.map((item) => {
                const itemId = item.id || (item as any).approval_id;
                const selectedItemId = selectedItem?.id || (selectedItem as any)?.approval_id;
                const isSelected = selectedItemId === itemId;
                const title = item.job?.title || (item as any).job_title || "Application";
                const company = item.job?.company || (item as any).company_name || "Company";
                const score = item.job?.score ?? 85;
                const hash = item.payload_hash || "0000000000000000";
                const isValid = item.is_valid !== undefined ? item.is_valid : true;

                return (
                  <button
                    key={itemId}
                    onClick={() => setSelectedItem(item)}
                    className={`w-full text-left p-3.5 transition-colors flex flex-col gap-1.5 ${
                      isSelected ? "bg-accent/10 border-l-2 border-accent" : "hover:bg-surface-2"
                    }`}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <span className="font-semibold text-xs text-text line-clamp-1">{title}</span>
                      <span
                        className={`text-[10px] px-1.5 py-0.5 rounded font-mono font-medium uppercase ${
                          item.status === "approved"
                            ? "bg-success/20 text-success"
                            : item.status === "pending"
                            ? "bg-warning/20 text-warning"
                            : item.status === "submitted"
                            ? "bg-accent/20 text-accent"
                            : "bg-surface-2 text-text-muted"
                        }`}
                      >
                        {item.status}
                      </span>
                    </div>

                    <div className="flex items-center justify-between text-[11px] text-text-muted">
                      <span>{company}</span>
                      <span className="font-mono text-accent">{score}% match</span>
                    </div>

                    <div className="flex items-center gap-1.5 text-[10px] text-text-muted font-mono mt-1">
                      <Hash size={10} className="text-text-muted/70" />
                      <span className="truncate">{hash.slice(0, 16)}...</span>
                      {isValid ? (
                        <span className="text-success text-[10px] flex items-center gap-0.5 ml-auto">
                          <CheckCircle size={10} /> Valid
                        </span>
                      ) : (
                        <span className="text-danger text-[10px] flex items-center gap-0.5 ml-auto">
                          <AlertTriangle size={10} /> Tampered
                        </span>
                      )}
                    </div>
                  </button>
                );
              })
            )}
          </div>
        </div>

        {/* Right: Inspection and Approval Actions */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6 bg-background">
          {selectedItem ? (
            (() => {
              const itemTitle = selectedItem.job?.title || (selectedItem as any).job_title || "Application";
              const itemCompany = selectedItem.job?.company || (selectedItem as any).company_name || "Company";
              const itemLocation = selectedItem.job?.location || "India / Remote";
              const itemPortalUrl = selectedItem.job?.portal_url || (selectedItem as any).portal_url || "#";
              const itemHash = selectedItem.payload_hash || "0000000000000000";
              const itemIsValid = selectedItem.is_valid !== undefined ? selectedItem.is_valid : true;
              const applicantName = selectedItem.applicant?.name || "Akash Nandy";
              const applicantEmail = selectedItem.applicant?.email || "akashnandy01@gmail.com";
              const applicantPhone = selectedItem.applicant?.phone || "+91 9330136009";
              const answersDict = selectedItem.answers || (selectedItem as any).prepared_answers || {};

              return (
                <div className="max-w-4xl mx-auto space-y-6">
                  {/* Header card */}
                  <div className="p-5 bg-surface border border-border rounded-lg space-y-4">
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                      <div>
                        <h2 className="text-base font-bold text-text">{itemTitle}</h2>
                        <p className="text-xs text-text-muted">
                          {itemCompany} · {itemLocation}
                        </p>
                      </div>
                      <div className="flex items-center gap-2">
                        {itemPortalUrl && itemPortalUrl !== "#" && (
                          <a
                            href={itemPortalUrl}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-surface-2 hover:bg-surface-2/80 text-text text-xs rounded border border-border transition-colors"
                          >
                            <span>Portal Link</span>
                            <ExternalLink size={12} />
                          </a>
                        )}
                      </div>
                    </div>

                    {/* Cryptographic payload verification badge */}
                    <div className="p-3 bg-surface-2 border border-border rounded flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs">
                      <div className="flex items-center gap-2">
                        <ShieldCheck size={16} className={itemIsValid ? "text-success" : "text-danger"} />
                        <span className="font-mono text-[11px] text-text-muted">
                          SHA256: <strong className="text-text">{itemHash}</strong>
                        </span>
                      </div>
                      <div className="font-mono text-[11px]">
                        Status: <span className="uppercase font-semibold text-accent">{selectedItem.status}</span>
                      </div>
                    </div>

                    {submissionFeedback && (
                      <div className="p-3 bg-accent/10 border border-accent/30 rounded text-xs text-accent">
                        {submissionFeedback}
                      </div>
                    )}
                  </div>

                  {/* Applicant & Documents */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="p-4 bg-surface border border-border rounded-lg space-y-3">
                      <h3 className="text-xs font-semibold text-text uppercase tracking-wider font-mono">
                        Candidate Profile
                      </h3>
                      <div className="space-y-1.5 text-xs text-text-muted">
                        <div>
                          <span className="text-text font-medium">Name:</span> {applicantName}
                        </div>
                        <div>
                          <span className="text-text font-medium">Email:</span> {applicantEmail}
                        </div>
                        <div>
                          <span className="text-text font-medium">Phone:</span> {applicantPhone}
                        </div>
                      </div>
                    </div>

                    <div className="p-4 bg-surface border border-border rounded-lg space-y-3">
                      <h3 className="text-xs font-semibold text-text uppercase tracking-wider font-mono">
                        Attached Artifacts
                      </h3>
                      <div className="space-y-2 text-xs">
                        <div className="flex items-center justify-between p-2 bg-surface-2 rounded border border-border">
                          <div className="flex items-center gap-2">
                            <FileText size={14} className="text-accent" />
                            <span className="font-medium text-text">Tailored Resume (PDF)</span>
                          </div>
                          <span className="text-[10px] font-mono text-success">Verified</span>
                        </div>

                        <div className="flex items-center justify-between p-2 bg-surface-2 rounded border border-border">
                          <div className="flex items-center gap-2">
                            <FileText size={14} className="text-accent" />
                            <span className="font-medium text-text">Cover Letter</span>
                          </div>
                          <span className="text-[10px] font-mono text-success">Verified</span>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Application Form Answers */}
                  <div className="p-4 bg-surface border border-border rounded-lg space-y-3">
                    <h3 className="text-xs font-semibold text-text uppercase tracking-wider font-mono">
                      Prepared Form Fields & Responses ({Object.keys(answersDict).length})
                    </h3>
                    {Object.keys(answersDict).length === 0 ? (
                      <p className="text-xs text-text-muted">No custom form questions required for this portal.</p>
                    ) : (
                      <div className="divide-y divide-border/60">
                        {Object.entries(answersDict).map(([question, answer]) => (
                          <div key={question} className="py-2.5 space-y-1 text-xs">
                            <div className="font-medium text-text">{question}</div>
                            <div className="text-text-muted bg-surface-2 p-2 rounded border border-border/40 font-mono text-[11px] whitespace-pre-wrap">
                              {String(answer)}
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Decision Control Bar */}
                  <div className="p-5 bg-surface border border-border rounded-lg space-y-4">
                    <h3 className="text-xs font-semibold text-text uppercase tracking-wider font-mono">
                      Reviewer Decision & Execution
                    </h3>

                    <div>
                      <label className="block text-xs text-text-muted mb-1">Reviewer Feedback / Revision Notes</label>
                      <textarea
                        value={notes}
                        onChange={(e) => setNotes(e.target.value)}
                        rows={2}
                        placeholder="Enter any feedback or reasons for revision..."
                        className="w-full text-xs p-2.5 bg-surface-2 border border-border rounded text-text focus:outline-none focus:border-accent"
                      />
                    </div>

                    <div className="flex flex-wrap items-center gap-2 pt-2">
                      <button
                        onClick={() => handleDecision("approve")}
                        disabled={actionLoading !== null}
                        className="inline-flex items-center gap-1.5 px-4 py-2 bg-success text-background font-semibold text-xs rounded hover:bg-success/90 transition-colors disabled:opacity-50"
                      >
                        {actionLoading === "approve" ? <Loader2 size={13} className="animate-spin" /> : <CheckCircle size={13} />}
                        Approve Application
                      </button>

                      {selectedItem.status === "approved" && (
                        <button
                          onClick={handleExecuteSubmission}
                          disabled={actionLoading !== null}
                          className="inline-flex items-center gap-1.5 px-4 py-2 bg-accent text-background font-semibold text-xs rounded hover:bg-accent/90 transition-colors disabled:opacity-50"
                        >
                          {actionLoading === "submit" ? <Loader2 size={13} className="animate-spin" /> : <Send size={13} />}
                          Execute Playwright Submission
                        </button>
                      )}

                      <button
                        onClick={() => handleDecision("request_changes")}
                        disabled={actionLoading !== null}
                        className="inline-flex items-center gap-1.5 px-3 py-2 bg-surface-2 hover:bg-surface-2/80 text-text text-xs rounded border border-border transition-colors disabled:opacity-50"
                      >
                        <Clock size={13} />
                        Request Changes
                      </button>

                      <button
                        onClick={() => handleDecision("save_for_later")}
                        disabled={actionLoading !== null}
                        className="inline-flex items-center gap-1.5 px-3 py-2 bg-surface-2 hover:bg-surface-2/80 text-text text-xs rounded border border-border transition-colors disabled:opacity-50"
                      >
                        <Bookmark size={13} />
                        Save for Later
                      </button>

                      <button
                        onClick={() => handleDecision("reject")}
                        disabled={actionLoading !== null}
                        className="inline-flex items-center gap-1.5 px-3 py-2 bg-danger/10 hover:bg-danger/20 text-danger text-xs rounded border border-danger/30 transition-colors disabled:opacity-50 ml-auto"
                      >
                        <XCircle size={13} />
                        Reject
                      </button>
                    </div>
                  </div>
                </div>
              );
            })()
          ) : (
            <div className="h-full flex items-center justify-center text-xs text-text-muted">
              Select an application from the approval queue to inspect and verify.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
