"""
Chat Router - "Ask the Script" feature
Enables users to chat with their screenplay using Gemini RAG
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from ..agent.gemini_client import get_gemini_client

logger = logging.getLogger(__name__)

router = APIRouter()


class ChatMessage(BaseModel):
    role: str = Field(..., description="Message role: 'user' or 'assistant'")
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ChatRequest(BaseModel):
    report_id: str = Field(..., description="Report ID to chat about")
    question: str = Field(..., min_length=3, max_length=1000, description="User question about the script")
    script_text: Optional[str] = Field(default=None, description="Original script text if available")
    history: List[ChatMessage] = Field(default_factory=list, description="Chat history for context")


class ChatResponse(BaseModel):
    answer: str
    sources: List[Dict[str, str]] = Field(default_factory=list)
    related_scenes: List[int] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)


def _build_report_context(report_data: Dict[str, Any], script_text: Optional[str] = None) -> str:
    """Build context string from report data for RAG"""
    context_parts = []
    
    # Add script text if available
    if script_text:
        context_parts.append(f"=== SCRIPT CONTENT ===\n{script_text[:8000]}\n")
    
    # Add risk assessment
    risk = report_data.get("risk_assessment", {})
    if risk:
        context_parts.append(
            f"=== RISK ASSESSMENT ===\n"
            f"Overall Risk Score: {risk.get('overall_risk_score', 'N/A')}/100\n"
            f"Risk Level: {risk.get('risk_level', 'N/A')}\n"
            f"Risk Factors: {', '.join(risk.get('risk_factors', []))}\n"
        )
    
    # Add agent results summary
    agent_results = report_data.get("agent_results", {})
    if agent_results:
        context_parts.append("=== AGENT ANALYSIS RESULTS ===")
        for agent_name, result in agent_results.items():
            if result.get("success"):
                context_parts.append(f"\n--- {agent_name.upper()} AGENT ---")
                data_summary = result.get("data_summary", {})
                if data_summary:
                    for key, value in data_summary.items():
                        context_parts.append(f"  {key}: {value}")
    
    # Add claims
    claims = report_data.get("claims", [])
    if claims:
        context_parts.append("\n=== FACTUAL CLAIMS EXTRACTED ===")
        for claim in claims[:15]:  # Limit to avoid token overflow
            context_parts.append(
                f"- [{claim.get('type', 'unknown')}] {claim.get('text', 'N/A')} "
                f"(Verdict: {claim.get('verdict', 'N/A')}, "
                f"Confidence: {claim.get('confidence', 0):.0%})"
            )
    
    # Add suggestions
    suggestions = report_data.get("suggestions", [])
    if suggestions:
        context_parts.append("\n=== AI SUGGESTIONS ===")
        for sug in suggestions[:10]:
            context_parts.append(
                f"- [{sug.get('severity', 'N/A')}] {sug.get('issue_type', 'N/A')}: "
                f"{sug.get('rationale', 'N/A')}"
            )
    
    # Add scenes if available
    scenes = report_data.get("scenes", [])
    if scenes:
        context_parts.append(f"\n=== SCENE BREAKDOWN ({len(scenes)} scenes) ===")
        for scene in scenes[:20]:
            context_parts.append(
                f"Scene {scene.get('scene_number', '?')}: "
                f"{scene.get('title', 'Untitled')} "
                f"({scene.get('location', 'Unknown location')}, "
                f"{scene.get('time_of_day', 'Unknown time')})"
            )
    
    return "\n".join(context_parts)


async def _generate_chat_response(
    question: str,
    context: str,
    history: List[ChatMessage]
) -> ChatResponse:
    """Generate response using Gemini with RAG context"""
    
    client = await get_gemini_client()
    
    system_prompt = """You are an expert film production analyst and script consultant. 
You have access to a comprehensive analysis of a screenplay including:
- Risk assessment results
- Legal analysis (copyright, trademark, clearance issues)
- Fact verification results
- Continuity analysis
- Character analysis
- Scene breakdowns

