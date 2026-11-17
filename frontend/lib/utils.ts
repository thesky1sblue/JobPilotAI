import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatScore(score: number | null | undefined): string {
  if (score == null) return "—";
  return `${score.toFixed(0)}%`;
}

export function classificationColor(cls: string | null | undefined): string {
  switch (cls) {
    case "strong": return "text-success";
    case "good": return "text-accent";
    case "review": return "text-warning";
    case "low": return "text-muted";
    default: return "text-text-muted";
  }
}

export function classificationBg(cls: string | null | undefined): string {
  switch (cls) {
    case "strong": return "bg-success/10 text-success border-success/20";
    case "good": return "bg-accent/10 text-accent border-accent/20";
    case "review": return "bg-warning/10 text-warning border-warning/20";
    case "low": return "bg-muted/10 text-muted border-muted/20";
    default: return "bg-surface-2 text-text-muted border-border";
  }
}

export function statusColor(status: string): string {
  const map: Record<string, string> = {
    discovered: "text-text-muted",
    shortlisted: "text-accent",
    preparing: "text-warning",
    pending_approval: "text-warning",
    approved: "text-success",
    submitted: "text-success",
    assessment: "text-accent",
    interview: "text-accent",
    rejected: "text-danger",
    offer: "text-success",
  };
  return map[status] || "text-text-muted";
}

export function formatDate(date: string | null | undefined): string {
  if (!date) return "—";
  return new Date(date).toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" });
}

export function formatSalary(min: number | null, max: number | null): string {
  if (!min && !max) return "Not disclosed";
  if (min && max) return `₹${(min / 100000).toFixed(1)}L – ₹${(max / 100000).toFixed(1)}L`;
  if (min) return `₹${(min / 100000).toFixed(1)}L+`;
  return `Up to ₹${(max! / 100000).toFixed(1)}L`;
}