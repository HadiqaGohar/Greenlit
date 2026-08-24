"""
Legal Agent - Identifies potential legal and licensing issues using Gemini AI
Acts as the "legal advisor" who flags copyright, trademark, and clearance risks
"""

import json
import logging
import re
import time
from typing import Dict, List, Any, Optional

from ..agent.gemini_client import get_gemini_client
from ..models.agent_schemas import AgentTask, AgentResult

logger = logging.getLogger(__name__)


class LegalAgent:
    """
    AI-powered legal analysis agent using Gemini
    Identifies copyright, trademark, and clearance issues in scripts
    """
    
    def __init__(self):
        self.agent_type = "legal"
    
    async def process_task(self, task: AgentTask) -> AgentResult:
        """Process legal analysis task using Gemini AI"""
        
        start_time = time.time()
        
        try:
            script_text = task.task_data.get("script_text", "")
            if not script_text:
                raise ValueError("No script text provided")
            
            # Get Gemini client
            gemini_client = await get_gemini_client()
            
            # System prompt for legal analysis
            system_prompt = """You are a specialized entertainment law attorney analyzing scripts for production legal risks.

Analyze the script for ALL of the following legal issues:

1. COPYRIGHT RISKS: Music, films, books, artwork, or any copyrighted content referenced
2. TRADEMARK ISSUES: Brand names, company names, product names used in dialogue or action
3. CLEARANCE NEEDS: Real locations, landmarks, businesses that need filming permissions
4. PRIVACY CONCERNS: References to real people, "based on true story" claims, defamation risks

For EACH issue found, provide:
- type: "copyright", "trademark", "clearance", or "privacy"
- content: The specific text/quote from the script
- severity: "high", "medium", or "low"
- description: What the legal risk is
- suggested_fix: How to resolve it
- estimated_cost: Rough cost estimate (e.g., "$500-2000")
- clearance_action: What specific action to take

Format as JSON array:
[
  {
    "type": "copyright",
    "content": "specific text from script",
    "severity": "high",
    "description": "Why this is a legal risk",
    "suggested_fix": "How to resolve",
    "estimated_cost": "$1000-5000",
    "clearance_action": "Contact music licensing agency"
  }
]

If NO legal issues are found, return an empty array [].
Only flag genuine legal concerns, not creative fiction."""

            # Call Gemini for legal analysis
            response = await gemini_client.generate_content(
                prompt=f"Analyze this script for legal and licensing issues:\n\n{script_text}",
                system_prompt=system_prompt,
                temperature=0.2,
                max_tokens=3000
            )
            
            # Parse the response
            legal_issues = self._parse_legal_response(response)
            
            # Categorize issues
            copyright_risks = [i for i in legal_issues if i.get("type") == "copyright"]
            trademark_issues = [i for i in legal_issues if i.get("type") == "trademark"]
            clearance_items = [i for i in legal_issues if i.get("type") == "clearance"]
            privacy_concerns = [i for i in legal_issues if i.get("type") == "privacy"]
            
            # Generate recommendations
            recommendations = self._generate_recommendations(
                copyright_risks, trademark_issues, clearance_items, privacy_concerns
            )
            
            # Build result data
            result_data = {
                "copyright_risks": copyright_risks[:5],
                "trademark_issues": trademark_issues[:3],
                "clearance_required": clearance_items[:4],
                "privacy_concerns": privacy_concerns,
                "estimated_clearance_cost": self._estimate_costs(copyright_risks, trademark_issues, clearance_items),
                "legal_recommendations": recommendations,
                "risk_summary": {
                    "total_risks": len(legal_issues),
                    "high_priority": len([i for i in legal_issues if i.get("severity") == "high"]),
                    "clearance_items": len(clearance_items)
                },
                "analysis_method": "gemini_ai"
            }
            
            processing_time = time.time() - start_time
            confidence = min(0.9, 0.7 + (0.2 * len(legal_issues) / 10))
            
            return AgentResult(
                agent_type=self.agent_type,
                task_id=task.task_id,
                success=True,
                data=result_data,
                confidence_score=confidence,
                processing_time=processing_time
            )
            
        except Exception as e:
            logger.error(f"Legal agent processing failed: {str(e)}")
            processing_time = time.time() - start_time
            
            return AgentResult(
                agent_type=self.agent_type,
                task_id=task.task_id,
                success=False,
                error_message=str(e),
                confidence_score=0.0,
                processing_time=processing_time
            )
    
    def _parse_legal_response(self, response: str) -> List[Dict[str, Any]]:
        """Parse Gemini response for legal issues"""
        
        try:
            # Try to extract JSON array from response
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                issues = json.loads(json_match.group(0))
                
                # Validate and clean
                cleaned = []
                for issue in issues:
                    if isinstance(issue, dict) and "type" in issue and "content" in issue:
                        cleaned.append({
                            "type": issue.get("type", "unknown"),
                            "content": str(issue.get("content", ""))[:200],
                            "severity": issue.get("severity", "medium"),
                            "description": str(issue.get("description", ""))[:300],
                            "suggested_fix": str(issue.get("suggested_fix", ""))[:200],
                            "estimated_cost": str(issue.get("estimated_cost", "TBD")),
                            "clearance_action": str(issue.get("clearance_action", ""))[:200]
                        })
                
                return cleaned[:10]  # Limit
        
        except Exception as e:
            logger.warning(f"Failed to parse legal response JSON: {str(e)}")
        
        # If parsing fails, return empty list (no false positives)
        return []
    
    def _estimate_costs(
        self, 
        copyright_risks: List[Dict], 
        trademark_issues: List[Dict], 
        clearance_items: List[Dict]
    ) -> str:
        """Estimate total clearance costs"""
        
        total_items = len(copyright_risks) + len(trademark_issues) + len(clearance_items)
        
        if total_items == 0:
            return "$0"
        elif total_items <= 2:
            return "$500-2,000"
        elif total_items <= 5:
            return "$2,000-10,000"
        else:
            return "$10,000+"
    
    def _generate_recommendations(
        self,
        copyright_risks: List[Dict],
        trademark_issues: List[Dict], 
        clearance_items: List[Dict],
        privacy_concerns: List[Dict]
    ) -> List[str]:
        """Generate actionable legal recommendations"""
        
        recommendations = []
        
        if copyright_risks:
            recommendations.append("Review all music and copyrighted content references")
            recommendations.append("Obtain necessary licensing agreements before production")
        
        if trademark_issues:
            recommendations.append("Clear all brand mentions with respective trademark holders")
            high_risk = [i for i in trademark_issues if i.get("severity") == "high"]
            if high_risk:
                recommendations.append("Priority: Address negative brand references immediately")
        
        if clearance_items:
            recommendations.append("Secure location and product placement clearances")
        
        if privacy_concerns:
            recommendations.append("Obtain life rights for any real person references")
        
        if not any([copyright_risks, trademark_issues, clearance_items, privacy_concerns]):
            recommendations.append("No major legal risks identified in script analysis")
        
        return recommendations
