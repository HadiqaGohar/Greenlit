"use client";

import type { ReadinessScore } from "@/lib/types";

const dimensions = [
  { key: "legal_clearance", label: "Legal", icon: "⚖️" },
  { key: "historical_accuracy", label: "Accuracy", icon: "📜" },
  { key: "continuity", label: "Continuity", icon: "🔗" },
  { key: "budget_feasibility", label: "Budget", icon: "💰" },
] as const;

const gradeColors: Record<string, string> = {
  A: "text-green-600 dark:text-green-400",
  B: "text-blue-600 dark:text-blue-400",
  C: "text-yellow-600 dark:text-yellow-400",
  D: "text-orange-600 dark:text-orange-400",
  F: "text-red-600 dark:text-red-400",
};

const barColors: Record<string, string> = {
  legal_clearance: "bg-emerald-500",
  historical_accuracy: "bg-blue-500",
  continuity: "bg-purple-500",
  budget_feasibility: "bg-amber-500",
};

interface ReadinessRadarProps {
  scores: ReadinessScore;
}

export function ReadinessRadar({ scores }: ReadinessRadarProps) {
  const overallPercent = scores.overall;

  return (
    <div className="rounded-xl border border-gray-200 bg-white p-6 dark:border-gray-700 dark:bg-gray-900">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            Production Readiness
          </h3>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            How ready is your script for production?
          </p>
        </div>
        <div className="text-center">
          <div
            className={`text-4xl font-bold ${gradeColors[scores.grade] || "text-gray-900 dark:text-white"}`}
          >
            {scores.grade}
          </div>
          <div className="text-xs text-gray-500 dark:text-gray-400">
            {scores.overall.toFixed(0)}/100
          </div>
        </div>
      </div>

      {/* Overall progress bar */}
      <div className="mb-6">
        <div className="mb-1 flex justify-between text-xs text-gray-500 dark:text-gray-400">
          <span>Overall Readiness</span>
          <span>{scores.overall.toFixed(0)}%</span>
        </div>
        <div className="h-3 w-full overflow-hidden rounded-full bg-gray-200 dark:bg-gray-700">
          <div
            className="h-full rounded-full bg-gradient-to-r from-red-500 via-yellow-500 to-green-500 transition-all duration-1000 ease-out"
            style={{ width: `${overallPercent}%` }}
          />
        </div>
      </div>

      {/* Dimension bars */}
      <div className="space-y-4">
        {dimensions.map(({ key, label, icon }) => {
          const value = scores[key];
          return (
            <div key={key}>
              <div className="mb-1 flex items-center justify-between text-sm">
                <span className="flex items-center gap-2 text-gray-700 dark:text-gray-300">
                  <span>{icon}</span>
                  <span>{label}</span>
                </span>
                <span className="font-medium text-gray-900 dark:text-white">
                  {value.toFixed(0)}%
                </span>
              </div>
              <div className="h-2 w-full overflow-hidden rounded-full bg-gray-200 dark:bg-gray-700">
                <div
                  className={`h-full rounded-full ${barColors[key]} transition-all duration-1000 ease-out`}
                  style={{ width: `${value}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>

      {/* Grade description */}
      <div className="mt-6 rounded-lg bg-gray-50 p-3 dark:bg-gray-800">
        <p className="text-sm text-gray-600 dark:text-gray-400">
          {scores.grade === "A" && "Excellent! Your script is production-ready with minimal issues."}
          {scores.grade === "B" && "Good. Minor issues to address before full production."}
          {scores.grade === "C" && "Fair. Several issues need attention before shooting."}
          {scores.grade === "D" && "Needs work. Significant issues must be resolved."}
          {scores.grade === "F" && "Critical. Major issues found — script requires revision."}
        </p>
      </div>
    </div>
  );
}
