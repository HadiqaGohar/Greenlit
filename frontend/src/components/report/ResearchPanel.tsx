"use client";

import type { AgentResult, Claim } from "@/lib/types";

interface ResearchPanelProps {
  agentResult: AgentResult | null;
  claims: Claim[];
}

export function ResearchPanel({ agentResult, claims }: ResearchPanelProps) {
  const data = agentResult?.data ?? {};

  const verifiedCount = data.verified_count ?? claims.filter((c) => c.verdict === "verified").length;
  const flaggedCount = data.flagged_count ?? claims.filter((c) => c.verdict === "flagged").length;
  const uncertainCount = data.uncertain_count ?? claims.filter((c) => c.verdict === "uncertain").length;
  const sourcesFound = data.sources_found ?? 0;

  // Group claims by type
  const claimsByType = claims.reduce(
    (acc, claim) => {
      acc[claim.type] = (acc[claim.type] || 0) + 1;
      return acc;
    },
    {} as Record<string, number>,
  );

  return (
    <div className="space-y-6">
      {/* Summary stats */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <StatBox label="Verified" value={verifiedCount} color="green" icon="✅" />
        <StatBox label="Flagged" value={flaggedCount} color="red" icon="🚩" />
        <StatBox label="Uncertain" value={uncertainCount} color="amber" icon="❓" />
        <StatBox label="Sources Found" value={sourcesFound} color="blue" icon="📚" />
      </div>

      {/* Claims by type */}
      <div>
        <h3 className="mb-3 text-sm font-semibold text-gray-900 dark:text-gray-100">
          Claims by Category
        </h3>
        <div className="space-y-2">
          {Object.entries(claimsByType).map(([type, count]) => {
            const percentage = claims.length > 0 ? (count / claims.length) * 100 : 0;
            return (
              <div key={type}>
                <div className="flex items-center justify-between text-sm">
                  <span className="capitalize text-gray-700 dark:text-gray-300">{type}</span>
                  <span className="text-gray-500 dark:text-gray-400">{count}</span>
                </div>
                <div className="mt-1 h-2 w-full overflow-hidden rounded-full bg-gray-200 dark:bg-gray-700">
                  <div
                    className="h-full rounded-full bg-blue-500 transition-all duration-500"
                    style={{ width: `${percentage}%` }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Research summary */}
      {data.research_summary && (
        <div>
          <h3 className="mb-3 text-sm font-semibold text-gray-900 dark:text-gray-100">
            Research Summary
          </h3>
          <p className="rounded-lg bg-gray-50 p-4 text-sm text-gray-700 dark:bg-gray-800/50 dark:text-gray-300">
            {data.research_summary}
          </p>
        </div>
      )}

      {/* Top flagged claims */}
      {flaggedCount > 0 && (
        <div>
          <h3 className="mb-3 text-sm font-semibold text-gray-900 dark:text-gray-100">
            Flagged Claims
          </h3>
          <div className="space-y-2">
            {claims
              .filter((c) => c.verdict === "flagged")
              .slice(0, 5)
              .map((claim) => (
                <div
                  key={claim.id}
                  className="rounded-lg border border-red-200 bg-red-50 p-3 dark:border-red-800 dark:bg-red-900/20"
                >
                  <p className="text-sm font-medium text-red-800 dark:text-red-200">
                    &ldquo;{claim.text}&rdquo;
                  </p>
                  <p className="mt-1 text-xs text-red-600 dark:text-red-400">{claim.note}</p>
                  <div className="mt-2 flex items-center gap-3 text-xs text-red-500 dark:text-red-400">
                    <span>Confidence: {Math.round(claim.confidence * 100)}%</span>
                    <span>Type: {claim.type}</span>
                  </div>
                </div>
              ))}
          </div>
        </div>
      )}

      {/* Sources */}
      {data.sources && Array.isArray(data.sources) && data.sources.length > 0 && (
        <div>
          <h3 className="mb-3 text-sm font-semibold text-gray-900 dark:text-gray-100">
            Sources Used
          </h3>
          <ul className="space-y-1">
            {data.sources.slice(0, 10).map((source: any, i: number) => (
              <li key={i} className="text-xs text-gray-600 dark:text-gray-400">
                {source.title || source.name || `Source ${i + 1}`}
                {source.url && (
                  <a
                    href={source.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="ml-2 text-blue-500 hover:underline"
                  >
                    (link)
                  </a>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

function StatBox({
  label,
  value,
  color,
  icon,
}: {
  label: string;
  value: number;
  color: string;
  icon: string;
}) {
  const colorMap: Record<string, string> = {
    green: "border-green-200 bg-green-50 dark:border-green-800 dark:bg-green-900/20",
    red: "border-red-200 bg-red-50 dark:border-red-800 dark:bg-red-900/20",
    amber: "border-amber-200 bg-amber-50 dark:border-amber-800 dark:bg-amber-900/20",
    blue: "border-blue-200 bg-blue-50 dark:border-blue-800 dark:bg-blue-900/20",
  };

  return (
    <div className={`rounded-lg border p-3 ${colorMap[color] ?? colorMap.blue}`}>
      <div className="flex items-center gap-2">
        <span>{icon}</span>
        <span className="text-xs text-gray-600 dark:text-gray-400">{label}</span>
      </div>
      <p className="mt-1 text-2xl font-bold text-gray-900 dark:text-gray-100">{value}</p>
    </div>
  );
}
