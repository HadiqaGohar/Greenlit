"use client";

import { useState } from "react";

interface StakeholderFinding {
  category: string;
  severity: string;
  items: string[];
}

interface StakeholderRole {
  role: string;
  title: string;
  icon: string;
  overall_score: number;
  score_label: string;
  risk_level: string;
  key_concerns: string[];
  findings: StakeholderFinding[];
  recommendations: string[];
  summary: string;
}

interface StakeholderResponse {
  stakeholder_id: string;
  report_id: string;
  success: boolean;
  stakeholders: StakeholderRole[];
  overall_readiness: number;
  roles_analyzed: number;
  processing_time: number;
  generated_at: string;
  error: string | null;
}

interface StakeholderPanelProps {
  reportId: string;
}

const SEVERITY_COLORS: Record<string, string> = {
  high: "border-red-300 bg-red-50 dark:border-red-800 dark:bg-red-900/20",
  medium: "border-amber-300 bg-amber-50 dark:border-amber-800 dark:bg-amber-900/20",
  low: "border-blue-300 bg-blue-50 dark:border-blue-800 dark:bg-blue-900/20",
  info: "border-gray-200 bg-gray-50 dark:border-gray-700 dark:bg-gray-800",
  positive: "border-green-300 bg-green-50 dark:border-green-800 dark:bg-green-900/20",
  warning: "border-amber-300 bg-amber-50 dark:border-amber-800 dark:bg-amber-900/20",
};

const SEVERITY_DOT: Record<string, string> = {
  high: "bg-red-500",
  medium: "bg-amber-500",
  low: "bg-blue-500",
  info: "bg-gray-400",
  positive: "bg-green-500",
  warning: "bg-amber-500",
};

const RISK_BADGE: Record<string, string> = {
  low: "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300",
  medium: "bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-300",
  high: "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300",
  critical: "bg-red-200 text-red-900 dark:bg-red-900/50 dark:text-red-200",
};

