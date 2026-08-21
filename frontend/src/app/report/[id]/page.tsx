"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { ClaimHighlight } from "@/components/ClaimHighlight";
import { ReportSidebar } from "@/components/ReportSidebar";
import { LoadingReel } from "@/components/LoadingReel";
import { getReport, ApiError } from "@/lib/api";
import type { AnalyzeResponse, Verdict } from "@/lib/types";

type FilterVerdict = Verdict | "all";

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

  useEffect(() => {
    getReport(params.id)
      .then((reportData) => {
        setReport(reportData);
        // For now, we'll generate mock script text since the backend doesn't return it yet
        // In a real implementation, the backend would return the original script text
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
        </p>

        {report.claims.length > 0 && (
          <div className="mt-4 flex gap-4 text-xs">
            <span className="text-verified">{verified} verified</span>
            <span className="text-flagged">{flagged} flagged</span>
            <span className="text-amber">{uncertain} uncertain</span>
          </div>
        )}
      </div>

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
    </div>
  );
}

// Temporary function to generate mock script text that contains the claims
// This will be replaced when the backend returns the original script text
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
