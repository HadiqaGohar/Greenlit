"use client";

import type { AgentResult, AgentType } from "@/lib/types";

interface OverviewPanelProps {
  riskScore: number;
  riskLevel: string;
  riskFactors: string[];
  recommendedActions: string[];
  agentResults: Record<AgentType, AgentResult>;
  processingTime: number;
  claimsCount: number;
}

const agentLabels: Record<AgentType, { name: string; icon: string; description: string }> = {
  director: { name: "Director", icon: "🎬", description: "Script analysis & claim extraction" },
  research: { name: "Research", icon: "🔍", description: "Fact verification & source finding" },
  legal: { name: "Legal", icon: "⚖️", description: "Clearance & rights analysis" },
  continuity: { name: "Continuity", icon: "🔗", description: "Timeline & consistency checking" },
};

export function OverviewPanel({
  riskScore,
  riskLevel,
  riskFactors,
  recommendedActions,
  agentResults,
  processingTime,
  claimsCount,
}: OverviewPanelProps) {
  const agents = Object.entries(agentResults) as [AgentType, AgentResult][];
  const successfulAgents = agents.filter(([, r]) => r.success);
  const getConfidence = (r: AgentResult) => {
    const val = r.confidence ?? r.confidence_score;
    return Number.isFinite(val) ? val : 0;
  };
  const avgConfidence =
    successfulAgents.length > 0
      ? successfulAgents.reduce((sum, [, r]) => sum + getConfidence(r), 0) / successfulAgents.length
      : 0;

  return (
    <div className="space-y-6">
      {/* Summary stats */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <StatCard label="Claims Found" value={claimsCount} icon="📋" />
        <StatCard label="Risk Score" value={`${Math.round(riskScore)}`} icon="🎯" color={riskLevel} />
        <StatCard label="Avg Confidence" value={`${Math.round(avgConfidence * 100)}%`} icon="📊" />
        <StatCard label="Processing Time" value={`${processingTime.toFixed(1)}s`} icon="⏱️" />
      </div>

      {/* Agent Results */}
      <div>
        <h3 className="mb-3 text-sm font-semibold text-gray-900 dark:text-gray-100">
          Agent Performance
        </h3>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          {agents.map(([type, result]) => {
            const info = agentLabels[type];
            return (
              <div
                key={type}
                className={`rounded-lg border p-4 ${
                  result.success
                    ? "border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-800"
                    : "border-red-200 bg-red-50 dark:border-red-800 dark:bg-red-900/20"
                }`}
              >
                <div className="flex items-center gap-3">
                  <span className="text-2xl">{info.icon}</span>
                  <div className="flex-1">
                    <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
                      {info.name}
                    </p>
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      {info.description}
                    </p>
                  </div>
                  <span
                    className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                      result.success
                        ? "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200"
                        : "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200"
                    }`}
                  >
                    {result.success ? "Success" : "Failed"}
                  </span>
                </div>
                <div className="mt-3 flex items-center gap-4 text-xs text-gray-500 dark:text-gray-400">
                  <span>Confidence: {Math.round(getConfidence(result) * 100)}%</span>
                  <span>Time: {Number.isFinite(result.processing_time) ? result.processing_time.toFixed(1) : "0.0"}s</span>
                </div>
                {!result.success && (result as any).error && (
                  <div className="mt-2 p-2 rounded bg-red-100 dark:bg-red-900/30 text-xs text-red-700 dark:text-red-300">
                    {(result as any).error}
                  </div>
                )}
                {/* Confidence bar */}
                <div className="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-gray-200 dark:bg-gray-700">
                  <div
                    className="h-full rounded-full bg-blue-500 transition-all duration-500"
                    style={{ width: `${getConfidence(result) * 100}%` }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Risk Factors */}
      {riskFactors && riskFactors.length > 0 && (
        <div>
          <h3 className="mb-3 text-sm font-semibold text-gray-900 dark:text-gray-100">
            Risk Factors
          </h3>
          <ul className="space-y-2">
            {riskFactors.map((factor, i) => (
              <li
                key={i}
                className="flex items-start gap-2 rounded-lg bg-gray-50 px-3 py-2 text-sm text-gray-700 dark:bg-gray-800/50 dark:text-gray-300"
              >
                <span className="mt-1 h-1.5 w-1.5 flex-shrink-0 rounded-full bg-amber-500" />
                {factor}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Recommended Actions */}
      {recommendedActions && recommendedActions.length > 0 && (
        <div>
          <h3 className="mb-3 text-sm font-semibold text-gray-900 dark:text-gray-100">
            Recommended Actions
          </h3>
          <ol className="space-y-2">
            {recommendedActions.map((action, i) => (
              <li
                key={i}
                className="flex items-start gap-3 rounded-lg bg-blue-50 px-3 py-2 text-sm text-blue-800 dark:bg-blue-900/20 dark:text-blue-300"
              >
                <span className="flex h-5 w-5 flex-shrink-0 items-center justify-center rounded-full bg-blue-200 text-xs font-bold text-blue-800 dark:bg-blue-800 dark:text-blue-200">
                  {i + 1}
                </span>
                {action}
              </li>
            ))}
          </ol>
        </div>
      )}
    </div>
  );
}

function StatCard({
  label,
  value,
  icon,
  color,
}: {
  label: string;
  value: string;
  icon: string;
  color?: string;
}) {
  return (
    <div className="rounded-lg border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-800">
      <div className="flex items-center gap-2">
        <span className="text-lg">{icon}</span>
        <span className="text-xs text-gray-500 dark:text-gray-400">{label}</span>
      </div>
      <p className="mt-2 text-2xl font-bold text-gray-900 dark:text-gray-100">{value}</p>
    </div>
  );
}
