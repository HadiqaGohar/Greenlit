import type { Claim, Verdict } from "./types";

export interface HighlightSegment {
  text: string;
  claimId?: string;
  verdict?: Verdict;
}

export function buildHighlightSegments(
  scriptText: string,
  claims: Claim[],
): HighlightSegment[] {
  const located = claims
    .filter((claim) => claim.location !== null && claim.location !== undefined)
    .sort((a, b) => a.location!.start - b.location!.start);

  if (located.length === 0) {
    return [{ text: scriptText }];
  }

  const segments: HighlightSegment[] = [];
  let cursor = 0;

  for (const claim of located) {
    if (!claim.location || typeof claim.location.start === 'undefined' || typeof claim.location.end === 'undefined') {
      continue;
    }
    const { start, end } = claim.location;
    if (end <= cursor) continue;

    const segmentStart = Math.max(start, cursor);
    if (segmentStart > cursor) {
      segments.push({ text: scriptText.slice(cursor, segmentStart) });
    }

    segments.push({
      text: scriptText.slice(segmentStart, end),
      claimId: claim.id,
      verdict: claim.verdict,
    });
    cursor = end;
  }

  if (cursor < scriptText.length) {
    segments.push({ text: scriptText.slice(cursor) });
  }

  return segments;
}
