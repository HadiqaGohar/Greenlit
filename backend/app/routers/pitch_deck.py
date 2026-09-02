"""
Pitch Deck Router - On-demand AI pitch deck generation endpoint
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


class PitchDeckRequest(BaseModel):
    """Request model for pitch deck generation"""
    report_id: Optional[str] = Field(default=None, description="Report ID to generate deck for")
    script_text: Optional[str] = Field(default=None, description="Script text (used if report_id not provided)")


class PitchDeckSlide(BaseModel):
    title: str
    bullets: list
    icon: Optional[str] = None


class PitchDeckResponse(BaseModel):
    deck_id: str
    report_id: str
    success: bool
    title: str
    slides: list
    slide_count: int
    generation_method: str
    processing_time: float
    generated_at: str
    error: Optional[str] = None


_pitch_deck_cache: Dict[str, dict] = {}


def _load_report_data(report_id: str):
    report_file = f"data/reports/{report_id}.json"
    if os.path.exists(report_file):
        with open(report_file, "r") as f:
            return json.load(f)
    return None


@router.post("/pitch-deck/generate", response_model=PitchDeckResponse)
async def generate_pitch_deck(request: PitchDeckRequest):
    """Generate an AI pitch deck (slides) for a script/report"""
    from ..agents.pitch_deck_agent import PitchDeckAgent
    from ..models.agent_schemas import AgentTask

    deck_id = str(uuid4())
    start_time = datetime.now(timezone.utc)

    try:
        script_text = request.script_text
        report_id = request.report_id or f"adhoc_{deck_id[:8]}"
        if not script_text and request.report_id:
            data = _load_report_data(request.report_id)
            if data:
                script_text = data.get("script_text", "")

        if not script_text or len(script_text.strip()) < 20:
            raise HTTPException(status_code=400, detail="No script text available for pitch deck generation.")

        agent = PitchDeckAgent()
        task = AgentTask(agent_type="pitch_deck", task_data={"script_text": script_text})
        result = await agent.process_task(task)

        if not result.success:
            raise HTTPException(status_code=500, detail=f"Pitch deck failed: {result.error_message}")

        d = result.data
        deck_data = {
            "deck_id": deck_id,
            "report_id": report_id,
            "data": d,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
        _pitch_deck_cache[deck_id] = deck_data
        _pitch_deck_cache[report_id] = deck_data

        return PitchDeckResponse(
            deck_id=deck_id,
            report_id=report_id,
            success=True,
            title=d.get("title", "Untitled Project"),
            slides=d.get("slides", []),
            slide_count=d.get("slide_count", len(d.get("slides", []))),
            generation_method=d.get("generation_method", "heuristic"),
            processing_time=(datetime.now(timezone.utc) - start_time).total_seconds(),
            generated_at=datetime.now(timezone.utc).isoformat(),
            error=None,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Pitch deck generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Pitch deck generation failed: {str(e)}")


@router.get("/pitch-deck/{deck_id}")
async def get_pitch_deck(deck_id: str):
    deck = _pitch_deck_cache.get(deck_id)
    if not deck:
        raise HTTPException(status_code=404, detail="Pitch deck not found")
    return deck


@router.get("/pitch-deck/report/{report_id}")
async def get_pitch_deck_by_report(report_id: str):
    deck = _pitch_deck_cache.get(report_id)
    if not deck:
        raise HTTPException(status_code=404, detail="No pitch deck found for this report")
    return deck
