"""
Relationship Router - On-demand character relationship graph generation endpoint
"""

import logging
import os
import json
from typing import Dict, List, Optional
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter()


class RelationshipRequest(BaseModel):
    """Request model for relationship graph generation"""
    report_id: str = Field(..., description="Report ID to generate relationship graph for")


class RelationshipNode(BaseModel):
    id: str
    name: str
    scenes_count: int
    is_primary: bool
    centrality: float
    degree: int


class RelationshipEdge(BaseModel):
    source: str
    target: str
    weight: int
    shared_scenes: List[int]
    type: str
    label: str
    confidence: float


class RelationshipResponse(BaseModel):
    """Response model for relationship graph generation"""
    graph_id: str
    report_id: str
    success: bool
    nodes: List[RelationshipNode]
    edges: List[RelationshipEdge]
    stats: dict
    processing_time: float
    generated_at: str
    error: Optional[str] = None


# In-memory cache for relationship results
_relationship_cache: Dict[str, dict] = {}


def _load_report_data(report_id: str):
    """Load report data from file storage"""
    report_file = f"data/reports/{report_id}.json"
    if os.path.exists(report_file):
        with open(report_file, "r") as f:
            return json.load(f)
    return None


@router.post("/relationship/generate", response_model=RelationshipResponse)
async def generate_relationship(request: RelationshipRequest):
    """Generate a character relationship graph for a report's script"""

    from ..agents.relationship_agent import CharacterRelationshipAgent
    from ..models.agent_schemas import AgentTask
    from ..services.scene_parser import parse_screenplay

    graph_id = str(uuid4())
    start_time = datetime.now(timezone.utc)

    try:
        report_data = _load_report_data(request.report_id)
        if not report_data:
            raise HTTPException(status_code=404, detail=f"Report {request.report_id} not found")

        script_text = report_data.get("script_text", "")
        if not script_text:
            raise HTTPException(status_code=400, detail="Report has no script text for relationship analysis")

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
            raise HTTPException(status_code=400, detail="No scenes found in script for relationship analysis")

        agent = CharacterRelationshipAgent()
        task = AgentTask(agent_type="relationship", task_data={"scenes": scenes})
        result = await agent.process_task(task)

        if not result.success:
            raise HTTPException(status_code=500, detail=f"Relationship analysis failed: {result.error_message}")

        processing_time = (datetime.now(timezone.utc) - start_time).total_seconds()
        data = result.data

        graph_data = {
            "graph_id": graph_id,
            "report_id": request.report_id,
            "data": data,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
        _relationship_cache[graph_id] = graph_data
        _relationship_cache[request.report_id] = graph_data

        return RelationshipResponse(
            graph_id=graph_id,
            report_id=request.report_id,
            success=True,
            nodes=[RelationshipNode(**n) for n in data["nodes"]],
            edges=[RelationshipEdge(**e) for e in data["edges"]],
            stats=data["stats"],
            processing_time=processing_time,
            generated_at=datetime.now(timezone.utc).isoformat(),
            error=None,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Relationship generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Relationship generation failed: {str(e)}")


@router.get("/relationship/{graph_id}")
async def get_relationship(graph_id: str):
    """Get cached relationship graph by ID"""
    graph = _relationship_cache.get(graph_id)
    if not graph:
        raise HTTPException(status_code=404, detail="Relationship graph not found")
    return graph


@router.get("/relationship/report/{report_id}")
async def get_relationship_by_report(report_id: str):
    """Get relationship graph for a report"""
    graph = _relationship_cache.get(report_id)
    if not graph:
        raise HTTPException(status_code=404, detail="No relationship graph found for this report")
    return graph
