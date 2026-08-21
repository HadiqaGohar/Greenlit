"""
Continuity Agent - Specializes in script consistency and continuity checking
Tracks character details, timeline, locations, and props across scenes
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import re

from ..agent.gemini_client import GeminiClient
from ..models.agent_schemas import AgentTask, AgentResult, ContinuityAgentResult
from .prompts.continuity_prompts import CONTINUITY_SYSTEM_PROMPT, CHARACTER_TRACKING_PROMPT, TIMELINE_ANALYSIS_PROMPT

logger = logging.getLogger(__name__)


class ContinuityAgent:
    """
    Continuity Agent - The 'script supervisor' ensuring consistency
    Tracks characters, timeline, locations, and props for production continuity
    """
    
    def __init__(self):
        self.gemini_client = GeminiClient()
        self.agent_name = "ContinuityAgent"
        
    async def process_task(self, task: AgentTask) -> AgentResult:
        """
        Process continuity-specific tasks for script consistency checking
        Focus on character, timeline, location, and prop continuity
        """
        start_time = datetime.utcnow()
        
        try:
            logger.info(f"Continuity Agent processing task: {task.task_id}")
            
            script_text = task.task_data.get("script_text", "")
            focus = task.task_data.get("focus", "consistency_check")
            
            if focus == "character_tracking":
                result_data = await self._analyze_character_continuity(script_text, task.task_data)
            elif focus == "timeline_analysis":
                result_data = await self._analyze_timeline_continuity(script_text, task.task_data)
            else:
                result_data = await self._comprehensive_continuity_check(script_text, task.task_data)
            
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            return AgentResult(
                agent_type="continuity",
                task_id=task.task_id,
                success=True,
                confidence_score=result_data.get("confidence", 0.8),
                processing_time=processing_time,
                data=result_data,
                metadata={
                    "gemini_model_used": self.gemini_client.model_name,
                    "analysis_focus": focus,
                    "continuity_categories": list(result_data.keys())
                }
            )
            
        except Exception as e:
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            logger.error(f"Continuity Agent failed on task {task.task_id}: {str(e)}")
            
            return AgentResult(
                agent_type="continuity",
                task_id=task.task_id,
                success=False,
                confidence_score=0.0,
                processing_time=processing_time,
                error_message=str(e)
            )
    
    async def _comprehensive_continuity_check(self, script_text: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Comprehensive continuity analysis covering all major aspects
        Combines Gemini analysis with pattern-based detection
        """
        
        # Run multiple continuity checks in parallel
        character_analysis, timeline_analysis, location_analysis, prop_analysis = await asyncio.gather(
            self._analyze_character_continuity(script_text, context),
            self._analyze_timeline_continuity(script_text, context),
            self._analyze_location_continuity(script_text, context),
            self._analyze_prop_continuity(script_text, context),
            return_exceptions=True
        )
        
        # Handle any exceptions from parallel execution
        if isinstance(character_analysis, Exception):
            logger.error(f"Character analysis failed: {character_analysis}")
            character_analysis = {"character_inconsistencies": [], "confidence": 0.3}
            
        if isinstance(timeline_analysis, Exception):
            logger.error(f"Timeline analysis failed: {timeline_analysis}")
            timeline_analysis = {"timeline_issues": [], "confidence": 0.3}
            
        if isinstance(location_analysis, Exception):
            logger.error(f"Location analysis failed: {location_analysis}")
            location_analysis = {"location_continuity": [], "confidence": 0.3}
            
        if isinstance(prop_analysis, Exception):
            logger.error(f"Prop analysis failed: {prop_analysis}")
            prop_analysis = {"prop_tracking": [], "confidence": 0.3}
        
        # Combine all analyses
        combined_analysis = {
            "character_inconsistencies": character_analysis.get("character_inconsistencies", []),
            "timeline_issues": timeline_analysis.get("timeline_issues", []),
            "location_continuity": location_analysis.get("location_continuity", []),
            "prop_tracking": prop_analysis.get("prop_tracking", []),
            "scene_transitions": await self._analyze_scene_transitions(script_text),
            "metadata": {
                "analysis_method": "comprehensive_multi_check",
                "components_analyzed": ["characters", "timeline", "locations", "props", "transitions"],
                "total_issues_found": (
                    len(character_analysis.get("character_inconsistencies", [])) +
                    len(timeline_analysis.get("timeline_issues", [])) +
                    len(location_analysis.get("location_continuity", [])) +
                    len(prop_analysis.get("prop_tracking", []))
                )
            }
        }
        
        # Calculate overall confidence
        confidences = [
            character_analysis.get("confidence", 0.5),
            timeline_analysis.get("confidence", 0.5), 
            location_analysis.get("confidence", 0.5),
            prop_analysis.get("confidence", 0.5)
        ]
        combined_analysis["confidence"] = sum(confidences) / len(confidences)
        
        return combined_analysis
    
    async def _analyze_character_continuity(self, script_text: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze character consistency across the script
        Tracks age, appearance, background, relationships, etc.
        """
        
        prompt = CHARACTER_TRACKING_PROMPT.format(
            script_text=script_text,
            context_info=context.get("context", {})
        )
        
        try:
            # Use Gemini for sophisticated character analysis
            gemini_response = await self.gemini_client.generate_content(
                prompt=prompt,
                system_prompt=CONTINUITY_SYSTEM_PROMPT
            )
            
            # Parse character inconsistencies
            character_issues = await self._parse_character_issues(gemini_response, script_text)
            
            # Add pattern-based character tracking
            pattern_issues = await self._pattern_character_check(script_text)
            
            # Combine findings
            all_issues = character_issues + pattern_issues
            
            return {
                "character_inconsistencies": all_issues,
                "character_count": self._count_characters(script_text),
                "confidence": 0.85 if gemini_response else 0.6,
                "analysis_method": "gemini_plus_patterns"
            }
            
        except Exception as e:
            logger.error(f"Character analysis failed: {str(e)}")
            # Fallback to pattern-based only
            return {
                "character_inconsistencies": await self._pattern_character_check(script_text),
                "confidence": 0.5,
                "analysis_method": "pattern_fallback"
            }
    
    async def _analyze_timeline_continuity(self, script_text: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze timeline and chronological consistency
        Identifies date conflicts, time progression issues, etc.
        """
        
        prompt = TIMELINE_ANALYSIS_PROMPT.format(
            script_text=script_text,
            context_info=context.get("context", {})
        )
        
        try:
            gemini_response = await self.gemini_client.generate_content(
                prompt=prompt,
                system_prompt=CONTINUITY_SYSTEM_PROMPT
            )
            
            timeline_issues = await self._parse_timeline_issues(gemini_response, script_text)
            pattern_timeline = await self._pattern_timeline_check(script_text)
            
            return {
                "timeline_issues": timeline_issues + pattern_timeline,
                "time_references_found": self._count_time_references(script_text),
                "confidence": 0.8,
                "analysis_method": "gemini_plus_patterns"
            }
            
        except Exception as e:
            logger.error(f"Timeline analysis failed: {str(e)}")
            return {
                "timeline_issues": await self._pattern_timeline_check(script_text),
                "confidence": 0.5,
                "analysis_method": "pattern_fallback"
            }
    
    async def _analyze_location_continuity(self, script_text: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze location consistency and geography
        Tracks scene locations, travel time, geographic accuracy
        """
        
        location_issues = []
        
        # Extract scene headers and locations
        scenes = self._extract_scene_locations(script_text)
        
        # Check for location inconsistencies
        for i, scene in enumerate(scenes):
            if i > 0:
                prev_scene = scenes[i-1]
                
                # Check for impossible travel times
                if self._check_travel_feasibility(prev_scene, scene):
                    location_issues.append({
                        "type": "travel_time",
                        "description": f"Potentially impossible travel from {prev_scene['location']} to {scene['location']}",
                        "severity": "medium",
                        "scenes": [prev_scene['scene_number'], scene['scene_number']]
                    })
        
        return {
            "location_continuity": location_issues,
            "scenes_analyzed": len(scenes),
            "unique_locations": len(set(s['location'] for s in scenes)),
            "confidence": 0.7
        }
    
    async def _analyze_prop_continuity(self, script_text: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Track props, costumes, and physical elements across scenes
        Identifies continuity issues with objects and appearances
        """
        
        prop_issues = []
        
        # Look for prop mentions
        prop_patterns = [
            r'(wearing|carries|holding|puts on|takes off)\s+([a-zA-Z\s]+)',
            r'(gun|weapon|phone|watch|glasses|hat|jacket|bag)\b',
            r'(car|vehicle|motorcycle|bicycle)\b'
        ]
        
        props_mentioned = []
        for pattern in prop_patterns:
            matches = re.findall(pattern, script_text, re.IGNORECASE)
            props_mentioned.extend(matches)
        
        # Simple prop tracking (would be enhanced with more sophisticated analysis)
        if len(props_mentioned) > 0:
            prop_issues.append({
                "type": "prop_tracking",
                "description": f"Found {len(props_mentioned)} prop references requiring continuity tracking",
                "severity": "low",
                "props_count": len(props_mentioned)
            })
        
        return {
            "prop_tracking": prop_issues,
            "props_identified": len(props_mentioned),
            "confidence": 0.6
        }
    
    async def _analyze_scene_transitions(self, script_text: str) -> List[Dict[str, Any]]:
        """Analyze scene transitions for continuity flow"""
        
        transitions = []
        scenes = self._extract_scene_locations(script_text)
        
        for i in range(len(scenes) - 1):
            current_scene = scenes[i]
            next_scene = scenes[i + 1]
            
            transition = {
                "from_scene": current_scene['scene_number'],
                "to_scene": next_scene['scene_number'],
                "location_change": current_scene['location'] != next_scene['location'],
                "time_jump": self._detect_time_jump(current_scene, next_scene)
            }
            
            transitions.append(transition)
        
        return transitions
    
    # Helper methods for parsing and pattern detection
    
    async def _parse_character_issues(self, gemini_response: str, script_text: str) -> List[Dict[str, Any]]:
        """Parse character inconsistencies from Gemini response"""
        
        issues = []
        
        try:
            lines = gemini_response.strip().split('\n')
            
            current_issue = {}
            for line in lines:
                line = line.strip()
                
                if line.startswith("CHARACTER_ISSUE:"):
                    if current_issue:
                        issues.append(current_issue)
                    current_issue = {
                        "type": "character",
                        "description": line.replace("CHARACTER_ISSUE:", "").strip()
                    }
                    
                elif line.startswith("CHARACTER:"):
                    current_issue["character"] = line.replace("CHARACTER:", "").strip()
                    
                elif line.startswith("SEVERITY:"):
                    current_issue["severity"] = line.replace("SEVERITY:", "").strip().lower()
                    
                elif line.startswith("LOCATION:"):
                    current_issue["location"] = line.replace("LOCATION:", "").strip()
            
            if current_issue:
                issues.append(current_issue)
                
        except Exception as e:
            logger.error(f"Failed to parse character issues: {str(e)}")
        
        return issues
    
    async def _parse_timeline_issues(self, gemini_response: str, script_text: str) -> List[Dict[str, Any]]:
        """Parse timeline inconsistencies from Gemini response"""
        
        issues = []
        
        try:
            lines = gemini_response.strip().split('\n')
            
            current_issue = {}
            for line in lines:
                line = line.strip()
                
                if line.startswith("TIMELINE_ISSUE:"):
                    if current_issue:
                        issues.append(current_issue)
                    current_issue = {
                        "type": "timeline",
                        "description": line.replace("TIMELINE_ISSUE:", "").strip()
                    }
                    
                elif line.startswith("TIME_CONFLICT:"):
                    current_issue["conflict"] = line.replace("TIME_CONFLICT:", "").strip()
                    
                elif line.startswith("SEVERITY:"):
                    current_issue["severity"] = line.replace("SEVERITY:", "").strip().lower()
            
            if current_issue:
                issues.append(current_issue)
                
        except Exception as e:
            logger.error(f"Failed to parse timeline issues: {str(e)}")
        
        return issues
    
    async def _pattern_character_check(self, script_text: str) -> List[Dict[str, Any]]:
        """Pattern-based character consistency checking"""
        
        issues = []
        
        # Look for character name variations
        character_names = re.findall(r'\b[A-Z]{2,}(?:\s+[A-Z]{2,})*\b', script_text)
        character_counts = {}
        
        for name in character_names:
            character_counts[name] = character_counts.get(name, 0) + 1
        
        # Check for potential name inconsistencies
        names = list(character_counts.keys())
        for i, name1 in enumerate(names):
            for name2 in names[i+1:]:
                if self._names_similar(name1, name2):
                    issues.append({
                        "type": "character_naming",
                        "description": f"Potential character name inconsistency: {name1} vs {name2}",
                        "severity": "medium",
                        "characters": [name1, name2]
                    })
        
        return issues
    
    async def _pattern_timeline_check(self, script_text: str) -> List[Dict[str, Any]]:
        """Pattern-based timeline checking"""
        
        issues = []
        
        # Extract time references
        time_patterns = [
            r'\b(19|20)\d{2}\b',  # Years
            r'\b(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\b',
            r'\b(January|February|March|April|May|June|July|August|September|October|November|December)\b',
            r'\b\d{1,2}:\d{2}\s*(AM|PM)?\b'  # Times
        ]
        
        time_references = []
        for pattern in time_patterns:
            matches = re.findall(pattern, script_text, re.IGNORECASE)
            time_references.extend(matches)
        
        # Simple chronology check
        years = [match for match in time_references if match.isdigit() and len(match) == 4]
        if len(set(years)) > 1:
            sorted_years = sorted(set(years))
            if len(sorted_years) > 2:
                issues.append({
                    "type": "timeline_span",
                    "description": f"Script spans multiple years: {sorted_years[0]} to {sorted_years[-1]}",
                    "severity": "low",
                    "years": sorted_years
                })
        
        return issues
    
    # Utility methods
    
    def _extract_scene_locations(self, script_text: str) -> List[Dict[str, str]]:
        """Extract scene headers and locations"""
        
        scenes = []
        lines = script_text.split('\n')
        scene_number = 1
        
        for line in lines:
            line = line.strip().upper()
            if any(indicator in line for indicator in ['EXT.', 'INT.']):
                scenes.append({
                    "scene_number": scene_number,
                    "location": line,
                    "type": "EXT" if "EXT." in line else "INT"
                })
                scene_number += 1
        
        return scenes
    
    def _count_characters(self, script_text: str) -> int:
        """Count unique character names in script"""
        character_names = re.findall(r'\b[A-Z]{2,}(?:\s+[A-Z]{2,})*\b', script_text)
        return len(set(character_names))
    
    def _count_time_references(self, script_text: str) -> int:
        """Count time/date references in script"""
        time_patterns = [
            r'\b(19|20)\d{2}\b',
            r'\b\d{1,2}:\d{2}\s*(AM|PM)?\b',
            r'\b(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\b'
        ]
        
        count = 0
        for pattern in time_patterns:
            count += len(re.findall(pattern, script_text, re.IGNORECASE))
        
        return count
    
    def _names_similar(self, name1: str, name2: str) -> bool:
        """Check if two character names might be the same person with spelling variations"""
        
        # Simple similarity check (could be enhanced with fuzzy matching)
        if abs(len(name1) - len(name2)) > 3:
            return False
        
        # Check for common prefixes (nicknames)
        if name1.startswith(name2[:3]) or name2.startswith(name1[:3]):
            return True
        
        return False
    
    def _check_travel_feasibility(self, scene1: Dict, scene2: Dict) -> bool:
        """Check if travel between locations is feasible (simplified)"""
        
        # This would be enhanced with real geographic data
        location1 = scene1['location'].lower()
        location2 = scene2['location'].lower()
        
        # Simple checks for obviously impossible travel
        international_indicators = ['london', 'paris', 'tokyo', 'new york', 'los angeles']
        
        loc1_international = any(indicator in location1 for indicator in international_indicators)
        loc2_international = any(indicator in location2 for indicator in international_indicators)
        
        # Flag potential international travel without time indication
        return loc1_international and loc2_international and location1 != location2
    
    def _detect_time_jump(self, scene1: Dict, scene2: Dict) -> bool:
        """Detect if there's a time jump between scenes"""
        
        # Simple detection based on scene headers
        time_indicators = ['later', 'next day', 'morning', 'evening', 'night', 'week later']
        
        scene1_text = scene1['location'].lower()
        scene2_text = scene2['location'].lower()
        
        return any(indicator in scene1_text or indicator in scene2_text for indicator in time_indicators)