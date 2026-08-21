import type { Claim, Verdict } from "@/lib/types";

const VERDICT_STYLES: Record<Verdict, string> = {
  verified: "border-verified/40 bg-verified/10 text-verified",
  flagged: "border-flagged/40 bg-flagged/10 text-flagged",
  uncertain: "border-amber/40 bg-amber/10 text-amber",
};

interface ClaimCardProps {
  claim: Claim;
  index: number;
  isActive?: boolean;
  isExpanded?: boolean;
  onSelect?: () => void;
}

export function ClaimCard({
  claim,
  index,
  isActive = false,
  isExpanded = true,
  onSelect,
}: ClaimCardProps) {
  const interactive = Boolean(onSelect);

  return (
    <article
      className={`rounded-lg border p-4 transition-colors ${
        isActive
          ? "border-amber/60 bg-amber/5 ring-1 ring-amber/30"
          : "border-charcoal-light bg-charcoal-light/30 hover:border-charcoal-light/80"
      } ${interactive ? "cursor-pointer" : ""}`}
      onClick={onSelect}
      onKeyDown={
        onSelect
          ? (event) => {
              if (event.key === "Enter" || event.key === " ") {
                event.preventDefault();
                onSelect();
              }
            }
          : undefined
      }
      role={interactive ? "button" : undefined}
      tabIndex={interactive ? 0 : undefined}
    >
      <div className="mb-3 flex items-start justify-between gap-3">
        <span className="text-xs font-medium uppercase tracking-wider text-parchment/40">
          Claim {index + 1} · {claim.type}
        </span>
        <span
          className={`rounded-full border px-2.5 py-0.5 text-xs font-medium capitalize ${VERDICT_STYLES[claim.verdict]}`}
        >
          {claim.verdict}
        </span>
      </div>

      <p className="script-text mb-3 text-sm text-parchment">
        &ldquo;{claim.text}&rdquo;
      </p>

      {isExpanded && claim.note && (
        <p className="mb-3 text-sm text-parchment/70">{claim.note}</p>
      )}

      <div className="flex items-center justify-between text-xs text-parchment/50">
        <span>Confidence: {Math.round(claim.confidence * 100)}%</span>
        {claim.sources.length > 0 && (
          <span>{claim.sources.length} source(s)</span>
        )}
      </div>

      {isExpanded && claim.sources.length > 0 && (
        <ul className="mt-3 space-y-1 border-t border-charcoal-light pt-3">
          {claim.sources.map((source) => (
            <li key={source.url}>
              <a
                href={source.url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-xs text-amber hover:text-amber-light transition-colors"
                onClick={(event) => event.stopPropagation()}
              >
                {source.title}
              </a>
            </li>
          ))}
        </ul>
      )}
    </article>
  );
}
