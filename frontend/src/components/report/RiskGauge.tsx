"use client";

import { useEffect, useRef } from "react";
import { getRiskColor, getRiskLevel } from "@/lib/utils";

interface RiskGaugeProps {
  score: number;
  size?: "sm" | "md" | "lg";
  showLabel?: boolean;
  showDetails?: boolean;
  riskFactors?: string[];
}

const sizeConfig = {
  sm: { width: 120, height: 80, fontSize: "text-xl", labelSize: "text-xs" },
  md: { width: 180, height: 110, fontSize: "text-3xl", labelSize: "text-sm" },
  lg: { width: 240, height: 140, fontSize: "text-4xl", labelSize: "text-base" },
};

export function RiskGauge({
  score,
  size = "md",
  showLabel = true,
  showDetails = false,
  riskFactors = [],
}: RiskGaugeProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const config = sizeConfig[size];
  const color = getRiskColor(score);
  const level = getRiskLevel(score);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const dpr = window.devicePixelRatio || 1;
    canvas.width = config.width * dpr;
    canvas.height = config.height * dpr;
    ctx.scale(dpr, dpr);

    const cx = config.width / 2;
    const cy = config.height - 10;
    const radius = Math.min(cx, cy) - 10;
    const startAngle = Math.PI;
    const endAngle = 2 * Math.PI;

    // Clear
    ctx.clearRect(0, 0, config.width, config.height);

    // Background arc
    ctx.beginPath();
    ctx.arc(cx, cy, radius, startAngle, endAngle);
    ctx.lineWidth = 12;
    ctx.strokeStyle = "#374151"; // gray-700
    ctx.lineCap = "round";
    ctx.stroke();

    // Score arc
    const scoreAngle = startAngle + (score / 100) * Math.PI;
    ctx.beginPath();
    ctx.arc(cx, cy, radius, startAngle, scoreAngle);
    ctx.lineWidth = 12;
    ctx.strokeStyle = color;
    ctx.lineCap = "round";
    ctx.stroke();

    // Glow effect
    ctx.beginPath();
    ctx.arc(cx, cy, radius, startAngle, scoreAngle);
    ctx.lineWidth = 18;
    ctx.strokeStyle = color + "30";
    ctx.lineCap = "round";
    ctx.stroke();

    // Tick marks
    for (let i = 0; i <= 10; i++) {
      const angle = startAngle + (i / 10) * Math.PI;
      const innerR = radius - 18;
      const outerR = radius - 14;
      ctx.beginPath();
      ctx.moveTo(cx + Math.cos(angle) * innerR, cy + Math.sin(angle) * innerR);
      ctx.lineTo(cx + Math.cos(angle) * outerR, cy + Math.sin(angle) * outerR);
      ctx.lineWidth = i % 5 === 0 ? 2 : 1;
      ctx.strokeStyle = "#6b7280";
      ctx.stroke();
    }

    // Needle
    const needleAngle = startAngle + (score / 100) * Math.PI;
    const needleLen = radius - 25;
    ctx.beginPath();
    ctx.moveTo(cx, cy);
    ctx.lineTo(cx + Math.cos(needleAngle) * needleLen, cy + Math.sin(needleAngle) * needleLen);
    ctx.lineWidth = 2.5;
    ctx.strokeStyle = "#e5e7eb";
    ctx.lineCap = "round";
    ctx.stroke();

    // Center dot
    ctx.beginPath();
    ctx.arc(cx, cy, 4, 0, 2 * Math.PI);
    ctx.fillStyle = color;
    ctx.fill();
  }, [score, color, config]);

  return (
    <div className="flex flex-col items-center">
      <div className="relative" style={{ width: config.width, height: config.height }}>
        <canvas
          ref={canvasRef}
          style={{ width: config.width, height: config.height }}
        />
        {/* Score text overlaid on canvas */}
        <div className="absolute inset-0 flex flex-col items-center justify-end pb-6">
          <span className={`font-bold ${config.fontSize}`} style={{ color }}>
            {Math.round(score)}
          </span>
        </div>
      </div>

      {showLabel && (
        <div className="mt-1 text-center">
          <span
            className={`rounded-full px-3 py-1 text-xs font-semibold ${config.labelSize}`}
            style={{ backgroundColor: color + "20", color }}
          >
            {level} Risk
          </span>
        </div>
      )}

      {showDetails && riskFactors && riskFactors.length > 0 && (
        <div className="mt-4 w-full max-w-xs">
          <p className="mb-2 text-xs font-medium text-gray-500 dark:text-gray-400">
            Risk Factors
          </p>
          <ul className="space-y-1">
            {riskFactors.map((factor, i) => (
              <li
                key={i}
                className="flex items-start gap-2 text-xs text-gray-600 dark:text-gray-400"
              >
                <span className="mt-1 h-1.5 w-1.5 flex-shrink-0 rounded-full" style={{ backgroundColor: color }} />
                {factor}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
