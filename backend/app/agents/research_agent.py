"""
Research Agent - Specializes in fact verification using Parallel API
Handles real-time research and source attribution for claims
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from ..research.parallel_client import ParallelClient
from ..models.agent_schemas import AgentTask, AgentResult, ResearchAgentResult

logger = logging.getLogger(__name__)


class ResearchAgent:
    """
    Research Agent - The 'fact-checker' of the production team
    Uses Parallel API for real-time research and verification
    """
    
    def __init__(self):
        self.parallel_client = ParallelClient()
        self.agent_name = "ResearchAgent"
        
    async def process_task(self, task: AgentTask) -> AgentResult:
        """
        Process research-specific tasks for fact verification
        Uses Parallel API for real-time research
        """
        start_time = datetime.utcnow()
        
        try:
            logger.info(f"Research Agent processing task: {task.task_id}")
            
            # Get claims from Director Agent or extract from script
            claims = task.task_data.get("claims", [])
            if not claims:
                # If no pre-extracted claims, do basic extraction for research
                claims = await self._extract_researchable_claims(
                    task.task_data.get("script_text", "")
                )
            
            result_data = await self._research_claims(claims, task.task_data)
            
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            return AgentResult(
                agent_type="research",
                task_id=task.task_id,
                success=True,
                confidence_score=result_data.get("confidence", 0.8),
                processing_time=processing_time,
                data=result_data,
                metadata={
                    "parallel_api_calls": result_data.get("parallel_api_calls", 0),
                    "claims_researched": len(claims),
                    "research_approach": "parallel_api_primary"
                }
            )
            
        except Exception as e:
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            logger.error(f"Research Agent failed on task {task.task_id}: {str(e)}")
            
            return AgentResult(
                agent_type="research",
                task_id=task.task_id,
                success=False,
                confidence_score=0.0,
                processing_time=processing_time,
                error_message=str(e)
            )
    
    async def _research_claims(self, claims: List[Dict[str, Any]], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Research each claim using Parallel API
        Returns verified, flagged, and uncertain claims with sources
        """
        
        verified_claims = []
        flagged_claims = []
        uncertain_claims = []
        all_sources = []
        api_call_count = 0
        
        # Process claims in batches to avoid overwhelming the API
        batch_size = 5
        for i in range(0, len(claims), batch_size):
            batch = claims[i:i + batch_size]
            
            # Research each claim in the batch
            batch_results = await asyncio.gather(*[
                self._research_single_claim(claim) for claim in batch
            ], return_exceptions=True)
            
            # Process batch results
            for claim, result in zip(batch, batch_results):
                api_call_count += 1
                
                if isinstance(result, Exception):
                    logger.warning(f"Research failed for claim {claim.get('id')}: {result}")
                    uncertain_claims.append({
                        **claim,
                        "verdict": "uncertain",
                        "note": f"Research failed: {str(result)}",
                        "sources": []
                    })
                    continue
                
                # Categorize based on research results
                verdict = result.get("verdict", "uncertain")
                claim_with_result = {
                    **claim,
                    "verdict": verdict,
                    "confidence": result.get("confidence", 0.5),
                    "sources": result.get("sources", []),
                    "note": result.get("note", ""),
                    "research_summary": result.get("summary", "")
                }
                
                if verdict == "verified":
                    verified_claims.append(claim_with_result)
                elif verdict == "flagged":
                    flagged_claims.append(claim_with_result)
                else:
                    uncertain_claims.append(claim_with_result)
                
                # Collect all sources
                all_sources.extend(result.get("sources", []))
        
        # Calculate overall research confidence
        total_claims = len(verified_claims) + len(flagged_claims) + len(uncertain_claims)
        research_confidence = self._calculate_research_confidence(
            verified_claims, flagged_claims, uncertain_claims
        )
        
        return {
            "claims_researched": total_claims,
            "verified_claims": verified_claims,
            "flagged_claims": flagged_claims,
            "uncertain_claims": uncertain_claims,
            "sources": list({s["url"]: s for s in all_sources}.values()),  # Deduplicate sources
            "parallel_api_calls": api_call_count,
            "confidence": research_confidence,
            "research_summary": {
                "verified_count": len(verified_claims),
                "flagged_count": len(flagged_claims),
                "uncertain_count": len(uncertain_claims),
                "success_rate": (len(verified_claims) + len(flagged_claims)) / max(total_claims, 1)
            }
        }
    
    async def _research_single_claim(self, claim: Dict[str, Any]) -> Dict[str, Any]:
        """
        Research a single claim using Parallel API
        Returns verdict, confidence, sources, and notes
        """
        
        try:
            claim_text = claim.get("text", "")
            claim_type = claim.get("type", "general")
            
            # Format research query based on claim type
            query = self._format_research_query(claim_text, claim_type)
            
            # Call Parallel API
            research_result = await self.parallel_client.research_query(
                query=query,
                context={
                    "claim_type": claim_type,
                    "original_claim": claim_text
                }
            )
            
            # Analyze research results to determine verdict
            verdict_analysis = await self._analyze_research_result(
                claim_text, research_result, claim_type
            )
            
            return {
                "verdict": verdict_analysis["verdict"],
                "confidence": verdict_analysis["confidence"], 
                "sources": research_result.get("sources", []),
                "note": verdict_analysis["note"],
                "summary": research_result.get("summary", ""),
                "parallel_response": research_result
            }
            
        except Exception as e:
            logger.error(f"Single claim research failed: {str(e)}")
            return {
                "verdict": "uncertain",
                "confidence": 0.2,
                "sources": [],
                "note": f"Research error: {str(e)}",
                "summary": ""
            }
    
    def _format_research_query(self, claim_text: str, claim_type: str) -> str:
        """Format the claim into an optimal research query for Parallel API"""
        
        # Customize query based on claim type
        if claim_type == "historical":
            return f"Historical fact check: {claim_text}"
        elif claim_type == "location":
            return f"Geographic information: {claim_text}"
        elif claim_type == "technical":
            return f"Technical specifications: {claim_text}"
        elif claim_type == "licensing":
            return f"Copyright and trademark information: {claim_text}"
        else:
            return f"Fact check: {claim_text}"
    
    async def _analyze_research_result(
        self, 
        claim_text: str, 
        research_result: Dict[str, Any], 
        claim_type: str
    ) -> Dict[str, Any]:
        """
        Analyze Parallel API results to determine verdict and confidence
        Returns structured analysis with verdict, confidence, and explanatory note
        """
        
        sources = research_result.get("sources", [])
        summary = research_result.get("summary", "")
        
        # Default to uncertain if no clear research results
        if not sources and not summary:
            return {
                "verdict": "uncertain",
                "confidence": 0.3,
                "note": "Insufficient research data available"
            }
        
        # Analyze source credibility and content
        credible_sources = [s for s in sources if self._is_credible_source(s)]
        
        # Simple heuristic-based analysis (would be enhanced with more sophisticated NLP)
        positive_indicators = ["confirmed", "accurate", "verified", "established", "documented"]
        negative_indicators = ["false", "incorrect", "disputed", "unverified", "myth"]
        
        summary_lower = summary.lower()
        
        positive_score = sum(1 for indicator in positive_indicators if indicator in summary_lower)
        negative_score = sum(1 for indicator in negative_indicators if indicator in summary_lower)
        
        # Determine verdict based on analysis
        if len(credible_sources) >= 2 and positive_score > negative_score:
            return {
                "verdict": "verified",
                "confidence": 0.85,
                "note": f"Verified by {len(credible_sources)} credible sources"
            }
        elif negative_score > 0 or len(credible_sources) == 0:
            return {
                "verdict": "flagged",
                "confidence": 0.75,
                "note": "Potential inaccuracy detected - manual review recommended"
            }
        else:
            return {
                "verdict": "uncertain", 
                "confidence": 0.6,
                "note": "Limited verification available - additional research suggested"
            }
    
    def _is_credible_source(self, source: Dict[str, Any]) -> bool:
        """Determine if a source is credible for fact-checking"""
        
        url = source.get("url", "").lower()
        title = source.get("title", "").lower()
        
        # Credible domains (this would be expanded significantly)
        credible_domains = [
            "wikipedia.org", "britannica.com", "smithsonian.edu",
            "nationalgeographic.com", "bbc.com", "reuters.com",
            "gov", ".edu", "imdb.com"
        ]
        
        # Check if source URL contains credible domains
        return any(domain in url for domain in credible_domains)
    
    async def _extract_researchable_claims(self, script_text: str) -> List[Dict[str, Any]]:
        """
        Fallback claim extraction if Director Agent didn't provide claims
        Simple pattern-based extraction for research purposes
        """
        
        import re
        
        claims = []
        
        # Extract years (potential historical references)
        years = re.findall(r'\b(19|20)\d{2}\b', script_text)
        for year in set(years):
            claims.append({
                "id": f"research_year_{year}",
                "text": f"Year {year}",
                "type": "historical"
            })
        
        # Extract proper nouns (potential people/places)
        proper_nouns = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', script_text)
        for noun in set(proper_nouns[:10]):  # Limit to avoid too many API calls
            if len(noun) > 2:  # Skip very short matches
                claims.append({
                    "id": f"research_noun_{len(claims)}",
                    "text": noun,
                    "type": "general"
                })
        
        return claims
    
    def _calculate_research_confidence(
        self, 
        verified_claims: List[Dict], 
        flagged_claims: List[Dict], 
        uncertain_claims: List[Dict]
    ) -> float:
        """Calculate overall confidence in research results"""
        
        total_claims = len(verified_claims) + len(flagged_claims) + len(uncertain_claims)
        
        if total_claims == 0:
            return 0.5  # Neutral confidence if no claims
        
        # Weight by claim outcomes
        confidence_sum = (
            sum(c.get("confidence", 0.8) for c in verified_claims) +
            sum(c.get("confidence", 0.7) for c in flagged_claims) + 
            sum(c.get("confidence", 0.4) for c in uncertain_claims)
        )
        
        return min(0.95, confidence_sum / total_claims)