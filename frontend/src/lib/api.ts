import type {
  AnalyzeRequest,
  AnalyzeResponse,
  Comment,
  TeamMember,
  ReviewStatus,
  ActivityItem,
  ProductionRole,
  Notification,
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

async function request<T>(path: string, options?: RequestInit): Promise<T> {
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
}

export async function analyzeScript(
  payload: AnalyzeRequest,
): Promise<AnalyzeResponse> {
  return request<AnalyzeResponse>("/api/analyze", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function getReport(reportId: string): Promise<AnalyzeResponse> {
  return request<AnalyzeResponse>(`/api/report/${reportId}`);
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
  watched_folders?: any[];
}> {
  return request("/automation/status");
}

export async function getWatchedFolders(): Promise<{ folders: any[]; total: number }> {
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
): Promise<{ exports: any[] }> {
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
