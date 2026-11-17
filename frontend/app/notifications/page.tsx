"use client";
import { TopBar } from "@/components/layout/TopBar";
import { Bell } from "lucide-react";

export default function NotificationsPage() {
  return (
    <div className="flex flex-col h-full">
      <TopBar title="Notifications" />
      <div className="flex-1 flex items-center justify-center">
        <div className="text-center">
          <Bell size={32} className="text-text-muted mx-auto mb-3" />
          <p className="text-sm text-text-muted">No notifications yet.</p>
          <p className="text-xs text-text-muted mt-1">You&apos;ll be notified about strong matches and pending approvals.</p>
        </div>
      </div>
    </div>
  );
}