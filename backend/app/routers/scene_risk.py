"""
Scene Risk Router - Risk Heatmap data endpoint
Provides per-scene risk data for visual heatmap rendering
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter()


class SceneRiskHighlight(BaseModel):
    scene_number: int
    title: str
    location: str
    time_of_day: str
    risk_score: float = Field(ge=0.0, le=100.0)
    risk_level: str = Field(description="low, medium, high, critical")
    risk_factors: List[str] = Field(default_factory=list)
    legal_issues: List[Dict[str, Any]] = Field(default_factory=list)
    continuity_issues: List[Dict[str, Any]] = Field(default_factory=list)
    research_flags: List[Dict[str, Any]] = Field(default_factory=list)
    estimated_cost: float = 0.0
    text_start: int = Field(default=0, description="Start position in script text")
    text_end: int = Field(default=0, description="End position in script text")
    reasoning: str = Field(default="", description="AI reasoning for risk assessment")


class SceneRiskResponse(BaseModel):
    report_id: str
    total_scenes: int
    overall_risk_score: float
    scenes: List[SceneRiskHighlight]
    risk_distribution: Dict[str, int]  # {"low": 5, "medium": 3, "high": 2}
    generated_at: datetime


def _calculate_scene_risk(
    scene: Dict[str, Any],
    agent_results: Dict[str, Any],
    all_scenes: List[Dict[str, Any]]
) -> SceneRiskHighlight:
    """Calculate risk score for a single scene based on agent findings"""
    
    risk_score = 0.0
    risk_factors = []
    legal_issues = []
    continuity_issues = []
    research_flags = []
    reasoning_parts = []
    
    # Check legal agent results
    legal_result = agent_results.get("legal", {})
    if legal_result and legal_result.get("success"):
        legal_data = legal_result.get("data_summary", {})
        
        # Check copyright risks
        copyright_risks = legal_data.get("copyright_risks", [])
        for risk in copyright_risks:
            if _issue_affects_scene(risk, scene):
                risk_score += 25 if risk.get("severity") == "high" else 15
                legal_issues.append(risk)
                risk_factors.append(f"Copyright: {risk.get('type', 'unknown')}")
                reasoning_parts.append(f"Copyright risk identified: {risk.get('description', '')}")
        
        # Check trademark issues
        trademark_issues = legal_data.get("trademark_issues", [])
        for issue in trademark_issues:
            if _issue_affects_scene(issue, scene):
                risk_score += 20 if issue.get("severity") == "high" else 10
                legal_issues.append(issue)
                risk_factors.append(f"Trademark: {issue.get('brand', 'unknown')}")
                reasoning_parts.append(f"Trademark issue: {issue.get('description', '')}")
    
    # Check research agent results
    research_result = agent_results.get("research", {})
    if research_result and research_result.get("success"):
        research_data = research_result.get("data_summary", {})
        claims = research_data.get("claims", [])
        
        for claim in claims:
            if _claim_in_scene(claim, scene):
                if claim.get("verdict") == "flagged":
                    risk_score += 20
                    research_flags.append(claim)
                    risk_factors.append(f"Fact check flagged: {claim.get('text', '')[:50]}")
                    reasoning_parts.append(f"Research flagged claim: {claim.get('text', '')}")
    
    # Check continuity agent results
    continuity_result = agent_results.get("continuity", {})
    if continuity_result and continuity_result.get("success"):
        continuity_data = continuity_result.get("data_summary", {})
        
        character_issues = continuity_data.get("character_inconsistencies", [])
        for issue in character_issues:
            if _issue_affects_scene(issue, scene):
                risk_score += 15
                continuity_issues.append(issue)
                risk_factors.append(f"Character continuity: {issue.get('description', '')[:50]}")
                reasoning_parts.append(f"Character inconsistency: {issue.get('description', '')}")
        
        timeline_issues = continuity_data.get("timeline_issues", [])
        for issue in timeline_issues:
            if _issue_affects_scene(issue, scene):
                risk_score += 10
                continuity_issues.append(issue)
                risk_factors.append(f"Timeline: {issue.get('description', '')[:50]}")
                reasoning_parts.append(f"Timeline issue: {issue.get('description', '')}")
    
    # Cap risk score at 100
    risk_score = min(risk_score, 100.0)
    
    # Determine risk level
    if risk_score >= 70:
        risk_level = "critical"
    elif risk_score >= 50:
        risk_level = "high"
    elif risk_score >= 25:
        risk_level = "medium"
    else:
        risk_level = "low"
    
    # Get scene text positions
    text_start = scene.get("text_start", 0)
    text_end = scene.get("text_end", 0)
    
    # Build reasoning
    reasoning = " ".join(reasoning_parts) if reasoning_parts else f"Scene has {risk_level} overall risk."
    
    return SceneRiskHighlight(
        scene_number=scene.get("scene_number", 0),
        title=scene.get("title", "Untitled"),
        location=scene.get("location", "Unknown"),
        time_of_day=scene.get("time_of_day", "Unknown"),
        risk_score=round(risk_score, 1),
        risk_level=risk_level,
        risk_factors=risk_factors[:10],  # Limit factors
        legal_issues=legal_issues,
        continuity_issues=continuity_issues,
        research_flags=research_flags,
        estimated_cost=scene.get("estimated_cost", 0.0),
        text_start=text_start,
        text_end=text_end,
        reasoning=reasoning
    )


def _issue_affects_scene(issue: Dict[str, Any], scene: Dict[str, Any]) -> bool:
    """Check if an issue affects a specific scene"""
    # Simple heuristic based on scene number or text matching
    scene_num = scene.get("scene_number", 0)
    issue_text = str(issue.get("description", "")) + str(issue.get("content", ""))
    
    # Check if scene number is mentioned
    if f"scene {scene_num}" in issue_text.lower():
        return True
    
    # Check location matching
    scene_location = scene.get("location", "").lower()
    if scene_location and scene_location in issue_text.lower():
        return True
    
    # Check character matching
    scene_characters = scene.get("characters_present", [])
    for char in scene_characters:
        if char.lower() in issue_text.lower():
            return True
    
    # Default: distribute issues across scenes (simplified)
    return False


def _claim_in_scene(claim: Dict[str, Any], scene: Dict[str, Any]) -> bool:
    """Check if a claim is related to a scene"""
    location = claim.get("location", {})
    if isinstance(location, dict):
        claim_scene = location.get("scene_number")
        if claim_scene == scene.get("scene_number"):
            return True
    
    # Check text content
    claim_text = claim.get("text", "").lower()
    scene_title = scene.get("title", "").lower()
    scene_location = scene.get("location", "").lower()
    
    if scene_title and scene_title in claim_text:
        return True
    if scene_location and scene_location in claim_text:
        return True
    
    return False


@router.get("/scene-risk/{report_id}", response_model=SceneRiskResponse)
async def get_scene_risk_data(report_id: str, request: Request):
    """
    Get per-scene risk data for heatmap visualization
    Returns risk scores, factors, and reasoning for each scene
    """
    try:
        orchestrator = request.app.state.orchestrator
        if not orchestrator:
            raise HTTPException(status_code=503, detail="Analysis system not available")
        
        # Load report
        from .analyze import _load_report_from_storage
        report = await _load_report_from_storage(orchestrator, report_id)
        
        if not report:
            raise HTTPException(
                status_code=404,
                detail=f"Report {report_id} not found"
            )
        
        # Get scenes from report
        scenes = []
        if hasattr(report, 'scenes'):
            scenes = report.scenes
        
        # If no scenes in report, create placeholder
        if not scenes:
            scenes = [{"scene_number": 1, "title": "Full Script", "location": "N/A", "time_of_day": "N/A"}]
        
        # Build agent results dict for risk calculation
        agent_results = {}
        if hasattr(report, 'agent_results'):
            for agent_name, result in report.agent_results.items():
                agent_results[agent_name] = {
                    "success": result.success,
                    "data_summary": result.data if result.success else {}
                }
        
        # Calculate risk for each scene
        scene_risks = []
        for scene in scenes:
            scene_risk = _calculate_scene_risk(scene, agent_results, scenes)
            scene_risks.append(scene_risk)
        
        # Calculate risk distribution
        risk_distribution = {"low": 0, "medium": 0, "high": 0, "critical": 0}
        for risk in scene_risks:
            risk_distribution[risk.risk_level] = risk_distribution.get(risk.risk_level, 0) + 1
        
        # Overall risk score
        overall_risk = report.risk_assessment.overall_risk_score if hasattr(report, 'risk_assessment') else 50.0
        
        return SceneRiskResponse(
            report_id=report_id,
            total_scenes=len(scene_risks),
            overall_risk_score=overall_risk,
            scenes=scene_risks,
            risk_distribution=risk_distribution,
            generated_at=datetime.utcnow()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get scene risk data: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate scene risk data: {str(e)}"
        )


@router.get("/scene-risk/{report_id}/scene/{scene_number}")
async def get_single_scene_risk(report_id: str, scene_number: int, request: Request):
    """Get detailed risk data for a single scene"""
    try:
        orchestrator = request.app.state.orchestrator
        from .analyze import _load_report_from_storage
        report = await _load_report_from_storage(orchestrator, report_id)
        
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
        
        scenes = report.scenes if hasattr(report, 'scenes') else []
        target_scene = None
        
        for scene in scenes:
            if scene.get("scene_number") == scene_number:
                target_scene = scene
                break
        
        if not target_scene:
            raise HTTPException(status_code=404, detail=f"Scene {scene_number} not found")
        
        agent_results = {}
        if hasattr(report, 'agent_results'):
            for agent_name, result in report.agent_results.items():
                agent_results[agent_name] = {
                    "success": result.success,
                    "data_summary": result.data if result.success else {}
                }
        
        scene_risk = _calculate_scene_risk(target_scene, agent_results, scenes)
        
        return scene_risk
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