export function StakeholderPanel({ reportId }: StakeholderPanelProps) {
  const [data, setData] = useState<StakeholderResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeRole, setActiveRole] = useState<string>("studio_executive");
  const [expandedFindings, setExpandedFindings] = useState<Set<number>>(new Set());

  const runAnalysis = async () => {
    setLoading(true);
    setError(null);
    try {
      const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const res = await fetch(`${API_URL}/api/stakeholder/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ report_id: reportId }),
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Failed to analyze stakeholders");
      }
      setData(await res.json());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to analyze stakeholders");
    } finally {
      setLoading(false);
    }
  };

  const activeStakeholder = data?.stakeholders.find((s) => s.role === activeRole);

  const toggleFinding = (idx: number) => {
    const next = new Set(expandedFindings);
    if (next.has(idx)) next.delete(idx);
    else next.add(idx);
    setExpandedFindings(next);
  };

  return (
    <div className="rounded-xl border border-gray-200 bg-white p-6 dark:border-gray-700 dark:bg-gray-900">
      {/* Header */}
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            🏢 Multi-Stakeholder Analysis
          </h3>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            See your script through the eyes of 8 production stakeholders
          </p>
        </div>
        {!data && !loading && (
          <button
            onClick={runAnalysis}
            className="rounded-lg bg-gradient-to-r from-indigo-600 to-purple-600 px-4 py-2 text-sm font-medium text-white shadow-lg hover:from-indigo-700 hover:to-purple-700 transition-all"
          >
            🏢 Analyze Stakeholders
          </button>
        )}
        {data && (
          <button
            onClick={runAnalysis}
            className="rounded-lg border border-gray-300 bg-white px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-300"
          >
            🔄 Re-analyze
          </button>
        )}
      </div>

      {/* Loading */}
      {loading && (
        <div className="py-12 text-center">
          <div className="mb-4 inline-flex h-16 w-16 items-center justify-center rounded-full bg-indigo-100 dark:bg-indigo-900/30">
            <div className="h-10 w-10 animate-spin rounded-full border-4 border-indigo-200 border-t-indigo-600" />
          </div>
          <p className="text-sm font-medium text-gray-900 dark:text-white">
            Analyzing from 8 stakeholder perspectives...
          </p>
          <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
            Synthesizing data from all agent results
          </p>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-4 dark:border-red-800 dark:bg-red-900/20">
          <p className="text-sm text-red-800 dark:text-red-200">{error}</p>
          <button onClick={runAnalysis} className="mt-2 text-xs font-medium text-red-600 hover:text-red-800 dark:text-red-400">
            Try again
          </button>
        </div>
      )}

      {/* Results */}
      {data && !loading && (
        <div>
          {/* Overall Readiness Bar */}
          <div className="mb-6 rounded-xl border border-gray-200 bg-gradient-to-r from-gray-50 to-indigo-50 p-5 dark:border-gray-700 dark:from-gray-800 dark:to-indigo-900/20">
            <div className="flex items-center justify-between mb-3">
              <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300">
                Overall Production Readiness
              </h4>
              <span className="text-2xl font-bold text-indigo-600 dark:text-indigo-400">
                {data.overall_readiness}/100
              </span>
            </div>
            <div className="h-3 w-full overflow-hidden rounded-full bg-gray-200 dark:bg-gray-700">
              <div
                className="h-full rounded-full bg-gradient-to-r from-indigo-500 to-purple-500 transition-all duration-700"
                style={{ width: `${data.overall_readiness}%` }}
              />
            </div>
            <div className="mt-2 flex items-center gap-3 text-xs text-gray-500 dark:text-gray-400">
              <span>{data.roles_analyzed} stakeholder perspectives</span>
              <span>|</span>
              <span>Generated in {data.processing_time.toFixed(1)}s</span>
            </div>
          </div>

          {/* Stakeholder Quick Cards Grid */}
          <div className="mb-6 grid grid-cols-2 gap-2 sm:grid-cols-4">
            {data.stakeholders.map((s) => (
              <button
                key={s.role}
                onClick={() => setActiveRole(s.role)}
                className={`rounded-lg border p-3 text-left transition-all ${
                  activeRole === s.role
                    ? "border-indigo-400 bg-indigo-50 ring-1 ring-indigo-300 dark:border-indigo-600 dark:bg-indigo-900/20"
                    : "border-gray-200 bg-white hover:border-gray-300 dark:border-gray-700 dark:bg-gray-800"
                }`}
              >
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-lg">{s.icon}</span>
                  <span className="text-xs font-medium text-gray-700 dark:text-gray-300 truncate">
                    {s.title}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <ScoreBadge score={s.overall_score} />
                  <span className={`rounded-full px-1.5 py-0.5 text-[10px] font-medium ${RISK_BADGE[s.risk_level] || RISK_BADGE.medium}`}>
                    {s.risk_level}
                  </span>
                </div>
              </button>
            ))}
          </div>

          {/* Active Stakeholder Detail */}
          {activeStakeholder && (
            <StakeholderDetail
              stakeholder={activeStakeholder}
              expandedFindings={expandedFindings}
              onToggleFinding={toggleFinding}
            />
          )}
        </div>
      )}
    </div>
  );
}

function ScoreBadge({ score }: { score: number }) {
  const color =
    score >= 70 ? "text-green-600 dark:text-green-400" :
    score >= 40 ? "text-amber-600 dark:text-amber-400" :
    "text-red-600 dark:text-red-400";
  return (
    <span className={`text-sm font-bold ${color}`}>
      {score}
    </span>
  );
}

function StakeholderDetail({
  stakeholder,
  expandedFindings,
  onToggleFinding,
}: {
  stakeholder: StakeholderRole;
  expandedFindings: Set<number>;
  onToggleFinding: (idx: number) => void;
}) {
  const s = stakeholder;

  return (
    <div className="rounded-xl border border-gray-200 bg-white p-5 dark:border-gray-700 dark:bg-gray-800">
      {/* Role Header */}
      <div className="flex items-center gap-4 mb-5">
        <span className="text-4xl">{s.icon}</span>
        <div className="flex-1">
          <h4 className="text-lg font-bold text-gray-900 dark:text-white">{s.title}</h4>
          <p className="text-sm text-gray-500 dark:text-gray-400">{s.summary}</p>
        </div>
        <div className="text-right">
          <div className="text-3xl font-bold text-indigo-600 dark:text-indigo-400">{s.overall_score}</div>
          <div className="text-xs text-gray-500 dark:text-gray-400">{s.score_label}</div>
        </div>
      </div>

      {/* Key Concerns */}
      {s.key_concerns.length > 0 && (
        <div className="mb-5">
          <h5 className="mb-2 text-sm font-semibold text-gray-700 dark:text-gray-300">
            Key Concerns
          </h5>
          <div className="space-y-1.5">
            {s.key_concerns.map((concern, i) => (
              <div
                key={i}
                className="flex items-start gap-2 rounded-lg bg-amber-50 px-3 py-2 text-sm dark:bg-amber-900/10"
              >
                <span className="mt-0.5 h-1.5 w-1.5 flex-shrink-0 rounded-full bg-amber-500" />
                <span className="text-amber-800 dark:text-amber-200">{concern}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Findings */}
      {s.findings.length > 0 && (
        <div className="mb-5">
          <h5 className="mb-2 text-sm font-semibold text-gray-700 dark:text-gray-300">
            Detailed Findings
          </h5>
          <div className="space-y-2">
            {s.findings.map((finding, idx) => (
              <div
                key={idx}
                className={`rounded-lg border p-3 ${SEVERITY_COLORS[finding.severity] || SEVERITY_COLORS.info}`}
              >
                <button
                  onClick={() => onToggleFinding(idx)}
                  className="flex w-full items-center justify-between text-left"
                >
                  <div className="flex items-center gap-2">
                    <span className={`h-2 w-2 rounded-full ${SEVERITY_DOT[finding.severity] || SEVERITY_DOT.info}`} />
                    <span className="text-sm font-medium text-gray-800 dark:text-gray-200">
                      {finding.category}
                    </span>
                    <span className="rounded-full bg-gray-200 px-1.5 py-0.5 text-[10px] font-medium text-gray-600 dark:bg-gray-700 dark:text-gray-400">
                      {finding.items.length}
                    </span>
                  </div>
                  <svg
                    className={`h-4 w-4 text-gray-400 transition-transform ${expandedFindings.has(idx) ? "rotate-180" : ""}`}
                    fill="none" viewBox="0 0 24 24" stroke="currentColor"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </button>
                {expandedFindings.has(idx) && (
                  <ul className="mt-2 space-y-1 pl-5">
                    {finding.items.map((item, i) => (
                      <li key={i} className="text-xs text-gray-600 dark:text-gray-400 list-disc">
                        {item}
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recommendations */}
      {s.recommendations.length > 0 && (
        <div>
          <h5 className="mb-2 text-sm font-semibold text-gray-700 dark:text-gray-300">
            Recommendations
          </h5>
          <div className="space-y-1.5">
            {s.recommendations.map((rec, i) => (
              <div key={i} className="flex items-start gap-2 text-sm">
                <span className="mt-0.5 flex-shrink-0 text-indigo-500">
                  {i + 1}.
                </span>
                <span className="text-gray-700 dark:text-gray-300">{rec}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
