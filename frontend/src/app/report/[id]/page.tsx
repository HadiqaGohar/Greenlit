"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { ClaimHighlight } from "@/components/ClaimHighlight";
import { ReportSidebar } from "@/components/ReportSidebar";
import { LoadingReel } from "@/components/LoadingReel";
import { RiskGauge } from "@/components/report/RiskGauge";
import { AgentResultsTabs } from "@/components/report/AgentResultsTabs";
import { ExportModal } from "@/components/report/ExportModal";
import { AgentReplay } from "@/components/report/AgentReplay";
import { ReadinessRadar } from "@/components/report/ReadinessRadar";
import { SuggestionCard } from "@/components/report/SuggestionCard";
import { AgentFlowDiagram } from "@/components/report/AgentFlowDiagram";
import { SceneBreakdownDashboard } from "@/components/report/SceneBreakdownDashboard";
import { CharacterBible } from "@/components/report/CharacterBible";
import { LegalClearanceChecklist } from "@/components/report/LegalClearanceChecklist";
import { getReport, ApiError } from "@/lib/api";
import type { AnalyzeResponse, Verdict, AgentType } from "@/lib/types";

type FilterVerdict = Verdict | "all";
type ExtraTab = "replay" | "readiness" | "suggestions" | "flow" | "scenes" | "characters" | "legal-checklist";

interface ReportPageProps {
  params: { id: string };
}

