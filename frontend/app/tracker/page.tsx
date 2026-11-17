"use client";
import { useEffect, useState } from "react";
import { TopBar } from "@/components/layout/TopBar";
import { getApplications, Application } from "@/lib/api";
import { statusColor } from "@/lib/utils";

const STATUSES = ["discovered", "shortlisted", "preparing", "pending_approval", "submitted", "assessment", "interview", "rejected", "offer"];

export default function TrackerPage() {
  const [apps, setApps] = useState<Application[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getApplications().then(setApps).catch(() => {}).finally(() => setLoading(false));
  }, []);

  const byStatus = (s: string) => apps.filter(a => a.status === s);

  return (
    <div className="flex flex-col h-full">
      <TopBar title="Application Tracker" subtitle="Track all application stages" />
      <div className="flex-1 overflow-auto p-6">
        {loading ? (
          <div className="text-center text-text-muted text-xs p-12">Loading...</div>
        ) : (
          <div className="grid grid-cols-3 lg:grid-cols-5 gap-3">
            {STATUSES.map(status => {
              const count = byStatus(status).length;
              return (
                <div key={status} className="bg-surface border border-border rounded-lg p-3">
                  <div className="text-[10px] uppercase tracking-wider text-text-muted mb-2">{status.replace(/_/g, " ")}</div>
                  <div className={`text-2xl font-bold font-mono ${statusColor(status)}`}>{count}</div>
                </div>
              );
            })}
          </div>
        )}

        {!loading && apps.length === 0 && (
          <div className="mt-6 text-center text-text-muted text-xs">
            No applications tracked yet. Applications will appear here as they are prepared.
          </div>
        )}
      </div>
    </div>
  );
}