"use client";
import { useEffect, useState } from "react";
import { TopBar } from "@/components/layout/TopBar";
import { getApplications, approveApplication, rejectApplication, Application } from "@/lib/api";
import { statusColor, formatDate } from "@/lib/utils";
import { CheckCircle, XCircle } from "lucide-react";

export default function QueuePage() {
  const [apps, setApps] = useState<Application[]>([]);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    try { setApps(await getApplications()); } finally { setLoading(false); }
  };

  useEffect(() => { load(); }, []);

  const handleApprove = async (id: string) => {
    await approveApplication(id);
    await load();
  };

  const handleReject = async (id: string) => {
    await rejectApplication(id);
    await load();
  };

  const pending = apps.filter(a => a.status === "pending_approval");
  const others = apps.filter(a => a.status !== "pending_approval");

  return (
    <div className="flex flex-col h-full">
      <TopBar title="Application Queue" subtitle={`${pending.length} pending approval`} />
      <div className="flex-1 overflow-auto p-6 space-y-6">
        {pending.length > 0 && (
          <div>
            <h2 className="text-xs font-semibold text-text uppercase tracking-wider mb-3">Pending Your Approval</h2>
            <div className="bg-surface border border-warning/30 rounded-lg overflow-hidden">
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b border-border bg-surface-2">
                    <th className="text-left p-3 text-text-muted font-medium text-[10px] uppercase">Application ID</th>
                    <th className="text-left p-3 text-text-muted font-medium text-[10px] uppercase">Status</th>
                    <th className="text-left p-3 text-text-muted font-medium text-[10px] uppercase">Created</th>
                    <th className="p-3"></th>
                  </tr>
                </thead>
                <tbody>
                  {pending.map(a => (
                    <tr key={a.id} className="border-b border-border/50">
                      <td className="p-3 font-mono text-text-muted text-[11px]">{a.id.slice(0, 8)}...</td>
                      <td className="p-3"><span className="text-warning font-medium">Pending Approval</span></td>
                      <td className="p-3 font-mono text-text-muted">{formatDate(a.created_at)}</td>
                      <td className="p-3">
                        <div className="flex gap-2">
                          <button onClick={() => handleApprove(a.id)}
                            className="flex items-center gap-1 px-2 py-1 bg-success/10 text-success border border-success/20 rounded text-[11px] hover:bg-success/20">
                            <CheckCircle size={11} /> Approve
                          </button>
                          <button onClick={() => handleReject(a.id)}
                            className="flex items-center gap-1 px-2 py-1 bg-danger/10 text-danger border border-danger/20 rounded text-[11px] hover:bg-danger/20">
                            <XCircle size={11} /> Reject
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
          <h2 className="text-xs font-semibold text-text uppercase tracking-wider mb-3">All Applications</h2>
          <div className="bg-surface border border-border rounded-lg overflow-hidden">
            {loading ? (
              <div className="p-12 text-center text-text-muted text-xs">Loading...</div>
            ) : apps.length === 0 ? (
              <div className="p-12 text-center text-text-muted text-xs">No applications yet.</div>
            ) : (
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b border-border bg-surface-2">
                    <th className="text-left p-3 text-text-muted font-medium text-[10px] uppercase">ID</th>
                    <th className="text-left p-3 text-text-muted font-medium text-[10px] uppercase">Status</th>
                    <th className="text-left p-3 text-text-muted font-medium text-[10px] uppercase">Ready</th>
                    <th className="text-left p-3 text-text-muted font-medium text-[10px] uppercase">Submitted</th>
                    <th className="text-left p-3 text-text-muted font-medium text-[10px] uppercase">Created</th>
                  </tr>
                </thead>
                <tbody>
                  {apps.map(a => (
                    <tr key={a.id} className="border-b border-border/50 hover:bg-surface-2">
                      <td className="p-3 font-mono text-text-muted text-[11px]">{a.id.slice(0, 8)}...</td>
                      <td className="p-3"><span className={statusColor(a.status)}>{a.status.replace(/_/g, " ")}</span></td>
                      <td className="p-3">{a.is_ready ? "✓" : "—"}</td>
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