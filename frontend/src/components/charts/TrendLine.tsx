"use client";

import { useTheme } from "next-themes";
import { useEffect, useState } from "react";

interface TrendLineProps {
  labels: string[];
  data: number[];
  color?: string;
  height?: number;
  title?: string;
  showDots?: boolean;
  smooth?: boolean;
}

export function TrendLine({
  labels,
  data,
  color = "var(--accent)",
  height = 200,
  title,
  showDots = true,
  smooth = true,
}: TrendLineProps) {
  const { theme } = useTheme();
  const [mounted, setMounted] = useState(false);

  useEffect(() => setMounted(true), []);

  if (!mounted || data.length === 0) return null;

  const maxValue = Math.max(...data, 1);
  const minValue = Math.min(...data, 0);
  const range = maxValue - minValue || 1;

  const padding = { top: 20, right: 20, bottom: 40, left: 50 };
  const chartWidth = 100; // percentage-based
  const chartHeight = height - padding.top - padding.bottom;

  // Generate SVG path
  const points = data.map((value, i) => ({
    x: (i / (data.length - 1)) * chartWidth,
    y: padding.top + chartHeight - ((value - minValue) / range) * chartHeight,
  }));

  let pathD = "";
  if (smooth && points.length > 2) {
    // Smooth curve using cubic bezier
    pathD = `M ${points[0].x} ${points[0].y}`;
    for (let i = 1; i < points.length; i++) {
      const prev = points[i - 1];
      const curr = points[i];
      const cpx1 = prev.x + (curr.x - prev.x) / 3;
      const cpy1 = prev.y;
      const cpx2 = curr.x - (curr.x - prev.x) / 3;
      const cpy2 = curr.y;
      pathD += ` C ${cpx1} ${cpy1}, ${cpx2} ${cpy2}, ${curr.x} ${curr.y}`;
    }
  } else {
    // Straight lines
    pathD = points.map((p, i) => `${i === 0 ? "M" : "L"} ${p.x} ${p.y}`).join(" ");
  }

  // Area fill path
  const areaD = `${pathD} L ${points[points.length - 1].x} ${height - padding.bottom} L ${points[0].x} ${height - padding.bottom} Z`;

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

      <svg
        viewBox={`0 0 ${chartWidth + padding.left + padding.right} ${height}`}
        className="w-full"
        style={{ height }}
      >
        {/* Grid lines */}
        {[0, 0.25, 0.5, 0.75, 1].map((ratio) => {
          const y = padding.top + chartHeight * (1 - ratio);
          const value = minValue + range * ratio;
          return (
            <g key={ratio}>
              <line
                x1={padding.left}
                y1={y}
                x2={chartWidth + padding.left}
                y2={y}
                stroke="var(--border)"
                strokeWidth="0.5"
                strokeDasharray="4"
              />
              <text
                x={padding.left - 8}
                y={y + 4}
                textAnchor="end"
                fontSize="8"
                fill="var(--text-muted)"
              >
                {Math.round(value)}
              </text>
            </g>
          );
        })}

        {/* Area fill */}
        <path
          d={areaD}
          fill={color}
          opacity={0.1}
          style={{
            transition: "all 0.5s ease-out",
          }}
        />

        {/* Line */}
        <path
          d={pathD}
          fill="none"
          stroke={color}
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          style={{
            transition: "all 0.5s ease-out",
          }}
        />

        {/* Dots */}
        {showDots &&
          points.map((point, i) => (
            <g key={i}>
              <circle
                cx={point.x}
                cy={point.y}
                r="3"
                fill="var(--bg)"
                stroke={color}
                strokeWidth="2"
                style={{
                  transition: "all 0.3s ease-out",
                  transitionDelay: `${i * 50}ms`,
                }}
              />
              {/* Tooltip on hover */}
              <title>
                {labels[i]}: {data[i]}
              </title>
            </g>
          ))}

        {/* X-axis labels */}
        {labels.map((label, i) => {
          const x = (i / (labels.length - 1)) * chartWidth + padding.left;
          return (
            <text
              key={i}
              x={x}
              y={height - 10}
              textAnchor="middle"
              fontSize="8"
              fill="var(--text-muted)"
            >
              {label}
            </text>
          );
        })}
      </svg>
    </div>
  );
}
