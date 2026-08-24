"""
Analysis Router - Handles script analysis requests
Multi-agent orchestration endpoint
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Request, BackgroundTasks
from pydantic import BaseModel, Field

from ..models.agent_schemas import OrchestratorReport

logger = logging.getLogger(__name__)

router = APIRouter()


class AnalyzeRequest(BaseModel):
    """Request model for script analysis"""
    script_text: str = Field(..., min_length=10, max_length=50000, description="Script content to analyze")
    auto_mode: bool = Field(default=True, description="Enable automatic processing")
    agents: Optional[list[str]] = Field(default=None, description="Optional agent selection")
    priority: str = Field(default="normal", description="Processing priority")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context")


class AnalyzeResponse(BaseModel):
    """Response model for script analysis"""
    report_id: str
    processing_status: str
    risk_score: float
    agents_results: Dict[str, Any]
    auto_actions: Dict[str, Any]
    processing_time: float
    timestamp: datetime
    agent_timeline: list = []
    readiness_scores: Dict[str, Any] = {}
    agent_flow: list = []
    suggestions: list = []


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_script(
    request: AnalyzeRequest,
    fastapi_request: Request,
    background_tasks: BackgroundTasks
):
    """
    Multi-agent script analysis endpoint
    Orchestrates Director, Research, Legal, and Continuity agents
    """
    
    try:
        # Get orchestrator from app state
        orchestrator = fastapi_request.app.state.orchestrator
        if not orchestrator:
            raise HTTPException(status_code=503, detail="Multi-agent system not available")
        
        logger.info(f"Starting multi-agent analysis for {len(request.script_text)} characters")
        
        # Prepare analysis options
        analysis_options = {
            "priority": request.priority,
            "context": request.context or {},
            "auto_mode": request.auto_mode,
            "agents_requested": request.agents or ["director", "research", "legal", "continuity"]
        }
        
        # Run multi-agent orchestration
        orchestrator_report: OrchestratorReport = await orchestrator.analyze_script(
            script_text=request.script_text,
            options=analysis_options
        )
        
        # Format response
        response = AnalyzeResponse(
            report_id=orchestrator_report.report_id,
            processing_status="complete",
            risk_score=orchestrator_report.risk_assessment.overall_risk_score,
            agents_results={
                agent_name: {
                    "success": result.success,
                    "confidence": result.confidence_score,
                    "processing_time": result.processing_time,
                    "data_summary": _summarize_agent_data(agent_name, result.data) if result.success else None,
                    "error": result.error_message if not result.success else None
                }
                for agent_name, result in orchestrator_report.agent_results.items()
            },
            auto_actions=orchestrator_report.automation_actions,
            processing_time=orchestrator_report.processing_time,
            timestamp=orchestrator_report.timestamp,
            agent_timeline=[step.model_dump() for step in orchestrator_report.agent_timeline],
            readiness_scores=orchestrator_report.readiness_scores.model_dump(),
            agent_flow=[flow.model_dump() for flow in orchestrator_report.agent_flow],
            suggestions=[sug.model_dump() for sug in orchestrator_report.suggestions]
        )
        
        # Schedule background tasks if needed
        if request.auto_mode and orchestrator_report.risk_assessment.overall_risk_score > 70:
            background_tasks.add_task(
                _send_high_risk_notification,
                orchestrator_report
            )
        
        # Save report to persistent storage
        background_tasks.add_task(
            _save_report_to_storage,
            orchestrator_report
        )
        
        # Cache report for export and sharing
        try:
            from .export import cache_report
            cache_report(orchestrator_report.report_id, {
                "report_id": orchestrator_report.report_id,
                "risk_score": orchestrator_report.risk_assessment.overall_risk_score,
                "risk_level": orchestrator_report.risk_assessment.risk_level,
                "claims": [
                    {
                        "text": c.get("text", "") if isinstance(c, dict) else getattr(c, "text", ""),
                        "verdict": c.get("verdict", "unknown") if isinstance(c, dict) else getattr(c, "verdict", "unknown"),
                        "confidence": c.get("confidence", 0) if isinstance(c, dict) else getattr(c, "confidence", 0),
                    }
                    for c in (orchestrator_report.claims if hasattr(orchestrator_report, 'claims') else [])
                ],
                "agent_results": {
                    name: {
                        "success": r.success,
                        "confidence_score": r.confidence_score,
                        "processing_time": r.processing_time,
                    }
                    for name, r in orchestrator_report.agent_results.items()
                },
                "processing_time": orchestrator_report.processing_time,
            })
        except Exception as e:
            logger.warning(f"Failed to cache report: {e}")
        
        logger.info(f"Multi-agent analysis completed: {orchestrator_report.report_id}")
        return response
        
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}"
        )


@router.get("/report/{report_id}")
async def get_report(report_id: str, request: Request):
    """Get detailed report by ID"""
    
    try:
        # Get orchestrator from app state
        orchestrator = request.app.state.orchestrator
        if not orchestrator:
            raise HTTPException(status_code=503, detail="Multi-agent system not available")
        
        # Check persistent storage for report
        # Using file-based persistence to survive server restarts
        
        # Check both in-memory and file storage
        report = await _load_report_from_storage(orchestrator, report_id)
        
        if report:
            
            # Format the real orchestrator report for frontend
            claims = []
            
            # Extract claims from director agent results
            if 'director' in report.agent_results and report.agent_results['director'].success:
                director_data = report.agent_results['director'].data
                if director_data and 'claims' in director_data:
                    for claim in director_data['claims']:
                        claims.append({
                            "id": claim.get('id', 'unknown'),
                            "text": claim.get('text', 'No claim text'),
                            "type": claim.get('type', 'unknown'),
                            "verdict": "unverified",  # Default, would be set by research agent
                            "confidence": claim.get('confidence', 0.5),
                            "sources": [],  # Would be populated by research agent
                            "note": claim.get('context', 'Extracted from script'),
                            "location": claim.get('location_in_script', 'unknown')
                        })
            
            # If no real claims found, add a placeholder but with real data context
            if not claims:
                claims = [{
                    "id": "no_claims_extracted",
                    "text": "No factual claims could be extracted from this script",
                    "type": "system",
                    "verdict": "system_message", 
                    "confidence": 1.0,
                    "sources": [],
                    "note": f"Analysis completed but no claims found. Report ID: {report_id}"
                }]
            
            return {
                "report_id": report_id,
                "status": "completed",
                "claims": claims,
                "risk_assessment": {
                    "overall_risk_score": report.risk_assessment.overall_risk_score,
                    "risk_level": report.risk_assessment.risk_level
                },
                "agent_results": {
                    agent_name: {
                        "success": result.success,
                        "confidence": result.confidence_score,
                        "processing_time": result.processing_time,
                        "error": result.error_message if not result.success else None
                    }
                    for agent_name, result in report.agent_results.items()
                },
                "agent_timeline": [s.model_dump() for s in report.agent_timeline] if hasattr(report, 'agent_timeline') and report.agent_timeline else [],
                "readiness_scores": report.readiness_scores.model_dump() if hasattr(report, 'readiness_scores') else {},
                "agent_flow": [f.model_dump() for f in report.agent_flow] if hasattr(report, 'agent_flow') and report.agent_flow else [],
                "suggestions": [s.model_dump() for s in report.suggestions] if hasattr(report, 'suggestions') and report.suggestions else [],
                "processing_time": report.processing_time,
                "timestamp": report.timestamp.isoformat()
            }
        
        else:
            # Report not found - return 404
            raise HTTPException(
                status_code=404, 
                detail=f"Report {report_id} not found or has expired"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve report {report_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve report: {str(e)}"
        )


def _summarize_agent_data(agent_name: str, data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Summarize agent data for API response"""
    
    if not data:
        return {}
    
    if agent_name == "director":
        return {
            "claims_extracted": data.get("claims_extracted", 0),
            "claims_by_type": {k: len(v) for k, v in data.get("claims_by_type", {}).items()},
            "script_sections": len(data.get("script_sections", []))
        }
    
    elif agent_name == "research":
        return {
            "claims_researched": data.get("claims_researched", 0),
            "verified_count": len(data.get("verified_claims", [])),
            "flagged_count": len(data.get("flagged_claims", [])),
            "uncertain_count": len(data.get("uncertain_claims", [])),
            "sources_found": len(data.get("sources", []))
        }
    
    elif agent_name == "legal":
        return {
            "copyright_risks": len(data.get("copyright_risks", [])),
            "trademark_issues": len(data.get("trademark_issues", [])),
            "clearance_required": len(data.get("clearance_required", [])),
            "estimated_cost": data.get("estimated_clearance_cost", "unknown")
        }
    
    elif agent_name == "continuity":
        return {
            "character_issues": len(data.get("character_inconsistencies", [])),
            "timeline_issues": len(data.get("timeline_issues", [])),
            "location_issues": len(data.get("location_continuity", [])),
            "prop_issues": len(data.get("prop_tracking", []))
        }
    
    return {"summary": "Agent data available"}


