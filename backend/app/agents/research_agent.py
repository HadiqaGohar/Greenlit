"""
Research Agent - Verifies factual claims using Parallel API
Acts as the "researcher" who fact-checks extracted claims
"""

import asyncio
import logging
import time
from typing import Dict, List, Any, Optional

from ..research.parallel_client import get_parallel_client
from ..models.agent_schemas import AgentTask, AgentResult

logger = logging.getLogger(__name__)

# Max claims to research (balance between thoroughness and speed)
MAX_CLAIMS = 3
# Timeout per claim in seconds
CLAIM_TIMEOUT = 60.0


class ResearchAgent:
    """
    Research agent that verifies factual claims using live data sources
    Uses Parallel API to research and validate script content
    """
    
    def __init__(self):
        self.agent_type = "research"
    
    async def process_task(self, task: AgentTask) -> AgentResult:
        """Process research task to verify factual claims"""
        
        start_time = time.time()
        
        try:
            script_text = task.task_data.get("script_text", "")
            claims = task.task_data.get("claims", [])
            
            if not script_text:
                raise ValueError("No script text provided")
            
            # Extract or use provided claims
            if not claims:
                claims = await self._extract_research_queries(script_text)
            
            # Limit claims for speed
            claims = claims[:MAX_CLAIMS]
            logger.info(f"Research agent: verifying {len(claims)} claims (limited to {MAX_CLAIMS} for speed)")
            
            # Get Parallel client
            parallel_client = await get_parallel_client()
            
            # Research all claims IN PARALLEL with timeout
            async def research_single_claim(claim):
                try:
                    query = self._create_research_query(claim)
                    logger.info(f"Researching claim {claim.get('id', 'unknown')}: {query[:80]}...")
                    
                    # Add timeout per claim
                    research_result = await asyncio.wait_for(
                        parallel_client.research_query(
                            query=query,
                            context={"script_context": script_text[:500]}
                        ),
                        timeout=CLAIM_TIMEOUT
                    )
                    
                    verdict_info = self._analyze_research_result(claim, research_result)
                    logger.info(f"Claim {claim.get('id', 'unknown')}: {verdict_info['verdict']} ({verdict_info['confidence']:.0%})")
                    return {
                        **claim,
                        "verdict": verdict_info["verdict"],
                        "confidence": verdict_info["confidence"],
                        "sources": research_result.get("sources", []),
                        "research_summary": research_result.get("summary", ""),
                        "note": verdict_info["note"]
                    }
                except asyncio.TimeoutError:
                    logger.warning(f"Research timed out for claim {claim.get('id', 'unknown')} after {CLAIM_TIMEOUT}s")
                    return {
                        **claim,
                        "verdict": "uncertain",
                        "confidence": 0.5,
                        "sources": [],
                        "research_summary": "Research timed out",
                        "note": f"Research exceeded {CLAIM_TIMEOUT}s timeout - marked as uncertain"
                    }
                except Exception as e:
                    logger.warning(f"Research failed for claim {claim.get('id', 'unknown')}: {str(e)}")
                    return {
                        **claim,
                        "verdict": "error",
                        "confidence": 0.0,
                        "sources": [],
                        "research_summary": "Research failed",
                        "note": f"Research error: {str(e)}"
                    }
            
            # Fire all claims at once — total time = slowest claim, not sum of all
            researched_claims = await asyncio.gather(*[
                research_single_claim(claim) for claim in claims
            ])
            
            # Categorize results
            verified_claims = [c for c in researched_claims if c["verdict"] == "verified"]
            flagged_claims = [c for c in researched_claims if c["verdict"] == "flagged"] 
            uncertain_claims = [c for c in researched_claims if c["verdict"] in ["uncertain", "error"]]
            
            # Build result data
            result_data = {
                "claims": researched_claims,
                "claims_researched": len(researched_claims),
                "verified_claims": verified_claims,
                "flagged_claims": flagged_claims, 
                "uncertain_claims": uncertain_claims,
                "sources": self._collect_all_sources(researched_claims),
                "research_summary": {
                    "verified_count": len(verified_claims),
                    "flagged_count": len(flagged_claims),
                    "uncertain_count": len(uncertain_claims),
                    "overall_accuracy": len(verified_claims) / max(len(researched_claims), 1)
                }
            }
            
            processing_time = time.time() - start_time
            
            return AgentResult(
                agent_type=self.agent_type,
                task_id=task.task_id,
                success=True,
                data=result_data,
                confidence_score=min(0.9, sum(c["confidence"] for c in researched_claims) / max(len(researched_claims), 1)),
                processing_time=processing_time
            )
            
        except Exception as e:
            logger.error(f"Research agent processing failed: {str(e)}")
            processing_time = time.time() - start_time
            
            return AgentResult(
                agent_type=self.agent_type,
                task_id=task.task_id,
                success=False,
                error_message=str(e),
                confidence_score=0.0,
                processing_time=processing_time
            )
    
    async def _extract_research_queries(self, script_text: str) -> List[Dict[str, Any]]:
        """Extract basic research queries from script text as fallback"""
        
        import re
        from uuid import uuid4
        
        queries = []
        
        # Extract years for historical verification
        years = re.findall(r'\b(19\d{2}|20\d{2})\b', script_text)
        for year in set(years[:2]):
            queries.append({
                "id": f"year_{uuid4().hex[:8]}", 
                "text": f"Events in {year}",
                "type": "historical",
                "confidence": 0.8
            })
        
        # Extract proper nouns for fact-checking
        nouns = re.findall(r'\b[A-Z][a-zA-Z]{2,}\b', script_text)
        for noun in set(nouns[:3]):
            if noun not in ["THE", "AND", "BUT", "FOR", "WITH", "INT", "EXT"]:
                queries.append({
                    "id": f"noun_{uuid4().hex[:8]}",
                    "text": f"Information about {noun}",
                    "type": "factual",
                    "confidence": 0.6
                })
        
        return queries[:5]
    
    def _create_research_query(self, claim: Dict[str, Any]) -> str:
        """Create effective research query from claim"""
        
        claim_text = claim.get("text", "")
        claim_type = claim.get("type", "")
        
        # Optimize query based on claim type
        if claim_type == "historical":
            return f"Historical accuracy: {claim_text}"
        elif claim_type == "geographic":
            return f"Geographic information: {claim_text}"
        elif claim_type == "biographical":
            return f"Biography and facts: {claim_text}"
        elif claim_type == "technical":
            return f"Technical accuracy: {claim_text}"
        else:
            return f"Fact check: {claim_text}"
    
    def _analyze_research_result(
        self, 
        claim: Dict[str, Any], 
        research_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze research result and determine verdict"""
        
        confidence = research_result.get("confidence", 0.5)
        summary = research_result.get("summary", "").lower()
        sources = research_result.get("sources", [])
        
        # Check negative/flagged indicators first
        if any(w in summary for w in ["false", "inaccurate", "incorrect", "misleading", "anachronism", "unlicensed", "infring"]):
            verdict = "flagged"
            note = "Research indicates inaccuracy or clearance risk"
            confidence = min(confidence, 0.45)
        # Check positive/verified indicators
        elif any(w in summary for w in ["supported", "true", "accurate", "confirmed", "correct", "verified"]):
            verdict = "verified"
            note = "Research confirms this claim"
            confidence = max(confidence, 0.8)
        elif confidence >= 0.8:
            verdict = "verified"
            note = "Research confirms this claim with high confidence"
        elif confidence <= 0.35:
            verdict = "flagged" 
            note = "Research suggests this claim may be inaccurate or unverified"
        elif len(sources) == 0:
            verdict = "uncertain"
            note = "Insufficient research data to verify conclusively"
            confidence = 0.5
        else:
            verdict = "uncertain"
            note = "Research provides mixed or contextual results"
        
        return {
            "verdict": verdict,
            "confidence": confidence,
            "note": note
        }
    
    def _collect_all_sources(self, claims: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Collect all unique sources from researched claims"""
        
        all_sources = []
        seen_urls = set()
        
        for claim in claims:
            for source in claim.get("sources", []):
                url = source.get("url", "")
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    all_sources.append({
                        "title": source.get("title", "Unknown Source"),
                        "url": url,
                        "credibility": source.get("credibility", 0.7),
                        "used_for": claim.get("id", "unknown")
                    })
        
        # Sort by credibility
        all_sources.sort(key=lambda x: x["credibility"], reverse=True)
        return all_sources[:10]  # Limit to top 10 sources