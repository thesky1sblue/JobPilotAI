interface StatCardProps {
  label: string;
  value: number | string;
  delta?: string;
  color?: string;
  mono?: boolean;
}

export function StatCard({ label, value, delta, color = "text-text", mono = true }: StatCardProps) {
  return (
    <div className="bg-surface border border-border rounded-lg p-4">
      <div className="text-[11px] text-text-muted uppercase tracking-wider font-medium mb-2">{label}</div>
      <div className={`text-2xl font-bold ${mono ? "font-mono" : ""} ${color}`}>{value}</div>
      {delta && <div className="text-[11px] text-text-muted mt-1">{delta}</div>}
    </div>
  );
}