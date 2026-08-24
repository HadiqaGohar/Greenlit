"""
Director Agent - Extracts factual claims from script content
Acts as the "director" who identifies what needs to be fact-checked
"""

import json
import logging
import re
import time
from typing import Dict, List, Any, Optional
from uuid import uuid4

from ..agent.gemini_client import get_gemini_client
from ..models.agent_schemas import AgentTask, AgentResult

logger = logging.getLogger(__name__)


class DirectorAgent:
    """
    Script analysis agent that extracts factual claims for verification
    Simulates a director's eye for details that need research
    """
    
    def __init__(self):
        self.agent_type = "director"
    
    async def process_task(self, task: AgentTask) -> AgentResult:
        """Process script analysis task to extract factual claims"""
        
        start_time = time.time()
        
        try:
            script_text = task.task_data.get("script_text", "")
            if not script_text:
                raise ValueError("No script text provided")
            
            # Get Gemini client
            gemini_client = await get_gemini_client()
            
            # System prompt for claim extraction
            system_prompt = """You are a film director's assistant specialized in identifying factual claims in scripts that need research and verification for production accuracy.

Extract factual claims from the script that could affect production accuracy. Focus on:

1. HISTORICAL FACTS: Dates, events, historical figures
2. GEOGRAPHIC DETAILS: Real locations, addresses, landmarks  
3. TECHNICAL DETAILS: Scientific facts, medical procedures, technology
4. CULTURAL REFERENCES: Customs, traditions, languages
5. BRAND/TRADEMARK MENTIONS: Company names, product names
6. BIOGRAPHICAL INFO: Real people, their achievements, dates

For each claim, provide:
- The exact text/quote from script
- Type of claim (historical/geographic/technical/cultural/brand/biographical)
- Why it needs verification
- Location in script (approximate)

Format as JSON array:
[
  {
    "id": "unique_id",
    "text": "exact quote from script",
    "type": "historical|geographic|technical|cultural|brand|biographical", 
    "confidence": 0.8,
    "context": "why this needs verification",
    "location_in_script": "scene/line reference"
  }
]

Only extract genuine factual claims that could be verified or fact-checked. Ignore obvious fiction."""

            # Generate claims extraction
            response = await gemini_client.generate_content(
                prompt=f"Extract factual claims from this script:\n\n{script_text}",
                system_prompt=system_prompt,
                temperature=0.2,
                max_tokens=2000
            )
            
            # Parse JSON response
            claims = self._parse_claims_response(response)
            
            # Build result data
            result_data = {
                "claims": claims,
                "claims_extracted": len(claims),
                "claims_by_type": self._group_claims_by_type(claims),
                "script_sections": self._analyze_script_sections(script_text),
                "extraction_method": "gemini_ai",
                "agent_version": "1.0"
            }
            
            processing_time = time.time() - start_time
            
            return AgentResult(
                agent_type=self.agent_type,
                task_id=task.task_id,
                success=True,
                data=result_data,
                confidence_score=0.85,
                processing_time=processing_time
            )
            
        except Exception as e:
            logger.error(f"Director agent processing failed: {str(e)}")
            processing_time = time.time() - start_time
            
            return AgentResult(
                agent_type=self.agent_type,
                task_id=task.task_id,
                success=False,
                error_message=str(e),
                confidence_score=0.0,
                processing_time=processing_time
            )
    
    def _parse_claims_response(self, response: str) -> List[Dict[str, Any]]:
        """Parse Gemini response and extract claims"""
        
        try:
            import json
            import re
            
            # Try to extract JSON from response
            # Look for JSON array pattern
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                claims = json.loads(json_str)
                
                # Validate and clean claims
                cleaned_claims = []
                for claim in claims:
                    if isinstance(claim, dict) and "text" in claim and "type" in claim:
                        claim_id = claim.get("id", f"claim_{uuid4().hex[:8]}")
                        cleaned_claims.append({
                            "id": claim_id,
                            "text": claim["text"][:200],  # Limit length
                            "type": claim.get("type", "unknown"),
                            "confidence": float(claim.get("confidence", 0.7)),
                            "context": claim.get("context", "")[:300],
                            "location_in_script": claim.get("location_in_script", "unknown")
                        })
                
                return cleaned_claims[:10]  # Limit to 10 claims max
        
        except Exception as e:
            logger.warning(f"Failed to parse JSON claims: {str(e)}")
        
        # Fallback: create synthetic claims based on simple analysis
        return self._create_fallback_claims(response)
    
    def _create_fallback_claims(self, text: str) -> List[Dict[str, Any]]:
        """Create fallback claims if JSON parsing fails"""
        
        import re
        
        claims = []
        
        # Look for years (historical dates)
        years = re.findall(r'\b(19\d{2}|20\d{2})\b', text)
        for year in set(years[:3]):  # Max 3 years
            claims.append({
                "id": f"year_{uuid4().hex[:8]}",
                "text": f"Reference to year {year}",
                "type": "historical",
                "confidence": 0.8,
                "context": f"Year {year} mentioned in script - verify historical accuracy",
                "location_in_script": "detected_by_regex"
            })
        
        # Look for proper nouns (potential locations/people)
        proper_nouns = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)
        for noun in set(proper_nouns[:3]):  # Max 3 nouns
            if len(noun) > 3 and noun not in ["The", "And", "But", "For"]:
                claims.append({
                    "id": f"name_{uuid4().hex[:8]}",
                    "text": f"Reference to {noun}",
                    "type": "biographical" if " " in noun else "geographic",
                    "confidence": 0.6,
                    "context": f"Proper noun '{noun}' may need fact verification",
                    "location_in_script": "detected_by_regex"
                })
        
        # If no claims found, add a generic one
        if not claims:
            claims.append({
                "id": f"general_{uuid4().hex[:8]}",
                "text": "Script content analyzed",
                "type": "general",
                "confidence": 0.5,
                "context": "No specific factual claims automatically detected",
                "location_in_script": "full_script"
            })
        
        return claims[:5]  # Limit fallback claims
    
    def _group_claims_by_type(self, claims: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Group claims by their type"""
        
        groups = {}
        for claim in claims:
            claim_type = claim.get("type", "unknown")
            if claim_type not in groups:
                groups[claim_type] = []
            groups[claim_type].append(claim)
        
        return groups
    
    def _analyze_script_sections(self, script_text: str) -> List[Dict[str, Any]]:
        """Analyze script structure and sections"""
        
        sections = []
        lines = script_text.split('\n')
        
        # Simple scene detection
        current_section = {
            "type": "scene",
            "start_line": 0,
            "line_count": 0,
            "content_summary": ""
        }
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            # Detect scene headers (common patterns)
            if line.startswith(('INT.', 'EXT.', 'FADE IN:', 'FADE OUT:')):
                if current_section["line_count"] > 0:
                    sections.append(current_section)
                
                current_section = {
                    "type": "scene_header" if line.startswith(('INT.', 'EXT.')) else "transition",
                    "start_line": i,
                    "line_count": 1,
                    "content_summary": line[:50]
                }
            else:
                current_section["line_count"] += 1
        
        # Add final section
        if current_section["line_count"] > 0:
            sections.append(current_section)
        
        return sections