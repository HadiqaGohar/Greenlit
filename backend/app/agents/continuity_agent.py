"""
Continuity Agent - Identifies script consistency issues using Gemini AI
Acts as the "script supervisor" who tracks character, timeline, and location consistency
"""

import json
import logging
import re
import time
from typing import Dict, List, Any, Optional

from ..agent.gemini_client import get_gemini_client
from ..models.agent_schemas import AgentTask, AgentResult

logger = logging.getLogger(__name__)


class ContinuityAgent:
    """
    AI-powered continuity analysis agent using Gemini
    Identifies character, timeline, location, and prop inconsistencies
    """
    
    def __init__(self):
        self.agent_type = "continuity"
    
    async def process_task(self, task: AgentTask) -> AgentResult:
        """Process continuity analysis task using Gemini AI"""
        
        start_time = time.time()
        
        try:
            script_text = task.task_data.get("script_text", "")
            if not script_text:
                raise ValueError("No script text provided")
            
            # Get Gemini client
            gemini_client = await get_gemini_client()
            
            # System prompt for continuity analysis
            system_prompt = """You are an expert script supervisor analyzing screenplays for continuity issues.

Analyze the script for ALL of the following continuity problems:

1. CHARACTER INCONSISTENCIES:
   - Character names that might be typos or variations (e.g., "JOHN" vs "JON")
   - Character voice/speech pattern changes between scenes
   - Character descriptions that contradict each other

2. TIMELINE ISSUES:
   - Time-of-day conflicts between consecutive scenes
   - Impossible time sequences (e.g., "tomorrow" followed immediately by "yesterday")
   - Missing time transitions

3. LOCATION CONTINUITY:
   - Impossible geographic transitions (e.g., Tokyo to London in consecutive scenes without travel)
   - Same location appearing with conflicting time contexts
   - INT/EXT inconsistencies for same location

4. PROP TRACKING:
   - Objects picked up but never put down
   - Props that appear/disappear between scenes
   - Important objects mentioned but never shown

For EACH issue found, provide:
- type: "character", "timeline", "location", or "prop"
- severity: "high", "medium", or "low"
- description: What the continuity problem is
- location: Where in the script (scene/line reference)
- suggested_fix: How to resolve it

Format as JSON array:
[
  {
    "type": "character",
    "severity": "medium",
    "description": "Character 'SARAH' appears as 'SARA' in scene 3",
    "location": "Scene 3",
    "suggested_fix": "Verify if these are the same character"
  }
]

If NO continuity issues are found, return an empty array [].
Only flag genuine continuity problems, not creative choices."""

            # Call Gemini for continuity analysis
            response = await gemini_client.generate_content(
                prompt=f"Analyze this script for continuity and consistency issues:\n\n{script_text}",
                system_prompt=system_prompt,
                temperature=0.2,
                max_tokens=3000
            )
            
            # Parse the response
            issues = self._parse_continuity_response(response)
            
            # Categorize issues
            character_issues = [i for i in issues if i.get("type") == "character"]
            timeline_issues = [i for i in issues if i.get("type") == "timeline"]
            location_issues = [i for i in issues if i.get("type") == "location"]
            prop_issues = [i for i in issues if i.get("type") == "prop"]
            
            # Generate recommendations
            recommendations = self._generate_recommendations(
                character_issues, timeline_issues, location_issues, prop_issues
            )
            
            # Build result data
            result_data = {
                "character_inconsistencies": character_issues,
                "timeline_issues": timeline_issues,
                "location_continuity": location_issues,
                "prop_tracking": prop_issues,
                "continuity_recommendations": recommendations,
                "continuity_summary": {
                    "total_issues": len(issues),
                    "character_count": len(character_issues),
                    "location_count": len(location_issues),
                    "severity_breakdown": self._count_by_severity(issues)
                },
                "analysis_method": "gemini_ai"
            }
            
            processing_time = time.time() - start_time
            total_issues = len(issues)
            confidence = max(0.6, 0.9 - (total_issues * 0.05))
            
            return AgentResult(
                agent_type=self.agent_type,
                task_id=task.task_id,
                success=True,
                data=result_data,
                confidence_score=confidence,
                processing_time=processing_time
            )
            
        except Exception as e:
            logger.error(f"Continuity agent processing failed: {str(e)}")
            processing_time = time.time() - start_time
            
            return AgentResult(
                agent_type=self.agent_type,
                task_id=task.task_id,
                success=False,
                error_message=str(e),
                confidence_score=0.0,
                processing_time=processing_time
            )
    
    def _parse_continuity_response(self, response: str) -> List[Dict[str, Any]]:
        """Parse Gemini response for continuity issues"""
        
        # Log raw response for debugging
        logger.info(f"Raw continuity response ({len(response)} chars): {response[:500]}...")
        
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
            logger.error(f"No JSON array found in continuity response. Preview: {cleaned_response[:300]}")
            return []
        
        try:
            issues = json.loads(json_match.group(0))
            
            cleaned = []
            for issue in issues:
                if isinstance(issue, dict) and "type" in issue and "description" in issue:
                    cleaned.append({
                        "type": issue.get("type", "unknown"),
                        "severity": issue.get("severity", "low"),
                        "description": str(issue.get("description", ""))[:300],
                        "location": str(issue.get("location", "unknown")),
                        "suggested_fix": str(issue.get("suggested_fix", ""))[:200]
                    })
            
            logger.info(f"Successfully parsed {len(cleaned)} continuity issues")
            return cleaned[:10]
        
        except json.JSONDecodeError as e:
            logger.error(f"Continuity JSON parsing failed: {e}. Preview: {json_match.group(0)[:300]}")
            return []
    
    def _count_by_severity(self, issues: List[Dict[str, Any]]) -> Dict[str, int]:
        """Count issues by severity level"""
        
        severity_count = {"high": 0, "medium": 0, "low": 0}
        
        for issue in issues:
            severity = issue.get("severity", "low")
            if severity in severity_count:
                severity_count[severity] += 1
        
        return severity_count
    
    def _generate_recommendations(
        self,
        character_issues: List[Dict],
        timeline_issues: List[Dict], 
        location_issues: List[Dict],
        prop_issues: List[Dict]
    ) -> List[str]:
        """Generate actionable continuity recommendations"""
        
        recommendations = []
        
        if character_issues:
            recommendations.append("Review character voice and naming consistency")
            high_priority = [i for i in character_issues if i.get("severity") == "high"]
            if high_priority:
                recommendations.append("Priority: Resolve character naming conflicts")
        
        if timeline_issues:
            recommendations.append("Verify temporal continuity and scene transitions")
        
        if location_issues:
            recommendations.append("Check location transitions for geographical feasibility")
        
        if prop_issues:
            recommendations.append("Track prop continuity throughout scenes")
        
        if not any([character_issues, timeline_issues, location_issues, prop_issues]):
            recommendations.append("No significant continuity issues detected")
        
        return recommendations
