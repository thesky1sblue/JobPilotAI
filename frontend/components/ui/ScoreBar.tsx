interface ScoreBarProps {
  score: number;
  label?: string;
  showValue?: boolean;
}

function scoreColor(score: number): string {
  if (score >= 85) return "bg-success";
  if (score >= 70) return "bg-accent";
  if (score >= 55) return "bg-warning";
  return "bg-muted";
}

export function ScoreBar({ score, label, showValue = true }: ScoreBarProps) {
  return (
    <div className="w-full">
      {(label || showValue) && (
        <div className="flex justify-between mb-1">
          {label && <span className="text-[11px] text-text-muted">{label}</span>}
          {showValue && <span className="text-[11px] font-mono text-text">{score.toFixed(0)}%</span>}
        </div>
      )}
      <div className="h-1.5 bg-surface-2 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all ${scoreColor(score)}`}
          style={{ width: `${Math.min(score, 100)}%` }}
        />
      </div>
    </div>
  );
}