"""
Storyboard Router - On-demand storyboard generation endpoint
"""

import logging
from typing import List, Optional
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)
router = APIRouter()


class StoryboardRequest(BaseModel):
    """Request model for storyboard generation"""
    report_id: str = Field(..., description="Report ID to generate storyboard for")
    scene_numbers: Optional[List[int]] = Field(default=None, description="Specific scene numbers to generate (None = all)")


class StoryboardFrameResponse(BaseModel):
    """Single storyboard frame"""
    scene_number: int
    title: str
    description: str
    mood: str
    camera_angle: str
    visual_prompt: str
    image_base64: Optional[str] = None
    image_mime_type: str = "image/png"
    generation_error: Optional[str] = None


class StoryboardResponse(BaseModel):
    """Response model for storyboard generation"""
    storyboard_id: str
    report_id: str
    success: bool
    frames: List[StoryboardFrameResponse]
    total_frames: int
    successful_frames: int
    processing_time: float
    generated_at: str
    error: Optional[str] = None


# In-memory cache for storyboards
_storyboard_cache = {}


def _load_report_scenes(report_id: str):
    """Load report data from file storage to get scenes"""
    import os
    import json

    report_file = f"data/reports/{report_id}.json"
    if os.path.exists(report_file):
        with open(report_file, "r") as f:
            data = json.load(f)
        return data
    return None


@router.post("/storyboard/generate", response_model=StoryboardResponse)
async def generate_storyboard(request: StoryboardRequest):
    """Generate storyboard frames for a report's scenes"""

    from uuid import uuid4

    storyboard_id = str(uuid4())
    start_time = datetime.now(timezone.utc)

    try:
        # Load report data to get scenes
        report_data = _load_report_scenes(request.report_id)

        if not report_data:
            raise HTTPException(
                status_code=404,
                detail=f"Report {request.report_id} not found"
            )

        script_text = report_data.get("script_text", "")
        scenes = report_data.get("agent_results", {}).get("director", {}).get("data", {}).get("claims", [])

        # Get scenes from orchestrator data
        # The scenes are stored in the report file under 'scenes' key
        # But we need to re-parse them from script_text
        from ..services.scene_parser import parse_screenplay

        if script_text:
            parsed_scenes, _ = parse_screenplay(script_text)
            scenes = [
                {
                    "scene_number": s.scene_number,
                    "title": s.title,
                    "location": s.location,
                    "time_of_day": s.time_of_day,
                    "description": s.description,
                    "characters_present": s.characters_present,
                }
                for s in parsed_scenes
            ]
        else:
            raise HTTPException(
                status_code=400,
                detail="Report has no script text for storyboard generation"
            )

        if not scenes:
            raise HTTPException(
                status_code=400,
                detail="No scenes found in script for storyboard generation"
            )

        # Generate storyboard
        from ..agents.storyboard_agent import generate_storyboard as generate

        result = await generate(
            script_text=script_text,
            scenes=scenes,
            scene_numbers=request.scene_numbers
        )

        processing_time = (datetime.now(timezone.utc) - start_time).total_seconds()

        # Cache the storyboard
        storyboard_data = {
            "storyboard_id": storyboard_id,
            "report_id": request.report_id,
            "frames": result["frames"],
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
        _storyboard_cache[storyboard_id] = storyboard_data
        _storyboard_cache[request.report_id] = storyboard_data  # Also cache by report_id

        successful = len([f for f in result["frames"] if f.get("image_base64")])

        return StoryboardResponse(
            storyboard_id=storyboard_id,
            report_id=request.report_id,
            success=result["success"],
            frames=[StoryboardFrameResponse(**f) for f in result["frames"]],
            total_frames=result["total_frames"],
            successful_frames=successful,
            processing_time=processing_time,
            generated_at=datetime.now(timezone.utc).isoformat(),
            error=result.get("error")
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Storyboard generation failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Storyboard generation failed: {str(e)}"
        )


@router.get("/storyboard/{storyboard_id}")
async def get_storyboard(storyboard_id: str):
    """Get a cached storyboard by ID"""
    storyboard = _storyboard_cache.get(storyboard_id)
    if not storyboard:
        raise HTTPException(status_code=404, detail="Storyboard not found")
    return storyboard


@router.get("/storyboard/report/{report_id}")
async def get_storyboard_by_report(report_id: str):
    """Get storyboard for a report"""
    storyboard = _storyboard_cache.get(report_id)
    if not storyboard:
        raise HTTPException(status_code=404, detail="No storyboard found for this report")
    return storyboard
