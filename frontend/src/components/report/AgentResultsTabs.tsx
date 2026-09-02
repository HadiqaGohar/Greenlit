"use client";

import { useState } from "react";
import type { AgentResult, AgentType, Claim } from "@/lib/types";
import { OverviewPanel } from "./OverviewPanel";
import { ResearchPanel } from "./ResearchPanel";
import { LegalPanel } from "./LegalPanel";
import { ContinuityPanel } from "./ContinuityPanel";
import { StoryboardPanel } from "./StoryboardPanel";
import { TableReadPanel } from "./TableReadPanel";
import { SchedulePanel } from "./SchedulePanel";
import { StakeholderPanel } from "./StakeholderPanel";
import { RiskDashboard } from "./RiskDashboard";
import { BudgetTrackerPanel } from "./BudgetTrackerPanel";
import { CharacterRelationshipPanel } from "./CharacterRelationshipPanel";
import { ScriptComparePanel } from "./ScriptComparePanel";
import { PitchDeckPanel } from "./PitchDeckPanel";
import { LocationMatchPanel } from "./LocationMatchPanel";

type Tab = "overview" | "research" | "legal" | "continuity" | "storyboard" | "table-read" | "schedule" | "stakeholders" | "risk-dashboard" | "budget" | "relationships" | "script-compare" | "pitch-deck" | "locations";

interface AgentResultsTabsProps {
  agentResults: Record<AgentType, AgentResult>;
  riskScore: number;
  riskLevel: string;
  riskFactors: string[];
  recommendedActions: string[];
  processingTime: number;
  claimsCount: number;
  claims: Claim[];
  reportId?: string;
}

const tabs: { key: Tab; label: string; icon: string }[] = [
  { key: "overview", label: "Overview", icon: "📊" },
  { key: "research", label: "Research", icon: "🔍" },
  { key: "legal", label: "Legal", icon: "⚖️" },
  { key: "continuity", label: "Continuity", icon: "🔗" },
  { key: "storyboard", label: "Storyboard", icon: "🎬" },
  { key: "table-read", label: "Table Read", icon: "🎙️" },
  { key: "schedule", label: "Schedule", icon: "📅" },
  { key: "stakeholders", label: "Stakeholders", icon: "🏢" },
  { key: "risk-dashboard", label: "📊 Risk Dashboard", icon: "📊" },
  { key: "budget", label: "💰 Budget", icon: "💰" },
  { key: "relationships", label: "🕸️ Relationships", icon: "🕸️" },
  { key: "script-compare", label: "🔍 Compare", icon: "🔍" },
  { key: "pitch-deck", label: "📊 Pitch Deck", icon: "📊" },
  { key: "locations", label: "📍 Locations", icon: "📍" },
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
  reportId,
}: AgentResultsTabsProps) {
  const [activeTab, setActiveTab] = useState<Tab>("overview");

  return (
    <div className="rounded-xl border border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-900">
      {/* Tab headers */}
      <div className="flex border-b border-gray-200 dark:border-gray-700 overflow-x-auto">
        {tabs.map((tab) => {
          const isActive = activeTab === tab.key;
          return (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`flex items-center gap-2 px-4 py-3 text-sm font-medium transition-colors whitespace-nowrap ${
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
        {activeTab === "storyboard" && reportId && (
          <StoryboardPanel reportId={reportId} />
        )}
        {activeTab === "storyboard" && !reportId && (
          <div className="py-8 text-center text-gray-500 dark:text-gray-400">
            Report ID required for storyboard generation
          </div>
        )}
        {activeTab === "table-read" && reportId && (
          <TableReadPanel reportId={reportId} />
        )}
        {activeTab === "table-read" && !reportId && (
          <div className="py-8 text-center text-gray-500 dark:text-gray-400">
            Report ID required for table read generation
          </div>
        )}
        {activeTab === "schedule" && reportId && (
          <SchedulePanel reportId={reportId} />
        )}
        {activeTab === "schedule" && !reportId && (
          <div className="py-8 text-center text-gray-500 dark:text-gray-400">
            Report ID required for schedule generation
          </div>
        )}
        {activeTab === "stakeholders" && reportId && (
          <StakeholderPanel reportId={reportId} />
        )}
        {activeTab === "stakeholders" && !reportId && (
          <div className="py-8 text-center text-gray-500 dark:text-gray-400">
            Report ID required for stakeholder analysis
          </div>
        )}
        {activeTab === "risk-dashboard" && reportId && (
          <RiskDashboard reportId={reportId} />
        )}
        {activeTab === "risk-dashboard" && !reportId && (
          <div className="py-8 text-center text-gray-500 dark:text-gray-400">
            Report ID required for risk dashboard
          </div>
        )}
        {activeTab === "budget" && reportId && (
          <BudgetTrackerPanel reportId={reportId} />
        )}
        {activeTab === "budget" && !reportId && (
          <div className="py-8 text-center text-gray-500 dark:text-gray-400">
            Report ID required for budget tracking
          </div>
        )}
        {activeTab === "relationships" && reportId && (
          <CharacterRelationshipPanel reportId={reportId} />
        )}
        {activeTab === "relationships" && !reportId && (
          <div className="py-8 text-center text-gray-500 dark:text-gray-400">
            Report ID required for relationship graph
          </div>
        )}
        {activeTab === "script-compare" && (
          <ScriptComparePanel reportId={reportId} />
        )}
        {activeTab === "pitch-deck" && reportId && (
          <PitchDeckPanel reportId={reportId} />
        )}
        {activeTab === "pitch-deck" && !reportId && (
          <div className="py-8 text-center text-gray-500 dark:text-gray-400">
            Report ID required for pitch deck
          </div>
        )}
        {activeTab === "locations" && reportId && (
          <LocationMatchPanel reportId={reportId} />
        )}
        {activeTab === "locations" && !reportId && (
          <div className="py-8 text-center text-gray-500 dark:text-gray-400">
            Report ID required for location matching
          </div>
        )}
      </div>
    </div>
  );
}
