"use client";

import { useState, useEffect } from "react";
import { BarChart } from "@/components/charts/BarChart";
import { PieChart } from "@/components/charts/PieChart";
import { TrendLine } from "@/components/charts/TrendLine";
import { StatCard } from "@/components/charts/StatCard";
import {
  AnalyticsReport,
  getAnalyticsOverview,
  getAnalyticsTrends,
  getComparativeAnalysis,
  getProjectComparison,
  generateAnalyticsReport,
} from "@/lib/analytics";
import {
  FileText,
  AlertTriangle,
  CheckCircle,
  TrendingUp,
  TrendingDown,
  Clock,
  Zap,
} from "lucide-react";

type Timeframe = "week" | "month" | "quarter" | "year";

export default function AnalyticsPage() {
  const [timeframe, setTimeframe] = useState<Timeframe>("month");
  const [report, setReport] = useState<AnalyticsReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadAnalytics();
  }, [timeframe]);

  const loadAnalytics = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await generateAnalyticsReport(timeframe);
      setReport(data);
    } catch (err) {
      setError("Failed to load analytics. Please try again.");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-6 py-12">
        <div className="animate-pulse space-y-6">
          <div className="h-8 w-64 rounded" style={{ backgroundColor: "var(--border)" }} />
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="h-32 rounded-lg" style={{ backgroundColor: "var(--border)" }} />
            ))}
          </div>
          <div className="h-80 rounded-lg" style={{ backgroundColor: "var(--border)" }} />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-7xl mx-auto px-6 py-12">
        <div
          className="rounded-lg p-8 text-center"
          style={{
            border: "1px solid var(--flagged)",
            backgroundColor: "rgba(192, 57, 43, 0.1)",
          }}
        >
          <AlertTriangle
            size={48}
            className="mx-auto mb-4"
            style={{ color: "var(--flagged)" }}
          />
          <h2 className="text-xl font-semibold mb-2" style={{ color: "var(--text)" }}>
            Error Loading Analytics
          </h2>
          <p className="mb-4" style={{ color: "var(--text-muted)" }}>
            {error}
          </p>
          <button
            onClick={loadAnalytics}
            className="px-4 py-2 rounded-lg text-sm font-semibold"
            style={{
              backgroundColor: "var(--accent)",
              color: "var(--accent-contrast)",
            }}
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!report) return null;

  const { overview, risk_trend, scripts_trend, comparative, top_projects, insights } = report;

  const riskPieData = [
    { label: "Low", value: overview.risk_distribution.low || 0, color: "var(--verified)" },
    { label: "Medium", value: overview.risk_distribution.medium || 0, color: "var(--warning, #f59e0b)" },
    { label: "High", value: overview.risk_distribution.high || 0, color: "#f97316" },
    { label: "Critical", value: overview.risk_distribution.critical || 0, color: "var(--flagged)" },
  ];

  const claimsPieData = [
    { label: "Verified", value: overview.claims_by_status.verified || 0, color: "var(--verified)" },
    { label: "Pending", value: overview.claims_by_status.pending || 0, color: "var(--warning, #f59e0b)" },
    { label: "Flagged", value: overview.claims_by_status.flagged || 0, color: "var(--flagged)" },
    { label: "Needs Review", value: overview.claims_by_status.needs_review || 0, color: "#8b5cf6" },
  ];

  const projectBarData = {
    labels: top_projects.map((p) => p.title.substring(0, 12)),
    datasets: [
      {
        label: "Risk Score",
        data: top_projects.map((p) => p.risk_score),
        color: "var(--accent)",
      },
    ],
  };

  return (
    <div className="max-w-7xl mx-auto px-6 py-12">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-8">
        <div>
          <h1
            className="font-display text-4xl font-bold mb-2"
            style={{ color: "var(--text)" }}
          >
            Analytics Dashboard
          </h1>
          <p style={{ color: "var(--text-muted)" }}>
            Studio-level insights across all your projects
          </p>
        </div>

        {/* Timeframe selector */}
        <div
          className="flex rounded-lg p-1"
          style={{ backgroundColor: "var(--border)" }}
        >
          {(["week", "month", "quarter", "year"] as Timeframe[]).map((tf) => (
            <button
              key={tf}
              onClick={() => setTimeframe(tf)}
              className="px-4 py-2 rounded-md text-sm font-medium capitalize transition-colors"
              style={{
                backgroundColor: timeframe === tf ? "var(--bg)" : "transparent",
                color: timeframe === tf ? "var(--text)" : "var(--text-muted)",
                boxShadow: timeframe === tf ? "0 1px 3px rgba(0,0,0,0.1)" : "none",
              }}
            >
              {tf}
            </button>
          ))}
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <StatCard
          title="Total Scripts"
          value={overview.total_scripts}
          change={comparative.scripts_trend === "growing" ? 15 : -5}
          changeLabel="vs last period"
          icon={FileText}
          color="var(--accent)"
        />
        <StatCard
          title="Avg Risk Score"
          value={`${overview.average_risk_score.toFixed(1)}%`}
          change={comparative.risk_trend === "improving" ? -12 : 8}
          changeLabel="vs last period"
          icon={comparative.risk_trend === "improving" ? TrendingDown : TrendingUp}
          color={comparative.risk_trend === "improving" ? "var(--verified)" : "var(--flagged)"}
        />
        <StatCard
          title="Claims Verified"
          value={overview.verified_claims}
          change={12}
          changeLabel="this period"
          icon={CheckCircle}
          color="var(--verified)"
        />
        <StatCard
          title="Flagged Claims"
          value={overview.flagged_claims}
          change={-8}
          changeLabel="vs last period"
          icon={AlertTriangle}
          color="var(--flagged)"
        />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {/* Risk Distribution Pie */}
        <div className="claim-card rounded-lg p-6">
          <PieChart
            data={riskPieData}
            title="Risk Distribution"
            size={180}
          />
        </div>

        {/* Claims Status Pie */}
        <div className="claim-card rounded-lg p-6">
          <PieChart
            data={claimsPieData}
            title="Claims by Status"
            size={180}
          />
        </div>
      </div>

      {/* Trend Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {/* Risk Score Trend */}
        <div className="claim-card rounded-lg p-6">
          <TrendLine
            labels={risk_trend.labels}
            data={risk_trend.values}
            title="Risk Score Trend"
            color="var(--accent)"
            height={220}
          />
        </div>

        {/* Scripts Analyzed Trend */}
        <div className="claim-card rounded-lg p-6">
          <TrendLine
            labels={scripts_trend.labels}
            data={scripts_trend.values}
            title="Scripts Analyzed"
            color="var(--verified)"
            height={220}
          />
        </div>
      </div>

      {/* Project Comparison Bar Chart */}
      <div className="claim-card rounded-lg p-6 mb-8">
        <BarChart
          data={projectBarData}
          title="Project Risk Comparison"
          height={250}
          showLegend={false}
        />
      </div>

      {/* Top Issues */}
      <div className="claim-card rounded-lg p-6 mb-8">
        <h3
          className="text-sm font-semibold mb-4"
          style={{ color: "var(--text)" }}
        >
          Top Issues Detected
        </h3>
        <div className="space-y-3">
          {overview.top_issues.map((issue, i) => (
            <div
              key={i}
              className="flex items-center justify-between p-3 rounded-lg"
              style={{ backgroundColor: "var(--bg)" }}
            >
              <div className="flex items-center gap-3">
                <div
                  className="w-2 h-2 rounded-full"
                  style={{
                    backgroundColor:
                      issue.severity === "critical"
                        ? "var(--flagged)"
                        : issue.severity === "high"
                        ? "#f97316"
                        : issue.severity === "medium"
                        ? "var(--warning, #f59e0b)"
                        : "var(--verified)",
                  }}
                />
                <span className="text-sm" style={{ color: "var(--text)" }}>
                  {issue.category}
                </span>
              </div>
              <div className="flex items-center gap-4">
                <span className="text-sm font-medium" style={{ color: "var(--text)" }}>
                  {issue.count} issues
                </span>
                <span
                  className="text-xs px-2 py-1 rounded-full capitalize"
                  style={{
                    backgroundColor: `color-mix(in srgb, ${
                      issue.severity === "critical"
                        ? "var(--flagged)"
                        : issue.severity === "high"
                        ? "#f97316"
                        : issue.severity === "medium"
                        ? "var(--warning, #f59e0b)"
                        : "var(--verified)"
                    } 15%, transparent)`,
                    color:
                      issue.severity === "critical"
                        ? "var(--flagged)"
                        : issue.severity === "high"
                        ? "#f97316"
                        : issue.severity === "medium"
                        ? "var(--warning, #f59e0b)"
                        : "var(--verified)",
                  }}
                >
                  {issue.severity}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Insights */}
      <div className="claim-card rounded-lg p-6 mb-8">
        <div className="flex items-center gap-2 mb-4">
          <Zap size={18} style={{ color: "var(--accent)" }} />
          <h3 className="text-sm font-semibold" style={{ color: "var(--text)" }}>
            AI-Generated Insights
          </h3>
        </div>
        <div className="space-y-3">
          {insights.map((insight, i) => (
            <div
              key={i}
              className="flex items-start gap-3 p-3 rounded-lg"
              style={{ backgroundColor: "var(--bg)" }}
            >
              <CheckCircle
                size={16}
                className="mt-0.5 flex-shrink-0"
                style={{ color: "var(--verified)" }}
              />
              <span className="text-sm" style={{ color: "var(--text-muted)" }}>
                {insight}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Comparative Summary */}
      <div className="claim-card rounded-lg p-6">
        <h3
          className="text-sm font-semibold mb-4"
          style={{ color: "var(--text)" }}
        >
          Period Comparison ({comparative.period})
        </h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div className="p-4 rounded-lg" style={{ backgroundColor: "var(--bg)" }}>
            <p className="text-xs mb-1" style={{ color: "var(--text-muted)" }}>
              Scripts Analyzed
            </p>
            <div className="flex items-baseline gap-2">
              <span className="text-xl font-bold" style={{ color: "var(--text)" }}>
                {comparative.current_scripts}
              </span>
              <span className="text-sm" style={{ color: "var(--text-muted)" }}>
                vs {comparative.previous_scripts}
              </span>
            </div>
          </div>
          <div className="p-4 rounded-lg" style={{ backgroundColor: "var(--bg)" }}>
            <p className="text-xs mb-1" style={{ color: "var(--text-muted)" }}>
              Average Risk Score
            </p>
            <div className="flex items-baseline gap-2">
              <span className="text-xl font-bold" style={{ color: "var(--text)" }}>
                {comparative.current_avg_risk.toFixed(1)}%
              </span>
              <span className="text-sm" style={{ color: "var(--text-muted)" }}>
                vs {comparative.previous_avg_risk.toFixed(1)}%
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
