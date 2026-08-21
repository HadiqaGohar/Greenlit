"""
Legal Agent - Specializes in copyright, licensing, and legal risk assessment
Uses Gemini Enterprise with legal-focused prompts for comprehensive risk analysis
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import re

from ..agent.gemini_client import GeminiClient
from ..models.agent_schemas import AgentTask, AgentResult, LegalAgentResult
from .prompts.legal_prompts import LEGAL_SYSTEM_PROMPT, COPYRIGHT_ANALYSIS_PROMPT, CLEARANCE_CHECKLIST_PROMPT

logger = logging.getLogger(__name__)


class LegalAgent:
    """
    Legal Agent - The 'production lawyer' of the team
    Identifies copyright, trademark, and licensing risks that could impact production
    """
    
    def __init__(self):
        self.gemini_client = GeminiClient()
        self.agent_name = "LegalAgent"
        
    async def process_task(self, task: AgentTask) -> AgentResult:
        """
        Process legal-specific tasks for copyright and licensing analysis
        Focus on identifying potential legal risks before production
        """
        start_time = datetime.utcnow()
        
        try:
            logger.info(f"Legal Agent processing task: {task.task_id}")
            
            script_text = task.task_data.get("script_text", "")
            focus = task.task_data.get("focus", "licensing_risks")
            
            if focus == "licensing_risks":
                result_data = await self._analyze_licensing_risks(script_text, task.task_data)
            elif focus == "copyright_assessment":
                result_data = await self._analyze_copyright_risks(script_text, task.task_data)
            else:
                result_data = await self._comprehensive_legal_analysis(script_text, task.task_data)
            
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            return AgentResult(
                agent_type="legal",
                task_id=task.task_id,
                success=True,
                confidence_score=result_data.get("confidence", 0.8),
                processing_time=processing_time,
                data=result_data,
                metadata={
                    "gemini_model_used": self.gemini_client.model_name,
                    "analysis_focus": focus,
                    "risk_categories_checked": len(result_data.get("copyright_risks", [])) + len(result_data.get("trademark_issues", []))
                }
            )
            
        except Exception as e:
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            logger.error(f"Legal Agent failed on task {task.task_id}: {str(e)}")
            
            return AgentResult(
                agent_type="legal",
                task_id=task.task_id,
                success=False,
                confidence_score=0.0,
                processing_time=processing_time,
                error_message=str(e)
            )
    
    async def _analyze_licensing_risks(self, script_text: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Comprehensive analysis of licensing and clearance requirements
        Identifies copyrighted material, trademarks, real people, music, etc.
        """
        
        # Use Gemini for sophisticated legal analysis
        prompt = COPYRIGHT_ANALYSIS_PROMPT.format(
            script_text=script_text,
            context_info=context.get("context", {})
        )
        
        try:
            gemini_response = await self.gemini_client.generate_content(
                prompt=prompt,
                system_prompt=LEGAL_SYSTEM_PROMPT
            )
            
            # Parse Gemini's legal analysis
            legal_analysis = await self._parse_legal_analysis(gemini_response, script_text)
            
            # Combine with pattern-based detection for comprehensive coverage
            pattern_analysis = await self._pattern_based_legal_scan(script_text)
            
            # Merge and prioritize findings
            combined_analysis = self._merge_legal_findings(legal_analysis, pattern_analysis)
            
            # Generate clearance checklist
            clearance_checklist = await self._generate_clearance_checklist(combined_analysis)
            
            return {
                "copyright_risks": combined_analysis["copyright_risks"],
                "trademark_issues": combined_analysis["trademark_issues"],
                "clearance_required": combined_analysis["clearance_required"],
                "real_person_mentions": combined_analysis["real_person_mentions"],
                "music_references": combined_analysis.get("music_references", []),
                "licensing_checklist": clearance_checklist,
                "estimated_clearance_cost": self._estimate_clearance_costs(combined_analysis),
                "confidence": combined_analysis["confidence"],
                "metadata": {
                    "analysis_method": "gemini_plus_patterns",
                    "legal_categories": list(combined_analysis.keys()),
                    "high_risk_count": len([r for r in combined_analysis["copyright_risks"] if r.get("severity") == "high"])
                }
            }
            
        except Exception as e:
            logger.error(f"Legal analysis failed: {str(e)}")
            # Fallback to pattern-based analysis only
            return await self._pattern_based_legal_scan(script_text)
    
    async def _parse_legal_analysis(self, gemini_response: str, script_text: str) -> Dict[str, Any]:
        """Parse Gemini's legal analysis into structured findings"""
        
        analysis = {
            "copyright_risks": [],
            "trademark_issues": [],
            "clearance_required": [],
            "real_person_mentions": [],
            "confidence": 0.8
        }
        
        try:
            lines = gemini_response.strip().split('\n')
            
            current_risk = {}
            current_category = None
            
            for line in lines:
                line = line.strip()
                
                if line.startswith("COPYRIGHT_RISK:"):
                    if current_risk and current_category:
                        analysis[current_category].append(current_risk)
                    current_risk = {
                        "type": "copyright",
                        "description": line.replace("COPYRIGHT_RISK:", "").strip(),
                        "severity": "medium"  # Default severity
                    }
                    current_category = "copyright_risks"
                    
                elif line.startswith("TRADEMARK:"):
                    if current_risk and current_category:
                        analysis[current_category].append(current_risk)
                    current_risk = {
                        "type": "trademark", 
                        "description": line.replace("TRADEMARK:", "").strip(),
                        "severity": "medium"
                    }
                    current_category = "trademark_issues"
                    
                elif line.startswith("REAL_PERSON:"):
                    if current_risk and current_category:
                        analysis[current_category].append(current_risk)
                    current_risk = {
                        "type": "real_person",
                        "name": line.replace("REAL_PERSON:", "").strip(),
                        "severity": "high"  # Real people are high risk
                    }
                    current_category = "real_person_mentions"
                    
                elif line.startswith("SEVERITY:"):
                    if current_risk:
                        current_risk["severity"] = line.replace("SEVERITY:", "").strip().lower()
                        
                elif line.startswith("CLEARANCE_ACTION:"):
                    if current_risk:
                        current_risk["clearance_action"] = line.replace("CLEARANCE_ACTION:", "").strip()
                        
                elif line.startswith("LOCATION:"):
                    if current_risk:
                        current_risk["location_in_script"] = line.replace("LOCATION:", "").strip()
            
            # Add the last risk
            if current_risk and current_category:
                analysis[current_category].append(current_risk)
                
        except Exception as e:
            logger.error(f"Failed to parse legal analysis: {str(e)}")
        
        return analysis
    
    async def _pattern_based_legal_scan(self, script_text: str) -> Dict[str, Any]:
        """
        Pattern-based detection of potential legal issues
        Backup method and supplement to Gemini analysis
        """
        
        copyright_risks = []
        trademark_issues = []
        real_person_mentions = []
        music_references = []
        
        # Known brand patterns
        brand_patterns = [
            r'\b(Apple|iPhone|iPad|MacBook|Google|Microsoft|Facebook|Instagram|Twitter|YouTube|Netflix|Amazon|Coca-Cola|Pepsi|McDonald\'s|Starbucks|Nike|Adidas|BMW|Mercedes|Toyota|Ford)\b',
            r'\b(Marvel|DC Comics|Disney|Warner Bros|Sony|Universal|Paramount)\b'
        ]
        
        # Music and entertainment patterns
        music_patterns = [
            r'(song|music|album|band|singer|artist)[\s\w]*["\']([\w\s]+)["\']',
            r'plays?\s+["\']([\w\s]+)["\']',  # "plays 'Song Title'"
            r'listening to\s+["\']([\w\s]+)["\']'
        ]
        
        # Real person indicators (common surnames with titles)
        person_patterns = [
            r'(President|Mr\.|Mrs\.|Dr\.|Professor|Captain|Director)\s+([A-Z][a-z]+)',
            r'\b(Einstein|Shakespeare|Lincoln|Washington|Churchill|Kennedy|Roosevelt)\b'
        ]
        
        # Scan for brand mentions
        for pattern in brand_patterns:
            matches = re.findall(pattern, script_text, re.IGNORECASE)
            for match in matches:
                brand_name = match if isinstance(match, str) else match[0]
                trademark_issues.append({
                    "type": "trademark",
                    "brand": brand_name,
                    "description": f"Brand mention: {brand_name}",
                    "severity": "medium",
                    "clearance_action": f"Obtain permission to use {brand_name} or use generic alternative"
                })
        
        # Scan for music references
        for pattern in music_patterns:
            matches = re.findall(pattern, script_text, re.IGNORECASE)
            for match in matches:
                song_title = match[1] if isinstance(match, tuple) else match
                music_references.append({
                    "type": "music",
                    "title": song_title,
                    "description": f"Music reference: {song_title}",
                    "severity": "high",  # Music licensing is complex
                    "clearance_action": f"Obtain sync license for '{song_title}' or use alternative"
                })
        
        # Scan for real person mentions
        for pattern in person_patterns:
            matches = re.findall(pattern, script_text, re.IGNORECASE)
            for match in matches:
                person_name = match[1] if isinstance(match, tuple) else match
                real_person_mentions.append({
                    "type": "real_person",
                    "name": person_name,
                    "description": f"Real person reference: {person_name}",
                    "severity": "high",
                    "clearance_action": f"Review legal requirements for depicting {person_name}"
                })
        
        # Check for copyright-sensitive content
        copyright_indicators = [
            "based on the novel", "adapted from", "inspired by", "remake of"
        ]
        
        for indicator in copyright_indicators:
            if indicator.lower() in script_text.lower():
                copyright_risks.append({
                    "type": "adaptation",
                    "description": f"Potential adaptation: contains '{indicator}'",
                    "severity": "high",
                    "clearance_action": "Verify rights ownership for source material"
                })
        
        return {
            "copyright_risks": copyright_risks,
            "trademark_issues": trademark_issues,
            "clearance_required": copyright_risks + trademark_issues + music_references,
            "real_person_mentions": real_person_mentions,
            "music_references": music_references,
            "confidence": 0.7,  # Lower confidence for pattern-based analysis
            "metadata": {
                "analysis_method": "pattern_based",
                "patterns_checked": len(brand_patterns) + len(music_patterns) + len(person_patterns)
            }
        }
    
    def _merge_legal_findings(self, gemini_analysis: Dict[str, Any], pattern_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Merge and deduplicate findings from Gemini and pattern-based analysis"""
        
        merged = {
            "copyright_risks": [],
            "trademark_issues": [],
            "clearance_required": [],
            "real_person_mentions": [],
            "music_references": [],
            "confidence": (gemini_analysis.get("confidence", 0.8) + pattern_analysis.get("confidence", 0.7)) / 2
        }
        
        # Merge each category, avoiding duplicates
        for category in ["copyright_risks", "trademark_issues", "real_person_mentions"]:
            gemini_items = gemini_analysis.get(category, [])
            pattern_items = pattern_analysis.get(category, [])
            
            # Simple deduplication by description
            seen_descriptions = set()
            for item in gemini_items + pattern_items:
                desc = item.get("description", "")
                if desc not in seen_descriptions:
                    merged[category].append(item)
                    seen_descriptions.add(desc)
        
        # Music references from pattern analysis
        merged["music_references"] = pattern_analysis.get("music_references", [])
        
        # Clearance required is combination of all risks
        merged["clearance_required"] = (
            merged["copyright_risks"] + 
            merged["trademark_issues"] + 
            merged["music_references"]
        )
        
        return merged
    
    async def _generate_clearance_checklist(self, legal_analysis: Dict[str, Any]) -> List[str]:
        """Generate actionable clearance checklist for production team"""
        
        checklist = []
        
        # High-priority items first
        high_risk_items = [
            item for category in ["copyright_risks", "trademark_issues", "real_person_mentions"]
            for item in legal_analysis.get(category, [])
            if item.get("severity") == "high"
        ]
        
        if high_risk_items:
            checklist.append("🚨 HIGH PRIORITY - Address before pre-production:")
            for item in high_risk_items:
                action = item.get("clearance_action", f"Review {item.get('description', 'legal issue')}")
                checklist.append(f"   • {action}")
        
        # Medium priority items
        medium_risk_items = [
            item for category in ["copyright_risks", "trademark_issues"]
            for item in legal_analysis.get(category, [])
            if item.get("severity") == "medium"
        ]
        
        if medium_risk_items:
            checklist.append("⚠️ MEDIUM PRIORITY - Address during pre-production:")
            for item in medium_risk_items:
                action = item.get("clearance_action", f"Review {item.get('description', 'legal issue')}")
                checklist.append(f"   • {action}")
        
        # General recommendations
        if legal_analysis.get("real_person_mentions"):
            checklist.append("📋 GENERAL RECOMMENDATIONS:")
            checklist.append("   • Consult entertainment lawyer for real person depictions")
            checklist.append("   • Consider obtaining life rights or disclaimers")
        
        if legal_analysis.get("music_references"):
            checklist.append("   • Contact music supervisor for sync licensing")
            checklist.append("   • Budget for music clearance costs")
        
        return checklist if checklist else ["✅ No immediate legal clearances required"]
    
    def _estimate_clearance_costs(self, legal_analysis: Dict[str, Any]) -> str:
        """Estimate rough clearance costs based on identified issues"""
        
        total_high_risk = sum(
            len([item for item in legal_analysis.get(category, []) if item.get("severity") == "high"])
            for category in ["copyright_risks", "trademark_issues", "real_person_mentions"]
        )
        
        music_count = len(legal_analysis.get("music_references", []))
        
        if total_high_risk == 0 and music_count == 0:
            return "low"
        elif total_high_risk <= 2 and music_count <= 1:
            return "medium"
        else:
            return "high"