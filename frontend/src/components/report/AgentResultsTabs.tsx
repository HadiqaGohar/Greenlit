"use client";

import { useState } from "react";
import type { AgentResult, AgentType, Claim } from "@/lib/types";
import { OverviewPanel } from "./OverviewPanel";
import { ResearchPanel } from "./ResearchPanel";
import { LegalPanel } from "./LegalPanel";
import { ContinuityPanel } from "./ContinuityPanel";

type Tab = "overview" | "research" | "legal" | "continuity";

interface AgentResultsTabsProps {
  agentResults: Record<AgentType, AgentResult>;
  riskScore: number;
  riskLevel: string;
  riskFactors: string[];
  recommendedActions: string[];
  processingTime: number;
  claimsCount: number;
  claims: Claim[];
}

const tabs: { key: Tab; label: string; icon: string }[] = [
  { key: "overview", label: "Overview", icon: "📊" },
  { key: "research", label: "Research", icon: "🔍" },
  { key: "legal", label: "Legal", icon: "⚖️" },
  { key: "continuity", label: "Continuity", icon: "🔗" },
];

export function AgentResultsTabs({
  agentResults,
  riskScore,
  riskLevel,
  riskFactors,
  recommendedActions,
  processingTime,
  claimsCount,
  claims,
}: AgentResultsTabsProps) {
  const [activeTab, setActiveTab] = useState<Tab>("overview");

  return (
    <div className="rounded-xl border border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-900">
      {/* Tab headers */}
      <div className="flex border-b border-gray-200 dark:border-gray-700">
        {tabs.map((tab) => {
          const isActive = activeTab === tab.key;
          return (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`flex items-center gap-2 px-4 py-3 text-sm font-medium transition-colors ${
                isActive
                  ? "border-b-2 border-blue-600 text-blue-600 dark:text-blue-400"
                  : "text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300"
              }`}
            >
              <span>{tab.icon}</span>
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      {/* Tab content */}
      <div className="p-5">
        {activeTab === "overview" && (
          <OverviewPanel
            riskScore={riskScore}
            riskLevel={riskLevel}
            riskFactors={riskFactors}
            recommendedActions={recommendedActions}
            agentResults={agentResults}
            processingTime={processingTime}
            claimsCount={claimsCount}
          />
        )}
        {activeTab === "research" && (
          <ResearchPanel agentResult={agentResults.research ?? null} claims={claims} />
        )}
        {activeTab === "legal" && (
          <LegalPanel agentResult={agentResults.legal ?? null} />
        )}
        {activeTab === "continuity" && (
          <ContinuityPanel agentResult={agentResults.continuity ?? null} />
        )}
      </div>
    </div>
  );
}
