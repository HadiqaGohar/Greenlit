"use client";

import { useTheme } from "next-themes";
import { useEffect, useState } from "react";

interface PieChartSlice {
  label: string;
  value: number;
  color?: string;
}

interface PieChartProps {
  data: PieChartSlice[];
  size?: number;
  title?: string;
  showLegend?: boolean;
}

export function PieChart({ data, size = 200, title, showLegend = true }: PieChartProps) {
  const { theme } = useTheme();
  const [mounted, setMounted] = useState(false);

  useEffect(() => setMounted(true), []);

  if (!mounted) return null;

  const total = data.reduce((sum, item) => sum + item.value, 0);
  if (total === 0) return null;

  const defaultColors = [
    "var(--accent)",
    "var(--verified)",
    "var(--flagged)",
    "var(--warning, #f59e0b)",
    "#8b5cf6",
    "#ec4899",
    "#06b6d4",
  ];

  // Create conic gradient
  let currentAngle = 0;
  const gradientParts: string[] = [];

  data.forEach((item, i) => {
    if (item.value === 0) return;
    const color = item.color || defaultColors[i % defaultColors.length];
    const angle = (item.value / total) * 360;
    gradientParts.push(`${color} ${currentAngle}deg ${currentAngle + angle}deg`);
    currentAngle += angle;
  });

  const gradient = gradientParts.length > 0
    ? `conic-gradient(${gradientParts.join(", ")})`
    : `conic-gradient(var(--border) 0deg 360deg)`;

  return (
    <div className="flex flex-col items-center">
      {title && (
        <h3
          className="text-sm font-semibold mb-4"
          style={{ color: "var(--text)" }}
        >
          {title}
        </h3>
      )}

      <div className="relative" style={{ width: size, height: size }}>
        {/* Outer ring */}
        <div
          className="absolute inset-0 rounded-full"
          style={{ background: gradient }}
        />

        {/* Inner circle (donut hole) */}
        <div
          className="absolute rounded-full flex items-center justify-center"
          style={{
            top: size * 0.2,
            left: size * 0.2,
            width: size * 0.6,
            height: size * 0.6,
            backgroundColor: "var(--bg)",
          }}
        >
          <div className="text-center">
            <div className="text-lg font-bold" style={{ color: "var(--text)" }}>
              {total}
            </div>
            <div className="text-xs" style={{ color: "var(--text-muted)" }}>
              Total
            </div>
          </div>
        </div>
      </div>

      {showLegend && (
        <div className="flex flex-wrap gap-3 mt-4 justify-center max-w-xs">
          {data.map((item, i) => {
            if (item.value === 0) return null;
            const percentage = ((item.value / total) * 100).toFixed(1);
            return (
              <div key={i} className="flex items-center gap-2">
                <div
                  className="w-3 h-3 rounded-full flex-shrink-0"
                  style={{
                    backgroundColor: item.color || defaultColors[i % defaultColors.length],
                  }}
                />
                <span className="text-xs" style={{ color: "var(--text-muted)" }}>
                  {item.label} ({percentage}%)
                </span>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
