"use client";

import { ClaimCard } from "@/components/ClaimCard";
import type { Claim, Verdict } from "@/lib/types";

type FilterVerdict = Verdict | "all";

const FILTER_OPTIONS: { value: FilterVerdict; label: string }[] = [
  { value: "all", label: "All" },
  { value: "verified", label: "Verified" },
  { value: "flagged", label: "Flagged" },
  { value: "uncertain", label: "Uncertain" },
];

interface ReportSidebarProps {
  claims: Claim[];
  selectedClaimId: string | null;
  filter: FilterVerdict;
  onFilterChange: (filter: FilterVerdict) => void;
  onSelectClaim: (claimId: string) => void;
}

export function ReportSidebar({
  claims,
  selectedClaimId,
  filter,
  onFilterChange,
  onSelectClaim,
}: ReportSidebarProps) {
  const filtered =
    filter === "all" ? claims : claims.filter((c) => c.verdict === filter);

  return (
    <aside className="flex flex-col gap-4" aria-label="Claim notes">
      <div className="flex flex-wrap gap-2">
        {FILTER_OPTIONS.map((option) => (
          <button
            key={option.value}
            type="button"
            onClick={() => onFilterChange(option.value)}
            className={`rounded-full border px-3 py-1 text-xs font-medium transition-colors ${
              filter === option.value
                ? "border-amber bg-amber/15 text-amber"
                : "border-charcoal-light text-parchment/50 hover:border-parchment/30 hover:text-parchment/70"
            }`}
          >
            {option.label}
          </button>
        ))}
      </div>

      {filtered.length === 0 ? (
        <p className="text-sm text-parchment/50">No claims match this filter.</p>
      ) : (
        <div className="space-y-3">
          {filtered.map((claim) => {
            const index = claims.indexOf(claim);
            const isActive = claim.id === selectedClaimId;
            return (
              <div
                key={claim.id}
                id={`claim-${claim.id}`}
                className={`transition-opacity ${isActive ? "opacity-100" : "opacity-90"}`}
              >
                <ClaimCard
                  claim={claim}
                  index={index}
                  isActive={isActive}
                  isExpanded={isActive}
                  onSelect={() => onSelectClaim(claim.id)}
                />
              </div>
            );
          })}
        </div>
      )}
    </aside>
  );
}
