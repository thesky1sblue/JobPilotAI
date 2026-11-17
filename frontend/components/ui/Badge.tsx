import { cn, classificationBg } from "@/lib/utils";

interface BadgeProps {
  label: string;
  variant?: "default" | "classification";
  classification?: string | null;
  className?: string;
}

export function Badge({ label, variant = "default", classification, className }: BadgeProps) {
  const base = "inline-flex items-center px-2 py-0.5 rounded text-[10px] font-medium border uppercase tracking-wider";
  const style = variant === "classification" && classification
    ? classificationBg(classification)
    : "bg-surface-2 text-text-muted border-border";
  return <span className={cn(base, style, className)}>{label}</span>;
}