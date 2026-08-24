"use client";

import { LucideIcon } from "lucide-react";

interface StatCardProps {
  title: string;
  value: string | number;
  change?: number;
  changeLabel?: string;
  icon?: LucideIcon;
  color?: string;
}

export function StatCard({
  title,
  value,
  change,
  changeLabel,
  icon: Icon,
  color = "var(--accent)",
}: StatCardProps) {
  const isPositive = change && change > 0;
  const isNegative = change && change < 0;

  return (
    <div className="claim-card rounded-lg p-5">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p
            className="text-xs font-medium uppercase tracking-wide mb-1"
            style={{ color: "var(--text-muted)" }}
          >
            {title}
          </p>
          <p className="text-2xl font-bold" style={{ color: "var(--text)" }}>
            {value}
          </p>
          {change !== undefined && (
            <div className="flex items-center gap-1 mt-2">
              <span
                className="text-xs font-medium"
                style={{
                  color: isPositive
                    ? "var(--verified)"
                    : isNegative
                    ? "var(--flagged)"
                    : "var(--text-muted)",
                }}
              >
                {isPositive ? "+" : ""}
                {change}%
              </span>
              {changeLabel && (
                <span className="text-xs" style={{ color: "var(--text-muted)" }}>
                  {changeLabel}
                </span>
              )}
            </div>
          )}
        </div>
        {Icon && (
          <div
            className="p-2 rounded-lg"
            style={{
              backgroundColor: `color-mix(in srgb, ${color} 10%, transparent)`,
              color: color,
            }}
          >
            <Icon size={20} />
          </div>
        )}
      </div>
    </div>
  );
}
