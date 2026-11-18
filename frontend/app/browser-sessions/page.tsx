"use client";
import { useEffect, useState } from "react";
import { TopBar } from "@/components/layout/TopBar";
import {
  getBrowserSessions,
  BrowserSessionItem
} from "@/lib/api";
import { formatDate } from "@/lib/utils";
import {
  Globe,
  Camera,
  CheckCircle,
  AlertTriangle,
  ShieldAlert,
  ExternalLink,
  RefreshCw,
  FileText,
  Loader2,
  Layers
} from "lucide-react";

export default function BrowserSessionsPage() {
  const [sessions, setSessions] = useState<BrowserSessionItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedSession, setSelectedSession] = useState<BrowserSessionItem | null>(null);

  const loadSessions = async () => {
    setLoading(true);
    try {
      const items = await getBrowserSessions(50);
      setSessions(items);
      if (items.length > 0 && !selectedSession) {
        setSelectedSession(items[0]);
      } else if (selectedSession) {
        const found = items.find((s) => s.id === selectedSession.id);
        if (found) setSelectedSession(found);
      }
    } catch (err) {
      console.error("Failed to load browser sessions", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSessions();
  }, []);

  return (
    <div className="flex flex-col h-full bg-background text-text">
      <TopBar
        title="Browser Automation Sessions"
        subtitle="Playwright browser lifecycle, ATS form inspection, automated field mapping, and visual audit screenshots"
      />

      <div className="flex-1 overflow-hidden flex flex-col md:flex-row">
        {/* Left: Sessions List */}
        <div className="w-full md:w-96 border-r border-border flex flex-col bg-surface">
          <div className="p-3 border-b border-border flex items-center justify-between">
            <h3 className="text-xs font-semibold text-text uppercase tracking-wider font-mono">
              Automation Sessions ({sessions.length})
            </h3>
            <button
              onClick={() => loadSessions()}
              className="p-1 hover:bg-surface-2 rounded text-text-muted hover:text-text transition-colors"
              title="Refresh"
            >
              <RefreshCw size={13} className={loading ? "animate-spin" : ""} />
            </button>
          </div>

          <div className="flex-1 overflow-y-auto divide-y divide-border/60">
            {loading && sessions.length === 0 ? (
              <div className="p-6 text-center text-xs text-text-muted flex items-center justify-center gap-2">
                <Loader2 size={14} className="animate-spin text-accent" /> Loading browser sessions...
              </div>
            ) : sessions.length === 0 ? (
              <div className="p-6 text-center text-xs text-text-muted">
                No browser automation sessions recorded yet.
              </div>
            ) : (
              sessions.map((item) => {
                const isSelected = selectedSession?.id === item.id;
                return (
                  <button
                    key={item.id}
                    onClick={() => setSelectedSession(item)}
                    className={`w-full text-left p-3.5 transition-colors flex flex-col gap-1.5 ${
                      isSelected ? "bg-accent/10 border-l-2 border-accent" : "hover:bg-surface-2"
                    }`}
                  >
                    <div className="flex items-center justify-between gap-2">
                      <span className="font-semibold text-xs text-text capitalize">
                        {item.ats_type} Portal
                      </span>
                      <span
                        className={`text-[10px] px-1.5 py-0.5 rounded font-mono font-medium ${
                          item.success
                            ? "bg-success/20 text-success"
                            : "bg-danger/20 text-danger"
                        }`}
                      >
                        {item.success ? "Verified" : "Failed"}
                      </span>
                    </div>

                    <div className="text-[11px] text-text-muted font-mono truncate">
                      {item.portal_url}
                    </div>

                    <div className="flex items-center justify-between text-[10px] text-text-muted mt-1 font-mono">
                      <span>Fields: {Object.keys(item.field_mappings || {}).length}</span>
                      <span>{new Date(item.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</span>
                    </div>
                  </button>
                );
              })
            )}
          </div>
        </div>

        {/* Right: Inspection details and Screenshots */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6 bg-background">
          {selectedSession ? (
            <div className="max-w-4xl mx-auto space-y-6">
              {/* Session Overview Card */}
              <div className="p-5 bg-surface border border-border rounded-lg space-y-4">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                  <div>
                    <h2 className="text-base font-bold text-text capitalize">
                      {selectedSession.ats_type} Application Session
                    </h2>
                    <p className="text-xs text-text-muted font-mono mt-0.5 truncate max-w-xl">
                      {selectedSession.portal_url}
                    </p>
                  </div>

                  <a
                    href={selectedSession.portal_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-surface-2 hover:bg-surface-2/80 text-text text-xs rounded border border-border transition-colors shrink-0"
                  >
                    <span>Open Portal</span>
                    <ExternalLink size={12} />
                  </a>
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-3 border-t border-border text-xs">
                  <div>
                    <span className="text-text-muted text-[11px] block">ATS Detected</span>
                    <strong className="text-text font-mono uppercase">{selectedSession.ats_type}</strong>
                  </div>
                  <div>
                    <span className="text-text-muted text-[11px] block">Execution Mode</span>
                    <strong className="text-text font-mono">
                      {selectedSession.is_headful ? "Headful GUI" : "Headless Engine"}
                    </strong>
                  </div>
                  <div>
                    <span className="text-text-muted text-[11px] block">Anti-Bot Shield</span>
                    <strong className={`font-mono ${selectedSession.anti_bot_detected ? "text-danger" : "text-success"}`}>
                      {selectedSession.anti_bot_detected ? "Detected" : "Clean"}
                    </strong>
                  </div>
                  <div>
                    <span className="text-text-muted text-[11px] block">Execution Time</span>
                    <strong className="text-text font-mono">{formatDate(selectedSession.created_at)}</strong>
                  </div>
                </div>

                {selectedSession.error_message && (
                  <div className="p-3 bg-danger/10 border border-danger/30 rounded text-xs text-danger flex items-center gap-2">
                    <AlertTriangle size={15} className="shrink-0" />
                    <span>{selectedSession.error_message}</span>
                  </div>
                )}
              </div>

              {/* Visual Audit Screenshots */}
              <div className="p-5 bg-surface border border-border rounded-lg space-y-4">
                <div className="flex items-center gap-2">
                  <Camera size={16} className="text-accent" />
                  <h3 className="text-xs font-semibold text-text uppercase tracking-wider font-mono">
                    Visual Evidence & Verification Screenshots
                  </h3>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* Pre-submission Screenshot */}
                  <div className="space-y-2">
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-semibold text-text">Pre-Submit Inspection</span>
                      <span className="text-[10px] font-mono text-text-muted">Form Filled</span>
                    </div>
                    {selectedSession.pre_submit_screenshot ? (
                      <div className="border border-border rounded overflow-hidden bg-black/40">
                        <img
                          src={`http://127.0.0.1:8000/api/v1/browser/screenshots/${selectedSession.pre_submit_screenshot}`}
                          alt="Pre-submission form screenshot"
                          className="w-full h-auto object-cover max-h-80"
                          onError={(e) => {
                            (e.target as HTMLElement).style.display = "none";
                          }}
                        />
                        <div className="p-2 text-[10px] font-mono text-text-muted border-t border-border">
                          {selectedSession.pre_submit_screenshot}
                        </div>
                      </div>
                    ) : (
                      <div className="h-44 border border-dashed border-border rounded flex flex-col items-center justify-center text-xs text-text-muted gap-1">
                        <Camera size={20} className="text-text-muted/40" />
                        <span>No pre-submission screenshot recorded</span>
                      </div>
                    )}
                  </div>

                  {/* Post-submission Screenshot */}
                  <div className="space-y-2">
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-semibold text-text">Post-Submit Confirmation</span>
                      <span className="text-[10px] font-mono text-text-muted">Portal Response</span>
                    </div>
                    {selectedSession.post_submit_screenshot ? (
                      <div className="border border-border rounded overflow-hidden bg-black/40">
                        <img
                          src={`http://127.0.0.1:8000/api/v1/browser/screenshots/${selectedSession.post_submit_screenshot}`}
                          alt="Post-submission confirmation screenshot"
                          className="w-full h-auto object-cover max-h-80"
                          onError={(e) => {
                            (e.target as HTMLElement).style.display = "none";
                          }}
                        />
                        <div className="p-2 text-[10px] font-mono text-text-muted border-t border-border">
                          {selectedSession.post_submit_screenshot}
                        </div>
                      </div>
                    ) : (
                      <div className="h-44 border border-dashed border-border rounded flex flex-col items-center justify-center text-xs text-text-muted gap-1">
                        <Camera size={20} className="text-text-muted/40" />
                        <span>Awaiting final submission trigger</span>
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* Form Field Mappings */}
              <div className="p-5 bg-surface border border-border rounded-lg space-y-3">
                <div className="flex items-center gap-2">
                  <Layers size={16} className="text-accent" />
                  <h3 className="text-xs font-semibold text-text uppercase tracking-wider font-mono">
                    Field Mapping Dictionary ({Object.keys(selectedSession.field_mappings || {}).length})
                  </h3>
                </div>

                {Object.keys(selectedSession.field_mappings || {}).length === 0 ? (
                  <p className="text-xs text-text-muted">No custom form mappings recorded.</p>
                ) : (
                  <div className="divide-y divide-border/60">
                    {Object.entries(selectedSession.field_mappings).map(([field, value]) => (
                      <div key={field} className="py-2 flex items-center justify-between text-xs">
                        <span className="font-mono text-text-muted">{field}</span>
                        <span className="font-mono text-text font-medium">{String(value)}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="h-full flex items-center justify-center text-xs text-text-muted">
              Select a browser session to inspect execution details and visual audit screenshots.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
