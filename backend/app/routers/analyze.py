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
            timestamp=orchestrator_report.timestamp
        )
        
        # Schedule background tasks if needed
        if request.auto_mode and orchestrator_report.risk_assessment.overall_risk_score > 70:
            background_tasks.add_task(
                _send_high_risk_notification,
                orchestrator_report
            )
        
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
        
        # For now, since we don't have persistent storage, 
        # we'll return the most recent analysis results if report_id matches
        # In production, this would query a database
        
        # Check if orchestrator has recent results for this report_id
        if hasattr(orchestrator, 'recent_reports') and report_id in orchestrator.recent_reports:
            report = orchestrator.recent_reports[report_id]
            
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
        # This would integrate with notification service
        logger.info(f"High-risk report detected: {orchestrator_report.report_id} "
                   f"(Risk: {orchestrator_report.risk_assessment.overall_risk_score})")
        
        # Implement notification logic here
        # - Send Slack message
        # - Send email alert
        # - Create production issue ticket
        
    except Exception as e:
        logger.error(f"Failed to send high-risk notification: {str(e)}")