import type {
  AnalyzeRequest,
  AnalyzeResponse,
  Comment,
  TeamMember,
  ReviewStatus,
  ActivityItem,
  ProductionRole,
  Notification,
  WatchedFolder,
  ProductionIssue,
  AgentFlowStep,
  Suggestion,
  ReadinessScore,
} from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(path: string, options?: RequestInit, retries =2): Promise<T> {
  let lastError: Error | null = null;
  
  for (let attempt =0; attempt <= retries; attempt++) {
    try {
      const response = await fetch(`${API_URL}${path}`, {
        headers: {
          "Content-Type": "application/json",
          ...options?.headers,
        },
        ...options,
      });

      if (!response.ok) {
        let detail = response.statusText;
        try {
          const body = await response.json();
          detail = body.detail ?? detail;
        } catch {
          // use statusText
        }
        throw new ApiError(detail, response.status);
      }

      return response.json() as Promise<T>;
    } catch (error) {
      lastError = error as Error;
      
      // Don't retry on client errors (4xx)
      if (error instanceof ApiError && error.status >=400 && error.status <500) {
        throw error;
      }
      
      // Retry on network errors or server errors (5xx)
      if (attempt < retries) {
        const delay = Math.pow(2, attempt) *500; // Exponential backoff:500ms,1s
        await new Promise(resolve => setTimeout(resolve, delay));
        continue;
      }
    }
  }
  
  throw lastError ?? new Error("Request failed after retries");
}