async def _send_high_risk_notification(orchestrator_report: OrchestratorReport):
    """Background task to send notifications for high-risk reports"""
    
    try:
        from ..automation.notification_service import get_notification_service
        
        notification_service = get_notification_service()
        risk_score = orchestrator_report.risk_assessment.overall_risk_score
        
        logger.info(f"High-risk report detected: {orchestrator_report.report_id} "
                   f"(Risk: {risk_score})")
        
        # Send via NotificationService (Slack/webhook)
        await notification_service.send_high_risk_alert(orchestrator_report, threshold=70.0)
        
        # Also create in-app notification for the user
        from ..database.connection import SessionLocal
        from ..database.models import Notification
        from uuid import uuid4
        
        db = SessionLocal()
        try:
            # Determine urgency
            is_urgent = risk_score >= 85.0
            title = "🚨 Critical Risk Alert" if is_urgent else "⚠️ High Risk Alert"
            message = (
                f"Risk score: {risk_score:.1f}/100 ({orchestrator_report.risk_assessment.risk_level}). "
                f"{len(orchestrator_report.risk_assessment.critical_issues)} critical issues found."
            )
            
            notification = Notification(
                id=uuid4(),
                user_id="system",  # Will be updated with actual user when user auth is implemented
                type="high_risk",
                title=title,
                message=message,
                script_id=orchestrator_report.report_id,
                action_url=f"/report/{orchestrator_report.report_id}",
            )
            db.add(notification)
            db.commit()
            logger.info(f"In-app notification created for report {orchestrator_report.report_id}")
        finally:
            db.close()
        
    except Exception as e:
        logger.error(f"Failed to send high-risk notification: {str(e)}")


