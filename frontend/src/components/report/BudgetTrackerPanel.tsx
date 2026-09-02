"use client";

import { useState } from "react";
import { DollarSign, AlertTriangle, Lightbulb, TrendingUp, TrendingDown } from "lucide-react";
import { BarChart, BarChartData } from "../charts/BarChart";
import { trackBudget, type BudgetTrackingResponse, type BudgetTrackingCategory } from "@/lib/api";

interface BudgetTrackerPanelProps {
  reportId: string;
}

const STATUS_STYLES: Record<string, { chip: string; text: string }> = {
  over: { chip: "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300", text: "text-red-600 dark:text-red-400" },
  under: { chip: "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300", text: "text-green-600 dark:text-green-400" },
  on_track: { chip: "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300", text: "text-blue-600 dark:text-blue-400" },
};

function fmt(n: number): string {
  return `$${Math.round(n).toLocaleString()}`;
}

function fmtSigned(n: number): string {
  return `${n >= 0 ? "+" : "-"}${fmt(Math.abs(n))}`;
}

export function BudgetTrackerPanel({ reportId }: BudgetTrackerPanelProps) {
  const [data, setData] = useState<BudgetTrackingResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const runTracking = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await trackBudget(reportId);
      if (!res.success) throw new Error(res.error || "Budget tracking failed");
      setData(res);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to track budget");
    } finally {
      setLoading(false);
    }
  };

  const chartData: BarChartData | null = data
    ? {
        labels: data.categories.map((c) => c.name),
        datasets: [
          {
            label: "Planned",
            data: data.categories.map((c) => Math.round(c.planned_mid)),
            color: "var(--accent)",
          },
          {
            label: "Actual",
            data: data.categories.map((c) => Math.round(c.actual)),
            color: "var(--verified)",
          },
        ],
      }
    : null;

  return (
    <div className="claim-card rounded-xl p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <DollarSign size={20} style={{ color: "var(--verified)" }} />
          <h3 className="font-display text-lg font-semibold" style={{ color: "var(--text)" }}>
            Budget vs. Actual Tracker
          </h3>
        </div>
        {!data && !loading && (
          <button
            onClick={runTracking}
            className="px-4 py-2 rounded-lg text-sm font-medium transition-all hover:scale-105"
            style={{
              background: "linear-gradient(135deg, var(--verified) 0%, #059669 100%)",
              color: "white",
            }}
          >
            Track Budget
          </button>
        )}
        {data && (
          <button
            onClick={runTracking}
            className="px-3 py-1.5 rounded-lg text-sm font-medium"
            style={{ backgroundColor: "var(--bg)", color: "var(--text)", border: "1px solid var(--border)" }}
          >
            🔄 Re-track
          </button>
        )}
      </div>

      {loading && (
        <div className="flex items-center justify-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2" style={{ borderColor: "var(--accent)" }} />
          <span className="ml-3" style={{ color: "var(--text-muted)" }}>Building budget tracking report...</span>
        </div>
      )}

      {error && (
        <div className="text-center py-8">
          <p className="text-flagged mb-4">{error}</p>
          <button
            onClick={runTracking}
            className="px-4 py-2 rounded-lg text-sm font-medium"
            style={{ backgroundColor: "var(--bg)", color: "var(--text)", border: "1px solid var(--border)" }}
          >
            Try Again
          </button>
        </div>
      )}

      {data && !loading && (
        <div className="space-y-6">
          {/* Overall summary card */}
          <div
            className="p-4 rounded-lg"
            style={{ backgroundColor: "color-mix(in srgb, var(--verified) 10%, transparent)" }}
          >
            <div className="grid grid-cols-3 gap-4 text-center">
              <div>
                <p className="text-xs font-medium" style={{ color: "var(--text-muted)" }}>Planned</p>
                <p className="text-xl font-bold" style={{ color: "var(--text)" }}>{fmt(data.total_planned)}</p>
              </div>
              <div>
                <p className="text-xs font-medium" style={{ color: "var(--text-muted)" }}>Actual</p>
                <p className="text-xl font-bold" style={{ color: "var(--text)" }}>{fmt(data.total_actual)}</p>
              </div>
              <div>
                <p className="text-xs font-medium" style={{ color: "var(--text-muted)" }}>Variance</p>
                <p
                  className={`text-xl font-bold flex items-center justify-center gap-1 ${STATUS_STYLES[data.overall_status].text}`}
                >
                  {data.total_variance >= 0 ? <TrendingUp size={18} /> : <TrendingDown size={18} />}
                  {fmtSigned(data.total_variance)}
                </p>
              </div>
            </div>
            <div className="mt-3 flex items-center justify-center gap-2">
              <span
                className={`px-2 py-1 rounded text-xs font-medium ${STATUS_STYLES[data.overall_status].chip}`}
              >
                {data.overall_status === "over" ? "Over Budget" : data.overall_status === "under" ? "Under Budget" : "On Track"} (
                {data.total_variance_pct >= 0 ? "+" : ""}
                {data.total_variance_pct.toFixed(1)}%)
              </span>
              <span className="text-xs" style={{ color: "var(--text-muted)" }}>
                Estimated total: {data.total_estimated_budget}
              </span>
            </div>
          </div>

          {/* Planned vs Actual chart */}
          {chartData && (
            <div>
              <h4 className="text-sm font-semibold mb-3" style={{ color: "var(--text)" }}>
                Planned vs. Actual by Category
              </h4>
              <BarChart data={chartData} height={260} />
            </div>
          )}

          {/* Alerts */}
          {data.alerts.length > 0 && (
            <div className="p-4 rounded-lg border border-red-200 bg-red-50 dark:border-red-800 dark:bg-red-900/20">
              <div className="flex items-center gap-2 mb-2">
                <AlertTriangle size={16} className="text-red-500" />
                <span className="font-medium text-sm text-red-800 dark:text-red-200">Budget Alerts</span>
              </div>
              <ul className="space-y-1">
                {data.alerts.map((a, i) => (
                  <li key={i} className="text-sm text-red-700 dark:text-red-300">• {a}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Category breakdown table */}
          <div>
            <h4 className="text-sm font-semibold mb-3" style={{ color: "var(--text)" }}>
              Category Breakdown
            </h4>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr style={{ color: "var(--text-muted)" }} className="text-left border-b">
                    <th className="py-2 pr-2 font-medium">Category</th>
                    <th className="py-2 pr-2 font-medium">Planned</th>
                    <th className="py-2 pr-2 font-medium">Actual</th>
                    <th className="py-2 pr-2 font-medium">Variance</th>
                    <th className="py-2 font-medium">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {data.categories.map((c: BudgetTrackingCategory) => (
                    <tr key={c.name} className="border-b" style={{ borderColor: "var(--border)" }}>
                      <td className="py-2 pr-2 font-medium" style={{ color: "var(--text)" }}>{c.name}</td>
                      <td className="py-2 pr-2" style={{ color: "var(--text-muted)" }}>{c.planned_range}</td>
                      <td className="py-2 pr-2" style={{ color: "var(--text)" }}>{fmt(c.actual)}</td>
                      <td className={`py-2 pr-2 ${STATUS_STYLES[c.status].text}`}>
                        {fmtSigned(c.variance)} ({c.variance_pct >= 0 ? "+" : ""}
                        {c.variance_pct.toFixed(0)}%)
                      </td>
                      <td className="py-2">
                        <span className={`px-2 py-0.5 rounded text-xs font-medium ${STATUS_STYLES[c.status].chip}`}>
                          {c.status === "over" ? "Over" : c.status === "under" ? "Under" : "On Track"}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p className="mt-2 text-xs italic" style={{ color: "var(--text-muted)" }}>
              Actuals are simulated from the estimate for demo purposes. Provide real actuals via the API to track live spend.
            </p>
          </div>

          {/* Recommendations */}
          {data.recommendations.length > 0 && (
            <div className="p-4 rounded-lg" style={{ backgroundColor: "color-mix(in srgb, #f59e0b 10%, transparent)" }}>
              <div className="flex items-center gap-2 mb-2">
                <Lightbulb size={16} style={{ color: "#f59e0b" }} />
                <span className="font-medium text-sm" style={{ color: "var(--text)" }}>Recommendations</span>
              </div>
              <ul className="space-y-1">
                {data.recommendations.map((r, i) => (
                  <li key={i} className="text-sm" style={{ color: "var(--text-muted)" }}>• {r}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
