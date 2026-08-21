"use client";

import { useEffect, useRef } from "react";

import { buildHighlightSegments } from "@/lib/highlights";
import type { Claim, Verdict } from "@/lib/types";

const HIGHLIGHT_STYLES: Record<Verdict, string> = {
  verified: "claim-highlight claim-highlight-verified",
  flagged: "claim-highlight claim-highlight-flagged",
  uncertain: "claim-highlight claim-highlight-uncertain",
};

interface ClaimHighlightProps {
  scriptText: string;
  claims: Claim[];
  selectedClaimId: string | null;
  onSelectClaim: (claimId: string) => void;
}

export function ClaimHighlight({
  scriptText,
  claims,
  selectedClaimId,
  onSelectClaim,
}: ClaimHighlightProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const segments = buildHighlightSegments(scriptText, claims);

  useEffect(() => {
    if (!selectedClaimId || !containerRef.current) return;
    const mark = containerRef.current.querySelector(
      `[data-claim-id="${selectedClaimId}"]`,
    );
    mark?.scrollIntoView({ behavior: "smooth", block: "center" });
  }, [selectedClaimId]);

  return (
    <div
      ref={containerRef}
      className="script-panel script-text overflow-auto rounded-lg border border-charcoal-light bg-charcoal-light/20 p-6 text-sm leading-relaxed text-parchment/90"
      aria-label="Annotated script"
    >
      <pre className="whitespace-pre-wrap font-script">
        {segments.map((segment, index) => {
          if (!segment.claimId || !segment.verdict) {
            return <span key={index}>{segment.text}</span>;
          }

          const isActive = segment.claimId === selectedClaimId;
          return (
            <mark
              key={index}
              data-claim-id={segment.claimId}
              className={`${HIGHLIGHT_STYLES[segment.verdict]}${isActive ? " claim-highlight-active" : ""}`}
              onClick={() => onSelectClaim(segment.claimId!)}
              role="button"
              tabIndex={0}
              onKeyDown={(event) => {
                if (event.key === "Enter" || event.key === " ") {
                  event.preventDefault();
                  onSelectClaim(segment.claimId!);
                }
              }}
            >
              {segment.text}
            </mark>
          );
        })}
      </pre>
    </div>
  );
}
