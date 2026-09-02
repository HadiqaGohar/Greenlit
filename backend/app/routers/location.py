"""
Scene-to-Location Matching Router - On-demand location suggestion endpoint
"""

import logging
import os
import json
from typing import Dict, Optional
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter()


class LocationMatchRequest(BaseModel):
    report_id: Optional[str] = Field(default=None, description="Report ID to match locations for")
    script_text: Optional[str] = Field(default=None, description="Script text (used if report_id not provided)")


class LocationMatchResponse(BaseModel):
    match_id: str
    report_id: str
    success: bool
    matches: list
    match_count: int
    generation_method: str
    processing_time: float
    generated_at: str
    error: Optional[str] = None


_location_cache: Dict[str, dict] = {}


def _load_report_data(report_id: str):
    report_file = f"data/reports/{report_id}.json"
    if os.path.exists(report_file):
        try:
            with open(report_file, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Could not parse report {report_id}: {e}")
            return None
    return None


@router.post("/location/match", response_model=LocationMatchResponse)
async def match_locations(request: LocationMatchRequest):
    """Match script scenes to real-world filming locations"""
    from ..agents.location_agent import LocationMatchAgent
    from ..models.agent_schemas import AgentTask

    match_id = str(uuid4())
    start_time = datetime.now(timezone.utc)

    try:
        script_text = request.script_text
        report_id = request.report_id or f"adhoc_{match_id[:8]}"
        scenes = None
        if not script_text and request.report_id:
            data = _load_report_data(request.report_id)
            if data:
                script_text = data.get("script_text", "")
                scenes = data.get("scenes", [])

        if (not script_text or len(script_text.strip()) < 20) and not scenes:
            raise HTTPException(status_code=400, detail="No script text or scenes available for location matching.")

        agent = LocationMatchAgent()
        task_data = {"script_text": script_text or ""}
        if scenes:
            task_data["scenes"] = scenes
        task = AgentTask(agent_type="location", task_data=task_data)
        result = await agent.process_task(task)

        if not result.success:
            raise HTTPException(status_code=500, detail=f"Location matching failed: {result.error_message}")

        d = result.data
        match_data = {
            "match_id": match_id,
            "report_id": report_id,
            "data": d,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
        _location_cache[match_id] = match_data
        _location_cache[report_id] = match_data

        return LocationMatchResponse(
            match_id=match_id,
            report_id=report_id,
            success=True,
            matches=d.get("matches", []),
            match_count=d.get("match_count", len(d.get("matches", []))),
            generation_method=d.get("generation_method", "heuristic"),
            processing_time=(datetime.now(timezone.utc) - start_time).total_seconds(),
            generated_at=datetime.now(timezone.utc).isoformat(),
            error=None,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Location matching failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Location matching failed: {str(e)}")


@router.get("/location/match/{match_id}")
async def get_location_match(match_id: str):
    match = _location_cache.get(match_id)
    if not match:
        raise HTTPException(status_code=404, detail="Location match not found")
    return match


@router.get("/location/match/report/{report_id}")
async def get_location_match_by_report(report_id: str):
    match = _location_cache.get(report_id)
    if not match:
        raise HTTPException(status_code=404, detail="No location match found for this report")
    return match