Answer the user's questions about the script based on this analysis data.
Be specific, reference actual findings from the analysis, and provide actionable insights.
If a question relates to specific scenes or characters, mention them by name.
Keep responses concise but informative (2-4 paragraphs max).
If you don't have enough information to answer a question, say so clearly."""

    # Build conversation history
    history_text = ""
    if history:
        history_text = "\n\n=== CONVERSATION HISTORY ===\n"
        for msg in history[-6:]:  # Last 3 exchanges
            history_text += f"{msg.role.upper()}: {msg.content}\n"
    
    prompt = f"""{context}

{history_text}

=== CURRENT QUESTION ===
{question}

Please provide a detailed answer based on the analysis data above. If the question is about specific scenes, characters, or issues, reference them directly from the data."""

    try:
        response = await client.generate_content(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.4,
            max_tokens=1500
        )
        
        # Extract related scenes from response (simple heuristic)
        related_scenes = []
        import re
        scene_matches = re.findall(r'[Ss]cene\s+(\d+)', response)
        for match in scene_matches:
            try:
                related_scenes.append(int(match))
            except ValueError:
                pass
        related_scenes = sorted(set(related_scenes))[:5]
        
        return ChatResponse(
            answer=response,
            sources=[],
            related_scenes=related_scenes,
            confidence=0.85
        )
        
    except Exception as e:
        logger.error(f"Gemini chat generation failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate response: {str(e)}"
        )


@router.post("/chat", response_model=ChatResponse)
async def chat_with_script(request: ChatRequest, fastapi_request: Request):
    """
    Chat with your screenplay analysis
    Ask questions about risks, characters, scenes, legal issues, etc.
    """
    try:
        orchestrator = fastapi_request.app.state.orchestrator
        if not orchestrator:
            raise HTTPException(status_code=503, detail="Analysis system not available")
        
        # Load report data
        from .analyze import _load_report_from_storage
        report = await _load_report_from_storage(orchestrator, request.report_id)
        
        if not report:
            raise HTTPException(
                status_code=404,
                detail=f"Report {request.report_id} not found"
            )
        
        # Convert report to dict for context building
        report_dict = {
            "report_id": report.report_id,
            "risk_assessment": {
                "overall_risk_score": report.risk_assessment.overall_risk_score,
                "risk_level": report.risk_assessment.risk_level,
                "risk_factors": report.risk_assessment.risk_factors if hasattr(report.risk_assessment, 'risk_factors') else [],
            },
            "agent_results": {},
            "claims": [],
            "suggestions": [],
            "scenes": [],
            "characters": []
        }
        
        # Extract agent results
        if hasattr(report, 'agent_results'):
            for agent_name, result in report.agent_results.items():
                report_dict["agent_results"][agent_name] = {
                    "success": result.success,
                    "confidence": result.confidence_score,
                    "data_summary": result.data if result.success else {}
                }
        
        # Extract suggestions
        if hasattr(report, 'suggestions'):
            for sug in report.suggestions:
                report_dict["suggestions"].append({
                    "issue_type": sug.issue_type,
                    "severity": sug.severity,
                    "rationale": sug.rationale
                })
        
        # Extract scenes
        if hasattr(report, 'scenes'):
            report_dict["scenes"] = report.scenes
        
        # Build context
        context = _build_report_context(report_dict, request.script_text)
        
        # Generate response
        response = await _generate_chat_response(
            question=request.question,
            context=context,
            history=request.history
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Chat processing failed: {str(e)}"
        )


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest, fastapi_request: Request):
    """
    Stream chat response for real-time updates
    Uses Server-Sent Events (SSE)
    """
    from fastapi.responses import StreamingResponse
    import json
    
    async def event_generator():
        try:
            # Load report and generate response
            orchestrator = fastapi_request.app.state.orchestrator
            from .analyze import _load_report_from_storage
            report = await _load_report_from_storage(orchestrator, request.report_id)
            
            if not report:
                yield f"data: {json.dumps({'error': 'Report not found'})}\n\n"
                return
            
            # Build context and generate response
            report_dict = {"report_id": report.report_id}
            context = _build_report_context(report_dict, request.script_text)
            
            client = await get_gemini_client()
            
            system_prompt = """You are an expert film production analyst. Answer questions about the screenplay analysis."""
            
            prompt = f"""{context}\n\nQuestion: {request.question}\n\nProvide a concise answer based on the analysis data."""
            
            # Simulate streaming by chunking the response
            response = await client.generate_content(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.4,
                max_tokens=1500
            )
            
            # Send in chunks
            chunk_size = 50
            for i in range(0, len(response), chunk_size):
                chunk = response[i:i+chunk_size]
                yield f"data: {json.dumps({'chunk': chunk})}\n\n"
            
            yield f"data: {json.dumps({'done': True})}\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )
