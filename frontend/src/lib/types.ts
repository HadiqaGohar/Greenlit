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

// ─── Agent result types ───────────────────────────────────────────────────────

export type AgentType = "director" | "research" | "legal" | "continuity";

export interface AgentResult {
  agent_type: AgentType;
  success: boolean;
  confidence_score: number;
  confidence?: number;
  processing_time: number;
  data: Record<string, any> | null;
  error_message?: string;
  metadata?: Record<string, any>;
}

export interface RiskAssessment {
  overall_risk_score: number;
  risk_level: "low" | "medium" | "high" | "critical";
  risk_factors: string[];
  critical_issues: ProductionIssue[];
  recommended_actions: string[];
  confidence: number;
}

export interface ProductionIssue {
  type: string;
  severity: string;
  description: string;
  suggested_action: string;
  urgency: string;
}

// ─── Analyze response ────────────────────────────────────────────────────────

export interface AnalyzeResponse {
  report_id: string;
  claims: Claim[];
  risk_assessment?: RiskAssessment;
  agent_results?: Record<AgentType, AgentResult>;
  processing_time?: number;
  timestamp?: string;
  agent_timeline?: AgentTimelineStep[];
  readiness_scores?: ReadinessScore;
  agent_flow?: AgentFlowStep[];
  suggestions?: Suggestion[];
}

export interface AgentTimelineStep {
  agent: string;
  status: "queued" | "running" | "complete" | "error";
  start_time: string | null;
  end_time: string | null;
  duration_seconds: number | null;
  summary: string;
  claims_count: number | null;
  issues_found: number | null;
  confidence: number | null;
  phase: "sequential" | "parallel";
}

export interface ReadinessScore {
  legal_clearance: number;
  historical_accuracy: number;
  continuity: number;
  budget_feasibility: number;
  overall: number;
  grade: string;
}

export interface AgentFlowStep {
  agent: string;
  claims_in: number;
  claims_out: number;
  verified: number;
  flagged: number;
  uncertain: number;
  issues_high: number;
  issues_medium: number;
  issues_low: number;
}

export interface Suggestion {
  issue_id: string;
  issue_type: string;
  severity: string;
  original_text: string;
  suggested_text: string;
  rationale: string;
}

export interface AnalyzeRequest {
  script_text: string;
}

// Dashboard types
export interface ProjectSummary {
  id: string;
  title: string;
  status: string;
  riskScore: number;
  lastAnalyzed: string;
  scenesCount: number;
  charactersCount: number;
  issues: {
    critical: number;
    high: number;
    medium: number;
    low: number;
  };
  teamSize: number;
  progressPercentage: number;
}

export interface AnalyticsSummary {
  totalScripts: number;
  averageRiskScore: number;
  scriptsThisMonth: number;
  activeCollaborators: number;
  trends: TrendPoint[];
  topRiskCategories: Record<string, number>;
  recentActivity: any[];
}

export interface TrendPoint {
  date: string;
  value: number;
  metric: string;
}

export interface Notification {
  id: string;
  type: string;
  title: string;
  message: string;
  read: boolean;
  createdAt: string;
  actionUrl?: string;
}

export interface NotificationSettings {
  user_id: string;
  email_enabled: boolean;
  slack_enabled: boolean;
  slack_webhook: string;
  high_risk_threshold: number;
  notify_on_comments: boolean;
  notify_on_completion: boolean;
  digest_frequency: string;
}

export interface WatchedFolder {
  watch_id: string;
  folder_path: string;
  folder_type: string;
  auto_analyze: boolean;
  notification_webhook?: string;
  last_checked?: string;
  files_found?: number;
}

export interface ExportRequestItem {
  id: string;
  script_id: string;
  format: string;
  status: string;
  download_url?: string;
  created_at?: string;
}

export interface ShareLink {
  share_url: string;
  token: string;
  expires_at: string;
}

export interface DashboardData {
  projects: ProjectSummary[];
  analytics: AnalyticsSummary;
  notifications: Notification[];
  recentExports: any[];
}

// ─── Collaboration types ──────────────────────────────────────────────────────

export type ProductionRole =
  | "director"
  | "producer"
  | "script_supervisor"
  | "line_producer"
  | "legal_affairs"
  | "researcher";

export interface Comment {
  id: string;
  report_id: string;
  claim_id?: string;
  scene_id?: string;
  user_id: string;
  user_name: string;
  user_role: ProductionRole;
  content: string;
  parent_id?: string;
  resolved: boolean;
  created_at: string;
  updated_at: string;
  replies?: Comment[];
}

export interface TeamMember {
  id: string;
  user_id: string;
  script_id: string;
  role: ProductionRole;
  permissions: string[];
  added_at: string;
}

export interface ReviewStatus {
  id: string;
  script_id: string;
  reviewer_id: string;
  status: "pending" | "approved" | "rejected" | "needs_changes";
  comments: string;
  reviewed_at?: string;
}

export interface ActivityItem {
  type: "comment" | "review" | "status_change" | "member_added";
  user_name?: string;
  content?: string;
  status?: string;
  timestamp: string;
  resolved?: boolean;
}

export interface OnlineMember {
  user_id: string;
  user_name: string;
}

// ─── WebSocket message types ──────────────────────────────────────────────────

export type WSMessageType =
  | "user_joined"
  | "user_left"
  | "comment_added"
  | "comment_updated"
  | "comment_deleted"
  | "issue_resolved"
  | "review_status_changed"
  | "review_requested"
  | "team_member_added"
  | "team_member_removed"
  | "script_status_updated"
  | "cursor_position"
  | "typing";

export interface WSMessage {
  type: WSMessageType;
  timestamp?: string;
  [key: string]: any;
}
