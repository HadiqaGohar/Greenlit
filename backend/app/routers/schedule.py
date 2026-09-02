"""
Schedule Router - On-demand production schedule generation endpoint
"""

import logging
from typing import List, Optional
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)
router = APIRouter()


class ScheduleRequest(BaseModel):
    """Request model for schedule generation"""
    report_id: str = Field(..., description="Report ID to generate schedule for")
    pages_per_day: Optional[float] = Field(default=5.0, description="Target pages per shoot day")


class ShootDayResponse(BaseModel):
    """Single shoot day"""
    day_number: int
    scenes: List[dict]
    total_page_eighths: int
    total_page_count: str
    locations: List[str]
    company_moves: int
    cast_required: List[str]
    is_night_shoot: bool
    estimated_hours: float
    scene_count: int


class ScheduleResponse(BaseModel):
    """Response model for schedule generation"""
    schedule_id: str
    report_id: str
    success: bool
    shoot_days: List[ShootDayResponse]
    total_shoot_days: int
    contingency_days: int
    total_pages: str
    total_pages_eighths: int
    company_moves_total: int
    cast_schedule: dict
    location_summary: List[dict]
    optimization_notes: List[str]
    pages_per_day_target: float
    processing_time: float
    generated_at: str
    error: Optional[str] = None


# In-memory cache for schedule results
_schedule_cache = {}


def _load_report_data(report_id: str):
    """Load report data from file storage"""
    import os
    import json

    report_file = f"data/reports/{report_id}.json"
    if os.path.exists(report_file):
        with open(report_file, "r") as f:
            data = json.load(f)
        return data
    return None


@router.post("/schedule/generate", response_model=ScheduleResponse)
async def generate_schedule(request: ScheduleRequest):
    """Generate an optimized day-by-day shooting schedule for a report's script"""

    from uuid import uuid4

    schedule_id = str(uuid4())
    start_time = datetime.now(timezone.utc)

    try:
        # Load report data
        report_data = _load_report_data(request.report_id)

        if not report_data:
            raise HTTPException(
                status_code=404,
                detail=f"Report {request.report_id} not found"
            )

        script_text = report_data.get("script_text", "")

        if not script_text:
            raise HTTPException(
                status_code=400,
                detail="Report has no script text for schedule generation"
            )

        # Parse scenes from script
        from ..services.scene_parser import parse_screenplay
        parsed_scenes, _ = parse_screenplay(script_text)
        scenes = [
            {
                "scene_number": s.scene_number,
                "title": s.title,
                "location": s.location,
                "time_of_day": s.time_of_day,
                "description": s.description,
                "characters_present": s.characters_present,
                "dialogue_count": s.dialogue_count,
                "action_lines": s.action_lines,
            }
            for s in parsed_scenes
        ]

        if not scenes:
            raise HTTPException(
                status_code=400,
                detail="No scenes found in script for schedule generation"
            )

        # Generate schedule
        from ..agents.schedule_agent import ScheduleAgent
        agent = ScheduleAgent()

        from ..models.agent_schemas import AgentTask
        task = AgentTask(
            agent_type="schedule",
            task_data={
                "script_text": script_text,
                "scenes": scenes,
                "pages_per_day": request.pages_per_day,
            },
        )

        result = await agent.process_task(task)

        if not result.success:
            raise HTTPException(
                status_code=500,
                detail=f"Schedule generation failed: {result.error_message}"
            )

        processing_time = (datetime.now(timezone.utc) - start_time).total_seconds()

        # Cache the result
        schedule_data = {
            "schedule_id": schedule_id,
            "report_id": request.report_id,
            "data": result.data,
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
        _schedule_cache[schedule_id] = schedule_data
        _schedule_cache[request.report_id] = schedule_data

        data = result.data
        return ScheduleResponse(
            schedule_id=schedule_id,
            report_id=request.report_id,
            success=True,
            shoot_days=[ShootDayResponse(**d) for d in data["shoot_days"]],
            total_shoot_days=data["total_shoot_days"],
            contingency_days=data["contingency_days"],
            total_pages=data["total_pages"],
            total_pages_eighths=data["total_pages_eighths"],
            company_moves_total=data["company_moves_total"],
            cast_schedule=data["cast_schedule"],
            location_summary=data["location_summary"],
            optimization_notes=data["optimization_notes"],
            pages_per_day_target=data["pages_per_day_target"],
            processing_time=processing_time,
            generated_at=datetime.now(timezone.utc).isoformat(),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Schedule generation failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Schedule generation failed: {str(e)}"
        )


@router.get("/schedule/{schedule_id}")
async def get_schedule(schedule_id: str):
    """Get cached schedule by ID"""
    schedule = _schedule_cache.get(schedule_id)
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return schedule


@router.get("/schedule/report/{report_id}")
async def get_schedule_by_report(report_id: str):
    """Get schedule for a report"""
    schedule = _schedule_cache.get(report_id)
    if not schedule:
        raise HTTPException(status_code=404, detail="No schedule found for this report")
    return schedule
