export type ClaimType = "historical" | "location" | "technical" | "licensing";
export type Verdict = "verified" | "flagged" | "uncertain";

export interface Source {
  title: string;
  url: string;
}

export interface ClaimLocation {
  start: number;
  end: number;
}

export interface Claim {
  id: string;
  text: string;
  type: ClaimType;
  verdict: Verdict;
  confidence: number;
  sources: Source[];
  note: string;
  location: ClaimLocation | null;
}

export interface AnalyzeResponse {
  report_id: string;
  claims: Claim[];
}

export interface AnalyzeRequest {
  script_text: string;
}
