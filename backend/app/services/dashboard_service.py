"""
Dashboard Service - Provides analytics and project management data
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from ..database.models import Script, Scene, Character, Comment, Notification, Analytics
from ..models.production_schemas import (
    ProjectSummary, AnalyticsSummary, TrendPoint, 
    DashboardResponse, ScriptStatus, RiskLevel
)

logger = logging.getLogger(__name__)

class DashboardService:
    """
    Service for generating dashboard data and analytics
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    async def get_dashboard_data(self, user_id: str) -> DashboardResponse:
        """
        Get comprehensive dashboard data for a user
        """
        try:
            # Get user's projects
            projects = await self._get_user_projects(user_id)
            
            # Get analytics summary
            analytics = await self._get_analytics_summary(user_id)
            
            # Get recent notifications
            notifications = await self._get_recent_notifications(user_id)
            
            # Get recent exports (placeholder for now)
            recent_exports = []
            
            return DashboardResponse(
                projects=projects,
                analytics=analytics,
                notifications=notifications,
                recent_exports=recent_exports
            )
            
        except Exception as e:
            logger.error(f"Dashboard data generation failed: {e}")
            return DashboardResponse(
                projects=[],
                analytics=AnalyticsSummary(),
                notifications=[],
                recent_exports=[]
            )
    
    async def _get_user_projects(self, user_id: str) -> List[ProjectSummary]:
        """Get user's project summaries"""
        try:
            # Query scripts with scene and character counts
            scripts_query = (
                self.db.query(
                    Script,
                    func.count(Scene.id).label('scene_count'),
                    func.count(Character.id).label('character_count')
                )
                .outerjoin(Scene)
                .outerjoin(Character)
                .filter(Script.user_id == user_id)
                .group_by(Script.id)
                .order_by(desc(Script.updated_at))
                .limit(20)  # Limit to most recent 20 projects
            )
            
            results = scripts_query.all()
            projects = []
            
            for script, scene_count, character_count in results:
                # Calculate issue counts based on risk score (simplified)
                issues = self._calculate_issue_counts(script.risk_score)
                
                # Calculate progress percentage (simplified)
                progress = self._calculate_progress_percentage(script)
                
                # Get team size (placeholder)
                team_size = self._get_team_size(script.id)
                
                project = ProjectSummary(
                    id=str(script.id),
                    title=script.title,
                    status=ScriptStatus(script.status),
                    risk_score=script.risk_score,
                    last_analyzed=script.updated_at,
                    scenes_count=scene_count or 0,
                    characters_count=character_count or 0,
                    issues=issues,
                    team_size=team_size,
                    progress_percentage=progress
                )
                projects.append(project)
            
            return projects
            
        except Exception as e:
            logger.error(f"Failed to get user projects: {e}")
            return []
    
    async def _get_analytics_summary(self, user_id: str) -> AnalyticsSummary:
        """Get analytics summary for dashboard"""
        try:
            # Total scripts
            total_scripts = self.db.query(Script).filter(Script.user_id == user_id).count()
            
            # Average risk score
            avg_risk = (
                self.db.query(func.avg(Script.risk_score))
                .filter(Script.user_id == user_id)
                .scalar()
            ) or 0.0
            
            # Scripts this month
            month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            scripts_this_month = (
                self.db.query(Script)
                .filter(Script.user_id == user_id)
                .filter(Script.created_at >= month_start)
                .count()
            )
            
            # Get trend data
            trends = await self._get_trend_data(user_id)
            
            # Top risk categories (simplified)
            top_risk_categories = await self._get_top_risk_categories(user_id)
            
            # Recent activity
            recent_activity = await self._get_recent_activity(user_id)
            
            return AnalyticsSummary(
                total_scripts=total_scripts,
                average_risk_score=round(avg_risk, 2),
                scripts_this_month=scripts_this_month,
                active_collaborators=0,  # Placeholder
                trends=trends,
                top_risk_categories=top_risk_categories,
                recent_activity=recent_activity
            )
            
        except Exception as e:
            logger.error(f"Failed to get analytics summary: {e}")
            return AnalyticsSummary()
    
    async def _get_recent_notifications(self, user_id: str, limit: int = 10):
        """Get recent notifications for user"""
        try:
            notifications = (
                self.db.query(Notification)
                .filter(Notification.user_id == user_id)
                .order_by(desc(Notification.created_at))
                .limit(limit)
                .all()
            )
            
            return [
                {
                    "id": str(notif.id),
                    "type": notif.type,
                    "title": notif.title,
                    "message": notif.message,
                    "read": notif.read,
                    "created_at": notif.created_at,
                    "action_url": notif.action_url
                }
                for notif in notifications
            ]
            
        except Exception as e:
            logger.error(f"Failed to get recent notifications: {e}")
            return []
    
    async def _get_trend_data(self, user_id: str, days: int = 30) -> List[TrendPoint]:
        """Get trend data for the past N days"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # Get scripts created per day
            scripts_by_day = (
                self.db.query(
                    func.date(Script.created_at).label('date'),
                    func.count(Script.id).label('count')
                )
                .filter(Script.user_id == user_id)
                .filter(Script.created_at >= start_date)
                .group_by(func.date(Script.created_at))
                .all()
            )
            
            trends = []
            for date, count in scripts_by_day:
                trends.append(TrendPoint(
                    date=datetime.combine(date, datetime.min.time()),
                    value=float(count),
                    metric="scripts_analyzed"
                ))
            
            return sorted(trends, key=lambda x: x.date)
            
        except Exception as e:
            logger.error(f"Failed to get trend data: {e}")
            return []
    
    async def _get_top_risk_categories(self, user_id: str) -> Dict[str, int]:
        """Get top risk categories (simplified implementation)"""
        try:
            # Group scripts by risk level
            risk_counts = {"low": 0, "medium": 0, "high": 0, "critical": 0}
            
            scripts = self.db.query(Script).filter(Script.user_id == user_id).all()
            
            for script in scripts:
                risk_score = script.risk_score
                if risk_score < 30:
                    risk_counts["low"] += 1
                elif risk_score < 60:
                    risk_counts["medium"] += 1
                elif risk_score < 85:
                    risk_counts["high"] += 1
                else:
                    risk_counts["critical"] += 1
            
            return risk_counts
            
        except Exception as e:
            logger.error(f"Failed to get risk categories: {e}")
            return {}
    
    async def _get_recent_activity(self, user_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Get recent user activity"""
        try:
            activities = []
            
            # Recent scripts
            recent_scripts = (
                self.db.query(Script)
                .filter(Script.user_id == user_id)
                .order_by(desc(Script.updated_at))
                .limit(limit)
                .all()
            )
            
            for script in recent_scripts:
                activities.append({
                    "type": "script_analyzed",
                    "description": f"Analyzed script: {script.title}",
                    "timestamp": script.updated_at,
                    "script_id": str(script.id)
                })
            
            # Recent comments
            recent_comments = (
                self.db.query(Comment)
                .filter(Comment.user_id == user_id)
                .order_by(desc(Comment.created_at))
                .limit(limit)
                .all()
            )
            
            for comment in recent_comments:
                activities.append({
                    "type": "comment_added",
                    "description": f"Added comment on script analysis",
                    "timestamp": comment.created_at,
                    "script_id": str(comment.script_id)
                })
            
            # Sort by timestamp and return latest
            activities.sort(key=lambda x: x["timestamp"], reverse=True)
            return activities[:limit]
            
        except Exception as e:
            logger.error(f"Failed to get recent activity: {e}")
            return []
    
    def _calculate_issue_counts(self, risk_score: float) -> Dict[str, int]:
        """Calculate issue counts based on risk score (simplified)"""
        if risk_score >= 85:
            return {"critical": 2, "high": 3, "medium": 2, "low": 1}
        elif risk_score >= 60:
            return {"critical": 0, "high": 2, "medium": 3, "low": 2}
        elif risk_score >= 30:
            return {"critical": 0, "high": 0, "medium": 2, "low": 3}
        else:
            return {"critical": 0, "high": 0, "medium": 0, "low": 1}
    
    def _calculate_progress_percentage(self, script: Script) -> float:
        """Calculate project progress percentage (simplified)"""
        # Simple calculation based on status
        status_progress = {
            "draft": 25.0,
            "in_review": 75.0,
            "production_ready": 100.0,
            "archived": 100.0
        }
        return status_progress.get(script.status, 0.0)
    
    def _get_team_size(self, script_id: str) -> int:
        """Get team size for a script (placeholder)"""
        # In real implementation, count team members
        return 1  # Just the owner for now
    
    async def search_projects(self, user_id: str, query: str, filters: Dict[str, Any] = None) -> List[ProjectSummary]:
        """Search user's projects"""
        try:
            scripts_query = self.db.query(Script).filter(Script.user_id == user_id)
            
            # Apply search query
            if query:
                scripts_query = scripts_query.filter(Script.title.ilike(f"%{query}%"))
            
            # Apply filters
            if filters:
                if filters.get("status"):
                    scripts_query = scripts_query.filter(Script.status == filters["status"])
                if filters.get("min_risk_score"):
                    scripts_query = scripts_query.filter(Script.risk_score >= filters["min_risk_score"])
                if filters.get("max_risk_score"):
                    scripts_query = scripts_query.filter(Script.risk_score <= filters["max_risk_score"])
            
            scripts = scripts_query.order_by(desc(Script.updated_at)).all()
            
            # Convert to ProjectSummary objects
            projects = []
            for script in scripts:
                scene_count = self.db.query(Scene).filter(Scene.script_id == script.id).count()
                character_count = self.db.query(Character).filter(Character.script_id == script.id).count()
                
                project = ProjectSummary(
                    id=str(script.id),
                    title=script.title,
                    status=ScriptStatus(script.status),
                    risk_score=script.risk_score,
                    last_analyzed=script.updated_at,
                    scenes_count=scene_count,
                    characters_count=character_count,
                    issues=self._calculate_issue_counts(script.risk_score),
                    team_size=self._get_team_size(script.id),
                    progress_percentage=self._calculate_progress_percentage(script)
                )
                projects.append(project)
            
            return projects
            
        except Exception as e:
            logger.error(f"Project search failed: {e}")
            return []
    
    async def get_project_analytics(self, user_id: str, timeframe: str = "month") -> Dict[str, Any]:
        """Get detailed project analytics"""
        try:
            # Calculate timeframe
            if timeframe == "week":
                start_date = datetime.now() - timedelta(weeks=1)
            elif timeframe == "month":
                start_date = datetime.now() - timedelta(days=30)
            elif timeframe == "year":
                start_date = datetime.now() - timedelta(days=365)
            else:
                start_date = datetime.now() - timedelta(days=30)
            
            scripts = (
                self.db.query(Script)
                .filter(Script.user_id == user_id)
                .filter(Script.created_at >= start_date)
                .all()
            )
            
            if not scripts:
                return {"message": "No data available for selected timeframe"}
            
            # Calculate metrics
            total_scripts = len(scripts)
            avg_risk_score = sum(s.risk_score for s in scripts) / total_scripts
            risk_distribution = self._get_risk_distribution(scripts)
            genre_distribution = self._get_genre_distribution(scripts)
            
            return {
                "timeframe": timeframe,
                "total_scripts": total_scripts,
                "average_risk_score": round(avg_risk_score, 2),
                "risk_distribution": risk_distribution,
                "genre_distribution": genre_distribution,
                "highest_risk_script": max(scripts, key=lambda x: x.risk_score).title if scripts else None,
                "lowest_risk_script": min(scripts, key=lambda x: x.risk_score).title if scripts else None
            }
            
        except Exception as e:
            logger.error(f"Analytics generation failed: {e}")
            return {"error": str(e)}
    
    def _get_risk_distribution(self, scripts: List[Script]) -> Dict[str, int]:
        """Get risk score distribution"""
        distribution = {"low": 0, "medium": 0, "high": 0, "critical": 0}
        
        for script in scripts:
            risk_score = script.risk_score
            if risk_score < 30:
                distribution["low"] += 1
            elif risk_score < 60:
                distribution["medium"] += 1
            elif risk_score < 85:
                distribution["high"] += 1
            else:
                distribution["critical"] += 1
        
        return distribution
    
    def _get_genre_distribution(self, scripts: List[Script]) -> Dict[str, int]:
        """Get genre distribution"""
        distribution = {}
        
        for script in scripts:
            genre = script.genre or "unknown"
            distribution[genre] = distribution.get(genre, 0) + 1
        
        return distribution