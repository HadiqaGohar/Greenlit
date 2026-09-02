"""
Budget Agent - Estimates production costs from script content
Uses Gemini AI to analyze script requirements and estimate budget
"""

import json
import logging
import re
import time
from typing import Dict, List, Any, Optional

from ..agent.gemini_client import get_gemini_client
from ..models.agent_schemas import AgentTask, AgentResult

logger = logging.getLogger(__name__)


class BudgetAgent:
    """
    AI-powered budget estimation agent using Gemini
    Analyzes script to estimate production costs
    """
    
    def __init__(self):
        self.agent_type = "budget"
    
    async def process_task(self, task: AgentTask) -> AgentResult:
        """Process budget estimation task"""
        
        start_time = time.time()
        
        try:
            script_text = task.task_data.get("script_text", "")
            if not script_text:
                raise ValueError("No script text provided")
            
            gemini_client = await get_gemini_client()
            
            system_prompt = """You are a veteran film production accountant and line producer with 20+ years of experience estimating budgets for independent and studio films.

Analyze the script and provide a detailed production budget estimate. Consider:

1. CAST REQUIREMENTS:
   - Number of speaking roles
   - Number of background extras
   - stunt performers needed

2. LOCATIONS:
   - Number of unique locations
   - Interior vs exterior
   - Practical vs studio builds
   - Night shoots required

3. PROPS & SET DRESSING:
   - Vehicles (luxury cars, period cars, etc.)
   - Technology props
   - Period-specific items
   - Special props

4. VISUAL EFFECTS:
   - CGI requirements
   - Practical effects
   - Stunts and action sequences

5. WARDROBE & MAKEUP:
   - Costume changes
   - Special makeup/prosthetics
   - Period costumes

6. OTHER COSTS:
   - Music/soundtrack licensing
   - Equipment rental
   - Catering
   - Travel

For EACH category, provide:
- estimated_cost: Dollar range (e.g., "$5,000-15,000")
- line_items: Specific items with individual costs
- confidence: How confident you are in this estimate (0.0-1.0)
- notes: Any assumptions or considerations

Also provide:
- total_estimated_budget: Overall budget range
- budget_level: "micro" (<$500K), "low" ($500K-2M), "medium" ($2M-10M), "high" ($10M-50M), "blockbuster" ($50M+)
- cost-saving_tips: Suggestions to reduce budget

Format as JSON:
{
  "categories": [
    {
      "name": "Cast & Talent",
      "estimated_cost": "$50,000-100,000",
      "confidence": 0.8,
      "line_items": [
        {"item": "Lead Actor (1)", "cost": "$20,000-40,000"},
        {"item": "Supporting Cast (3)", "cost": "$15,000-30,000"}
      ],
      "notes": "Assuming SAG-AFTRA rates for indie production"
    }
  ],
  "total_estimated_budget": "$150,000-300,000",
  "budget_level": "low",
  "cost_saving_tips": [
    "Consider using real locations instead of studio builds",
    "Limit night shoots to reduce overtime costs"
  ]
}

Be realistic and specific. Base estimates on current industry rates."""

            response = await gemini_client.generate_content(
                prompt=f"Estimate production budget for this script:\n\n{script_text}",
                system_prompt=system_prompt,
                temperature=0.3,
                max_tokens=3000
            )
            
            budget_data = self._parse_budget_response(response)
            
            result_data = {
                "budget": budget_data,
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
            logger.error(f"Budget agent processing failed: {str(e)}")
            processing_time = time.time() - start_time
            
            return AgentResult(
                agent_type=self.agent_type,
                task_id=task.task_id,
                success=False,
                error_message=str(e),
                confidence_score=0.0,
                processing_time=processing_time
            )
    
    def _parse_budget_response(self, response: str) -> Dict[str, Any]:
        """Parse Gemini response for budget data"""
        
        logger.info(f"Raw budget response ({len(response)} chars): {response[:500]}...")
        
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
            logger.error(f"No JSON object found in budget response. Preview: {cleaned_response[:300]}")
            return self._get_default_budget()
        
        try:
            budget = json.loads(json_match.group(0))
            logger.info(f"Successfully parsed budget estimate: {budget.get('total_estimated_budget', 'unknown')}")
            return budget
        except json.JSONDecodeError as e:
            logger.error(f"Budget JSON parsing failed: {e}")
            return self._get_default_budget()
    
    def _get_default_budget(self) -> Dict[str, Any]:
        """Return default budget when parsing fails"""
        return {
            "categories": [],
            "total_estimated_budget": "Unable to estimate",
            "budget_level": "unknown",
            "cost_saving_tips": ["Please try analyzing the script again"]
        }
