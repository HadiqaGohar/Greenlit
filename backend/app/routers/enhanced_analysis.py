"""
Enhanced Analysis API endpoints with scene-by-scene breakdown and character bible
"""

import logging
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from ..database.connection import get_db
from ..services.scene_parser import parse_screenplay
from ..services.character_extractor import extract_characters
from ..services.scene_risk_analyzer import analyze_scene_risks
from ..services.character_bible_generator import generate_character_bible
from ..agents.orchestrator import AgentOrchestrator

logger = logging.getLogger(__name__)
router = APIRouter()

class EnhancedAnalysisRequest(BaseModel):
    script_text: str
    title: str
    options: Dict[str, Any] = {}
    include_scenes: bool = True
    include_characters: bool = True
    include_risk_analysis: bool = True
    budget_tier: str = "medium"  # low, medium, high

class SceneAnalysisResponse(BaseModel):
    scene_number: int
    title: str
    location: str
    time_of_day: str
    characters_present: List[str]
    risk_score: float
    complexity_level: str
    estimated_cost: Dict[str, float]
    production_notes: List[str]
    required_clearances: List[str]

class EnhancedAnalysisResponse(BaseModel):
    report_id: str
    script_analysis: Dict[str, Any]  # Original multi-agent analysis
    scene_breakdown: List[SceneAnalysisResponse] = []
    character_bible: Dict[str, Any] = {}
    risk_summary: Dict[str, Any] = {}
    production_insights: Dict[str, Any] = {}
    processing_time: float

