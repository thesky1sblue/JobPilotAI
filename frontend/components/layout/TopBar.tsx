"use client";
import { Bell, RefreshCw } from "lucide-react";
import { useState } from "react";
import { triggerDiscovery } from "@/lib/api";

interface TopBarProps {
  title: string;
  subtitle?: string;
}

export function TopBar({ title, subtitle }: TopBarProps) {
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState<{ text: string; isError: boolean } | null>(null);

  const handleDiscover = async () => {
    setRunning(true);
    setResult(null);
    try {
      const r = await triggerDiscovery();
      if (r.new_jobs > 0) {
        setResult({ text: `+${r.new_jobs} new jobs discovered`, isError: false });
      } else {
        setResult({ text: `Scanned ${r.companies_scanned} companies (up to date)`, isError: false });
      }
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Discovery request failed";
      setResult({ text: message, isError: true });
    } finally {
      setRunning(false);
    }
  };

  return (
    <header className="border-b border-border bg-surface px-6 py-3 flex items-center justify-between">
      <div>
        <h1 className="text-sm font-semibold text-text">{title}</h1>
        {subtitle && <p className="text-xs text-text-muted mt-0.5">{subtitle}</p>}
      </div>
      <div className="flex items-center gap-3">
        {result && (
          <span className={`text-xs font-mono ${result.isError ? "text-danger" : "text-success"}`}>
            {result.text}
          </span>
        )}
        <button
          onClick={handleDiscover}
          disabled={running}
          className="flex items-center gap-1.5 px-3 py-1.5 bg-accent/10 text-accent border border-accent/20 rounded text-xs font-medium hover:bg-accent/20 transition-colors disabled:opacity-50"
        >
          <RefreshCw size={12} className={running ? "animate-spin" : ""} />
          {running ? "Discovering..." : "Run Discovery"}
        </button>
        <button className="p-1.5 text-text-muted hover:text-text rounded hover:bg-surface-2 transition-colors">
          <Bell size={16} />
        </button>
      </div>
    </header>
  );
}
