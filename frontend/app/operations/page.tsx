"use client";
import { useEffect, useState } from "react";
import { TopBar } from "@/components/layout/TopBar";
import {
  getObservabilityMetrics,
  getAgentTraces,
  ObservabilityMetrics,
  AgentTraceItem
} from "@/lib/api";
import {
  Activity,
  Cpu,
  Coins,
  Clock,
  CheckCircle,
  AlertTriangle,
  RefreshCw,
  Search,
  Filter,
  Loader2
} from "lucide-react";

export default function OperationsPage() {
  const [metrics, setMetrics] = useState<ObservabilityMetrics | null>(null);
  const [traces, setTraces] = useState<AgentTraceItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterAgent, setFilterAgent] = useState<string>("");
  const [searchQuery, setSearchQuery] = useState<string>("");

  const loadData = async () => {
    setLoading(true);
    try {
      const [m, t] = await Promise.all([
        getObservabilityMetrics(),
        getAgentTraces(100, filterAgent || undefined)
      ]);
      setMetrics(m);
      setTraces(t);
    } catch (err) {
      console.error("Failed to load operations data", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [filterAgent]);

  const filteredTraces = traces.filter((t) => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return (
      t.agent_name.toLowerCase().includes(q) ||
      t.model_name.toLowerCase().includes(q) ||
      (t.workflow_run_id && t.workflow_run_id.toLowerCase().includes(q))
    );
  });

  return (
    <div className="flex flex-col h-full bg-background text-text">
      <TopBar
        title="Agent Operations & Telemetry"
        subtitle="Multi-agent orchestration observability, token accounting, and LLM inference telemetry"
      />

      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {/* Metric Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="p-4 bg-surface border border-border rounded-lg flex items-center justify-between">
            <div>
              <div className="text-[11px] text-text-muted font-mono uppercase">Agent Traces</div>
              <div className="text-xl font-bold text-text mt-1">
                {metrics ? metrics.total_traces.toLocaleString() : "..."}
              </div>
            </div>
            <div className="p-2.5 bg-accent/10 text-accent rounded-md">
              <Activity size={18} />
            </div>
          </div>

          <div className="p-4 bg-surface border border-border rounded-lg flex items-center justify-between">
            <div>
              <div className="text-[11px] text-text-muted font-mono uppercase">Total Tokens</div>
              <div className="text-xl font-bold text-text mt-1">
                {metrics ? (metrics.total_tokens / 1000).toFixed(1) + "k" : "..."}
              </div>
              <div className="text-[10px] text-text-muted mt-0.5">
                {metrics ? `${metrics.prompt_tokens} prompt / ${metrics.completion_tokens} comp` : ""}
              </div>
            </div>
            <div className="p-2.5 bg-info/10 text-info rounded-md">
              <Cpu size={18} />
            </div>
          </div>

          <div className="p-4 bg-surface border border-border rounded-lg flex items-center justify-between">
            <div>
              <div className="text-[11px] text-text-muted font-mono uppercase">Estimated Cost (USD)</div>
              <div className="text-xl font-bold text-text mt-1">
                {metrics ? `$${metrics.estimated_cost_usd.toFixed(4)}` : "..."}
              </div>
            </div>
            <div className="p-2.5 bg-warning/10 text-warning rounded-md">
              <Coins size={18} />
            </div>
          </div>

          <div className="p-4 bg-surface border border-border rounded-lg flex items-center justify-between">
            <div>
              <div className="text-[11px] text-text-muted font-mono uppercase">Average Latency</div>
              <div className="text-xl font-bold text-text mt-1">
                {metrics ? `${metrics.avg_latency_ms} ms` : "..."}
              </div>
            </div>
            <div className="p-2.5 bg-success/10 text-success rounded-md">
              <Clock size={18} />
            </div>
          </div>
        </div>

        {/* Breakdown by Agent and Model */}
        {metrics && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* By Agent */}
            <div className="p-4 bg-surface border border-border rounded-lg space-y-3">
              <h3 className="text-xs font-semibold text-text uppercase tracking-wider font-mono">
                Consumption By Agent
              </h3>
              <div className="space-y-2">
                {Object.entries(metrics.by_agent).map(([agent, stats]) => (
                  <div key={agent} className="p-2.5 bg-surface-2 rounded border border-border/50 flex items-center justify-between text-xs">
                    <div>
                      <div className="font-semibold text-text capitalize">{agent.replace("_", " ")}</div>
                      <div className="text-[10px] text-text-muted font-mono">{stats.count} calls</div>
                    </div>
                    <div className="text-right">
                      <div className="font-mono text-accent font-semibold">{stats.tokens.toLocaleString()} tokens</div>
                      <div className="text-[10px] text-text-muted font-mono">${stats.cost_usd.toFixed(4)}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* By Model */}
            <div className="p-4 bg-surface border border-border rounded-lg space-y-3">
              <h3 className="text-xs font-semibold text-text uppercase tracking-wider font-mono">
                Consumption By Model
              </h3>
              <div className="space-y-2">
                {Object.entries(metrics.by_model).map(([model, stats]) => (
                  <div key={model} className="p-2.5 bg-surface-2 rounded border border-border/50 flex items-center justify-between text-xs">
                    <div>
                      <div className="font-semibold text-text font-mono">{model}</div>
                      <div className="text-[10px] text-text-muted font-mono">{stats.count} invocations</div>
                    </div>
                    <div className="text-right">
                      <div className="font-mono text-info font-semibold">{stats.tokens.toLocaleString()} tokens</div>
                      <div className="text-[10px] text-text-muted font-mono">${stats.cost_usd.toFixed(4)}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Trace Table */}
        <div className="bg-surface border border-border rounded-lg overflow-hidden">
          <div className="p-4 border-b border-border flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <h3 className="text-xs font-semibold text-text uppercase tracking-wider font-mono">
              Live Agent Execution Traces ({filteredTraces.length})
            </h3>

            <div className="flex items-center gap-2">
              <div className="relative">
                <Search size={13} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-text-muted" />
                <input
                  type="text"
                  placeholder="Search traces..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-7 pr-3 py-1 text-xs bg-surface-2 border border-border rounded text-text placeholder:text-text-muted/60 focus:outline-none focus:border-accent"
                />
              </div>

              <select
                value={filterAgent}
                onChange={(e) => setFilterAgent(e.target.value)}
                className="text-xs py-1 px-2.5 bg-surface-2 border border-border rounded text-text focus:outline-none focus:border-accent font-mono"
              >
                <option value="">All Agents</option>
                <option value="matching_agent">Matching Agent</option>
                <option value="resume_agent">Resume Agent</option>
                <option value="cover_letter_agent">Cover Letter Agent</option>
                <option value="form_agent">Form Agent</option>
                <option value="extraction_agent">Extraction Agent</option>
                <option value="orchestrator">Orchestrator</option>
              </select>

              <button
                onClick={() => loadData()}
                className="p-1.5 hover:bg-surface-2 rounded text-text-muted hover:text-text transition-colors border border-border"
                title="Refresh"
              >
                <RefreshCw size={13} className={loading ? "animate-spin" : ""} />
              </button>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-surface-2/60 text-text-muted font-mono text-[10px] uppercase border-b border-border">
                <tr>
                  <th className="py-2 px-3 font-semibold">Agent</th>
                  <th className="py-2 px-3 font-semibold">Model</th>
                  <th className="py-2 px-3 font-semibold">Tokens (P / C)</th>
                  <th className="py-2 px-3 font-semibold">Cost</th>
                  <th className="py-2 px-3 font-semibold">Latency</th>
                  <th className="py-2 px-3 font-semibold">Status</th>
                  <th className="py-2 px-3 font-semibold">Time</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border/60">
                {filteredTraces.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="py-8 text-center text-text-muted text-xs">
                      {loading ? (
                        <div className="flex items-center justify-center gap-2">
                          <Loader2 size={13} className="animate-spin text-accent" /> Loading telemetry traces...
                        </div>
                      ) : (
                        "No traces found."
                      )}
                    </td>
                  </tr>
                ) : (
                  filteredTraces.map((trace) => (
                    <tr key={trace.id} className="hover:bg-surface-2/40 transition-colors">
                      <td className="py-2.5 px-3 font-medium text-text capitalize">
                        {trace.agent_name.replace("_", " ")}
                      </td>
                      <td className="py-2.5 px-3 font-mono text-[11px] text-text-muted">
                        {trace.model_name}
                      </td>
                      <td className="py-2.5 px-3 font-mono text-[11px] text-text">
                        <span>{trace.total_tokens.toLocaleString()}</span>
                        <span className="text-[10px] text-text-muted ml-1.5">
                          ({trace.prompt_tokens}/{trace.completion_tokens})
                        </span>
                      </td>
                      <td className="py-2.5 px-3 font-mono text-[11px] text-warning">
                        ${trace.cost_usd.toFixed(4)}
                      </td>
                      <td className="py-2.5 px-3 font-mono text-[11px] text-text-muted">
                        {trace.latency_ms} ms
                      </td>
                      <td className="py-2.5 px-3">
                        <span
                          className={`inline-flex items-center gap-1 text-[10px] px-1.5 py-0.5 rounded font-mono font-medium ${
                            trace.status === "success"
                              ? "bg-success/20 text-success"
                              : "bg-danger/20 text-danger"
                          }`}
                        >
                          {trace.status === "success" ? <CheckCircle size={10} /> : <AlertTriangle size={10} />}
                          {trace.status}
                        </span>
                      </td>
                      <td className="py-2.5 px-3 text-[11px] text-text-muted font-mono">
                        {new Date(trace.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" })}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
