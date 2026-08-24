"use client";

import type { AgentResult } from "@/lib/types";

interface ContinuityPanelProps {
  agentResult: AgentResult | null;
}

export function ContinuityPanel({ agentResult }: ContinuityPanelProps) {
  const data = agentResult?.data ?? {};

  const characterIssues = data.character_inconsistencies ?? [];
  const timelineIssues = data.timeline_issues ?? [];
  const locationIssues = data.location_continuity ?? [];
  const propIssues = data.prop_tracking ?? [];
  const dialogueConsistency = data.dialogue_consistency ?? [];
  const recommendations = data.continuity_recommendations ?? [];
  const summary = data.continuity_summary ?? "";

  const totalIssues =
    characterIssues.length + timelineIssues.length + locationIssues.length + propIssues.length;

  return (
    <div className="space-y-6">
      {/* Summary banner */}
      <div className="rounded-xl border border-blue-200 bg-gradient-to-r from-blue-50 to-indigo-50 p-5 dark:border-blue-800 dark:from-blue-900/20 dark:to-indigo-900/20">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-blue-800 dark:text-blue-200">
              Continuity Check
            </p>
            <p className="mt-1 text-3xl font-bold text-blue-900 dark:text-blue-100">
              {totalIssues} issue{totalIssues !== 1 ? "s" : ""}
            </p>
          </div>
          <div className="text-right">
            <p className="text-sm text-blue-700 dark:text-blue-300">
              Confidence: {Math.round((agentResult?.confidence_score ?? 0.7) * 100)}%
            </p>
          </div>
        </div>
      </div>

      {/* Continuity summary */}
      {summary && (
        <div>
          <h3 className="mb-3 text-sm font-semibold text-gray-900 dark:text-gray-100">
            Continuity Summary
          </h3>
          <p className="rounded-lg bg-gray-50 p-4 text-sm text-gray-700 dark:bg-gray-800/50 dark:text-gray-300">
            {summary}
          </p>
        </div>
      )}

      {/* Issue categories grid */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        {/* Character Inconsistencies */}
        <IssueSection
          title="Character Inconsistencies"
          icon="👤"
          issues={characterIssues}
          color="red"
        />

        {/* Timeline Issues */}
        <IssueSection
          title="Timeline Issues"
          icon="⏰"
          issues={timelineIssues}
          color="amber"
        />

        {/* Location Continuity */}
        <IssueSection
          title="Location Continuity"
          icon="📍"
          issues={locationIssues}
          color="purple"
        />

        {/* Prop Tracking */}
        <IssueSection
          title="Prop Tracking"
          icon="🎭"
          issues={propIssues}
          color="teal"
        />
      </div>

      {/* Dialogue Consistency */}
      {dialogueConsistency.length > 0 && (
        <div>
          <h3 className="mb-3 flex items-center gap-2 text-sm font-semibold text-gray-900 dark:text-gray-100">
            <span>💬</span> Dialogue Consistency ({dialogueConsistency.length})
          </h3>
          <div className="space-y-2">
            {dialogueConsistency.map((issue: any, i: number) => (
              <div
                key={i}
                className="rounded-lg border border-gray-200 bg-gray-50 p-3 dark:border-gray-700 dark:bg-gray-800/50"
              >
                <p className="text-sm text-gray-700 dark:text-gray-300">
                  {typeof issue === "string" ? issue : issue.description || issue.issue || `Issue ${i + 1}`}
                </p>
                {typeof issue === "object" && issue.scenes && (
                  <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                    Scenes: {issue.scenes.join(", ")}
                  </p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recommendations */}
      {recommendations.length > 0 && (
        <div>
          <h3 className="mb-3 text-sm font-semibold text-gray-900 dark:text-gray-100">
            Continuity Recommendations
          </h3>
          <ol className="space-y-2">
            {recommendations.map((rec: string, i: number) => (
              <li
                key={i}
                className="flex items-start gap-3 rounded-lg bg-green-50 px-3 py-2 text-sm text-green-800 dark:bg-green-900/20 dark:text-green-300"
              >
                <span className="flex h-5 w-5 flex-shrink-0 items-center justify-center rounded-full bg-green-200 text-xs font-bold text-green-800 dark:bg-green-800 dark:text-green-200">
                  {i + 1}
                </span>
                {rec}
              </li>
            ))}
          </ol>
        </div>
      )}

      {/* No issues */}
      {totalIssues === 0 && dialogueConsistency.length === 0 && (
        <div className="py-8 text-center">
          <span className="text-4xl">✅</span>
          <p className="mt-3 text-sm text-gray-600 dark:text-gray-400">
            No continuity issues detected. All scenes, characters, and timelines are consistent.
          </p>
        </div>
      )}
    </div>
  );
}

function IssueSection({
  title,
  icon,
  issues,
  color,
}: {
  title: string;
  icon: string;
  issues: any[];
  color: string;
}) {
  const colorMap: Record<string, string> = {
    red: "border-red-200 bg-red-50 dark:border-red-800 dark:bg-red-900/20",
    amber: "border-amber-200 bg-amber-50 dark:border-amber-800 dark:bg-amber-900/20",
    purple: "border-purple-200 bg-purple-50 dark:border-purple-800 dark:bg-purple-900/20",
    teal: "border-teal-200 bg-teal-50 dark:border-teal-800 dark:bg-teal-900/20",
  };

  const textColor: Record<string, string> = {
    red: "text-red-800 dark:text-red-200",
    amber: "text-amber-800 dark:text-amber-200",
    purple: "text-purple-800 dark:text-purple-200",
    teal: "text-teal-800 dark:text-teal-200",
  };

  return (
    <div className={`rounded-lg border p-4 ${colorMap[color]}`}>
      <div className="flex items-center gap-2">
        <span>{icon}</span>
        <h4 className={`text-sm font-semibold ${textColor[color]}`}>{title}</h4>
        <span className={`ml-auto rounded-full px-2 py-0.5 text-xs font-medium ${textColor[color]}`}>
          {issues.length}
        </span>
      </div>
      {issues.length > 0 ? (
        <ul className="mt-3 space-y-1.5">
          {issues.slice(0, 5).map((issue: any, i: number) => (
            <li
              key={i}
              className="text-xs text-gray-700 dark:text-gray-300"
            >
              • {typeof issue === "string" ? issue : issue.description || issue.issue || `Issue ${i + 1}`}
            </li>
          ))}
          {issues.length > 5 && (
            <li className="text-xs text-gray-500 dark:text-gray-400">
              +{issues.length - 5} more
            </li>
          )}
        </ul>
      ) : (
        <p className="mt-2 text-xs text-gray-500 dark:text-gray-400">No issues found</p>
      )}
    </div>
  );
}
