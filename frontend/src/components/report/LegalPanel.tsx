"use client";

import type { AgentResult } from "@/lib/types";

interface LegalPanelProps {
  agentResult: AgentResult | null;
}

export function LegalPanel({ agentResult }: LegalPanelProps) {
  const data = agentResult?.data ?? {};

  const copyrightRisks = data.copyright_risks ?? [];
  const trademarkIssues = data.trademark_issues ?? [];
  const clearanceRequired = data.clearance_required ?? [];
  const privacyConcerns = data.privacy_concerns ?? [];
  const estimatedCost = data.estimated_clearance_cost ?? 0;
  const recommendations = data.legal_recommendations ?? [];
  const riskSummary = data.risk_summary ?? "";

  const totalIssues = copyrightRisks.length + trademarkIssues.length + privacyConcerns.length;

  return (
    <div className="space-y-6">
      {/* Cost estimate banner */}
      <div className="rounded-xl border border-amber-200 bg-gradient-to-r from-amber-50 to-orange-50 p-5 dark:border-amber-800 dark:from-amber-900/20 dark:to-orange-900/20">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-amber-800 dark:text-amber-200">
              Estimated Clearance Cost
            </p>
            <p className="mt-1 text-3xl font-bold text-amber-900 dark:text-amber-100">
              ${estimatedCost.toLocaleString()}
            </p>
          </div>
          <div className="text-right">
            <p className="text-sm text-amber-700 dark:text-amber-300">
              {totalIssues} issue{totalIssues !== 1 ? "s" : ""} found
            </p>
            <p className="text-xs text-amber-600 dark:text-amber-400">
              Confidence: {Math.round((agentResult?.confidence_score ?? 0.8) * 100)}%
            </p>
          </div>
        </div>
      </div>

      {/* Risk summary */}
      {riskSummary && (
        <div>
          <h3 className="mb-3 text-sm font-semibold text-gray-900 dark:text-gray-100">
            Legal Risk Summary
          </h3>
          <p className="rounded-lg bg-gray-50 p-4 text-sm text-gray-700 dark:bg-gray-800/50 dark:text-gray-300">
            {riskSummary}
          </p>
        </div>
      )}

      {/* Copyright Risks */}
      {copyrightRisks.length > 0 && (
        <div>
          <h3 className="mb-3 flex items-center gap-2 text-sm font-semibold text-gray-900 dark:text-gray-100">
            <span>©️</span> Copyright Risks ({copyrightRisks.length})
          </h3>
          <div className="space-y-2">
            {copyrightRisks.map((risk: any, i: number) => (
              <div
                key={i}
                className="rounded-lg border border-red-200 bg-red-50 p-3 dark:border-red-800 dark:bg-red-900/20"
              >
                <p className="text-sm font-medium text-red-800 dark:text-red-200">
                  {risk.title || risk.description || `Copyright Risk ${i + 1}`}
                </p>
                {risk.details && (
                  <p className="mt-1 text-xs text-red-600 dark:text-red-400">{risk.details}</p>
                )}
                {risk.estimated_cost && (
                  <p className="mt-1 text-xs font-medium text-red-700 dark:text-red-300">
                    Est. Cost: ${risk.estimated_cost.toLocaleString()}
                  </p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Trademark Issues */}
      {trademarkIssues.length > 0 && (
        <div>
          <h3 className="mb-3 flex items-center gap-2 text-sm font-semibold text-gray-900 dark:text-gray-100">
            <span>™️</span> Trademark Issues ({trademarkIssues.length})
          </h3>
          <div className="space-y-2">
            {trademarkIssues.map((issue: any, i: number) => (
              <div
                key={i}
                className="rounded-lg border border-orange-200 bg-orange-50 p-3 dark:border-orange-800 dark:bg-orange-900/20"
              >
                <p className="text-sm font-medium text-orange-800 dark:text-orange-200">
                  {issue.title || issue.description || `Trademark Issue ${i + 1}`}
                </p>
                {issue.details && (
                  <p className="mt-1 text-xs text-orange-600 dark:text-orange-400">
                    {issue.details}
                  </p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Privacy Concerns */}
      {privacyConcerns.length > 0 && (
        <div>
          <h3 className="mb-3 flex items-center gap-2 text-sm font-semibold text-gray-900 dark:text-gray-100">
            <span>🔒</span> Privacy Concerns ({privacyConcerns.length})
          </h3>
          <div className="space-y-2">
            {privacyConcerns.map((concern: any, i: number) => (
              <div
                key={i}
                className="rounded-lg border border-purple-200 bg-purple-50 p-3 dark:border-purple-800 dark:bg-purple-900/20"
              >
                <p className="text-sm font-medium text-purple-800 dark:text-purple-200">
                  {concern.title || concern.description || `Privacy Concern ${i + 1}`}
                </p>
                {concern.details && (
                  <p className="mt-1 text-xs text-purple-600 dark:text-purple-400">
                    {concern.details}
                  </p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Clearance Required */}
      {clearanceRequired.length > 0 && (
        <div>
          <h3 className="mb-3 flex items-center gap-2 text-sm font-semibold text-gray-900 dark:text-gray-100">
            <span>📋</span> Clearance Required ({clearanceRequired.length})
          </h3>
          <ul className="space-y-1">
            {clearanceRequired.map((item: any, i: number) => (
              <li
                key={i}
                className="flex items-center gap-2 rounded-lg bg-gray-50 px-3 py-2 text-sm text-gray-700 dark:bg-gray-800/50 dark:text-gray-300"
              >
                <span className="h-1.5 w-1.5 rounded-full bg-amber-500" />
                {typeof item === "string" ? item : item.title || item.description || `Item ${i + 1}`}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Legal Recommendations */}
      {recommendations.length > 0 && (
        <div>
          <h3 className="mb-3 text-sm font-semibold text-gray-900 dark:text-gray-100">
            Legal Recommendations
          </h3>
          <ol className="space-y-2">
            {recommendations.map((rec: string, i: number) => (
              <li
                key={i}
                className="flex items-start gap-3 rounded-lg bg-blue-50 px-3 py-2 text-sm text-blue-800 dark:bg-blue-900/20 dark:text-blue-300"
              >
                <span className="flex h-5 w-5 flex-shrink-0 items-center justify-center rounded-full bg-blue-200 text-xs font-bold text-blue-800 dark:bg-blue-800 dark:text-blue-200">
                  {i + 1}
                </span>
                {rec}
              </li>
            ))}
          </ol>
        </div>
      )}

      {/* No issues */}
      {totalIssues === 0 && (
        <div className="py-8 text-center">
          <span className="text-4xl">✅</span>
          <p className="mt-3 text-sm text-gray-600 dark:text-gray-400">
            No legal issues detected. The script appears clear for production.
          </p>
        </div>
      )}
    </div>
  );
}