async def _load_report_from_storage(orchestrator, report_id: str):
    """Load report from in-memory cache or file storage"""
    
    # First check in-memory cache
    if hasattr(orchestrator, 'recent_reports') and report_id in orchestrator.recent_reports:
        return orchestrator.recent_reports[report_id]
    
    # Then check file storage (persistence across restarts)
    import os
    import json
    import aiofiles
    from datetime import datetime
    
    reports_dir = "data/reports"
    report_file = f"{reports_dir}/{report_id}.json"
    
    if os.path.exists(report_file):
        try:
            async with aiofiles.open(report_file, 'r') as f:
                report_data = json.loads(await f.read())
            
            # Convert back to OrchestratorReport object (simplified)
            from ..models.agent_schemas import OrchestratorReport, RiskAssessment, AgentResult
            from uuid import uuid4
            
            # Create mock report object with stored data
            class MockReport:
                def __init__(self, data):
                    self.report_id = data.get("report_id", report_id)
                    self.timestamp = datetime.fromisoformat(data.get("timestamp", datetime.now().isoformat()))
                    self.processing_time = data.get("processing_time", 0.0)
                    
                    # Create mock risk assessment
                    risk_data = data.get("risk_assessment", {})
                    self.risk_assessment = type('MockRiskAssessment', (), {
                        'overall_risk_score': risk_data.get("overall_risk_score", 50.0),
                        'risk_level': risk_data.get("risk_level", "medium")
                    })()
                    
                    # Create mock agent results
                    self.agent_results = {}
                    for agent_name, result_data in data.get("agent_results", {}).items():
                        self.agent_results[agent_name] = type('MockAgentResult', (), {
                            'success': result_data.get("success", True),
                            'confidence_score': result_data.get("confidence", 0.7),
                            'processing_time': result_data.get("processing_time", 0.0),
                            'data': result_data.get("data", {}),
                            'error_message': result_data.get("error", None)
                        })()
            
            return MockReport(report_data)
            
        except Exception as e:
            logger.warning(f"Failed to load report from file {report_file}: {str(e)}")
    
    return None


async def _save_report_to_storage(orchestrator_report):
    """Save report to file storage for persistence"""
    
    import os
    import json
    import aiofiles
    from pathlib import Path
    
    try:
        # Create reports directory
        reports_dir = Path("data/reports")
        reports_dir.mkdir(parents=True, exist_ok=True)
        
        # Serialize report data
        report_data = {
            "report_id": orchestrator_report.report_id,
            "timestamp": orchestrator_report.timestamp.isoformat(),
            "processing_time": orchestrator_report.processing_time,
            "risk_assessment": {
                "overall_risk_score": orchestrator_report.risk_assessment.overall_risk_score,
                "risk_level": orchestrator_report.risk_assessment.risk_level
            },
            "agent_results": {
                agent_name: {
                    "success": result.success,
                    "confidence": result.confidence_score, 
                    "processing_time": result.processing_time,
                    "data": result.data if result.success else {},
                    "error": result.error_message
                }
                for agent_name, result in orchestrator_report.agent_results.items()
            }
        }
        
        # Save to file
        report_file = reports_dir / f"{orchestrator_report.report_id}.json"
        async with aiofiles.open(report_file, 'w') as f:
            await f.write(json.dumps(report_data, indent=2))
        
        logger.info(f"Report {orchestrator_report.report_id} saved to persistent storage")
        
    except Exception as e:
        logger.error(f"Failed to save report to storage: {str(e)}")