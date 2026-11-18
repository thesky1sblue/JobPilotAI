"use client";
import { useEffect, useState } from "react";
import { TopBar } from "@/components/layout/TopBar";
import {
  getGmailMessages,
  syncGmailMessages,
  GmailRecruitmentMessage
} from "@/lib/api";
import { formatDate } from "@/lib/utils";
import {
  Mail,
  Calendar,
  Building2,
  AlertCircle,
  CheckCircle2,
  XCircle,
  HelpCircle,
  Clock,
  RefreshCw,
  ExternalLink,
  Loader2,
  Filter
} from "lucide-react";

export default function EmailsPage() {
  const [messages, setMessages] = useState<GmailRecruitmentMessage[]>([]);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [syncFeedback, setSyncFeedback] = useState<string | null>(null);
  const [selectedMessage, setSelectedMessage] = useState<GmailRecruitmentMessage | null>(null);
  const [classificationFilter, setClassificationFilter] = useState<string>("all");

  const loadMessages = async () => {
    setLoading(true);
    try {
      const items = await getGmailMessages(
        classificationFilter === "all" ? undefined : classificationFilter
      );
      setMessages(items);
      if (items.length > 0 && !selectedMessage) {
        setSelectedMessage(items[0]);
      } else if (selectedMessage) {
        const found = items.find((m) => m.id === selectedMessage.id);
        if (found) setSelectedMessage(found);
      }
    } catch (err) {
      console.error("Failed to load emails", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadMessages();
  }, [classificationFilter]);

  const handleSync = async () => {
    setSyncing(true);
    setSyncFeedback(null);
    try {
      const res = await syncGmailMessages();
      setSyncFeedback(`Scanned ${res.processed_count} messages, linked ${res.matched_count} to active applications.`);
      await loadMessages();
    } catch (err: any) {
      setSyncFeedback("Sync failed: " + (err?.response?.data?.detail || err.message));
    } finally {
      setSyncing(false);
    }
  };

  const getBadgeClass = (classification: string) => {
    switch (classification) {
      case "interview":
        return "bg-success/20 text-success border-success/30";
      case "assessment":
        return "bg-warning/20 text-warning border-warning/30";
      case "acknowledgement":
        return "bg-info/20 text-info border-info/30";
      case "rejection":
        return "bg-danger/20 text-danger border-danger/30";
      default:
        return "bg-surface-2 text-text-muted border-border";
    }
  };

  const getIcon = (classification: string) => {
    switch (classification) {
      case "interview":
        return <Calendar size={13} className="text-success" />;
      case "assessment":
        return <Clock size={13} className="text-warning" />;
      case "acknowledgement":
        return <CheckCircle2 size={13} className="text-info" />;
      case "rejection":
        return <XCircle size={13} className="text-danger" />;
      default:
        return <Mail size={13} className="text-text-muted" />;
    }
  };

  return (
    <div className="flex flex-col h-full bg-background text-text">
      <TopBar
        title="Email Intelligence (Gmail API)"
        subtitle="Automatic detection of application acknowledgements, technical assessments, interviews, and deadlines"
      />

      <div className="flex-1 overflow-hidden flex flex-col md:flex-row">
        {/* Left: Message list */}
        <div className="w-full md:w-96 border-r border-border flex flex-col bg-surface">
          <div className="p-3 border-b border-border flex items-center justify-between gap-2">
            <div className="flex items-center gap-1 overflow-x-auto">
              {["all", "interview", "assessment", "acknowledgement", "rejection"].map((cat) => (
                <button
                  key={cat}
                  onClick={() => setClassificationFilter(cat)}
                  className={`px-2 py-1 text-[11px] rounded font-medium capitalize whitespace-nowrap transition-colors ${
                    classificationFilter === cat
                      ? "bg-accent text-background font-semibold"
                      : "text-text-muted hover:text-text hover:bg-surface-2"
                  }`}
                >
                  {cat}
                </button>
              ))}
            </div>

            <button
              onClick={handleSync}
              disabled={syncing}
              className="p-1.5 bg-surface-2 hover:bg-surface-2/80 rounded text-text text-xs border border-border transition-colors flex items-center gap-1"
              title="Sync Inbound Emails"
            >
              <RefreshCw size={12} className={syncing ? "animate-spin text-accent" : ""} />
            </button>
          </div>

          {syncFeedback && (
            <div className="p-2.5 bg-accent/10 border-b border-accent/20 text-[11px] text-accent">
              {syncFeedback}
            </div>
          )}

          <div className="flex-1 overflow-y-auto divide-y divide-border/60">
            {loading && messages.length === 0 ? (
              <div className="p-6 text-center text-xs text-text-muted flex items-center justify-center gap-2">
                <Loader2 size={14} className="animate-spin text-accent" /> Scanning recruitment mailbox...
              </div>
            ) : messages.length === 0 ? (
              <div className="p-6 text-center text-xs text-text-muted">
                No recruitment emails matching this filter.
              </div>
            ) : (
              messages.map((item) => {
                const isSelected = selectedMessage?.id === item.id;
                return (
                  <button
                    key={item.id}
                    onClick={() => setSelectedMessage(item)}
                    className={`w-full text-left p-3.5 transition-colors flex flex-col gap-1.5 ${
                      isSelected ? "bg-accent/10 border-l-2 border-accent" : "hover:bg-surface-2"
                    }`}
                  >
                    <div className="flex items-center justify-between gap-2">
                      <span className="font-semibold text-xs text-text line-clamp-1">{item.sender}</span>
                      <span className="text-[10px] text-text-muted font-mono whitespace-nowrap">
                        {new Date(item.received_at).toLocaleDateString([], { month: "short", day: "numeric" })}
                      </span>
                    </div>

                    <div className="text-xs text-text font-medium line-clamp-1">{item.subject}</div>

                    <div className="flex items-center justify-between gap-2 mt-1">
                      <span
                        className={`inline-flex items-center gap-1 text-[10px] px-2 py-0.5 rounded-full font-mono uppercase border ${getBadgeClass(
                          item.classification
                        )}`}
                      >
                        {getIcon(item.classification)}
                        {item.classification}
                      </span>

                      {item.company_domain && (
                        <span className="text-[10px] text-text-muted font-mono">
                          @{item.company_domain}
                        </span>
                      )}
                    </div>
                  </button>
                );
              })
            )}
          </div>
        </div>

        {/* Right: Message Detail & Extracted Action Items */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6 bg-background">
          {selectedMessage ? (
            <div className="max-w-4xl mx-auto space-y-6">
              {/* Message Header */}
              <div className="p-5 bg-surface border border-border rounded-lg space-y-4">
                <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3">
                  <div>
                    <h2 className="text-base font-bold text-text">{selectedMessage.subject}</h2>
                    <div className="text-xs text-text-muted mt-1 space-y-0.5">
                      <div>From: <strong className="text-text">{selectedMessage.sender}</strong></div>
                      <div>To: {selectedMessage.recipient}</div>
                      <div>Received: {formatDate(selectedMessage.received_at)}</div>
                    </div>
                  </div>

                  <span
                    className={`inline-flex items-center gap-1.5 text-xs px-3 py-1 rounded-full font-mono uppercase border font-semibold ${getBadgeClass(
                      selectedMessage.classification
                    )}`}
                  >
                    {getIcon(selectedMessage.classification)}
                    {selectedMessage.classification} ({Math.round(selectedMessage.confidence_score * 100)}%)
                  </span>
                </div>

                {/* Classification & Linked Company Badge */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-3 border-t border-border">
                  <div className="flex items-center gap-2 text-xs">
                    <Building2 size={15} className="text-accent" />
                    <span className="text-text-muted">Associated Company:</span>
                    <strong className="text-text font-mono">
                      {selectedMessage.company_domain || "Unknown Domain"}
                    </strong>
                  </div>

                  <div className="flex items-center gap-2 text-xs">
                    <Clock size={15} className="text-warning" />
                    <span className="text-text-muted">Detected Deadline:</span>
                    <strong className="text-text font-mono">
                      {selectedMessage.deadline ? formatDate(selectedMessage.deadline) : "None extracted"}
                    </strong>
                  </div>
                </div>
              </div>

              {/* Action Item Alert */}
              {selectedMessage.action_required && selectedMessage.suggested_action && (
                <div className="p-4 bg-warning/10 border border-warning/30 rounded-lg flex items-start gap-3">
                  <AlertCircle size={18} className="text-warning shrink-0 mt-0.5" />
                  <div>
                    <h4 className="text-xs font-semibold text-warning uppercase font-mono tracking-wider">
                      Action Item Required
                    </h4>
                    <p className="text-xs text-text mt-1">{selectedMessage.suggested_action}</p>
                  </div>
                </div>
              )}

              {/* Linked Application Pill */}
              {selectedMessage.application_id && (
                <div className="p-3 bg-surface-2 border border-border rounded-lg flex items-center justify-between text-xs">
                  <div className="flex items-center gap-2">
                    <CheckCircle2 size={15} className="text-success" />
                    <span className="text-text-muted">Linked Application ID:</span>
                    <span className="font-mono text-accent font-semibold">{selectedMessage.application_id}</span>
                  </div>
                  <span className="text-[10px] text-text-muted font-mono">Auto-matched</span>
                </div>
              )}

              {/* Email Content Body */}
              <div className="p-5 bg-surface border border-border rounded-lg space-y-3">
                <h3 className="text-xs font-semibold text-text uppercase tracking-wider font-mono">
                  Message Body
                </h3>
                <div className="p-4 bg-surface-2 border border-border/50 rounded text-xs text-text font-mono whitespace-pre-wrap leading-relaxed">
                  {selectedMessage.snippet}
                </div>
              </div>
            </div>
          ) : (
            <div className="h-full flex items-center justify-center text-xs text-text-muted">
              Select an email from the inbox list to inspect classification details.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
