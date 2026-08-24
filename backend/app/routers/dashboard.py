"""
Dashboard API endpoints for project management and analytics
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional

from ..database.connection import get_db
from ..services.dashboard_service import DashboardService
from ..models.production_schemas import DashboardResponse, ProjectSummary

router = APIRouter()

@router.get("/", response_model=DashboardResponse)
async def get_dashboard(
    user_id: str = Query(..., description="User ID"),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive dashboard data including projects, analytics, and notifications
    """
    try:
        dashboard_service = DashboardService(db)
        dashboard_data = await dashboard_service.get_dashboard_data(user_id)
        return dashboard_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Dashboard data retrieval failed: {str(e)}")

@router.get("/projects", response_model=List[ProjectSummary])
async def get_projects(
    user_id: str = Query(..., description="User ID"),
    search: Optional[str] = Query(None, description="Search query for project titles"),
    status: Optional[str] = Query(None, description="Filter by project status"),
    min_risk: Optional[float] = Query(None, description="Minimum risk score"),
    max_risk: Optional[float] = Query(None, description="Maximum risk score"),
    limit: Optional[int] = Query(20, description="Maximum number of results"),
    db: Session = Depends(get_db)
):
    """
    Get user's projects with optional search and filtering
    """
    try:
        dashboard_service = DashboardService(db)
        
        # Build filters
        filters = {}
        if status:
            filters["status"] = status
        if min_risk is not None:
            filters["min_risk_score"] = min_risk
        if max_risk is not None:
            filters["max_risk_score"] = max_risk
        
        projects = await dashboard_service.search_projects(
            user_id=user_id,
            query=search or "",
            filters=filters
        )
        
        return projects[:limit] if limit else projects
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Project retrieval failed: {str(e)}")

@router.get("/analytics")
async def get_analytics(
    user_id: str = Query(..., description="User ID"),
    timeframe: str = Query("month", description="Analytics timeframe: week, month, year"),
    db: Session = Depends(get_db)
):
    """
    Get detailed analytics for user's projects
    """
    try:
        dashboard_service = DashboardService(db)
        analytics = await dashboard_service.get_project_analytics(user_id, timeframe)
        return analytics
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analytics retrieval failed: {str(e)}")

@router.get("/stats")
async def get_quick_stats(
    user_id: str = Query(..., description="User ID"),
    db: Session = Depends(get_db)
):
    """
    Get quick statistics for dashboard widgets
    """
    try:
        dashboard_service = DashboardService(db)
        dashboard_data = await dashboard_service.get_dashboard_data(user_id)
        
        return {
            "total_scripts": dashboard_data.analytics.total_scripts,
            "average_risk_score": dashboard_data.analytics.average_risk_score,
            "scripts_this_month": dashboard_data.analytics.scripts_this_month,
            "active_projects": len([p for p in dashboard_data.projects if p.status != "archived"]),
            "high_risk_projects": len([p for p in dashboard_data.projects if p.risk_score > 70]),
            "unread_notifications": len([n for n in dashboard_data.notifications if not n.get("read", False)])
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stats retrieval failed: {str(e)}")

@router.get("/recent-activity")
async def get_recent_activity(
    user_id: str = Query(..., description="User ID"),
    limit: int = Query(10, description="Number of recent activities to return"),
    db: Session = Depends(get_db)
):
    """
    Get recent user activity feed
    """
    try:
        dashboard_service = DashboardService(db)
        activity = await dashboard_service._get_recent_activity(user_id, limit)
        return {"activities": activity}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Activity retrieval failed: {str(e)}")

@router.get("/risk-breakdown")
async def get_risk_breakdown(
    user_id: str = Query(..., description="User ID"),
    db: Session = Depends(get_db)
):
    """
    Get detailed risk breakdown across all projects
    """
    try:
        dashboard_service = DashboardService(db)
        dashboard_data = await dashboard_service.get_dashboard_data(user_id)
        
        # Calculate detailed risk metrics
        projects = dashboard_data.projects
        if not projects:
            return {"message": "No projects found"}
        
        risk_scores = [p.risk_score for p in projects]
        total_issues = {
            "critical": sum(p.issues.get("critical", 0) for p in projects),
            "high": sum(p.issues.get("high", 0) for p in projects),
            "medium": sum(p.issues.get("medium", 0) for p in projects),
            "low": sum(p.issues.get("low", 0) for p in projects)
        }
        
        return {
            "average_risk_score": round(sum(risk_scores) / len(risk_scores), 2),
            "highest_risk_score": max(risk_scores),
            "lowest_risk_score": min(risk_scores),
            "total_issues": total_issues,
            "risk_distribution": dashboard_data.analytics.top_risk_categories,
            "projects_by_risk": {
                "low": len([p for p in projects if p.risk_score < 30]),
                "medium": len([p for p in projects if 30 <= p.risk_score < 60]),
                "high": len([p for p in projects if 60 <= p.risk_score < 85]),
                "critical": len([p for p in projects if p.risk_score >= 85])
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Risk breakdown failed: {str(e)}")

@router.post("/project/{project_id}/update-status")
async def update_project_status(
    project_id: str,
    status: str,
    user_id: str = Query(..., description="User ID"),
    db: Session = Depends(get_db)
):
    """
    Update project status
    """
    try:
        from ..database.models import Script
        
        # Verify user owns the project
        script = db.query(Script).filter(
            Script.id == project_id,
            Script.user_id == user_id
        ).first()
        
        if not script:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Update status
        valid_statuses = ["draft", "in_review", "production_ready", "archived"]
        if status not in valid_statuses:
            raise HTTPException(status_code=400, detail="Invalid status")
        
        script.status = status
        db.commit()
        
        return {"message": f"Project status updated to {status}"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Status update failed: {str(e)}")

@router.delete("/project/{project_id}")
async def delete_project(
    project_id: str,
    user_id: str = Query(..., description="User ID"),
    db: Session = Depends(get_db)
):
    """
    Delete a project (soft delete by archiving)
    """
    try:
        from ..database.models import Script
        
        # Verify user owns the project
        script = db.query(Script).filter(
            Script.id == project_id,
            Script.user_id == user_id
        ).first()
        
        if not script:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Soft delete by archiving
        script.status = "archived"
        db.commit()
        
        return {"message": "Project archived successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Project deletion failed: {str(e)}")

@router.get("/trends")
async def get_trends(
    user_id: str = Query(..., description="User ID"),
    metric: str = Query("scripts_analyzed", description="Metric to track: scripts_analyzed, risk_scores"),
    days: int = Query(30, description="Number of days to include"),
    db: Session = Depends(get_db)
):
    """
    Get trend data for charts and analytics
    """
    try:
        dashboard_service = DashboardService(db)
        trends = await dashboard_service._get_trend_data(user_id, days)
        
        # Filter by metric if specified
        if metric != "scripts_analyzed":
            trends = [t for t in trends if t.metric == metric]
        
        return {
            "metric": metric,
            "timeframe_days": days,
            "data_points": len(trends),
            "trends": [
                {
                    "date": t.date.isoformat(),
                    "value": t.value,
                    "metric": t.metric
                }
                for t in trends
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Trends retrieval failed: {str(e)}")