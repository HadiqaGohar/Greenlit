"""
Stakeholder Router - On-demand multi-stakeholder analysis endpoint
"""

import logging
from typing import List, Optional
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)
router = APIRouter()


class StakeholderRequest(BaseModel):
    report_id: str = Field(..., description="Report ID to analyze stakeholders for")


class StakeholderRoleResponse(BaseModel):
    role: str
    title: str
    icon: str
    overall_score: int
    score_label: str
    risk_level: str
    key_concerns: List[str]
    findings: List[dict]
    recommendations: List[str]
    summary: str


class StakeholderResponse(BaseModel):
    stakeholder_id: str
    report_id: str
    success: bool
    stakeholders: List[StakeholderRoleResponse]
    overall_readiness: float
    roles_analyzed: int
    processing_time: float
    generated_at: str
    error: Optional[str] = None


_stakeholder_cache = {}


def _load_report_data(report_id: str):
    import os
    import json
    report_file = f"data/reports/{report_id}.json"
    if os.path.exists(report_file):
        with open(report_file, "r") as f:
            return json.load(f)
    return None


@router.post("/stakeholder/analyze", response_model=StakeholderResponse)
async def analyze_stakeholders(request: StakeholderRequest):
    """Analyze script from 8 production stakeholder perspectives"""
    from uuid import uuid4

    stakeholder_id = str(uuid4())
    start_time = datetime.now(timezone.utc)

    try:
        report_data = _load_report_data(request.report_id)
        if not report_data:
            raise HTTPException(status_code=404, detail=f"Report {request.report_id} not found")

        from ..agents.stakeholder_agent import StakeholderAgent
        agent = StakeholderAgent()

        from ..models.agent_schemas import AgentTask
        task = AgentTask(
            agent_type="stakeholder",
            task_data={"report_data": report_data},
        )

        result = await agent.process_task(task)

        if not result.success:
            raise HTTPException(status_code=500, detail=f"Stakeholder analysis failed: {result.error_message}")

        processing_time = (datetime.now(timezone.utc) - start_time).total_seconds()
        data = result.data

        stakeholder_data = {
            "stakeholder_id": stakeholder_id,
            "report_id": request.report_id,
            "data": data,
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
        _stakeholder_cache[stakeholder_id] = stakeholder_data
        _stakeholder_cache[request.report_id] = stakeholder_data

        return StakeholderResponse(
            stakeholder_id=stakeholder_id,
            report_id=request.report_id,
            success=True,
            stakeholders=[StakeholderRoleResponse(**s) for s in data["stakeholders"]],
            overall_readiness=data["overall_readiness"],
            roles_analyzed=data["roles_analyzed"],
            processing_time=processing_time,
            generated_at=datetime.now(timezone.utc).isoformat(),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Stakeholder analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Stakeholder analysis failed: {str(e)}")


@router.get("/stakeholder/{stakeholder_id}")
async def get_stakeholder(stakeholder_id: str):
    st = _stakeholder_cache.get(stakeholder_id)
    if not st:
        raise HTTPException(status_code=404, detail="Stakeholder analysis not found")
    return st


@router.get("/stakeholder/report/{report_id}")
async def get_stakeholder_by_report(report_id: str):
    st = _stakeholder_cache.get(report_id)
    if not st:
        raise HTTPException(status_code=404, detail="No stakeholder analysis found for this report")
    return st
