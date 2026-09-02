"""
TTS Router - On-demand table read generation endpoint
"""

import logging
from typing import List, Optional
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)
router = APIRouter()


class TTSRequest(BaseModel):
    """Request model for TTS generation"""
    report_id: str = Field(..., description="Report ID to generate table read for")
    scene_numbers: Optional[List[int]] = Field(default=None, description="Specific scene numbers (None = all)")


class TTSSceneResponse(BaseModel):
    """Single TTS scene"""
    scene_number: int
    title: str
    characters: List[str]
    audio_base64: Optional[str] = None
    audio_format: str = "wav"
    duration_seconds: float
    generation_error: Optional[str] = None


class TTSResponse(BaseModel):
    """Response model for TTS generation"""
    tts_id: str
    report_id: str
    success: bool
    scenes: List[TTSSceneResponse]
    total_scenes: int
    successful_scenes: int
    voice_map: dict
    total_duration: float
    processing_time: float
    generated_at: str
    error: Optional[str] = None


# In-memory cache for TTS results
_tts_cache = {}


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


@router.post("/tts/generate", response_model=TTSResponse)
async def generate_tts(request: TTSRequest):
    """Generate table read audio for a report's script"""

    from uuid import uuid4

    tts_id = str(uuid4())
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
                detail="Report has no script text for table read generation"
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
            }
            for s in parsed_scenes
        ]

        if not scenes:
            raise HTTPException(
                status_code=400,
                detail="No scenes found in script for table read generation"
            )

        # Generate TTS
        from ..agents.tts_agent import generate_table_read

        result = await generate_table_read(
            script_text=script_text,
            scenes=scenes,
            scene_numbers=request.scene_numbers
        )

        processing_time = (datetime.now(timezone.utc) - start_time).total_seconds()

        # Cache the result
        tts_data = {
            "tts_id": tts_id,
            "report_id": request.report_id,
            "scenes": result["scenes"],
            "voice_map": result["voice_map"],
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
        _tts_cache[tts_id] = tts_data
        _tts_cache[request.report_id] = tts_data  # Also cache by report_id

        successful = len([s for s in result["scenes"] if s.get("audio_base64")])

        return TTSResponse(
            tts_id=tts_id,
            report_id=request.report_id,
            success=result["success"],
            scenes=[TTSSceneResponse(**s) for s in result["scenes"]],
            total_scenes=result["total_scenes"],
            successful_scenes=successful,
            voice_map=result["voice_map"],
            total_duration=result["total_duration"],
            processing_time=processing_time,
            generated_at=datetime.now(timezone.utc).isoformat(),
            error=result.get("error")
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"TTS generation failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"TTS generation failed: {str(e)}"
        )


@router.get("/tts/{tts_id}")
async def get_tts(tts_id: str):
    """Get cached TTS by ID"""
    tts = _tts_cache.get(tts_id)
    if not tts:
        raise HTTPException(status_code=404, detail="TTS not found")
    return tts


@router.get("/tts/report/{report_id}")
async def get_tts_by_report(report_id: str):
    """Get TTS for a report"""
    tts = _tts_cache.get(report_id)
    if not tts:
        raise HTTPException(status_code=404, detail="No table read found for this report")
    return tts
