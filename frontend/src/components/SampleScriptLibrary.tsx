"use client";

import { useState } from "react";
import Link from "next/link";
import { SAMPLE_SCRIPTS } from "@/lib/sampleData";

const genreIcons: Record<string, string> = {
  "Action/Thriller": "💥",
  "Period Drama": "📜",
  "Science Fiction": "🚀",
};

const statusColors: Record<string, string> = {
  "draft": "bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300",
  "in-review": "bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-300",
  "production-ready": "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300",
};

export function SampleScriptLibrary() {
  const [selectedScript, setSelectedScript] = useState<string | null>(null);

  return (
    <div className="rounded-2xl border border-gray-200 bg-white p-8 dark:border-gray-700 dark:bg-gray-900">
      <div className="mb-6 text-center">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
          Try It Now
        </h2>
        <p className="mt-2 text-gray-500 dark:text-gray-400">
          Load a sample script and see AI analysis in action — no upload needed
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
        {SAMPLE_SCRIPTS.map((script) => {
          const isSelected = selectedScript === script.id;
          return (
            <div
              key={script.id}
              onClick={() => setSelectedScript(isSelected ? null : script.id)}
              className={`cursor-pointer rounded-xl border-2 p-5 transition-all hover:shadow-lg ${
                isSelected
                  ? "border-blue-500 ring-2 ring-blue-200 dark:ring-blue-800"
                  : "border-gray-200 hover:border-gray-300 dark:border-gray-700 dark:hover:border-gray-600"
              }`}
            >
              {/* Header */}
              <div className="mb-3 flex items-start justify-between">
                <span className="text-3xl">{genreIcons[script.genre] || "🎬"}</span>
                <span
                  className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                    statusColors[script.status]
                  }`}
                >
                  {script.status}
                </span>
              </div>

              {/* Title & Description */}
              <h3 className="text-lg font-bold text-gray-900 dark:text-white">
                {script.title}
              </h3>
              <p className="mt-1 text-sm text-gray-500 dark:text-gray-400 line-clamp-2">
                {script.description}
              </p>

              {/* Stats */}
              <div className="mt-4 grid grid-cols-3 gap-2">
                <div className="text-center">
                  <p
                    className={`text-xl font-bold ${
                      script.riskScore >= 70
                        ? "text-red-600"
                        : script.riskScore >= 40
                        ? "text-yellow-600"
                        : "text-green-600"
                    }`}
                  >
                    {script.riskScore}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">Risk</p>
                </div>
                <div className="text-center">
                  <p className="text-xl font-bold text-gray-900 dark:text-white">
                    {script.scenes}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">Scenes</p>
                </div>
                <div className="text-center">
                  <p className="text-xl font-bold text-red-600">
                    {script.issues.critical}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">Critical</p>
                </div>
              </div>

              {/* Genre Tag */}
              <div className="mt-3">
                <span className="rounded-full bg-blue-100 px-3 py-1 text-xs font-medium text-blue-700 dark:bg-blue-900/30 dark:text-blue-300">
                  {script.genre}
                </span>
              </div>

              {/* Quick Preview (when selected) */}
              {isSelected && (
                <div className="mt-4 border-t border-gray-200 pt-4 dark:border-gray-700">
                  <h4 className="mb-2 text-xs font-bold text-gray-700 dark:text-gray-300">
                    ANALYSIS PREVIEW:
                  </h4>
                  <div className="space-y-1 text-xs text-gray-600 dark:text-gray-400">
                    <p>
                      ✓ {script.analysisResults.overview.verifiedClaims} claims
                      verified
                    </p>
                    <p>
                      ✗ {script.analysisResults.overview.flaggedClaims} claims
                      flagged
                    </p>
                    <p>
                      ⚖️ {script.analysisResults.legal.length} legal issues
                      found
                    </p>
                    <p>
                      🔗 {script.analysisResults.continuity.length} continuity
                      issues
                    </p>
                  </div>

                  <Link
                    href={`/report/${script.id}`}
                    className="mt-4 block w-full rounded-lg bg-blue-600 py-2 text-center text-sm font-medium text-white hover:bg-blue-700 transition-colors"
                  >
                    View Full Report →
                  </Link>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
