"use client";

import { useState } from "react";
import type { Suggestion } from "@/lib/types";

const typeIcons: Record<string, string> = {
  factual: "🔍",
  legal: "⚖️",
  trademark: "™️",
  continuity: "🔗",
};

const severityColors: Record<string, string> = {
  high: "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300",
  medium: "bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-300",
  low: "bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300",
};

interface SuggestionCardProps {
  suggestions: Suggestion[];
}

export function SuggestionCard({ suggestions }: SuggestionCardProps) {
  const [expandedId, setExpandedId] = useState<string | null>(null);

  if (suggestions.length === 0) {
    return (
      <div className="rounded-xl border border-gray-200 bg-white p-6 dark:border-gray-700 dark:bg-gray-900">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
          Smart Suggestions
        </h3>
        <p className="mt-2 text-sm text-gray-500 dark:text-gray-400">
          No issues found — your script looks great!
        </p>
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-gray-200 bg-white p-6 dark:border-gray-700 dark:bg-gray-900">
      <div className="mb-4">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
          Smart Suggestions
        </h3>
        <p className="text-sm text-gray-500 dark:text-gray-400">
          AI-generated fixes for flagged issues ({suggestions.length})
        </p>
      </div>

      <div className="space-y-3">
        {suggestions.map((sug) => {
          const isExpanded = expandedId === sug.issue_id;
          return (
            <div
              key={sug.issue_id}
              className="rounded-lg border border-gray-200 dark:border-gray-700"
            >
              <button
                onClick={() =>
                  setExpandedId(isExpanded ? null : sug.issue_id)
                }
                className="flex w-full items-center justify-between p-3 text-left hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
              >
                <div className="flex items-center gap-2">
                  <span>{typeIcons[sug.issue_type] || "⚠️"}</span>
                  <span className="text-sm font-medium text-gray-900 dark:text-white truncate max-w-[300px]">
                    {sug.original_text.slice(0, 80)}
                    {sug.original_text.length > 80 ? "..." : ""}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <span
                    className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                      severityColors[sug.severity] || ""
                    }`}
                  >
                    {sug.severity}
                  </span>
                  <span className="text-gray-400">{isExpanded ? "▲" : "▼"}</span>
                </div>
              </button>

              {isExpanded && (
                <div className="border-t border-gray-200 p-3 dark:border-gray-700">
                  <div className="mb-2">
                    <span className="text-xs font-medium text-gray-500 dark:text-gray-400">
                      ORIGINAL:
                    </span>
                    <p className="mt-1 rounded bg-red-50 p-2 text-sm text-red-700 line-through dark:bg-red-900/20 dark:text-red-300">
                      {sug.original_text}
                    </p>
                  </div>
                  <div className="mb-2">
                    <span className="text-xs font-medium text-gray-500 dark:text-gray-400">
                      SUGGESTED:
                    </span>
                    <p className="mt-1 rounded bg-green-50 p-2 text-sm text-green-700 dark:bg-green-900/20 dark:text-green-300">
                      {sug.suggested_text}
                    </p>
                  </div>
                  <div>
                    <span className="text-xs font-medium text-gray-500 dark:text-gray-400">
                      RATIONALE:
                    </span>
                    <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
                      {sug.rationale}
                    </p>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