export default function ReportPage({ params }: ReportPageProps) {
  const [report, setReport] = useState<AnalyzeResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedClaimId, setSelectedClaimId] = useState<string | null>(null);
  const [filter, setFilter] = useState<FilterVerdict>("all");
  const [scriptText, setScriptText] = useState<string>("");
  const [showExportModal, setShowExportModal] = useState(false);
  const [activeExtra, setActiveExtra] = useState<ExtraTab | null>(null);

  useEffect(() => {
    getReport(params.id)
      .then((reportData) => {
        setReport(reportData);
        setScriptText(generateMockScript());
      })
      .catch((err) => {
        const message =
          err instanceof ApiError ? err.message : "Failed to load report.";
        setError(message);
      })
      .finally(() => setIsLoading(false));
  }, [params.id]);

  if (isLoading) {
    return (
      <div className="mx-auto max-w-6xl px-6 py-12">
        <LoadingReel message="Loading report..." />
      </div>
    );
  }

  if (error || !report) {
    return (
      <div className="mx-auto max-w-6xl px-6 py-12 text-center">
        <p className="text-flagged">{error ?? "Report not found."}</p>
        <Link
          href="/"
          className="mt-4 inline-block text-sm text-amber hover:text-amber-light"
        >
          ← Back to script input
        </Link>
      </div>
    );
  }

  const verified = report.claims.filter((c) => c.verdict === "verified").length;
  const flagged = report.claims.filter((c) => c.verdict === "flagged").length;
  const uncertain = report.claims.filter((c) => c.verdict === "uncertain").length;

  const riskAssessment = report.risk_assessment;
  const agentResults = report.agent_results;
  const hasMultiAgentData = riskAssessment && agentResults;
  const hasTimeline = report.agent_timeline && report.agent_timeline.length > 0;
  const hasReadiness = report.readiness_scores && report.readiness_scores.overall > 0;
  const hasSuggestions = report.suggestions && report.suggestions.length > 0;
  const hasFlow = report.agent_flow && report.agent_flow.length > 0;
  const hasScenes = (report as any).scenes && (report as any).scenes.length > 0;
  const hasCharacters = (report as any).characters && (report as any).characters.length > 0;
  const hasLegalIssues = report.claims.some((c) => c.type === "licensing");

  return (
    <div className="mx-auto max-w-7xl px-6 py-8">
      {/* Header */}
      <div className="mb-8">
        <Link
          href="/"
          className="text-sm text-amber hover:text-amber-light transition-colors"
        >
          ← Analyze another script
        </Link>
        <h1 className="mt-4 font-display text-3xl font-semibold text-parchment">
          Production Notes
        </h1>
        <p className="mt-2 text-sm text-parchment/50">
          Report {report.report_id.slice(0, 8)}… · {report.claims.length} claim
          {report.claims.length !== 1 ? "s" : ""} found
          {report.processing_time && (
            <> · Processed in {report.processing_time.toFixed(1)}s</>
          )}
        </p>

        {report.claims.length > 0 && (
          <div className="mt-4 flex gap-4 text-xs">
            <span className="text-verified">{verified} verified</span>
            <span className="text-flagged">{flagged} flagged</span>
            <span className="text-amber">{uncertain} uncertain</span>
          </div>
        )}

        {/* Export & Share buttons */}
        <div className="mt-4 flex gap-3">
          <button
            onClick={() => setShowExportModal(true)}
            className="inline-flex items-center gap-2 rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 shadow-sm hover:bg-gray-50 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700"
          >
            <span>📥</span> Export Report
          </button>
        </div>
      </div>

      {/* New feature tabs */}
      {(hasTimeline || hasReadiness || hasSuggestions || hasFlow) && (
        <div className="mb-6">
          <div className="flex flex-wrap gap-2">
            {hasReadiness && (
              <button
                onClick={() => setActiveExtra(activeExtra === "readiness" ? null : "readiness")}
                className={`rounded-lg px-4 py-2 text-sm font-medium transition-colors ${
                  activeExtra === "readiness"
                    ? "bg-blue-600 text-white"
                    : "border border-gray-300 text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-800"
                }`}
              >
                📊 Readiness Score
              </button>
            )}
            {hasTimeline && (
              <button
                onClick={() => setActiveExtra(activeExtra === "replay" ? null : "replay")}
                className={`rounded-lg px-4 py-2 text-sm font-medium transition-colors ${
                  activeExtra === "replay"
                    ? "bg-blue-600 text-white"
                    : "border border-gray-300 text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-800"
                }`}
              >
                ▶ Agent Replay
              </button>
            )}
            {hasFlow && (
              <button
                onClick={() => setActiveExtra(activeExtra === "flow" ? null : "flow")}
                className={`rounded-lg px-4 py-2 text-sm font-medium transition-colors ${
                  activeExtra === "flow"
                    ? "bg-blue-600 text-white"
                    : "border border-gray-300 text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-800"
                }`}
              >
                🔗 Agent Pipeline
              </button>
            )}
            {hasSuggestions && (
              <button
                onClick={() => setActiveExtra(activeExtra === "suggestions" ? null : "suggestions")}
                className={`rounded-lg px-4 py-2 text-sm font-medium transition-colors ${
                  activeExtra === "suggestions"
                    ? "bg-blue-600 text-white"
                    : "border border-gray-300 text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-800"
                }`}
              >
                💡 Suggestions ({report.suggestions!.length})
              </button>
            )}
            {hasScenes && (
              <button
                onClick={() => setActiveExtra(activeExtra === "scenes" ? null : "scenes")}
                className={`rounded-lg px-4 py-2 text-sm font-medium transition-colors ${
                  activeExtra === "scenes"
                    ? "bg-blue-600 text-white"
                    : "border border-gray-300 text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-800"
                }`}
              >
                🎬 Scenes
              </button>
            )}
            {hasCharacters && (
              <button
                onClick={() => setActiveExtra(activeExtra === "characters" ? null : "characters")}
                className={`rounded-lg px-4 py-2 text-sm font-medium transition-colors ${
                  activeExtra === "characters"
                    ? "bg-blue-600 text-white"
                    : "border border-gray-300 text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-800"
                }`}
              >
                👥 Characters
              </button>
            )}
            {hasLegalIssues && (
              <button
                onClick={() => setActiveExtra(activeExtra === "legal-checklist" ? null : "legal-checklist")}
                className={`rounded-lg px-4 py-2 text-sm font-medium transition-colors ${
                  activeExtra === "legal-checklist"
                    ? "bg-blue-600 text-white"
                    : "border border-gray-300 text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-800"
                }`}
              >
                📋 Legal Checklist
              </button>
            )}
          </div>
        </div>
      )}

      {/* Extra feature panels */}
      {activeExtra === "readiness" && hasReadiness && (
        <div className="mb-8">
          <ReadinessRadar scores={report.readiness_scores!} />
        </div>
      )}

      {activeExtra === "replay" && hasTimeline && (
        <div className="mb-8">
          <AgentReplay
            timeline={report.agent_timeline!}
            totalProcessingTime={report.processing_time ?? 0}
          />
        </div>
      )}

      {activeExtra === "flow" && hasFlow && (
        <div className="mb-8">
          <AgentFlowDiagram flow={report.agent_flow!} />
        </div>
      )}

      {activeExtra === "suggestions" && hasSuggestions && (
        <div className="mb-8">
          <SuggestionCard suggestions={report.suggestions!} />
        </div>
      )}

      {activeExtra === "scenes" && hasScenes && (
        <div className="mb-8">
          <SceneBreakdownDashboard scenes={(report as any).scenes} />
        </div>
      )}

      {activeExtra === "characters" && hasCharacters && (
        <div className="mb-8">
          <CharacterBible characters={(report as any).characters} />
        </div>
      )}

      {activeExtra === "legal-checklist" && hasLegalIssues && (
        <div className="mb-8">
          <LegalClearanceChecklist
            items={report.claims
              .filter((c) => c.type === "licensing")
              .map((c, i) => ({
                id: c.id || `legal-${i}`,
                type: "copyright" as const,
                description: c.text,
                severity: c.confidence > 0.7 ? "high" : "medium",
                status: "pending" as const,
                estimated_cost: "$500-2,000",
                action_required: c.note || "Review and obtain clearance",
              }))}
          />
        </div>
      )}

      {/* Multi-agent results section */}
      {hasMultiAgentData && (
        <div className="mb-8">
          <div className="mb-4 flex flex-col gap-6 sm:flex-row sm:items-start">
            {/* Risk Gauge */}
            <div className="flex-shrink-0">
              <RiskGauge
                score={riskAssessment.overall_risk_score}
                size="md"
                showDetails
                riskFactors={riskAssessment.risk_factors}
              />
            </div>

            {/* Agent Results Tabs */}
            <div className="flex-1 min-w-0">
              <AgentResultsTabs
                agentResults={agentResults}
                riskScore={riskAssessment.overall_risk_score}
                riskLevel={riskAssessment.risk_level}
                riskFactors={riskAssessment.risk_factors}
                recommendedActions={riskAssessment.recommended_actions}
                processingTime={report.processing_time ?? 0}
                claimsCount={report.claims.length}
                claims={report.claims}
              />
            </div>
          </div>
        </div>
      )}

      {/* Script + Claims view */}
      {report.claims.length === 0 ? (
        <p className="text-parchment/60">
          No factual claims were found in this script.
        </p>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 h-[calc(100vh-16rem)]">
          {/* Script Panel with Highlights */}
          <div className="lg:col-span-1">
            <div className="sticky top-6">
              <h2 className="mb-4 text-lg font-semibold text-parchment">
                Annotated Script
              </h2>
              <ClaimHighlight
                scriptText={scriptText}
                claims={report.claims}
                selectedClaimId={selectedClaimId}
                onSelectClaim={setSelectedClaimId}
              />
            </div>
          </div>

          {/* Sidebar with Claims */}
          <div className="lg:col-span-1">
            <div className="sticky top-6">
              <h2 className="mb-4 text-lg font-semibold text-parchment">
                Research Notes
              </h2>
              <ReportSidebar
                claims={report.claims}
                selectedClaimId={selectedClaimId}
                filter={filter}
                onFilterChange={setFilter}
                onSelectClaim={setSelectedClaimId}
              />
            </div>
          </div>
        </div>
      )}

      {/* Export Modal */}
      <ExportModal
        scriptId={report.report_id}
        userId="default-user"
        isOpen={showExportModal}
        onClose={() => setShowExportModal(false)}
      />
    </div>
  );
}

