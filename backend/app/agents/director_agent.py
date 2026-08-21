"""
Director Agent - Specializes in script analysis and claims extraction
Uses Gemini Enterprise for sophisticated natural language understanding
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from ..agent.gemini_client import GeminiClient
from ..models.agent_schemas import AgentTask, AgentResult, DirectorAgentResult
from .prompts.director_prompts import DIRECTOR_SYSTEM_PROMPT, CLAIM_EXTRACTION_PROMPT

logger = logging.getLogger(__name__)


class DirectorAgent:
    """
    Director Agent - The 'creative lead' of script analysis
    Responsible for understanding narrative structure and extracting factual claims
    """
    
    def __init__(self):
        self.gemini_client = GeminiClient()
        self.agent_name = "DirectorAgent"
        
    async def process_task(self, task: AgentTask) -> AgentResult:
        """
        Process director-specific tasks for script analysis
        Focus on claims extraction and narrative understanding
        """
        start_time = datetime.utcnow()
        
        try:
            logger.info(f"Director Agent processing task: {task.task_id}")
            
            script_text = task.task_data.get("script_text", "")
            focus = task.task_data.get("focus", "claims_extraction")
            
            if focus == "claims_extraction":
                result_data = await self._extract_claims(script_text, task.task_data)
            else:
                result_data = await self._analyze_script_structure(script_text, task.task_data)
            
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            return AgentResult(
                agent_type="director",
                task_id=task.task_id,
                success=True,
                confidence_score=result_data.get("confidence", 0.85),
                processing_time=processing_time,
                data=result_data,
                metadata={
                    "gemini_model_used": self.gemini_client.model_name,
                    "script_length": len(script_text),
                    "focus_area": focus
                }
            )
            
        except Exception as e:
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            logger.error(f"Director Agent failed on task {task.task_id}: {str(e)}")
            
            return AgentResult(
                agent_type="director",
                task_id=task.task_id,
                success=False,
                confidence_score=0.0,
                processing_time=processing_time,
                error_message=str(e)
            )
    
    async def _extract_claims(self, script_text: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract factual claims from script using Gemini Enterprise
        Identifies historical facts, locations, technical details, people, etc.
        """
        
        prompt = CLAIM_EXTRACTION_PROMPT.format(
            script_text=script_text,
            context_info=context.get("context", {})
        )
        
        try:
            # Use Gemini to extract and categorize claims
            response = await self.gemini_client.generate_content(
                prompt=prompt,
                system_prompt=DIRECTOR_SYSTEM_PROMPT
            )
            
            # Parse Gemini response into structured claims
            claims = await self._parse_gemini_claims_response(response, script_text)
            
            # Group claims by type for better organization
            claims_by_type = self._categorize_claims(claims)
            
            return {
                "claims": claims,
                "claims_by_type": claims_by_type,
                "claims_extracted": len(claims),
                "script_sections": self._identify_script_sections(script_text),
                "confidence": self._calculate_extraction_confidence(claims, script_text),
                "metadata": {
                    "extraction_method": "gemini_enterprise",
                    "prompt_version": "v1.0",
                    "processing_approach": "narrative_aware"
                }
            }
            
        except Exception as e:
            logger.error(f"Gemini claims extraction failed: {str(e)}")
            # Fallback to pattern-based extraction
            return await self._fallback_claims_extraction(script_text)
    
    async def _parse_gemini_claims_response(self, response: str, script_text: str) -> List[Dict[str, Any]]:
        """Parse Gemini's response into structured claim objects"""
        
        claims = []
        
        try:
            # Expect Gemini to return structured format
            # This would be enhanced based on actual Gemini response format
            lines = response.strip().split('\n')
            
            current_claim = {}
            for line in lines:
                line = line.strip()
                
                if line.startswith("CLAIM:"):
                    if current_claim:
                        claims.append(current_claim)
                    current_claim = {
                        "id": f"claim_{len(claims) + 1}",
                        "text": line.replace("CLAIM:", "").strip(),
                        "confidence": 0.8  # Default confidence
                    }
                    
                elif line.startswith("TYPE:"):
                    current_claim["type"] = line.replace("TYPE:", "").strip().lower()
                    
                elif line.startswith("LOCATION:"):
                    current_claim["location_in_script"] = line.replace("LOCATION:", "").strip()
                    
                elif line.startswith("CONTEXT:"):
                    current_claim["context"] = line.replace("CONTEXT:", "").strip()
                    
                elif line.startswith("CONFIDENCE:"):
                    try:
                        current_claim["confidence"] = float(line.replace("CONFIDENCE:", "").strip())
                    except ValueError:
                        current_claim["confidence"] = 0.8
            
            # Add the last claim
            if current_claim:
                claims.append(current_claim)
                
        except Exception as e:
            logger.error(f"Failed to parse Gemini response: {str(e)}")
            # Return basic claim structure if parsing fails
            claims = [{
                "id": "claim_1",
                "text": "Failed to parse claims - manual review needed", 
                "type": "technical",
                "confidence": 0.3,
                "location_in_script": "unknown"
            }]
        
        return claims
    
    def _categorize_claims(self, claims: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Group claims by type for organized presentation"""
        
        categories = {
            "historical": [],
            "location": [],
            "technical": [],
            "licensing": [],
            "character": [],
            "other": []
        }
        
        for claim in claims:
            claim_type = claim.get("type", "other")
            if claim_type in categories:
                categories[claim_type].append(claim)
            else:
                categories["other"].append(claim)
        
        # Remove empty categories
        return {k: v for k, v in categories.items() if v}
    
    def _identify_script_sections(self, script_text: str) -> List[Dict[str, str]]:
        """Identify major script sections (scenes, acts, etc.)"""
        
        sections = []
        lines = script_text.split('\n')
        
        current_scene = None
        scene_start_line = 0
        
        for i, line in enumerate(lines):
            line = line.strip().upper()
            
            # Look for scene headers (common screenplay format)
            if any(indicator in line for indicator in ['EXT.', 'INT.', 'FADE IN:', 'FADE OUT']):
                if current_scene:
                    sections.append({
                        "type": "scene",
                        "title": current_scene,
                        "start_line": scene_start_line,
                        "end_line": i,
                        "line_count": i - scene_start_line
                    })
                
                current_scene = line
                scene_start_line = i
        
        # Add the final scene
        if current_scene:
            sections.append({
                "type": "scene", 
                "title": current_scene,
                "start_line": scene_start_line,
                "end_line": len(lines),
                "line_count": len(lines) - scene_start_line
            })
        
        return sections
    
    def _calculate_extraction_confidence(self, claims: List[Dict[str, Any]], script_text: str) -> float:
        """Calculate overall confidence in claims extraction"""
        
        if not claims:
            return 0.3  # Low confidence if no claims found
        
        # Base confidence on claim quality and script complexity
        avg_claim_confidence = sum(c.get("confidence", 0.5) for c in claims) / len(claims)
        
        # Adjust based on script length and structure
        script_complexity_factor = min(1.0, len(script_text) / 5000)  # Longer scripts are more complex
        
        final_confidence = (avg_claim_confidence * 0.7) + (script_complexity_factor * 0.3)
        
        return min(0.95, max(0.1, final_confidence))  # Clamp between 0.1 and 0.95
    
    async def _fallback_claims_extraction(self, script_text: str) -> Dict[str, Any]:
        """Fallback extraction method if Gemini fails"""
        
        # Simple pattern-based extraction as backup
        import re
        
        # Look for years (potential historical references)
        years = re.findall(r'\b(19|20)\d{2}\b', script_text)
        
        # Look for location indicators
        locations = re.findall(r'(EXT\.|INT\.)\s+([A-Z\s]+)', script_text)
        
        fallback_claims = []
        
        for year in set(years):
            fallback_claims.append({
                "id": f"fallback_year_{year}",
                "text": f"Year reference: {year}",
                "type": "historical", 
                "confidence": 0.6,
                "location_in_script": "pattern_detected"
            })
        
        for ext_int, location in locations:
            fallback_claims.append({
                "id": f"fallback_loc_{len(fallback_claims)}",
                "text": f"Location: {location.strip()}",
                "type": "location",
                "confidence": 0.7, 
                "location_in_script": f"{ext_int} {location}"
            })
        
        return {
            "claims": fallback_claims,
            "claims_extracted": len(fallback_claims),
            "confidence": 0.5,  # Lower confidence for fallback
            "metadata": {
                "extraction_method": "pattern_fallback",
                "note": "Gemini extraction failed, using pattern matching"
            }
        }