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

IMPORTANT: For each claim, provide the COMPLETE SENTENCE or full phrase from the script. Do not extract partial text or fragments. If a claim spans multiple sentences, include the full context.

For each claim, provide:
- The exact text/quote from script (COMPLETE SENTENCE, not fragments)
- Type of claim (historical/geographic/technical/cultural/brand/biographical) 
- Why it needs verification
- Location in script (approximate)

Format as JSON array:
[
  {
    "id": "unique_id",
    "text": "complete sentence or full phrase from script - not fragments",
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
                max_tokens=3000
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
        
        # Log raw response for debugging
        logger.info(f"Raw Gemini response ({len(response)} chars): {response[:500]}...")
        
        # Step 1: Strip markdown code fences if present
        cleaned_response = response.strip()
        if cleaned_response.startswith("```json"):
            cleaned_response = cleaned_response[7:]  # Remove ```json
        if cleaned_response.startswith("```"):
            cleaned_response = cleaned_response[3:]  # Remove ```
        if cleaned_response.endswith("```"):
            cleaned_response = cleaned_response[:-3]  # Remove trailing ```
        cleaned_response = cleaned_response.strip()
        
        # Step 2: Try to extract JSON array
        json_match = re.search(r'\[.*\]', cleaned_response, re.DOTALL)
        
        # If no complete array found, try to handle truncated JSON
        if not json_match:
            logger.warning(f"No complete JSON array found. Attempting to fix truncated JSON...")
            
            # Check if response starts with [ but is truncated
            if cleaned_response.startswith('['):
                # Try to fix truncated JSON by closing brackets
                truncated = cleaned_response
                # Count open vs close brackets
                open_braces = truncated.count('{') - truncated.count('}')
                open_brackets = truncated.count('[') - truncated.count(']')
                
                # Add missing closing brackets/braces
                truncated += '}' * open_braces + ']' * open_brackets
                
                # Remove trailing incomplete objects (common in truncation)
                last_complete = truncated.rfind('},')
                if last_complete > 0:
                    truncated = truncated[:last_complete + 1] + ']'
                    json_match = re.search(r'\[.*\]', truncated, re.DOTALL)
                    if json_match:
                        logger.info("Successfully repaired truncated JSON response")
        
        if not json_match:
            logger.error(f"No JSON array found in response. Cleaned response preview: {cleaned_response[:300]}")
            raise ValueError(f"Failed to extract JSON array from Gemini response. Response does not contain a valid JSON array. Preview: {cleaned_response[:200]}")
        
        json_str = json_match.group(0)
        
        # Step 3: Parse JSON
        try:
            claims = json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing failed: {e}. JSON string preview: {json_str[:300]}")
            raise ValueError(f"Invalid JSON in Gemini response: {e}")
        
        # Step 4: Validate and clean claims
        cleaned_claims = []
        for claim in claims:
            if isinstance(claim, dict) and "text" in claim and "type" in claim:
                claim_id = claim.get("id", f"claim_{uuid4().hex[:8]}")
                claim_text = claim["text"]
                # Skip very short fragments (less than 15 chars)
                if len(claim_text) < 15:
                    logger.warning(f"Skipping short claim fragment: {claim_text[:50]}")
                    continue
                cleaned_claims.append({
                    "id": claim_id,
                    "text": claim_text,
                    "type": claim.get("type", "unknown"),
                    "confidence": float(claim.get("confidence", 0.7)),
                    "context": claim.get("context", ""),
                    "location_in_script": claim.get("location_in_script", "unknown")
                })
        
        if not cleaned_claims:
            logger.warning(f"Parsed {len(claims)} claims but none passed validation. Raw claims: {claims[:3]}")
        
        logger.info(f"Successfully parsed {len(cleaned_claims)} claims from Gemini response")
        return cleaned_claims[:10]  # Limit to 10 claims max
    
    def _create_fallback_claims(self, text: str) -> List[Dict[str, Any]]:
        """Create fallback claims if JSON parsing fails"""
        
        import re
        
        claims = []
        
        # Look for years with context (historical dates)
        # Find sentences containing years
        year_pattern = r'[^.]*(?:19\d{2}|20\d{2})[^.]*\.'
        year_sentences = re.findall(year_pattern, text)
        for sentence in year_sentences[:3]:
            sentence = sentence.strip()
            if len(sentence) >20:  # Only meaningful sentences
                claims.append({
                    "id": f"year_{uuid4().hex[:8]}",
                    "text": sentence,
                    "type": "historical",
                    "confidence": 0.8,
                    "context": "Historical reference found in script - verify accuracy",
                    "location_in_script": "detected_by_regex"
                })
        
        # Look for real place names with context
        # Find sentences mentioning known cities/landmarks
        location_pattern = r'[^.]*(?:New York|London|Paris|Tokyo|Berlin|Moscow|Times Square|Central Park|White House)[^.]*\.'
        location_sentences = re.findall(location_pattern, text, re.IGNORECASE)
        for sentence in location_sentences[:3]:
            sentence = sentence.strip()
            if len(sentence) >20:
                claims.append({
                    "id": f"location_{uuid4().hex[:8]}",
                    "text": sentence,
                    "type": "geographic",
                    "confidence": 0.7,
                    "context": "Real location mentioned - verify geographic accuracy",
                    "location_in_script": "detected_by_regex"
                })
        
        # If no meaningful claims found, add a generic one
        if not claims:
            # Get first meaningful sentence
            sentences = re.split(r'[.!?]+', text)
            for sentence in sentences:
                sentence = sentence.strip()
                if len(sentence) >30:
                    claims.append({
                        "id": f"general_{uuid4().hex[:8]}",
                        "text": sentence,
                        "type": "general",
                        "confidence": 0.5,
                        "context": "Content analyzed for factual accuracy",
                        "location_in_script": "full_script"
                    })
                    break
        
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