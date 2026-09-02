"use client";

import { useState } from "react";
import { DollarSign, ChevronDown, ChevronUp, Lightbulb } from "lucide-react";

interface LineItem {
  item: string;
  cost: string;
}

interface BudgetCategory {
  name: string;
  estimated_cost: string;
  confidence: number;
  line_items: LineItem[];
  notes: string;
}

interface BudgetData {
  categories: BudgetCategory[];
  total_estimated_budget: string;
  budget_level: string;
  cost_saving_tips: string[];
}

interface BudgetEstimatorProps {
  scriptText: string;
}

const budgetLevelColors: Record<string, string> = {
  micro: "#10b981",
  low: "#3b82f6",
  medium: "#f59e0b",
  high: "#ef4444",
  blockbuster: "#dc2626",
  unknown: "#6b7280",
};

const budgetLevelLabels: Record<string, string> = {
  micro: "Micro Budget (<$500K)",
  low: "Low Budget ($500K-2M)",
  medium: "Medium Budget ($2M-10M)",
  high: "High Budget ($10M-50M)",
  blockbuster: "Blockbuster ($50M+)",
  unknown: "Unable to Determine",
};

export function BudgetEstimator({ scriptText }: BudgetEstimatorProps) {
  const [budget, setBudget] = useState<BudgetData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expandedCategory, setExpandedCategory] = useState<string | null>(null);

  const estimateBudget = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}/api/budget-estimate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ script_text: scriptText }),
      });

      if (!response.ok) {
        throw new Error("Budget estimation failed");
      }

      const data = await response.json();
      setBudget(data.budget);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to estimate budget");
    } finally {
      setLoading(false);
    }
  };

  const toggleCategory = (name: string) => {
    setExpandedCategory(expandedCategory === name ? null : name);
  };

  return (
    <div className="claim-card rounded-xl p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <DollarSign size={20} style={{ color: "var(--verified)" }} />
          <h3 className="font-display text-lg font-semibold" style={{ color: "var(--text)" }}>
            Production Budget Estimator
          </h3>
        </div>
        {!budget && !loading && (
          <button
            onClick={estimateBudget}
            className="px-4 py-2 rounded-lg text-sm font-medium transition-all hover:scale-105"
            style={{
              background: "linear-gradient(135deg, var(--verified) 0%, #059669 100%)",
              color: "white",
            }}
          >
            Estimate Budget
          </button>
        )}
      </div>

      {loading && (
        <div className="flex items-center justify-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2" style={{ borderColor: "var(--accent)" }} />
          <span className="ml-3" style={{ color: "var(--text-muted)" }}>Analyzing script for budget...</span>
        </div>
      )}

      {error && (
        <div className="text-center py-8">
          <p className="text-flagged mb-4">{error}</p>
          <button
            onClick={estimateBudget}
            className="px-4 py-2 rounded-lg text-sm font-medium"
            style={{ backgroundColor: "var(--bg)", color: "var(--text)", border: "1px solid var(--border)" }}
          >
            Try Again
          </button>
        </div>
      )}

      {budget && (
        <div>
          {/* Total Budget */}
          <div className="mb-6 p-4 rounded-lg" style={{ backgroundColor: "color-mix(in srgb, var(--verified) 10%, transparent)" }}>
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium" style={{ color: "var(--text-muted)" }}>Estimated Total Budget</span>
              <span className="text-2xl font-bold" style={{ color: "var(--text)" }}>{budget.total_estimated_budget}</span>
            </div>
            <div className="mt-2 flex items-center gap-2">
              <span
                className="px-2 py-1 rounded text-xs font-medium"
                style={{
                  backgroundColor: `color-mix(in srgb, ${budgetLevelColors[budget.budget_level] || budgetLevelColors.unknown} 20%, transparent)`,
                  color: budgetLevelColors[budget.budget_level] || budgetLevelColors.unknown,
                }}
              >
                {budgetLevelLabels[budget.budget_level] || budget.budget_level}
              </span>
            </div>
          </div>

          {/* Categories */}
          <div className="space-y-2 mb-6">
            {budget.categories.map((cat) => (
              <div key={cat.name} className="rounded-lg border" style={{ borderColor: "var(--border)" }}>
                <button
                  onClick={() => toggleCategory(cat.name)}
                  className="w-full flex items-center justify-between p-3 text-left"
                  style={{ backgroundColor: "var(--bg)" }}
                >
                  <div className="flex items-center gap-3">
                    <span className="font-medium" style={{ color: "var(--text)" }}>{cat.name}</span>
                    <span className="text-sm" style={{ color: "var(--text-muted)" }}>{cat.estimated_cost}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs px-2 py-1 rounded" style={{ backgroundColor: "var(--surface)", color: "var(--text-muted)" }}>
                      {Math.round(cat.confidence * 100)}% confidence
                    </span>
                    {expandedCategory === cat.name ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                  </div>
                </button>
                {expandedCategory === cat.name && (
                  <div className="p-3 border-t" style={{ borderColor: "var(--border)" }}>
                    <div className="space-y-2">
                      {cat.line_items.map((item, i) => (
                        <div key={i} className="flex justify-between text-sm">
                          <span style={{ color: "var(--text-muted)" }}>{item.item}</span>
                          <span style={{ color: "var(--text)" }}>{item.cost}</span>
                        </div>
                      ))}
                    </div>
                    {cat.notes && (
                      <p className="mt-3 text-xs italic" style={{ color: "var(--text-muted)" }}>{cat.notes}</p>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>

          {/* Cost Saving Tips */}
          {budget.cost_saving_tips && budget.cost_saving_tips.length > 0 && (
            <div className="p-4 rounded-lg" style={{ backgroundColor: "color-mix(in srgb, #f59e0b 10%, transparent)" }}>
              <div className="flex items-center gap-2 mb-2">
                <Lightbulb size={16} style={{ color: "#f59e0b" }} />
                <span className="font-medium text-sm" style={{ color: "var(--text)" }}>Cost Saving Tips</span>
              </div>
              <ul className="space-y-1">
                {budget.cost_saving_tips.map((tip, i) => (
                  <li key={i} className="text-sm" style={{ color: "var(--text-muted)" }}>• {tip}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
