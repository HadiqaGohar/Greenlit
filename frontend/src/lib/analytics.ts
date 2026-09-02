"use client";

export interface AnalyticsOverview {
  total_scripts: number;
  total_claims: number;
  verified_claims: number;
  flagged_claims: number;
  average_risk_score: number;
  scripts_this_month: number;
  risk_distribution: Record<string, number>;
  claims_by_status: Record<string, number>;
  top_issues: Array<{
    category: string;
    count: number;
    severity: string;
  }>;
}

export interface TrendData {
  labels: string[];
  values: number[];
  metric: string;
}

export interface ComparativeAnalysis {
  period: string;
  current_scripts: number;
  previous_scripts: number;
  current_avg_risk: number;
  previous_avg_risk: number;
  risk_trend: "improving" | "worsening" | "stable";
  scripts_trend: "growing" | "declining" | "stable";
}

export interface ProjectComparison {
  project_id: string;
  title: string;
  risk_score: number;
  claims_count: number;
  flagged_count: number;
  status: string;
}

export interface AnalyticsReport {
  generated_at: string;
  timeframe: string;
  overview: AnalyticsOverview;
  risk_trend: TrendData;
  scripts_trend: TrendData;
  comparative: ComparativeAnalysis;
  top_projects: ProjectComparison[];
  insights: string[];
}

export interface PerformanceMetrics {
  api_calls_today: number;
  api_calls_this_month: number;
  average_response_time_ms: number;
  uptime_percentage: number;
  active_users: number;
  peak_concurrent_users: number;
  storage_used_mb: number;
  storage_limit_mb: number;
  agents_executed_today: number;
  average_analysis_time_seconds: number;
  success_rate: number;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function fetchAnalytics<T>(endpoint: string): Promise<T> {
  try {
    const response = await fetch(`${API_BASE}/api/analytics${endpoint}`);
    
    if (!response.ok) {
      let detail = response.statusText;
      try {
        const body = await response.json();
        detail = body.detail ?? detail;
      } catch {
        // use statusText
      }
      throw new Error(`Analytics request failed: ${detail}`);
    }
    
    return response.json();
  } catch (error) {
    // Handle network errors (backend down)
    if (error instanceof TypeError && error.message.includes("fetch")) {
      throw new Error("Cannot connect to analytics server. Please ensure the backend is running.");
    }
    // Re-throw other errors
    throw error;
  }
}

export async function getAnalyticsOverview(): Promise<AnalyticsOverview> {
  return fetchAnalytics<AnalyticsOverview>("/overview");
}

export async function getAnalyticsTrends(
  timeframe: "week" | "month" | "quarter" | "year" = "month"
): Promise<TrendData[]> {
  return fetchAnalytics<TrendData[]>(`/trends?timeframe=${timeframe}`);
}

export async function getComparativeAnalysis(
  timeframe: "week" | "month" | "year" = "month"
): Promise<ComparativeAnalysis> {
  return fetchAnalytics<ComparativeAnalysis>(`/comparative?timeframe=${timeframe}`);
}

export async function getProjectComparison(
  limit: number = 10,
  sortBy: "risk_score" | "claims_count" | "flagged_count" = "risk_score"
): Promise<ProjectComparison[]> {
  return fetchAnalytics<ProjectComparison[]>(
    `/projects?limit=${limit}&sort_by=${sortBy}`
  );
}

export async function generateAnalyticsReport(
  timeframe: "week" | "month" | "quarter" | "year" = "month"
): Promise<AnalyticsReport> {
  return fetchAnalytics<AnalyticsReport>(`/report?timeframe=${timeframe}`);
}

export async function getPerformanceMetrics(): Promise<PerformanceMetrics> {
  return fetchAnalytics<PerformanceMetrics>("/performance");
}