@router.post("/enhanced-analyze", response_model=EnhancedAnalysisResponse)
async def enhanced_analyze(
    request: EnhancedAnalysisRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Perform enhanced script analysis with scene breakdown and character bible
    """
    try:
        # Get orchestrator instance
        orchestrator = AgentOrchestrator()
        
        # Perform standard multi-agent analysis
        standard_analysis = await orchestrator.analyze_script(
            script_text=request.script_text,
            options=request.options
        )
        
        # Parse screenplay into scenes
        scenes, scene_stats = parse_screenplay(request.script_text)
        
        # Extract characters
        characters, continuity_issues, char_stats = extract_characters(scenes, request.script_text)
        
        # Scene-by-scene risk analysis
        scene_analyses = []
        if request.include_risk_analysis:
            scene_risk_analyses = analyze_scene_risks(
                scenes=scenes,
                agent_findings=standard_analysis.agent_results,
                budget_tier=request.budget_tier
            )
            
            for analysis in scene_risk_analyses:
                scene_analyses.append(SceneAnalysisResponse(
                    scene_number=analysis.scene_number,
                    title=scenes[analysis.scene_number - 1].title if analysis.scene_number <= len(scenes) else "Unknown",
                    location=scenes[analysis.scene_number - 1].location if analysis.scene_number <= len(scenes) else "Unknown",
                    time_of_day=scenes[analysis.scene_number - 1].time_of_day if analysis.scene_number <= len(scenes) else "DAY",
                    characters_present=scenes[analysis.scene_number - 1].characters_present if analysis.scene_number <= len(scenes) else [],
                    risk_score=analysis.overall_risk_score,
                    complexity_level=analysis.complexity_level,
                    estimated_cost=analysis.cost_estimates,
                    production_notes=analysis.production_notes,
                    required_clearances=analysis.required_clearances
                ))
        
        # Generate character bible
        character_bible_data = {}
        if request.include_characters:
            character_bible = generate_character_bible(scenes, request.script_text)
            character_bible_data = {
                "characters": {
                    name: {
                        "name": profile.name,
                        "character_type": profile.character_type,
                        "first_appearance": profile.first_appearance,
                        "total_scenes": profile.total_scenes,
                        "descriptions": profile.descriptions[:3],  # Limit for API response
                        "relationships": dict(profile.relationships),
                        "scene_appearances": profile.scene_appearances
                    }
                    for name, profile in character_bible.characters.items()
                },
                "production_notes": character_bible.production_notes,
                "casting_suggestions": character_bible.casting_suggestions,
                "continuity_issues": continuity_issues
            }
        
        # Risk summary across all scenes
        risk_summary = _calculate_risk_summary(scene_analyses, standard_analysis)
        
        # Production insights
        production_insights = _generate_production_insights(
            scenes, characters, scene_analyses, scene_stats, char_stats
        )
        
        response = EnhancedAnalysisResponse(
            report_id=standard_analysis.report_id,
            script_analysis={
                "agent_results": {
                    agent_type: {
                        "success": result.success,
                        "confidence_score": result.confidence_score,
                        "processing_time": result.processing_time,
                        "data_summary": _summarize_agent_data(result.data) if result.data else {}
                    }
                    for agent_type, result in standard_analysis.agent_results.items()
                },
                "risk_assessment": {
                    "overall_risk_score": standard_analysis.risk_assessment.overall_risk_score,
                    "risk_level": standard_analysis.risk_assessment.risk_level,
                    "critical_issues": len(standard_analysis.risk_assessment.critical_issues),
                    "recommended_actions": standard_analysis.risk_assessment.recommended_actions
                }
            },
            scene_breakdown=scene_analyses,
            character_bible=character_bible_data,
            risk_summary=risk_summary,
            production_insights=production_insights,
            processing_time=standard_analysis.processing_time
        )
        
        # Save to database in background
        background_tasks.add_task(_save_enhanced_analysis, db, request, response)
        
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Enhanced analysis failed: {str(e)}"
        )

@router.get("/scene-breakdown/{report_id}")
async def get_scene_breakdown(
    report_id: str,
    db: Session = Depends(get_db)
):
    """
    Get detailed scene breakdown for a report
    """
    try:
        # In production, fetch from database
        # For now, return mock data
        return {
            "report_id": report_id,
            "scenes": [
                {
                    "scene_number": 1,
                    "title": "INT. COFFEE SHOP - DAY",
                    "location": "Coffee Shop",
                    "characters": ["SARAH", "MIKE"],
                    "risk_score": 25,
                    "complexity": "low",
                    "notes": ["Simple dialogue scene", "Standard lighting setup"]
                }
            ]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get scene breakdown: {str(e)}"
        )

@router.get("/character-bible/{report_id}")
async def get_character_bible(
    report_id: str,
    db: Session = Depends(get_db)
):
    """
    Get character bible for a report
    """
    try:
        # In production, fetch from database
        return {
            "report_id": report_id,
            "characters": {
                "SARAH": {
                    "name": "SARAH",
                    "type": "lead",
                    "scenes": 12,
                    "description": "Young professional, determined",
                    "relationships": {"MIKE": "romantic interest"}
                }
            },
            "casting_notes": {
                "SARAH": ["Lead role - experienced actor required", "Age 25-30"]
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get character bible: {str(e)}"
        )

@router.get("/production-insights/{report_id}")
async def get_production_insights(
    report_id: str,
    db: Session = Depends(get_db)
):
    """
    Get production insights and recommendations
    """
    try:
        return {
            "report_id": report_id,
            "budget_estimate": {
                "total": 250000,
                "breakdown": {
                    "cast": 80000,
                    "locations": 50000,
                    "equipment": 60000,
                    "legal": 15000,
                    "contingency": 45000
                }
            },
            "shooting_schedule": {
                "estimated_days": 18,
                "complexity_factors": ["Multiple locations", "Large cast scenes"],
                "recommendations": ["Schedule dialogue scenes first", "Plan for weather delays"]
            },
            "risk_mitigation": [
                "Obtain location permits early",
                "Secure legal clearances for mentioned brands",
                "Plan backup locations for exterior scenes"
            ]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get production insights: {str(e)}"
        )

# Helper functions
def _calculate_risk_summary(scene_analyses: List[SceneAnalysisResponse], standard_analysis) -> Dict[str, Any]:
    """Calculate overall risk summary"""
    if not scene_analyses:
        return {"total_scenes": 0, "average_risk": 0}
    
    total_scenes = len(scene_analyses)
    total_risk = sum(scene.risk_score for scene in scene_analyses)
    average_risk = total_risk / total_scenes
    
    # Risk distribution
    low_risk = len([s for s in scene_analyses if s.risk_score < 30])
    medium_risk = len([s for s in scene_analyses if 30 <= s.risk_score < 60])
    high_risk = len([s for s in scene_analyses if s.risk_score >= 60])
    
    # Total estimated costs
    total_costs = {}
    for scene in scene_analyses:
        for cost_type, cost in scene.estimated_cost.items():
            total_costs[cost_type] = total_costs.get(cost_type, 0) + cost
    
    return {
        "total_scenes": total_scenes,
        "average_risk_score": round(average_risk, 2),
        "risk_distribution": {
            "low": low_risk,
            "medium": medium_risk,
            "high": high_risk
        },
        "highest_risk_scene": max(scene_analyses, key=lambda x: x.risk_score).scene_number if scene_analyses else None,
        "total_estimated_costs": total_costs,
        "script_level_risk": standard_analysis.risk_assessment.overall_risk_score
    }

def _generate_production_insights(
    scenes, characters, scene_analyses, scene_stats, char_stats
) -> Dict[str, Any]:
    """Generate production insights and recommendations"""
    insights = {
        "script_statistics": {
            "total_scenes": len(scenes),
            "total_characters": len(characters),
            "day_scenes": scene_stats.get("day_scenes", 0),
            "night_scenes": scene_stats.get("night_scenes", 0),
            "interior_scenes": scene_stats.get("interior_scenes", 0),
            "exterior_scenes": scene_stats.get("exterior_scenes", 0)
        },
        "production_complexity": _assess_production_complexity(scenes, scene_analyses),
        "scheduling_recommendations": _generate_scheduling_recommendations(scenes, scene_analyses),
        "budget_considerations": _generate_budget_considerations(scene_analyses),
        "casting_priorities": _generate_casting_priorities(characters)
    }
    
    return insights

def _assess_production_complexity(scenes, scene_analyses) -> Dict[str, Any]:
    """Assess overall production complexity"""
    if not scene_analyses:
        return {"level": "unknown"}
    
    avg_risk = sum(s.risk_score for s in scene_analyses) / len(scene_analyses)
    high_risk_scenes = len([s for s in scene_analyses if s.risk_score > 60])
    
    if avg_risk > 60 or high_risk_scenes > len(scenes) * 0.3:
        complexity = "high"
        factors = ["Multiple high-risk scenes", "Complex production requirements"]
    elif avg_risk > 35 or high_risk_scenes > 0:
        complexity = "medium"
        factors = ["Some challenging scenes", "Moderate production requirements"]
    else:
        complexity = "low"
        factors = ["Straightforward production", "Standard requirements"]
    
    return {
        "level": complexity,
        "factors": factors,
        "high_risk_scene_count": high_risk_scenes
    }

def _generate_scheduling_recommendations(scenes, scene_analyses) -> List[str]:
    """Generate scheduling recommendations"""
    recommendations = []
    
    if not scene_analyses:
        return ["Unable to generate recommendations"]
    
    # Check for night scenes
    night_scenes = len([s for s in scene_analyses if "night" in s.time_of_day.lower()])
    if night_scenes > 3:
        recommendations.append(f"Plan {night_scenes} night shooting days - schedule consecutively")
    
    # Check for high-risk scenes
    high_risk_scenes = [s for s in scene_analyses if s.risk_score > 60]
    if high_risk_scenes:
        recommendations.append("Schedule high-risk scenes early in production when crew is fresh")
    
    # Check for location diversity
    locations = set(s.location for s in scene_analyses)
    if len(locations) > 5:
        recommendations.append("Group scenes by location to minimize company moves")
    
    return recommendations if recommendations else ["Standard scheduling considerations apply"]

def _generate_budget_considerations(scene_analyses) -> List[str]:
    """Generate budget considerations"""
    considerations = []
    
    if not scene_analyses:
        return ["Unable to generate budget considerations"]
    
    # High cost scenes
    high_cost_scenes = [s for s in scene_analyses if s.estimated_cost.get("total", 0) > 10000]
    if high_cost_scenes:
        considerations.append(f"{len(high_cost_scenes)} scenes require additional budget allocation")
    
    # Legal clearances
    clearance_scenes = [s for s in scene_analyses if s.required_clearances]
    if clearance_scenes:
        considerations.append("Budget for legal clearances and licensing fees")
    
    return considerations if considerations else ["Standard budget considerations apply"]

def _generate_casting_priorities(characters) -> Dict[str, str]:
    """Generate casting priorities"""
    priorities = {}
    
    for name, profile in characters.items():
        if profile.character_type == "lead":
            priorities[name] = "high_priority"
        elif profile.character_type == "supporting":
            priorities[name] = "medium_priority"
        else:
            priorities[name] = "low_priority"
    
    return priorities

def _summarize_agent_data(agent_data) -> Dict[str, Any]:
    """Summarize agent data for API response"""
    if not agent_data:
        return {}
    
    summary = {}
    
    # Summarize claims if present
    if "claims" in agent_data:
        claims = agent_data["claims"]
        summary["claims_count"] = len(claims)
        summary["claims_by_type"] = {}
        for claim in claims:
            claim_type = claim.get("type", "unknown")
            summary["claims_by_type"][claim_type] = summary["claims_by_type"].get(claim_type, 0) + 1
    
    # Summarize other relevant data
    for key in ["verified_claims", "flagged_claims", "copyright_risks", "inconsistencies"]:
        if key in agent_data:
            summary[f"{key}_count"] = len(agent_data[key])
    
    return summary

async def _save_enhanced_analysis(db: Session, request: EnhancedAnalysisRequest, response: EnhancedAnalysisResponse):
    """Save enhanced analysis to database (background task)"""
    try:
        # In production, save to database
        # For now, just log
        logger.info(f"Enhanced analysis completed: {response.report_id}")
    except Exception as e:
        logger.error(f"Failed to save enhanced analysis: {e}")