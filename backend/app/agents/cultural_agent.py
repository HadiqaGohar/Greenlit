"""
Cultural Sensitivity Agent - Identifies cultural issues in scripts
Uses Gemini AI to detect stereotyping, misrepresentation, and cultural concerns
"""

import json
import logging
import re
import time
from typing import Dict, List, Any, Optional

from ..agent.gemini_client import get_gemini_client
from ..models.agent_schemas import AgentTask, AgentResult

logger = logging.getLogger(__name__)


class CulturalSensitivityAgent:
    """
    AI-powered cultural sensitivity analysis agent using Gemini
    Identifies stereotyping, misrepresentation, and cultural concerns
    """
    
    def __init__(self):
        self.agent_type = "cultural"
    
    async def process_task(self, task: AgentTask) -> AgentResult:
        """Process cultural sensitivity analysis task"""
        
        start_time = time.time()
        
        try:
            script_text = task.task_data.get("script_text", "")
            if not script_text:
                raise ValueError("No script text provided")
            
            gemini_client = await get_gemini_client()
            
            system_prompt = """You are a cultural sensitivity consultant specializing in entertainment media. Your job is to identify potential cultural issues in scripts that could cause controversy, offend audiences, or misrepresent communities.

Analyze the script for:

1. RACIAL/ETHNIC STEREOTYPES:
   - One-dimensional characters based on race/ethnicity
   - Language or dialogue that reinforces stereotypes
   - Cultural practices shown inaccurately or disrespectfully

2. GENDER REPRESENTATION:
   - Gender stereotyping in roles or behavior
   - Lack of diverse gender representation
   - Objectification or demeaning portrayals

3. DISABILITY REPRESENTATION:
   - Ableist language or tropes
   - "Inspiration porn" or one-dimensional disabled characters
   - Inaccurate depictions of disabilities

4. LGBTQ+ REPRESENTATION:
   - Harmful tropes (bury your gays, etc.)
   - Stereotypical portrayals
   - Lack of authentic representation

5. CULTURAL APPROPRIATION/INACCURACY:
   - Sacred symbols or practices used inappropriately
   - Cultural elements shown without context
   - Mixing or confusing distinct cultures

6. RELIGIOUS SENSITIVITY:
   - Inaccurate or disrespectful religious depictions
   - Stereotyping based on religion
   - Sacred elements used casually

7. AGE REPRESENTATION:
   - Ageist stereotypes
   - Inaccurate depictions of age groups

For EACH issue found, provide:
- category: The type of cultural issue
- severity: "high" (could cause major controversy), "medium" (concerning), "low" (minor)
- description: What the issue is and why it's problematic
- location: Where in the script this occurs
- impact: Who might be offended and how
- suggestion: How to fix or improve the representation

Format as JSON:
{
  "issues": [
    {
      "category": "racial_stereotype",
      "severity": "high",
      "description": "Character uses stereotypical dialect",
      "location": "Scene 2, Page 3",
      "impact": "Could be perceived as mocking African American Vernacular English",
      "suggestion": "Give the character standard dialogue that showcases personality without relying on dialect stereotypes"
    }
  ],
  "overall_sensitivity_score": 75,
  "positive_representations": ["List any good examples of diverse representation"],
  "recommendations": ["General recommendations for improvement"]
}

Be thorough but fair. Focus on genuine issues that could cause real-world harm or offense. Not every mention of culture is problematic - context matters."""

            response = await gemini_client.generate_content(
                prompt=f"Analyze this script for cultural sensitivity issues:\n\n{script_text}",
                system_prompt=system_prompt,
                temperature=0.3,
                max_tokens=3000
            )
            
            cultural_data = self._parse_cultural_response(response)
            
            result_data = {
                "cultural_analysis": cultural_data,
                "analysis_method": "gemini_ai",
                "agent_version": "1.0"
            }
            
            processing_time = time.time() - start_time
            
            return AgentResult(
                agent_type=self.agent_type,
                task_id=task.task_id,
                success=True,
                data=result_data,
                confidence_score=0.75,
                processing_time=processing_time
            )
            
        except Exception as e:
            logger.error(f"Cultural sensitivity agent processing failed: {str(e)}")
            processing_time = time.time() - start_time
            
            return AgentResult(
                agent_type=self.agent_type,
                task_id=task.task_id,
                success=False,
                error_message=str(e),
                confidence_score=0.0,
                processing_time=processing_time
            )
    
    def _parse_cultural_response(self, response: str) -> Dict[str, Any]:
        """Parse Gemini response for cultural sensitivity data"""
        
        logger.info(f"Raw cultural response ({len(response)} chars): {response[:500]}...")
        
        # Strip code fences
        cleaned_response = response.strip()
        if cleaned_response.startswith("```json"):
            cleaned_response = cleaned_response[7:]
        if cleaned_response.startswith("```"):
            cleaned_response = cleaned_response[3:]
        if cleaned_response.endswith("```"):
            cleaned_response = cleaned_response[:-3]
        cleaned_response = cleaned_response.strip()
        
        # Try to extract JSON object
        json_match = re.search(r'\{.*\}', cleaned_response, re.DOTALL)
        if not json_match:
            logger.error(f"No JSON object found in cultural response. Preview: {cleaned_response[:300]}")
            return self._get_default_cultural()
        
        try:
            cultural = json.loads(json_match.group(0))
            logger.info(f"Successfully parsed cultural analysis: {len(cultural.get('issues', []))} issues found")
            return cultural
        except json.JSONDecodeError as e:
            logger.error(f"Cultural JSON parsing failed: {e}")
            return self._get_default_cultural()
    
    def _get_default_cultural(self) -> Dict[str, Any]:
        """Return default cultural data when parsing fails"""
        return {
            "issues": [],
            "overall_sensitivity_score": 50,
            "positive_representations": [],
            "recommendations": ["Please try analyzing the script again"]
        }
