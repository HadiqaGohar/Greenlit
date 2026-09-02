"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState, useEffect } from "react";
import {
  LayoutDashboard,
  FileSearch,
  BarChart3,
  Settings,
  Menu,
  X,
  Film,
  FileText,
  Clock,
} from "lucide-react";
import { listReports, type ReportListItem } from "@/lib/api";
import { useAuth } from "@/contexts/AuthContext";

const navItems = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/analyze", label: "Analyze", icon: FileSearch },
  { href: "/analytics", label: "Analytics", icon: BarChart3 },
  { href: "/settings", label: "Settings", icon: Settings },
];

export default function Sidebar() {
  const pathname = usePathname();
  const { user } = useAuth();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [reports, setReports] = useState<ReportListItem[]>([]);

  useEffect(() => {
    listReports(user?.uid)
      .then(({ reports }) => setReports(reports.slice(0, 5)))
      .catch(() => {});
  }, [user?.uid]);

  const isActive = (href: string) => {
    if (href === "/dashboard") return pathname === "/dashboard" || pathname.startsWith("/report");
    return pathname.startsWith(href);
  };

  const formatTime = (date: string) => {
    const d = new Date(date);
    const now = new Date();
    const diff = now.getTime() - d.getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return "just now";
    if (mins < 60) return `${mins}m ago`;
    const hrs = Math.floor(mins / 60);
    if (hrs < 24) return `${hrs}h ago`;
    return `${Math.floor(hrs / 24)}d ago`;
  };

  const sidebarContent = (
    <nav className="flex flex-col h-full">
      {/* Logo - mobile only */}
      <div className="flex items-center gap-2 px-5 py-4 border-b md:hidden" style={{ borderColor: "var(--border)" }}>
        <Film size={20} style={{ color: "var(--accent)" }} />
        <span className="font-display font-bold text-sm" style={{ color: "var(--text)" }}>
          GreenLit AI
        </span>
      </div>

      {/* Nav Links */}
      <div className="px-3 py-4 space-y-1">
        {navItems.map((item) => {
          const active = isActive(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              onClick={() => setMobileOpen(false)}
              className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all"
              style={{
                backgroundColor: active
                  ? "color-mix(in srgb, var(--accent) 15%, transparent)"
                  : "transparent",
                color: active ? "var(--accent)" : "var(--text-muted)",
                borderLeft: active ? "2px solid var(--accent)" : "2px solid transparent",
              }}
              onMouseEnter={(e) => {
                if (!active) {
                  e.currentTarget.style.backgroundColor = "color-mix(in srgb, var(--accent) 8%, transparent)";
                  e.currentTarget.style.color = "var(--text)";
                }
              }}
              onMouseLeave={(e) => {
                if (!active) {
                  e.currentTarget.style.backgroundColor = "transparent";
                  e.currentTarget.style.color = "var(--text-muted)";
                }
              }}
            >
              <item.icon size={18} />
              {item.label}
            </Link>
          );
        })}
      </div>

      {/* Recent Reports */}
      {reports.length > 0 && (
        <div className="flex-1 overflow-hidden">
          <div className="px-3 py-2">
            <p className="px-3 text-xs font-semibold uppercase tracking-wider" style={{ color: "var(--text-muted)" }}>
              Recent Reports
            </p>
          </div>
          <div className="px-3 space-y-0.5 overflow-y-auto max-h-[40vh]">
            {reports.map((report) => (
              <Link
                key={report.id}
                href={`/report/${report.id}`}
                onClick={() => setMobileOpen(false)}
                className="flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm transition-all group"
                style={{
                  backgroundColor: pathname === `/report/${report.id}`
                    ? "color-mix(in srgb, var(--accent) 15%, transparent)"
                    : "transparent",
                  color: pathname === `/report/${report.id}` ? "var(--accent)" : "var(--text-muted)",
                }}
                onMouseEnter={(e) => {
                  if (pathname !== `/report/${report.id}`) {
                    e.currentTarget.style.backgroundColor = "color-mix(in srgb, var(--accent) 8%, transparent)";
                    e.currentTarget.style.color = "var(--text)";
                  }
                }}
                onMouseLeave={(e) => {
                  if (pathname !== `/report/${report.id}`) {
                    e.currentTarget.style.backgroundColor = "transparent";
                    e.currentTarget.style.color = "var(--text-muted)";
                  }
                }}
              >
                <FileText size={14} className="flex-shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="truncate text-xs font-medium">{report.title}</p>
                  <p className="flex items-center gap-1 text-[10px] opacity-60">
                    <Clock size={9} />
                    {formatTime(report.date)}
                    <span className="mx-0.5">·</span>
                    {report.claimCount} claims
                  </p>
                </div>
                {report.riskScore !== undefined && report.riskScore > 0 && (
                  <span
                    className="text-[10px] font-medium px-1.5 py-0.5 rounded-full"
                    style={{
                      backgroundColor: report.riskScore > 70
                        ? "color-mix(in srgb, var(--flagged) 15%, transparent)"
                        : "color-mix(in srgb, var(--verified) 15%, transparent)",
                      color: report.riskScore > 70 ? "var(--flagged)" : "var(--verified)",
                    }}
                  >
                    {Math.round(report.riskScore)}
                  </span>
                )}
              </Link>
            ))}
          </div>
        </div>
      )}

      {/* Footer */}
      <div className="px-5 py-4 border-t mt-auto" style={{ borderColor: "var(--border)" }}>
        <p className="text-xs" style={{ color: "var(--text-muted)" }}>
          GreenLit AI v1.0
        </p>
      </div>
    </nav>
  );

  return (
    <>
      {/* Mobile hamburger button */}
      <button
        onClick={() => setMobileOpen(true)}
        className="fixed top-3 left-3 z-50 p-2 rounded-lg md:hidden"
        style={{
          backgroundColor: "var(--surface)",
          color: "var(--text)",
          border: "1px solid var(--border)",
        }}
      >
        <Menu size={20} />
      </button>

      {/* Desktop sidebar */}
      <aside
        className="hidden md:flex flex-col w-60 flex-shrink-0 border-r h-[calc(100vh-64px)] sticky top-16"
        style={{
          backgroundColor: "var(--surface)",
          borderColor: "var(--border)",
        }}
      >
        {sidebarContent}
      </aside>

      {/* Mobile overlay */}
      {mobileOpen && (
        <div className="fixed inset-0 z-50 md:hidden">
          <div
            className="absolute inset-0 bg-black/50"
            onClick={() => setMobileOpen(false)}
          />
          <aside
            className="absolute left-0 top-0 bottom-0 w-64 flex flex-col"
            style={{ backgroundColor: "var(--surface)" }}
          >
            <button
              onClick={() => setMobileOpen(false)}
              className="absolute top-3 right-3 p-1 rounded"
              style={{ color: "var(--text)" }}
            >
              <X size={18} />
            </button>
            {sidebarContent}
          </aside>
        </div>
      )}
    </>
  );
}
