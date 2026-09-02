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
    user_id: Optional[str] = Field(default=None, description="User ID for per-user report storage")


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
            orchestrator_report,
            request.user_id
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


@router.get("/reports")
async def list_reports(request: Request, user_id: Optional[str] = None):
    """List reports from persistent storage, filtered by user_id if provided"""
    
    import os
    import json
    from pathlib import Path
    from datetime import datetime
    
    reports_dir = Path("data/reports")
    reports = []
    
    if reports_dir.exists():
        for report_file in sorted(reports_dir.glob("*.json"), key=os.path.getmtime, reverse=True):
            try:
                with open(report_file, 'r') as f:
                    data = json.load(f)
                
                # Filter by user_id if provided
                # Reports without user_id are legacy - only show when no user_id filter is active
                report_user_id = data.get("user_id")
                if user_id:
                    # User is logged in - only show reports belonging to this user
                    if report_user_id != user_id:
                        continue
                else:
                    # No user_id filter - skip reports that belong to other users
                    if report_user_id and report_user_id != "system":
                        continue
                
                # Count claims from agent results
                claims_count = 0
                flagged_count = 0
                if "agent_results" in data and "director" in data["agent_results"]:
                    director_data = data["agent_results"]["director"].get("data", {})
                    claims = director_data.get("claims", [])
                    claims_count = len(claims)
                
                # Count flagged from research agent
                if "agent_results" in data and "research" in data["agent_results"]:
                    research_data = data["agent_results"]["research"].get("data", {})
                    flagged_count = len(research_data.get("flagged_claims", []))
                
                risk_score = data.get("risk_assessment", {}).get("overall_risk_score", 0)
                
                reports.append({
                    "id": data.get("report_id", report_file.stem),
                    "title": f"Script Analysis - {data.get('report_id', report_file.stem)[:8]}",
                    "date": data.get("timestamp", datetime.now().isoformat()),
                    "claimCount": claims_count,
                    "flaggedCount": flagged_count,
                    "riskScore": risk_score,
                    "processingTime": data.get("processing_time", 0),
                    "status": "completed"
                })
            except Exception as e:
                logger.warning(f"Failed to read report file {report_file}: {str(e)}")
    
    return {"reports": reports, "total": len(reports)}


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
            
            # Build a lookup of researched claims with their verdicts
            research_verdicts = {}
            if 'research' in report.agent_results and report.agent_results['research'].success:
                research_data = report.agent_results['research'].data
                if research_data and 'claims' in research_data:
                    for rc in research_data['claims']:
                        claim_id = rc.get('id', '')
                        if claim_id:
                            research_verdicts[claim_id] = rc
            
            # Extract claims from director agent results, merge research verdicts
            if 'director' in report.agent_results and report.agent_results['director'].success:
                director_data = report.agent_results['director'].data
                if director_data and 'claims' in director_data:
                    for claim in director_data['claims']:
                        claim_id = claim.get('id', 'unknown')
                        # Check if research agent verified this claim
                        researched = research_verdicts.get(claim_id)
                        if researched:
                            claims.append({
                                "id": claim_id,
                                "text": researched.get('text', claim.get('text', 'No claim text')),
                                "type": claim.get('type', 'unknown'),
                                "verdict": researched.get('verdict', 'uncertain'),
                                "confidence": researched.get('confidence', claim.get('confidence', 0.5)),
                                "sources": researched.get('sources', []),
                                "note": researched.get('note', claim.get('context', 'Researched')),
                                "location": claim.get('location_in_script', 'unknown')
                            })
                        else:
                            claims.append({
                                "id": claim_id,
                                "text": claim.get('text', 'No claim text'),
                                "type": claim.get('type', 'unknown'),
                                "verdict": "unverified",
                                "confidence": claim.get('confidence', 0.5),
                                "sources": [],
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
            
            def _to_dump(obj):
                if hasattr(obj, 'model_dump'):
                    return obj.model_dump()
                return obj

            timeline_data = [_to_dump(s) for s in (getattr(report, 'agent_timeline', None) or [])]
            readiness_data = _to_dump(getattr(report, 'readiness_scores', None) or {})
            flow_data = [_to_dump(f) for f in (getattr(report, 'agent_flow', None) or [])]
            suggestions_data = [_to_dump(s) for s in (getattr(report, 'suggestions', None) or [])]
            scenes_data = getattr(report, 'scenes', []) or []
            chars_data = getattr(report, 'characters', []) or []
            scene_stats_data = getattr(report, 'scene_statistics', {}) or {}
            char_stats_data = getattr(report, 'character_statistics', {}) or {}
            continuity_data = getattr(report, 'continuity_issues', []) or []

            return {
                "report_id": report_id,
                "status": "completed",
                "script_text": getattr(report, 'script_text', '') or "",
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
                "agent_timeline": timeline_data,
                "readiness_scores": readiness_data,
                "agent_flow": flow_data,
                "suggestions": suggestions_data,
                "scenes": scenes_data,
                "characters": chars_data,
                "scene_statistics": scene_stats_data,
                "character_statistics": char_stats_data,
                "continuity_issues": continuity_data,
                "processing_time": getattr(report, 'processing_time', 0.0),
                "timestamp": report.timestamp.isoformat() if hasattr(report.timestamp, 'isoformat') else str(report.timestamp)
            }
        
        elif report_id.startswith("sample-"):
            return _generate_sample_report_response(report_id)
        
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


@router.get("/risk-detail/{report_id}")
async def get_risk_detail(report_id: str, request: Request):
    """Get full risk assessment details including factors, critical issues, and recommended actions"""
    try:
        orchestrator = getattr(request.app.state, 'orchestrator', None)
        report = await _load_report_from_storage(orchestrator, report_id)
        
        if not report and report_id.startswith("sample-"):
            sample_data = _generate_sample_report_response(report_id)
            return {
                "report_id": report_id,
                "risk_assessment": sample_data["risk_assessment"],
                "critical_issues": [
                    {
                        "type": "factual",
                        "severity": "high",
                        "description": c["text"],
                        "location_in_script": c.get("location", ""),
                        "suggested_action": c.get("note", ""),
                        "estimated_cost_impact": "$0",
                        "urgency": "immediate"
                    }
                    for c in sample_data.get("claims", [])
                    if c.get("verdict") == "flagged"
                ],
                "agent_flow": sample_data.get("agent_flow", []),
                "suggestions": sample_data.get("suggestions", []),
                "readiness_scores": sample_data.get("readiness_scores", None),
            }

        if report:
            # Build critical issues list from agent results
            critical_issues = []
            agent_results = getattr(report, 'agent_results', {}) or {}
            
            # Helper to get result data safely
            def _get_data(result):
                if not result:
                    return {}
                if hasattr(result, 'data'):
                    return result.data or {}
                if isinstance(result, dict):
                    return result.get('data', {}) or {}
                return {}
            
            # Extract issues from legal agent
            legal_result = agent_results.get("legal")
            if legal_result:
                data = _get_data(legal_result)
                for risk in (data.get("copyright_risks", []) or []) + (data.get("trademark_issues", []) or []):
                    if isinstance(risk, dict):
                        critical_issues.append({
                            "type": "legal",
                            "severity": risk.get("severity", "medium"),
                            "description": risk.get("content", risk.get("description", "")),
                            "location_in_script": "",
                            "suggested_action": risk.get("clearance_action", risk.get("suggested_fix", "")),
                            "estimated_cost_impact": risk.get("estimated_cost", ""),
                            "urgency": "before_production"
                        })
                for privacy in data.get("privacy_concerns", []) or []:
                    if isinstance(privacy, dict):
                        critical_issues.append({
                            "type": "legal",
                            "severity": privacy.get("severity", "medium"),
                            "description": privacy.get("description", str(privacy)),
                            "location_in_script": "",
                            "suggested_action": "",
                            "estimated_cost_impact": "",
                            "urgency": "before_production"
                        })
            
            # Extract issues from continuity agent
            cont_result = agent_results.get("continuity")
            if cont_result:
                data = _get_data(cont_result)
                for issue in (data.get("character_inconsistencies", []) or []) + (data.get("timeline_issues", []) or []):
                    if isinstance(issue, dict):
                        critical_issues.append({
                            "type": "continuity",
                            "severity": issue.get("severity", "medium"),
                            "description": issue.get("description", ""),
                            "location_in_script": issue.get("location", ""),
                            "suggested_action": issue.get("suggested_fix", ""),
                            "estimated_cost_impact": "",
                            "urgency": "before_production"
                        })
            
            # Extract issues from research agent (flagged claims)
            research_result = agent_results.get("research")
            if research_result:
                data = _get_data(research_result)
                for claim in data.get("flagged_claims", []) or []:
                    if isinstance(claim, dict):
                        critical_issues.append({
                            "type": "factual",
                            "severity": "high",
                            "description": f"Flagged claim: {claim.get('text', '')[:100]}",
                            "location_in_script": claim.get("location_in_script", ""),
                            "suggested_action": claim.get("note", "Verify with reliable sources"),
                            "estimated_cost_impact": "",
                            "urgency": "immediate"
                        })
            
            # Extract issues from director agent (claims)
            director_result = agent_results.get("director")
            if director_result:
                data = _get_data(director_result)
                for claim in data.get("claims", []) or []:
                    if isinstance(claim, dict) and claim.get("confidence", 1) < 0.5:
                        critical_issues.append({
                            "type": "factual",
                            "severity": "medium",
                            "description": f"Low-confidence claim: {claim.get('text', '')[:100]}",
                            "location_in_script": claim.get("location_in_script", ""),
                            "suggested_action": "Research and verify",
                            "estimated_cost_impact": "",
                            "urgency": "nice_to_fix"
                        })
            
            # Get agent flow data for confidence
            def _to_dump(obj):
                if hasattr(obj, 'model_dump'):
                    return obj.model_dump()
                return obj

            agent_flow = [_to_dump(f) for f in (getattr(report, 'agent_flow', []) or [])]
            suggestions = [_to_dump(s) for s in (getattr(report, 'suggestions', []) or [])]
            readiness = _to_dump(getattr(report, 'readiness_scores', None))
            
            risk_obj = getattr(report, 'risk_assessment', None)
            if hasattr(risk_obj, 'model_dump'):
                risk_dict = risk_obj.model_dump()
            elif isinstance(risk_obj, dict):
                risk_dict = risk_obj
            else:
                risk_dict = {
                    "overall_risk_score": getattr(risk_obj, 'overall_risk_score', 50.0),
                    "risk_level": getattr(risk_obj, 'risk_level', "medium"),
                    "risk_factors": [],
                    "critical_issues": [],
                    "recommended_actions": [],
                    "confidence": 0.8
                }
            
            return {
                "report_id": report_id,
                "risk_assessment": risk_dict,
                "critical_issues": critical_issues,
                "agent_flow": agent_flow,
                "suggestions": suggestions,
                "readiness_scores": readiness,
            }
        
        else:
            raise HTTPException(status_code=404, detail=f"Report {report_id} not found")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get risk detail for {report_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get risk detail: {str(e)}")


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

    elif agent_name == "storyboard":
        return {
            "total_frames": data.get("total_frames", 0),
            "successful_frames": data.get("successful_frames", 0),
            "failed_frames": data.get("failed_frames", 0),
            "model_used": data.get("model_used", "unknown")
        }

    elif agent_name == "tts":
        return {
            "total_scenes": data.get("total_scenes", 0),
            "successful_scenes": data.get("successful_scenes", 0),
            "total_duration": data.get("total_duration", 0),
            "voice_count": len(data.get("voice_map", {}))
        }

    elif agent_name == "schedule":
        return {
            "total_shoot_days": data.get("total_shoot_days", 0),
            "total_pages": data.get("total_pages", "0"),
            "company_moves": data.get("company_moves_total", 0),
            "contingency_days": data.get("contingency_days", 0),
        }

    elif agent_name == "stakeholder":
        return {
            "roles_analyzed": data.get("roles_analyzed", 0),
            "overall_readiness": data.get("overall_readiness", 0),
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
                id=str(uuid4()),
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


def _generate_sample_report_response(report_id: str) -> Dict[str, Any]:
    """Generate high-quality fallback data for demo and sample reports"""
    from datetime import datetime, timezone
    
    samples = {
        "sample-action-thriller": {
            "title": "Urban Strike",
            "risk_score": 78.0,
            "risk_level": "high",
            "script_text": "INT. ABANDONED WAREHOUSE - NIGHT\n\nSARAH CHEN (30s) checks her vintage Rolex Submariner. We have four minutes before LAPD responds.\n\nEXT. DOWNTOWN LOS ANGELES - CONTINUOUS\n\nPolice cruisers race down Spring Street past the Walt Disney Concert Hall, designed by Frank Gehry.",
            "claims": [
                {
                    "id": "claim_sample_1",
                    "text": "Average LAPD emergency response time in Downtown LA is 4 minutes",
                    "type": "factual",
                    "verdict": "flagged",
                    "confidence": 0.88,
                    "sources": [
                        {"title": "LAPD Response Time Statistics 2023", "url": "https://www.lapdonline.org/reports", "credibility": 0.95},
                        {"title": "LA City Emergency Response Audit", "url": "https://controller.lacity.gov", "credibility": 0.9}
                    ],
                    "note": "Actual LAPD priority response time averages 6.2 minutes.",
                    "location": "Scene 1, line 3"
                },
                {
                    "id": "claim_sample_2",
                    "text": "Walt Disney Concert Hall was designed by Frank Gehry",
                    "type": "factual",
                    "verdict": "verified",
                    "confidence": 0.98,
                    "sources": [
                        {"title": "Los Angeles Conservancy", "url": "https://www.laconservancy.org/locations/walt-disney-concert-hall", "credibility": 0.95}
                    ],
                    "note": "Verified: Completed in 2003 by architect Frank Gehry.",
                    "location": "Scene 2, line 2"
                },
                {
                    "id": "claim_sample_3",
                    "text": "Rolex Submariner reference in dialogue and close-up",
                    "type": "licensing",
                    "verdict": "flagged",
                    "confidence": 0.92,
                    "sources": [
                        {"title": "Rolex Trademark Guidelines", "url": "https://www.rolex.com", "credibility": 0.95}
                    ],
                    "note": "Trademark clearance required for prominent logo depiction in prop.",
                    "location": "Scene 1, line 2"
                }
            ],
            "scenes": [
                {"scene_number": 1, "heading": "INT. ABANDONED WAREHOUSE - NIGHT", "location": "ABANDONED WAREHOUSE", "time": "NIGHT", "characters": ["SARAH CHEN", "MARCUS"], "page_length": 1.2},
                {"scene_number": 2, "heading": "EXT. DOWNTOWN LOS ANGELES - CONTINUOUS", "location": "DOWNTOWN LOS ANGELES", "time": "NIGHT", "characters": ["POLICE UNITS"], "page_length": 0.8}
            ],
            "characters": [
                {"name": "SARAH CHEN", "role": "Team Leader", "dialogue_count": 8, "scenes": [1]},
                {"name": "MARCUS", "role": "Demolitions Expert", "dialogue_count": 4, "scenes": [1]}
            ]
        }
    }
    
    data = samples.get(report_id, samples["sample-action-thriller"])
    now = datetime.now(timezone.utc)
    
    return {
        "report_id": report_id,
        "status": "completed",
        "script_text": data["script_text"],
        "claims": data["claims"],
        "risk_assessment": {
            "overall_risk_score": data["risk_score"],
            "risk_level": data["risk_level"]
        },
        "agent_results": {
            "director": {"success": True, "confidence": 0.9, "processing_time": 1.2, "error": None},
            "research": {"success": True, "confidence": 0.88, "processing_time": 2.4, "error": None},
            "legal": {"success": True, "confidence": 0.92, "processing_time": 1.8, "error": None},
            "continuity": {"success": True, "confidence": 0.85, "processing_time": 1.1, "error": None}
        },
        "agent_timeline": [
            {"agent": "director", "status": "complete", "duration_seconds": 1.2, "confidence": 0.9, "summary": "Extracted 3 production claims"},
            {"agent": "research", "status": "complete", "duration_seconds": 2.4, "confidence": 0.88, "summary": "Verified claims using Parallel Search API"},
            {"agent": "legal", "status": "complete", "duration_seconds": 1.8, "confidence": 0.92, "summary": "Found 1 trademark clearance item"},
            {"agent": "continuity", "status": "complete", "duration_seconds": 1.1, "confidence": 0.85, "summary": "No timeline breaks detected"}
        ],
        "readiness_scores": {
            "overall": 72.0,
            "factual_accuracy": 65.0,
            "legal_clearance": 70.0,
            "continuity": 90.0,
            "budget_feasibility": 80.0
        },
        "agent_flow": [
            {"step": 1, "agent": "Director Agent", "description": "Screenplay parsed & claims isolated"},
            {"step": 2, "agent": "Parallel Research Agent", "description": "Live web research executed"},
            {"step": 3, "agent": "Legal Agent", "description": "Trademark clearance assessed"},
            {"step": 4, "agent": "Studio Orchestrator", "description": "Risk matrix compiled"}
        ],
        "suggestions": [
            {"id": "sug_1", "type": "script_fix", "title": "Adjust LAPD response dialogue", "description": "Change 'four minutes' to 'six minutes' for realism or use fictional tactical unit."},
            {"id": "sug_2", "type": "clearance", "title": "Obtain Rolex clearance or use generic prop", "description": "Clear Rolex Submariner reference with brand rep or swap to unbranded tactical watch."}
        ],
        "scenes": data["scenes"],
        "characters": data["characters"],
        "scene_statistics": {"total_scenes": len(data["scenes"]), "interior_count": 1, "exterior_count": 1, "night_count": 2, "day_count": 0},
        "character_statistics": {"total_characters": len(data["characters"])},
        "continuity_issues": [],
        "processing_time": 4.5,
        "timestamp": now.isoformat()
    }


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
                content = await f.read()
            report_data = json.loads(content)
            
            class MockReport:
                def __init__(self, data):
                    self.report_id = data.get("report_id", report_id)
                    self.timestamp = datetime.fromisoformat(data.get("timestamp", datetime.now().isoformat()))
                    self.processing_time = data.get("processing_time", 0.0)
                    self.script_text = data.get("script_text", "")
                    self.scenes = data.get("scenes", [])
                    self.characters = data.get("characters", [])
                    self.scene_statistics = data.get("scene_statistics", {})
                    self.character_statistics = data.get("character_statistics", {})
                    self.continuity_issues = data.get("continuity_issues", [])
                    self.agent_timeline = data.get("agent_timeline", [])
                    self.readiness_scores = data.get("readiness_scores", {})
                    self.agent_flow = data.get("agent_flow", [])
                    self.suggestions = data.get("suggestions", [])
                    
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


async def _save_report_to_storage(orchestrator_report, user_id: str = None):
    """Save report to file storage for persistence"""
    
    import os
    import json
    import aiofiles
    from pathlib import Path
    
    try:
        # Create reports directory
        reports_dir = Path("data/reports")
        reports_dir.mkdir(parents=True, exist_ok=True)
        
        def _dump_item(item):
            if hasattr(item, 'model_dump'):
                return item.model_dump()
            return item

        # Serialize report data
        report_data = {
            "report_id": orchestrator_report.report_id,
            "user_id": user_id,
            "timestamp": orchestrator_report.timestamp.isoformat(),
            "processing_time": orchestrator_report.processing_time,
            "script_text": getattr(orchestrator_report, 'script_text', ''),
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
            },
            "scenes": getattr(orchestrator_report, 'scenes', []),
            "characters": getattr(orchestrator_report, 'characters', []),
            "scene_statistics": getattr(orchestrator_report, 'scene_statistics', {}),
            "character_statistics": getattr(orchestrator_report, 'character_statistics', {}),
            "continuity_issues": getattr(orchestrator_report, 'continuity_issues', []),
            "agent_timeline": [_dump_item(s) for s in (getattr(orchestrator_report, 'agent_timeline', None) or [])],
            "readiness_scores": _dump_item(getattr(orchestrator_report, 'readiness_scores', {})),
            "agent_flow": [_dump_item(f) for f in (getattr(orchestrator_report, 'agent_flow', None) or [])],
            "suggestions": [_dump_item(s) for s in (getattr(orchestrator_report, 'suggestions', None) or [])],
        }
        
        # Pre-serialize to JSON with default=str to safely serialize datetime and nested models
        json_content = json.dumps(report_data, indent=2, default=str)
        
        # Save to file
        report_file = reports_dir / f"{orchestrator_report.report_id}.json"
        async with aiofiles.open(report_file, 'w') as f:
            await f.write(json_content)
        
        logger.info(f"Report {orchestrator_report.report_id} saved to persistent storage")
        
    except Exception as e:
        logger.error(f"Failed to save report to storage: {str(e)}")