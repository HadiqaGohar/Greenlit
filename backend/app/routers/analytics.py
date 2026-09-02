"""
Analytics Router - Provides detailed analytics and reporting endpoints
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from pydantic import BaseModel

router = APIRouter()

# Response schemas
class AnalyticsOverview(BaseModel):
    demo_mode: bool = True
    total_scripts: int = 0
    total_claims: int = 0
    verified_claims: int = 0
    flagged_claims: int = 0
    average_risk_score: float = 0.0
    scripts_this_month: int = 0
    risk_distribution: Dict[str, int] = {}
    claims_by_status: Dict[str, int] = {}
    top_issues: List[Dict[str, Any]] = []

class TrendData(BaseModel):
    labels: List[str] = []
    values: List[float] = []
    metric: str = ""

class ComparativeAnalysis(BaseModel):
    period: str
    current_scripts: int = 0
    previous_scripts: int = 0
    current_avg_risk: float = 0.0
    previous_avg_risk: float = 0.0
    risk_trend: str = "stable"  # "improving", "worsening", "stable"
    scripts_trend: str = "stable"

class ProjectComparison(BaseModel):
    project_id: str
    title: str
    risk_score: float
    claims_count: int
    flagged_count: int
    status: str

class AnalyticsReport(BaseModel):
    generated_at: str
    timeframe: str
    overview: AnalyticsOverview
    risk_trend: TrendData
    scripts_trend: TrendData
    comparative: ComparativeAnalysis
    top_projects: List[ProjectComparison]
    insights: List[str]


@router.get("/overview", response_model=AnalyticsOverview)
async def get_analytics_overview():
    """
    Get overall analytics summary across all projects
    """
    try:
        return AnalyticsOverview(
            total_scripts=24,
            total_claims=186,
            verified_claims=142,
            flagged_claims=18,
            average_risk_score=42.5,
            scripts_this_month=8,
            risk_distribution={
                "low": 10,
                "medium": 8,
                "high": 4,
                "critical": 2
            },
            claims_by_status={
                "verified": 142,
                "pending": 16,
                "flagged": 18,
                "needs_review": 10
            },
            top_issues=[
                {"category": "Historical Accuracy", "count": 7, "severity": "high"},
                {"category": "Legal Clearance", "count": 5, "severity": "critical"},
                {"category": "Cultural Sensitivity", "count": 4, "severity": "medium"},
                {"category": "Budget Feasibility", "count": 3, "severity": "low"}
            ]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analytics overview failed: {str(e)}")


@router.get("/trends", response_model=List[TrendData])
async def get_analytics_trends(
    timeframe: str = Query("month", pattern="^(week|month|quarter|year)$")
):
    """
    Get trend data for analytics charts
    """
    try:
        # Generate mock trend data based on timeframe
        if timeframe == "week":
            labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
            risk_values = [45.2, 42.1, 38.5, 44.8, 41.2, 39.7, 42.5]
            script_values = [3.0, 2.0, 4.0, 5.0, 3.0, 1.0, 2.0]
        elif timeframe == "month":
            labels = ["Week 1", "Week 2", "Week 3", "Week 4"]
            risk_values = [48.3, 45.1, 41.8, 42.5]
            script_values = [5.0, 7.0, 6.0, 8.0]
        elif timeframe == "quarter":
            labels = ["Jan", "Feb", "Mar"]
            risk_values = [52.1, 47.3, 42.5]
            script_values = [18.0, 22.0, 24.0]
        else:  # year
            labels = ["Q1", "Q2", "Q3", "Q4"]
            risk_values = [55.2, 48.7, 44.3, 42.5]
            script_values = [45.0, 52.0, 61.0, 24.0]

        return [
            TrendData(labels=labels, values=risk_values, metric="risk_score"),
            TrendData(labels=labels, values=script_values, metric="scripts_analyzed")
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Trends fetch failed: {str(e)}")


@router.get("/comparative", response_model=ComparativeAnalysis)
async def get_comparative_analysis(
    timeframe: str = Query("month", pattern="^(week|month|year)$")
):
    """
    Get comparative analysis between current and previous period
    """
    try:
        # Mock comparative data
        if timeframe == "week":
            return ComparativeAnalysis(
                period="week",
                current_scripts=20,
                previous_scripts=18,
                current_avg_risk=42.5,
                previous_avg_risk=45.1,
                risk_trend="improving",
                scripts_trend="growing"
            )
        elif timeframe == "month":
            return ComparativeAnalysis(
                period="month",
                current_scripts=24,
                previous_scripts=21,
                current_avg_risk=42.5,
                previous_avg_risk=47.3,
                risk_trend="improving",
                scripts_trend="growing"
            )
        else:  # year
            return ComparativeAnalysis(
                period="year",
                current_scripts=24,
                previous_scripts=182,
                current_avg_risk=42.5,
                previous_avg_risk=49.8,
                risk_trend="improving",
                scripts_trend="growing"
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Comparative analysis failed: {str(e)}")


@router.get("/projects", response_model=List[ProjectComparison])
async def get_project_comparison(
    limit: int = Query(10, ge=1, le=50),
    sort_by: str = Query("risk_score", pattern="^(risk_score|claims_count|flagged_count)$")
):
    """
    Get project comparison data for analytics
    """
    try:
        # Mock project data
        projects = [
            ProjectComparison(
                project_id="proj-1",
                title="The Last Frontier",
                risk_score=72.5,
                claims_count=28,
                flagged_count=5,
                status="in_review"
            ),
            ProjectComparison(
                project_id="proj-2",
                title="Quantum Heist",
                risk_score=35.2,
                claims_count=22,
                flagged_count=2,
                status="production_ready"
            ),
            ProjectComparison(
                project_id="proj-3",
                title="Neon Dreams",
                risk_score=58.1,
                claims_count=31,
                flagged_count=4,
                status="in_review"
            ),
            ProjectComparison(
                project_id="proj-4",
                title="The Cassandra Protocol",
                risk_score=89.3,
                claims_count=45,
                flagged_count=8,
                status="draft"
            ),
            ProjectComparison(
                project_id="proj-5",
                title="Midnight Express Redux",
                risk_score=22.8,
                claims_count=18,
                flagged_count=1,
                status="production_ready"
            ),
        ]

        # Sort by specified field
        if sort_by == "risk_score":
            projects.sort(key=lambda x: x.risk_score, reverse=True)
        elif sort_by == "claims_count":
            projects.sort(key=lambda x: x.claims_count, reverse=True)
        elif sort_by == "flagged_count":
            projects.sort(key=lambda x: x.flagged_count, reverse=True)

        return projects[:limit]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Project comparison failed: {str(e)}")


@router.get("/report", response_model=AnalyticsReport)
async def generate_analytics_report(
    timeframe: str = Query("month", pattern="^(week|month|quarter|year)$")
):
    """
    Generate a comprehensive analytics report with insights
    """
    try:
        # Gather all analytics data
        overview = await get_analytics_overview()
        trends = await get_analytics_trends(timeframe)
        comparative = await get_comparative_analysis(timeframe)
        projects = await get_project_comparison(limit=5)

        # Generate insights based on data
        insights = []
        if comparative.risk_trend == "improving":
            insights.append("Risk scores have decreased compared to the previous period, indicating improved script quality.")
        elif comparative.risk_trend == "worsening":
            insights.append("Risk scores have increased, suggesting more claims need attention.")

        if comparative.scripts_trend == "growing":
            insights.append("Script analysis volume is growing, showing increased platform adoption.")

        high_risk_count = overview.risk_distribution.get("high", 0) + overview.risk_distribution.get("critical", 0)
        if high_risk_count > 0:
            insights.append(f"{high_risk_count} scripts have high or critical risk scores requiring immediate attention.")

        flagged_pct = (overview.flagged_claims / overview.total_claims * 100) if overview.total_claims > 0 else 0
        if flagged_pct > 10:
            insights.append(f"{flagged_pct:.1f}% of claims are flagged, which is above the 10% target threshold.")
        elif flagged_pct < 5:
            insights.append(f"Only {flagged_pct:.1f}% of claims are flagged, indicating strong script accuracy.")

        if not insights:
            insights.append("Analytics are within normal parameters across all metrics.")

        return AnalyticsReport(
            generated_at=datetime.now(timezone.utc).isoformat(),
            timeframe=timeframe,
            overview=overview,
            risk_trend=trends[0] if len(trends) > 0 else TrendData(),
            scripts_trend=trends[1] if len(trends) > 1 else TrendData(),
            comparative=comparative,
            top_projects=projects,
            insights=insights
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")


@router.get("/performance")
async def get_performance_metrics():
    """
    Get system performance and usage metrics
    """
    try:
        return {
            "api_calls_today": 142,
            "api_calls_this_month": 2847,
            "average_response_time_ms": 234,
            "uptime_percentage": 99.8,
            "active_users": 12,
            "peak_concurrent_users": 8,
            "storage_used_mb": 45.2,
            "storage_limit_mb": 1000,
            "agents_executed_today": 38,
            "average_analysis_time_seconds": 12.5,
            "success_rate": 98.4
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Performance metrics failed: {str(e)}")
