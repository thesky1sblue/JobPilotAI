"use client";
import { useEffect, useState } from "react";
import { TopBar } from "@/components/layout/TopBar";
import { getCompanies, seedCompanies, Company } from "@/lib/api";
import { formatDate } from "@/lib/utils";
import { Building2, ExternalLink, CheckCircle, Loader } from "lucide-react";

export default function CompaniesPage() {
  const [companies, setCompanies] = useState<Company[]>([]);
  const [loading, setLoading] = useState(true);
  const [seeding, setSeeding] = useState(false);
  const [seedResult, setSeedResult] = useState<string | null>(null);

  const load = async () => {
    setLoading(true);
    try {
      const data = await getCompanies();
      setCompanies(data);
    } finally {
      setLoading(false);
    }
  };

  const handleSeed = async () => {
    setSeeding(true);
    try {
      const r = await seedCompanies();
      setSeedResult(`Seeded ${r.seeded} companies`);
      await load();
    } catch {
      setSeedResult("Seed failed");
    } finally {
      setSeeding(false);
    }
  };

  useEffect(() => { load(); }, []);

  return (
    <div className="flex flex-col h-full">
      <TopBar title="Company Intelligence" subtitle={`${companies.length} companies in watchlist`} />
      <div className="flex-1 overflow-auto p-6">
        <div className="flex items-center gap-3 mb-4">
          {seedResult && <span className="text-xs font-mono text-success">{seedResult}</span>}
          <button onClick={handleSeed} disabled={seeding}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-accent/10 text-accent border border-accent/20 rounded text-xs font-medium hover:bg-accent/20 disabled:opacity-50 ml-auto">
            {seeding ? <Loader size={12} className="animate-spin" /> : <Building2 size={12} />}
            {seeding ? "Seeding..." : "Seed 50 Companies"}
          </button>
        </div>
        <div className="bg-surface border border-border rounded-lg overflow-hidden">
          {loading ? (
            <div className="p-12 text-center text-text-muted text-xs">Loading...</div>
          ) : companies.length === 0 ? (
            <div className="p-12 text-center text-text-muted text-xs">
              No companies yet. Click &ldquo;Seed 50 Companies&rdquo; to populate the watchlist.
            </div>
          ) : (
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-border bg-surface-2">
                  <th className="text-left p-3 text-text-muted font-medium uppercase tracking-wider text-[10px]">Company</th>
                  <th className="text-left p-3 text-text-muted font-medium uppercase tracking-wider text-[10px]">Industry</th>
                  <th className="text-left p-3 text-text-muted font-medium uppercase tracking-wider text-[10px]">Location</th>
                  <th className="text-left p-3 text-text-muted font-medium uppercase tracking-wider text-[10px]">ATS</th>
                  <th className="text-left p-3 text-text-muted font-medium uppercase tracking-wider text-[10px]">Last Scan</th>
                  <th className="p-3"></th>
                </tr>
              </thead>
              <tbody>
                {companies.map(c => (
                  <tr key={c.id} className="border-b border-border/50 hover:bg-surface-2 transition-colors">
                    <td className="p-3">
                      <div className="flex items-center gap-2">
                        {c.is_verified && <CheckCircle size={12} className="text-success flex-shrink-0" />}
                        <span className="font-medium text-text">{c.name}</span>
                      </div>
                      <div className="text-text-muted text-[11px]">{c.domain}</div>
                    </td>
                    <td className="p-3 text-text-muted">{c.industry || "—"}</td>
                    <td className="p-3 text-text-muted">{c.location || "—"}</td>
                    <td className="p-3">
                      {c.ats_platform && c.ats_platform !== "custom" ? (
                        <span className="font-mono text-[10px] text-accent bg-accent/10 px-1.5 py-0.5 rounded uppercase">{c.ats_platform}</span>
                      ) : (
                        <span className="text-text-muted text-[11px]">custom</span>
                      )}
                    </td>
                    <td className="p-3 font-mono text-text-muted text-[11px]">{formatDate(c.last_discovered_at)}</td>
                    <td className="p-3">
                      {c.careers_url && (
                        <a href={c.careers_url} target="_blank" rel="noopener noreferrer" className="text-accent hover:text-accent-hover">
                          <ExternalLink size={12} />
                        </a>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
}