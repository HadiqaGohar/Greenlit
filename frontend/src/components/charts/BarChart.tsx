"use client";

import { useEffect, useState } from "react";

export interface BarChartData {
  labels: string[];
  datasets: {
    label: string;
    data: number[];
    color?: string;
  }[];
}

export interface BarChartProps {
  data: BarChartData;
  height?: number;
  showLegend?: boolean;
  title?: string;
}

export function BarChart({ data, height = 300, showLegend = true, title }: BarChartProps) {
  const [mounted, setMounted] = useState(false);

  useEffect(() => setMounted(true), []);

  if (!mounted) return null;

  const maxValue = Math.max(
    ...data.datasets.flatMap((ds) => ds.data),
    1
  );

  const defaultColors = [
    "var(--accent)",
    "var(--verified)",
    "var(--flagged)",
    "var(--warning, #f59e0b)",
    "#8b5cf6",
  ];

  return (
    <div className="w-full">
      {title && (
        <h3
          className="text-sm font-semibold mb-4"
          style={{ color: "var(--text)" }}
        >
          {title}
        </h3>
      )}

      <div className="flex items-end gap-2" style={{ height }}>
        {data.labels.map((label, i) => (
          <div key={label} className="flex-1 flex flex-col items-center gap-1">
            <div className="w-full flex gap-1 items-end" style={{ height: height - 40 }}>
              {data.datasets.map((ds, j) => {
                const value = ds.data[i] || 0;
                const barHeight = (value / maxValue) * (height - 60);
                const color = ds.color || defaultColors[j % defaultColors.length];

                return (
                  <div
                    key={j}
                    className="flex-1 rounded-t transition-all duration-500 hover:opacity-80"
                    style={{
                      height: mounted ? barHeight : 0,
                      backgroundColor: color,
                      minHeight: 4,
                    }}
                    title={`${ds.label}: ${value}`}
                  />
                );
              })}
            </div>
            <span
              className="text-xs truncate w-full text-center"
              style={{ color: "var(--text-muted)" }}
            >
              {label}
            </span>
          </div>
        ))}
      </div>

      {showLegend && data.datasets.length > 1 && (
        <div className="flex flex-wrap gap-4 mt-4 justify-center">
          {data.datasets.map((ds, j) => (
            <div key={j} className="flex items-center gap-2">
              <div
                className="w-3 h-3 rounded-full"
                style={{
                  backgroundColor: ds.color || defaultColors[j % defaultColors.length],
                }}
              />
              <span className="text-xs" style={{ color: "var(--text-muted)" }}>
                {ds.label}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