export async function analyzeScript(
  payload: AnalyzeRequest,
  userId?: string,
): Promise<AnalyzeResponse> {
  const body = userId ? { ...payload, user_id: userId } : payload;
  return request<AnalyzeResponse>("/api/analyze", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export async function getReport(reportId: string): Promise<AnalyzeResponse> {
  return request<AnalyzeResponse>(`/api/report/${reportId}`);
}

export interface ReportListItem {
  id: string;
  title: string;
  date: string;
  claimCount: number;
  flaggedCount: number;
  riskScore: number;
  processingTime: number;
  status: string;
}

export async function listReports(userId?: string): Promise<{ reports: ReportListItem[]; total: number }> {
  const params = userId ? `?user_id=${userId}` : "";
  return request<{ reports: ReportListItem[]; total: number }>(`/api/reports${params}`);
}

// ─── Collaboration API ────────────────────────────────────────────────────────

export async function getComments(
  scriptId: string,
  claimId?: string,
  sceneId?: string,
): Promise<Comment[]> {
  const params = new URLSearchParams();
  if (claimId) params.set("claim_id", claimId);
  if (sceneId) params.set("scene_id", sceneId);
  const qs = params.toString() ? `?${params.toString()}` : "";
  return request<Comment[]>(`/api/scripts/${scriptId}/comments${qs}`);
}

export async function createComment(
  scriptId: string,
  content: string,
  userId: string,
  userName: string,
  userRole: ProductionRole = "researcher",
  claimId?: string,
  sceneId?: string,
  parentId?: string,
): Promise<Comment> {
  const params = new URLSearchParams({
    user_id: userId,
    user_name: userName,
    user_role: userRole,
  });
  return request<Comment>(`/api/scripts/${scriptId}/comments?${params}`, {
    method: "POST",
    body: JSON.stringify({ content, claim_id: claimId, scene_id: sceneId, parent_id: parentId }),
  });
}

export async function updateComment(
  commentId: string,
  content: string,
  userId: string,
): Promise<Comment> {
  const params = new URLSearchParams({ user_id: userId, content });
  return request<Comment>(`/api/comments/${commentId}?${params}`, {
    method: "PUT",
  });
}

export async function deleteComment(commentId: string, userId: string): Promise<void> {
  const params = new URLSearchParams({ user_id: userId });
  await request(`/api/comments/${commentId}?${params}`, { method: "DELETE" });
}

export async function resolveComment(
  commentId: string,
  userId: string,
  userName: string,
): Promise<void> {
  const params = new URLSearchParams({ user_id: userId, user_name: userName });
  await request(`/api/comments/${commentId}/resolve?${params}`, { method: "POST" });
}

// ─── Team API ─────────────────────────────────────────────────────────────────

export async function getTeamMembers(scriptId: string): Promise<TeamMember[]> {
  return request<TeamMember[]>(`/api/scripts/${scriptId}/team`);
}

export async function inviteTeamMember(
  scriptId: string,
  userId: string,
  role: ProductionRole,
  permissions: string[] = ["view", "comment"],
): Promise<TeamMember> {
  const params = new URLSearchParams({ user_id: userId });
  return request<TeamMember>(`/api/scripts/${scriptId}/team/invite?${params}`, {
    method: "POST",
    body: JSON.stringify({ email: "", role, permissions }),
  });
}

export async function removeTeamMember(
  scriptId: string,
  targetUserId: string,
  userId: string,
): Promise<void> {
  const params = new URLSearchParams({ user_id: userId });
  await request(`/api/scripts/${scriptId}/team/${targetUserId}?${params}`, {
    method: "DELETE",
  });
}

// ─── Review API ───────────────────────────────────────────────────────────────

export async function getReviews(scriptId: string): Promise<ReviewStatus[]> {
  return request<ReviewStatus[]>(`/api/scripts/${scriptId}/reviews`);
}

export async function createReviewRequest(
  scriptId: string,
  reviewerId: string,
  userId: string,
): Promise<ReviewStatus> {
  const params = new URLSearchParams({ reviewer_id: reviewerId, user_id: userId });
  return request<ReviewStatus>(`/api/scripts/${scriptId}/reviews?${params}`, {
    method: "POST",
  });
}

export async function updateReviewStatus(
  reviewId: string,
  status: string,
  userId: string,
  userName: string,
  comments?: string,
): Promise<ReviewStatus> {
  const params = new URLSearchParams({
    status,
    user_id: userId,
    user_name: userName,
    ...(comments ? { comments } : {}),
  });
  return request<ReviewStatus>(`/api/reviews/${reviewId}?${params}`, {
    method: "PUT",
  });
}

// ─── Activity API ─────────────────────────────────────────────────────────────

export async function getActivityFeed(
  scriptId: string,
  limit = 20,
): Promise<{ activities: ActivityItem[] }> {
  return request(`/api/scripts/${scriptId}/activity?limit=${limit}`);
}

export async function getOnlineMembers(
  scriptId: string,
): Promise<{ members: { user_id: string; user_name: string }[]; count: number }> {
  return request(`/api/scripts/${scriptId}/online`);
}

// ─── Automation API ───────────────────────────────────────────────────────────

export async function getAutomationStatus(): Promise<{
  file_watching: boolean;
  watched_folders?: Array<Record<string, unknown>>;
}> {
  return request("/automation/status");
}

export async function getWatchedFolders(): Promise<{ folders: WatchedFolder[]; total: number }> {
  return request("/automation/watch-folders");
}

export async function addWatchFolder(config: {
  folder_path: string;
  folder_type?: string;
  auto_analyze?: boolean;
  notification_webhook?: string;
}): Promise<{ success: boolean; watch_id: string }> {
  return request("/automation/watch-folder", {
    method: "POST",
    body: JSON.stringify(config),
  });
}

export async function removeWatchFolder(watchId: string): Promise<{ success: boolean }> {
  return request(`/automation/watch-folder/${watchId}`, { method: "DELETE" });
}

// ─── Notification API ─────────────────────────────────────────────────────────

export interface NotificationSettingsData {
  user_id: string;
  email_enabled: boolean;
  slack_enabled: boolean;
  slack_webhook: string;
  high_risk_threshold: number;
  notify_on_comments: boolean;
  notify_on_completion: boolean;
  digest_frequency: string;
}

export async function getNotificationSettings(
  userId: string,
): Promise<NotificationSettingsData> {
  return request(`/automation/notifications/settings?user_id=${userId}`);
}

export async function updateNotificationSettings(
  userId: string,
  settings: Partial<NotificationSettingsData>,
): Promise<NotificationSettingsData> {
  return request(`/automation/notifications/settings?user_id=${userId}`, {
    method: "PUT",
    body: JSON.stringify({ settings }),
  });
}

export async function getNotifications(
  userId: string,
  unreadOnly = false,
  limit = 50,
): Promise<{ notifications: Notification[]; unread_count: number }> {
  const params = new URLSearchParams({ user_id: userId, limit: String(limit) });
  if (unreadOnly) params.set("unread_only", "true");
  return request(`/automation/notifications?${params}`);
}

export async function markNotificationRead(notificationId: string): Promise<void> {
  await request(`/automation/notifications/${notificationId}/read`, { method: "PUT" });
}

export async function markAllNotificationsRead(userId: string): Promise<void> {
  await request(`/automation/notifications/read-all?user_id=${userId}`, { method: "PUT" });
}

// ─── Export API ───────────────────────────────────────────────────────────────

export interface ExportRequestData {
  script_id: string;
  format: "pdf" | "json" | "csv";
  sections?: string[];
  include_comments?: boolean;
  branding?: { name?: string };
  report_data?: Record<string, unknown>;
}

export interface ExportResult {
  export_id: string;
  status: string;
  format: string;
  download_url: string;
  created_at: string;
}

export async function createExport(
  data: ExportRequestData,
  userId: string,
): Promise<ExportResult> {
  return request(`/api/export?user_id=${userId}`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function getExportStatus(exportId: string): Promise<ExportResult> {
  return request(`/api/export/${exportId}`);
}

export async function listExports(
  userId: string,
  limit = 20,
): Promise<{ exports: ExportResult[] }> {
  return request(`/api/export/exports?user_id=${userId}&limit=${limit}`);
}

export async function bulkExport(
  scriptIds: string[],
  format: string,
  userId: string,
): Promise<{ exports: Array<Record<string, unknown>> }> {
  return request(`/api/export/export/bulk?user_id=${userId}`, {
    method: "POST",
    body: JSON.stringify({ script_ids: scriptIds, format }),
  });
}

// ─── Share Link API ──────────────────────────────────────────────────────────

export interface ShareLinkResult {
  share_url: string;
  token: string;
  expires_at: string;
}

export async function createShareLink(
  scriptId: string,
  expiresInHours = 72,
): Promise<ShareLinkResult> {
  return request("/api/share", {
    method: "POST",
    body: JSON.stringify({ script_id: scriptId, expires_in_hours: expiresInHours }),
  });
}

export async function getSharedReport(token: string): Promise<{
  script_id: string;
  created_at: string;
  expires_at: string;
  access_count: number;
}> {
  return request(`/api/share/${token}`);
}

export async function revokeShareLink(token: string): Promise<void> {
  await request(`/api/share/${token}`, { method: "DELETE" });
}

export function getExportDownloadUrl(filename: string): string {
  return `${API_URL}/api/export/download/${filename}`;
}

// ─── Storyboard API ─────────────────────────────────────────────────────────

export interface StoryboardFrame {
  scene_number: number;
  title: string;
  description: string;
  mood: string;
  camera_angle: string;
  visual_prompt: string;
  image_base64: string | null;
  image_mime_type: string;
  generation_error: string | null;
}

export interface StoryboardResponse {
  storyboard_id: string;
  report_id: string;
  success: boolean;
  frames: StoryboardFrame[];
  total_frames: number;
  successful_frames: number;
  failed_frames: number;
  processing_time: number;
  generated_at: string;
  error: string | null;
}

export async function generateStoryboard(
  reportId: string,
  sceneNumbers?: number[],
): Promise<StoryboardResponse> {
  return request<StoryboardResponse>("/api/storyboard/generate", {
    method: "POST",
    body: JSON.stringify({ report_id: reportId, scene_numbers: sceneNumbers }),
  });
}

export async function getStoryboard(
  storyboardId: string,
): Promise<StoryboardResponse> {
  return request<StoryboardResponse>(`/api/storyboard/${storyboardId}`);
}

export async function getStoryboardByReport(
  reportId: string,
): Promise<StoryboardResponse> {
  return request<StoryboardResponse>(`/api/storyboard/report/${reportId}`);
}

// ─── TTS / Table Read API ──────────────────────────────────────────────────

export interface TTSScene {
  scene_number: number;
  title: string;
  characters: string[];
  audio_base64: string | null;
  audio_format: string;
  duration_seconds: number;
  generation_error: string | null;
}

export interface TTSResponse {
  tts_id: string;
  report_id: string;
  success: boolean;
  scenes: TTSScene[];
  total_scenes: number;
  successful_scenes: number;
  voice_map: Record<string, string>;
  total_duration: number;
  processing_time: number;
  generated_at: string;
  error: string | null;
}

export async function generateTableRead(
  reportId: string,
  sceneNumbers?: number[],
): Promise<TTSResponse> {
  return request<TTSResponse>("/api/tts/generate", {
    method: "POST",
    body: JSON.stringify({ report_id: reportId, scene_numbers: sceneNumbers }),
  });
}

export async function getTTS(
  ttsId: string,
): Promise<TTSResponse> {
  return request<TTSResponse>(`/api/tts/${ttsId}`);
}

export async function getTTSByReport(
  reportId: string,
): Promise<TTSResponse> {
  return request<TTSResponse>(`/api/tts/report/${reportId}`);
}

// ─── Production Schedule API ──────────────────────────────────────────────

export interface ScheduleScene {
  scene_number: number;
  title: string;
  location: string;
  int_ext: string;
  time_of_day: string;
  characters: string[];
  page_eighths: number;
  page_count: string;
  complexity: number;
  strip_color: string;
  dialogue_count: number;
  action_line_count: number;
}

export interface ShootDay {
  day_number: number;
  scenes: ScheduleScene[];
  total_page_eighths: number;
  total_page_count: string;
  locations: string[];
  company_moves: number;
  cast_required: string[];
  is_night_shoot: boolean;
  estimated_hours: number;
  scene_count: number;
}

export interface ScheduleResponse {
  schedule_id: string;
  report_id: string;
  success: boolean;
  shoot_days: ShootDay[];
  total_shoot_days: number;
  contingency_days: number;
  total_pages: string;
  total_pages_eighths: number;
  company_moves_total: number;
  cast_schedule: Record<string, Array<{ day: number; status: string }>>;
  location_summary: Array<{
    location: string;
    scene_count: number;
    scene_numbers: number[];
    total_pages: string;
    characters: string[];
    has_day: boolean;
    has_night: boolean;
  }>;
  optimization_notes: string[];
  pages_per_day_target: number;
  processing_time: number;
  generated_at: string;
  error: string | null;
}

export async function generateSchedule(
  reportId: string,
  pagesPerDay?: number,
): Promise<ScheduleResponse> {
  return request<ScheduleResponse>("/api/schedule/generate", {
    method: "POST",
    body: JSON.stringify({ report_id: reportId, pages_per_day: pagesPerDay }),
  });
}

export async function getSchedule(
  scheduleId: string,
): Promise<ScheduleResponse> {
  return request<ScheduleResponse>(`/api/schedule/${scheduleId}`);
}

export async function getScheduleByReport(
  reportId: string,
): Promise<ScheduleResponse> {
  return request<ScheduleResponse>(`/api/schedule/report/${reportId}`);
}

// ─── Multi-Stakeholder Analysis API ────────────────────────────────────────

export interface StakeholderFinding {
  category: string;
  severity: string;
  items: string[];
}

export interface StakeholderRole {
  role: string;
  title: string;
  icon: string;
  overall_score: number;
  score_label: string;
  risk_level: string;
  key_concerns: string[];
  findings: StakeholderFinding[];
  recommendations: string[];
  summary: string;
}

export interface StakeholderResponse {
  stakeholder_id: string;
  report_id: string;
  success: boolean;
  stakeholders: StakeholderRole[];
  overall_readiness: number;
  roles_analyzed: number;
  processing_time: number;
  generated_at: string;
  error: string | null;
}

export async function analyzeStakeholders(
  reportId: string,
): Promise<StakeholderResponse> {
  return request<StakeholderResponse>("/api/stakeholder/analyze", {
    method: "POST",
    body: JSON.stringify({ report_id: reportId }),
  });
}

export async function getStakeholders(
  stakeholderId: string,
): Promise<StakeholderResponse> {
  return request<StakeholderResponse>(`/api/stakeholder/${stakeholderId}`);
}

export async function getStakeholdersByReport(
  reportId: string,
): Promise<StakeholderResponse> {
  return request<StakeholderResponse>(`/api/stakeholder/report/${reportId}`);
}

// ─── Budget vs. Actual Tracking API ──────────────────────────────────────────

export interface BudgetTrackingCategory {
  name: string;
  planned_min: number;
  planned_mid: number;
  planned_max: number;
  planned_range: string;
  actual: number;
  variance: number;
  variance_pct: number;
  status: "under" | "on_track" | "over";
  confidence: number;
  line_items: Array<{ item: string; cost: string }>;
  notes: string;
  data_source: "estimated" | "provided";
}

export interface BudgetTrackingResponse {
  tracking_id: string;
  report_id: string;
  success: boolean;
  currency: string;
  total_planned: number;
  total_actual: number;
  total_variance: number;
  total_variance_pct: number;
  overall_status: "under" | "on_track" | "over";
  categories: BudgetTrackingCategory[];
  alerts: string[];
  recommendations: string[];
  cost_saving_tips: string[];
  budget_level: string;
  total_estimated_budget: string;
  processing_time: number;
  generated_at: string;
  error: string | null;
}

export async function trackBudget(
  reportId: string,
  actuals?: Record<string, number>,
): Promise<BudgetTrackingResponse> {
  return request<BudgetTrackingResponse>("/api/budget/track", {
    method: "POST",
    body: JSON.stringify({ report_id: reportId, actuals }),
  });
}

export async function getBudgetTrack(
  trackingId: string,
): Promise<BudgetTrackingResponse> {
  return request<BudgetTrackingResponse>(`/api/budget/track/${trackingId}`);
}

export async function getBudgetTrackByReport(
  reportId: string,
): Promise<BudgetTrackingResponse> {
  return request<BudgetTrackingResponse>(`/api/budget/track/report/${reportId}`);
}

// ─── Character Relationship Graph API ────────────────────────────────────────

export interface RelationshipNode {
  id: string;
  name: string;
  scenes_count: number;
  is_primary: boolean;
  centrality: number;
  degree: number;
}

export interface RelationshipEdge {
  source: string;
  target: string;
  weight: number;
  shared_scenes: number[];
  type: string;
  label: string;
  confidence: number;
}

export interface RelationshipResponse {
  graph_id: string;
  report_id: string;
  success: boolean;
  nodes: RelationshipNode[];
  edges: RelationshipEdge[];
  stats: {
    character_count: number;
    relationship_count: number;
    scene_count: number;
    most_connected: string;
    primary_characters: string[];
  };
  processing_time: number;
  generated_at: string;
  error: string | null;
}

export async function generateRelationshipGraph(
  reportId: string,
): Promise<RelationshipResponse> {
  return request<RelationshipResponse>("/api/relationship/generate", {
    method: "POST",
    body: JSON.stringify({ report_id: reportId }),
  });
}

export async function getRelationshipGraph(
  graphId: string,
): Promise<RelationshipResponse> {
  return request<RelationshipResponse>(`/api/relationship/${graphId}`);
}

export async function getRelationshipGraphByReport(
  reportId: string,
): Promise<RelationshipResponse> {
  return request<RelationshipResponse>(`/api/relationship/report/${reportId}`);
}

// ─── Script Comparison API ───────────────────────────────────────────────────

export interface SceneDiff {
  status: "added" | "removed" | "modified" | "unchanged";
  scene_number: number;
  title: string;
  location: string;
  characters_a: string[];
  characters_b: string[];
  change: string;
}

export interface ScriptCompareResponse {
  compare_id: string;
  label_a: string;
  label_b: string;
  summary: {
    similarity_pct: number;
    added_lines: number;
    removed_lines: number;
    scenes_added: number;
    scenes_removed: number;
    scenes_modified: number;
    scenes_unchanged: number;
    characters_added: number;
    characters_removed: number;
  };
  scenes: SceneDiff[];
  characters: { added: string[]; removed: string[]; common: string[] };
  line_diff: { diff: string; added_lines: number; removed_lines: number; similarity_percentage: number };
  processing_time: number;
  generated_at: string;
}

export async function compareScripts(payload: {
  script_a?: string;
  script_b?: string;
  report_id_a?: string;
  report_id_b?: string;
  label_a?: string;
  label_b?: string;
}): Promise<ScriptCompareResponse> {
  return request<ScriptCompareResponse>("/api/script-compare", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

// ─── Pitch Deck API ─────────────────────────────────────────────────────────

export interface PitchDeckSlide {
  title: string;
  bullets: string[];
  icon?: string;
}

export interface PitchDeckResponse {
  deck_id: string;
  report_id: string;
  success: boolean;
  title: string;
  slides: PitchDeckSlide[];
  slide_count: number;
  generation_method: string;
  processing_time: number;
  generated_at: string;
  error: string | null;
}

export async function generatePitchDeck(
  reportId: string,
  scriptText?: string,
): Promise<PitchDeckResponse> {
  return request<PitchDeckResponse>("/api/pitch-deck/generate", {
    method: "POST",
    body: JSON.stringify({ report_id: reportId, script_text: scriptText }),
  });
}

export async function getPitchDeckByReport(
  reportId: string,
): Promise<PitchDeckResponse> {
  return request<PitchDeckResponse>(`/api/pitch-deck/report/${reportId}`);
}

// ─── Scene-to-Location Matching API ──────────────────────────────────────────

export interface LocationMatch {
  index: number;
  matched_location: string;
  city: string;
  venue_type: string;
  permit_required: boolean;
  est_cost_usd: number;
  travel_note: string;
  rationale: string;
}

export interface LocationMatchResponse {
  match_id: string;
  report_id: string;
  success: boolean;
  matches: LocationMatch[];
  match_count: number;
  generation_method: string;
  processing_time: number;
  generated_at: string;
  error: string | null;
}

export async function generateLocationMatches(
  reportId: string,
  scriptText?: string,
): Promise<LocationMatchResponse> {
  return request<LocationMatchResponse>("/api/location/match", {
    method: "POST",
    body: JSON.stringify({ report_id: reportId, script_text: scriptText }),
  });
}

export async function getLocationMatchByReport(
  reportId: string,
): Promise<LocationMatchResponse> {
  return request<LocationMatchResponse>(`/api/location/match/report/${reportId}`);
}

// ─── Chat API ("Ask the Script") ────────────────────────────────────────────

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  timestamp: string;
}

export interface ChatResponse {
  answer: string;
  sources: Array<{ title: string; url: string }>;
  related_scenes: number[];
  confidence: number;
}

export async function chatWithScript(
  reportId: string,
  question: string,
  scriptText?: string,
  history: ChatMessage[] = [],
): Promise<ChatResponse> {
  return request<ChatResponse>("/api/chat", {
    method: "POST",
    body: JSON.stringify({
      report_id: reportId,
      question,
      script_text: scriptText,
      history,
    }),
  });
}

// ─── Scene Risk API (Heatmap) ───────────────────────────────────────────────

export interface SceneRiskData {
  scene_number: number;
  title: string;
  location: string;
  time_of_day: string;
  risk_score: number;
  risk_level: "low" | "medium" | "high" | "critical";
  risk_factors: string[];
  legal_issues: Array<Record<string, unknown>>;
  continuity_issues: Array<Record<string, unknown>>;
  research_flags: Array<Record<string, unknown>>;
  estimated_cost: number;
  text_start: number;
  text_end: number;
  reasoning: string;
}

export interface SceneRiskResponse {
  report_id: string;
  total_scenes: number;
  overall_risk_score: number;
  scenes: SceneRiskData[];
  risk_distribution: Record<string, number>;
  generated_at: string;
}

export async function getSceneRiskData(
  reportId: string,
): Promise<SceneRiskResponse> {
  return request<SceneRiskResponse>(`/api/scene-risk/${reportId}`);
}

export async function getSingleSceneRisk(
  reportId: string,
  sceneNumber: number,
): Promise<SceneRiskData> {
  return request<SceneRiskData>(
    `/api/scene-risk/${reportId}/scene/${sceneNumber}`,
  );
}

// ─── Risk Detail API (Dashboard) ───────────────────────────────────────────

export interface RiskDetailResponse {
  report_id: string;
  risk_assessment: {
    overall_risk_score: number;
    risk_level: string;
    risk_factors: string[];
    critical_issues: ProductionIssue[];
    recommended_actions: string[];
    confidence: number;
  };
  critical_issues: ProductionIssue[];
  agent_flow: AgentFlowStep[];
  suggestions: Suggestion[];
  readiness_scores?: ReadinessScore;
}

export async function getRiskDetail(
  reportId: string,
): Promise<RiskDetailResponse> {
  return request<RiskDetailResponse>(`/api/risk-detail/${reportId}`);
}
