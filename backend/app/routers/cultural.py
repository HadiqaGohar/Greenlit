"""
Cultural Sensitivity Router - Cultural analysis endpoint
"""

import logging
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter()


class CulturalRequest(BaseModel):
    """Request model for cultural sensitivity analysis"""
    script_text: str = Field(..., min_length=10, max_length=50000, description="Script content to analyze")


@router.post("/cultural-analysis")
async def analyze_cultural_sensitivity(request: CulturalRequest, fastapi_request: Request):
    """
    Analyze script for cultural sensitivity issues
    Uses Cultural Sensitivity Agent with Gemini AI
    """
    
    try:
        from ..agents.cultural_agent import CulturalSensitivityAgent
        from ..models.agent_schemas import AgentTask
        from uuid import uuid4
        
        cultural_agent = CulturalSensitivityAgent()
        
        task = AgentTask(
            task_id=str(uuid4()),
            agent_type="cultural",
            task_data={"script_text": request.script_text}
        )
        
        result = await cultural_agent.process_task(task)
        
        if result.success:
            return {
                "success": True,
                "cultural_analysis": result.data.get("cultural_analysis", {}),
                "processing_time": result.processing_time
            }
        else:
            raise HTTPException(status_code=500, detail=result.error_message)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Cultural analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Cultural analysis failed: {str(e)}")
