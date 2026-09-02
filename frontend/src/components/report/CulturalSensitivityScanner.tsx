"use client";

import { useState } from "react";
import { Globe, ChevronDown, ChevronUp, CheckCircle } from "lucide-react";

interface CulturalIssue {
  category: string;
  severity: string;
  description: string;
  location: string;
  impact: string;
  suggestion: string;
}

interface CulturalData {
  issues: CulturalIssue[];
  overall_sensitivity_score: number;
  positive_representations: string[];
  recommendations: string[];
}

interface CulturalSensitivityScannerProps {
  scriptText: string;
}

const severityColors: Record<string, string> = {
  high: "#ef4444",
  medium: "#f59e0b",
  low: "#10b981",
};

const severityLabels: Record<string, string> = {
  high: "High Risk",
  medium: "Medium Risk",
  low: "Low Risk",
};

const categoryLabels: Record<string, string> = {
  racial_stereotype: "Racial/Ethnic Stereotype",
  gender_representation: "Gender Representation",
  disability_representation: "Disability Representation",
  lgbtq_representation: "LGBTQ+ Representation",
  cultural_appropriation: "Cultural Appropriation",
  religious_sensitivity: "Religious Sensitivity",
  age_representation: "Age Representation",
  other: "Other Issue",
};

export function CulturalSensitivityScanner({ scriptText }: CulturalSensitivityScannerProps) {
  const [data, setData] = useState<CulturalData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expandedIssue, setExpandedIssue] = useState<number | null>(null);

  const analyzeCultural = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}/api/cultural-analysis`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ script_text: scriptText }),
      });

      if (!response.ok) {
        throw new Error("Cultural analysis failed");
      }

      const result = await response.json();
      setData(result.cultural_analysis);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to analyze cultural sensitivity");
    } finally {
      setLoading(false);
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 80) return "var(--verified)";
    if (score >= 50) return "var(--accent)";
    return "var(--flagged)";
  };

  return (
    <div className="claim-card rounded-xl p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Globe size={20} style={{ color: "var(--accent)" }} />
          <h3 className="font-display text-lg font-semibold" style={{ color: "var(--text)" }}>
            Cultural Sensitivity Scanner
          </h3>
        </div>
        {!data && !loading && (
          <button
            onClick={analyzeCultural}
            className="px-4 py-2 rounded-lg text-sm font-medium transition-all hover:scale-105"
            style={{
              background: "linear-gradient(135deg, var(--accent) 0%, #8b5cf6 100%)",
              color: "white",
            }}
          >
            Analyze Culture
          </button>
        )}
      </div>

      {loading && (
        <div className="flex items-center justify-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2" style={{ borderColor: "var(--accent)" }} />
          <span className="ml-3" style={{ color: "var(--text-muted)" }}>Analyzing cultural sensitivity...</span>
        </div>
      )}

      {error && (
        <div className="text-center py-8">
          <p className="text-flagged mb-4">{error}</p>
          <button
            onClick={analyzeCultural}
            className="px-4 py-2 rounded-lg text-sm font-medium"
            style={{ backgroundColor: "var(--bg)", color: "var(--text)", border: "1px solid var(--border)" }}
          >
            Try Again
          </button>
        </div>
      )}

      {data && (
        <div>
          {/* Sensitivity Score */}
          <div className="mb-6 p-4 rounded-lg" style={{ backgroundColor: "color-mix(in srgb, var(--accent) 10%, transparent)" }}>
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium" style={{ color: "var(--text-muted)" }}>Sensitivity Score</span>
              <span className="text-2xl font-bold" style={{ color: getScoreColor(data.overall_sensitivity_score) }}>
                {data.overall_sensitivity_score}/100
              </span>
            </div>
            <p className="text-xs mt-2" style={{ color: "var(--text-muted)" }}>
              {data.overall_sensitivity_score >= 80
                ? "Good representation overall"
                : data.overall_sensitivity_score >= 50
                ? "Some areas need improvement"
                : "Significant cultural issues found"}
            </p>
          </div>

          {/* Issues Summary */}
          <div className="grid grid-cols-3 gap-3 mb-6">
            <div className="p-3 rounded-lg text-center" style={{ backgroundColor: "var(--bg)" }}>
              <p className="text-2xl font-bold" style={{ color: "var(--text)" }}>{data.issues.length}</p>
              <p className="text-xs" style={{ color: "var(--text-muted)" }}>Total Issues</p>
            </div>
            <div className="p-3 rounded-lg text-center" style={{ backgroundColor: "var(--bg)" }}>
              <p className="text-2xl font-bold" style={{ color: "var(--flagged)" }}>
                {data.issues.filter(i => i.severity === "high").length}
              </p>
              <p className="text-xs" style={{ color: "var(--text-muted)" }}>High Risk</p>
            </div>
            <div className="p-3 rounded-lg text-center" style={{ backgroundColor: "var(--bg)" }}>
              <p className="text-2xl font-bold" style={{ color: "var(--verified)" }}>
                {data.positive_representations.length}
              </p>
              <p className="text-xs" style={{ color: "var(--text-muted)" }}>Positive</p>
            </div>
          </div>

          {/* Issues List */}
          {data.issues.length > 0 && (
            <div className="space-y-2 mb-6">
              <h4 className="font-medium text-sm" style={{ color: "var(--text)" }}>Issues Found</h4>
              {data.issues.map((issue, idx) => (
                <div key={idx} className="rounded-lg border" style={{ borderColor: "var(--border)" }}>
                  <button
                    onClick={() => setExpandedIssue(expandedIssue === idx ? null : idx)}
                    className="w-full flex items-center justify-between p-3 text-left"
                    style={{ backgroundColor: "var(--bg)" }}
                  >
                    <div className="flex items-center gap-3">
                      <span
                        className="px-2 py-1 rounded text-xs font-medium"
                        style={{
                          backgroundColor: `color-mix(in srgb, ${severityColors[issue.severity] || severityColors.low} 20%, transparent)`,
                          color: severityColors[issue.severity] || severityColors.low,
                        }}
                      >
                        {severityLabels[issue.severity] || issue.severity}
                      </span>
                      <span className="text-sm" style={{ color: "var(--text)" }}>
                        {categoryLabels[issue.category] || issue.category}
                      </span>
                    </div>
                    {expandedIssue === idx ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                  </button>
                  {expandedIssue === idx && (
                    <div className="p-3 border-t" style={{ borderColor: "var(--border)" }}>
                      <p className="text-sm mb-2" style={{ color: "var(--text)" }}>{issue.description}</p>
                      <p className="text-xs mb-1" style={{ color: "var(--text-muted)" }}>
                        <strong>Location:</strong> {issue.location}
                      </p>
                      <p className="text-xs mb-1" style={{ color: "var(--text-muted)" }}>
                        <strong>Impact:</strong> {issue.impact}
                      </p>
                      <p className="text-xs mt-2 p-2 rounded" style={{ backgroundColor: "color-mix(in srgb, var(--verified) 10%, transparent)", color: "var(--verified)" }}>
                        <strong>Suggestion:</strong> {issue.suggestion}
                      </p>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}

          {/* No Issues */}
          {data.issues.length === 0 && (
            <div className="text-center py-4 mb-6 rounded-lg" style={{ backgroundColor: "color-mix(in srgb, var(--verified) 10%, transparent)" }}>
              <CheckCircle size={24} className="mx-auto mb-2" style={{ color: "var(--verified)" }} />
              <p className="text-sm font-medium" style={{ color: "var(--verified)" }}>No cultural sensitivity issues detected</p>
            </div>
          )}

          {/* Positive Representations */}
          {data.positive_representations.length > 0 && (
            <div className="mb-6 p-4 rounded-lg" style={{ backgroundColor: "color-mix(in srgb, var(--verified) 10%, transparent)" }}>
              <h4 className="font-medium text-sm mb-2" style={{ color: "var(--verified)" }}>Positive Representations</h4>
              <ul className="space-y-1">
                {data.positive_representations.map((item, i) => (
                  <li key={i} className="text-sm" style={{ color: "var(--text-muted)" }}>✓ {item}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Recommendations */}
          {data.recommendations.length > 0 && (
            <div className="p-4 rounded-lg" style={{ backgroundColor: "color-mix(in srgb, #f59e0b 10%, transparent)" }}>
              <h4 className="font-medium text-sm mb-2" style={{ color: "#f59e0b" }}>Recommendations</h4>
              <ul className="space-y-1">
                {data.recommendations.map((rec, i) => (
                  <li key={i} className="text-sm" style={{ color: "var(--text-muted)" }}>• {rec}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