function generateMockScript(): string {
  const scriptParts = [
    "FADE IN:\n\nEXT. TIMES SQUARE - NIGHT\n\nThe bustling heart of New York City pulses with neon lights and endless crowds. Steam rises from manholes as yellow taxis weave through traffic.\n\n",
    "SARAH (25), a determined journalist, stands outside the iconic Flatiron Building, checking her watch. It reads 11:47 PM.\n\n",
    "She pulls out her iPhone and dials a number.\n\n",
    "SARAH\n(into phone)\nI'm here. The Titanic exhibition at the Natural History Museum opens tomorrow, right? We need to verify those passenger manifest details.\n\n",
    "A figure emerges from the shadows - MARCUS (30s), wearing a vintage Rolex Submariner that catches the streetlight.\n\n",
    "MARCUS\nThe White Star Line records show Captain Edward Smith was indeed the captain on that fatal voyage in 1912. But there's something else...\n\n",
    "They walk toward Central Park, passing under the glow of period-accurate gas lamps that were installed in 1880.\n\n",
    "SARAH\nWhat about the Tesla Model S parked over there? Seems anachronistic for a period piece.\n\n",
    "MARCUS\n(checking his Apple Watch)\nThat's exactly what I mean. Someone's been planting modern elements in historical settings. Like that Starbucks cup in the Game of Thrones finale.\n\n",
    "Thunder rumbles overhead as they approach the Shakespeare Garden, established in 1913 to commemorate the 300th anniversary of the playwright's death.\n\n",
    "FADE OUT."
  ];
  
  return scriptParts.join("");
}
