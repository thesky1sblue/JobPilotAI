"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import {
  LayoutDashboard, Search, Target, FileText, Briefcase, Building2,
  Settings, Bell, ChevronRight, Zap
} from "lucide-react";

const navItems = [
  { href: "/", icon: LayoutDashboard, label: "Overview" },
  { href: "/discovery", icon: Search, label: "Job Discovery" },
  { href: "/matches", icon: Target, label: "Match Intelligence" },
  { href: "/queue", icon: Briefcase, label: "Application Queue" },
  { href: "/resume", icon: FileText, label: "Resume Studio" },
  { href: "/tracker", icon: ChevronRight, label: "Tracker" },
  { href: "/companies", icon: Building2, label: "Companies" },
  { href: "/notifications", icon: Bell, label: "Notifications" },
  { href: "/settings", icon: Settings, label: "Settings" },
];

export function Sidebar() {
  const pathname = usePathname();
  return (
    <aside className="w-56 min-h-screen bg-surface border-r border-border flex flex-col">
      <div className="p-4 border-b border-border">
        <div className="flex items-center gap-2">
          <Zap size={18} className="text-accent" />
          <span className="font-semibold text-sm tracking-tight text-text">JobPilot AI</span>
        </div>
        <div className="text-[10px] text-text-muted mt-0.5 font-mono">RECRUITMENT INTELLIGENCE</div>
      </div>
      <nav className="flex-1 py-2">
        {navItems.map(({ href, icon: Icon, label }) => {
          const active = pathname === href;
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                "flex items-center gap-2.5 px-4 py-2 text-xs font-medium transition-colors",
                active
                  ? "text-accent bg-accent/10 border-r-2 border-accent"
                  : "text-text-muted hover:text-text hover:bg-surface-2"
              )}
            >
              <Icon size={14} />
              {label}
            </Link>
          );
        })}
      </nav>
      <div className="p-4 border-t border-border">
        <div className="text-[10px] text-text-muted font-mono">v1.0.0 · LOCAL</div>
      </div>
    </aside>
  );
}