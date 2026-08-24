"""
Screenplay Scene Parser Service
Analyzes script content and extracts scene information using industry-standard formatting
"""

import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class SceneData:
    """Data class for parsed scene information"""
    scene_number: int
    title: str
    location: str
    time_of_day: str
    description: str
    characters_present: List[str]
    page_start: Optional[int] = None
    page_end: Optional[int] = None
    dialogue_count: int = 0
    action_lines: List[str] = None
    
    def __post_init__(self):
        if self.action_lines is None:
            self.action_lines = []

class ScreenplayParser:
    """
    Parses screenplay content and extracts scene information
    Supports standard screenplay formatting conventions
    """
    
    # Regex patterns for screenplay elements
    SCENE_HEADER_PATTERN = r'^(INT\.|EXT\.|INTERIOR|EXTERIOR)\s*(.+?)\s*[-–—]\s*(DAY|NIGHT|DAWN|DUSK|MORNING|AFTERNOON|EVENING|CONTINUOUS|LATER|SAME TIME|\d+:\d+\s*[AP]M)\s*$'
    CHARACTER_NAME_PATTERN = r'^\s*([A-Z][A-Z\s\.]+[A-Z])\s*$'
    PARENTHETICAL_PATTERN = r'^\s*\([^)]+\)\s*$'
    DIALOGUE_PATTERN = r'^\s*[a-zA-Z].*$'
    ACTION_PATTERN = r'^\s*[A-Z].*[a-z].*$'
    TRANSITION_PATTERN = r'^(FADE IN:|FADE OUT:|CUT TO:|DISSOLVE TO:|SMASH CUT TO:|MATCH CUT TO:).*$'
    
    # Time of day mappings
    TIME_MAPPINGS = {
        'MORNING': 'DAY',
        'AFTERNOON': 'DAY', 
        'EVENING': 'NIGHT',
        'DAWN': 'DAY',
        'DUSK': 'NIGHT',
        'CONTINUOUS': 'CONTINUOUS',
        'LATER': 'CONTINUOUS',
        'SAME TIME': 'CONTINUOUS'
    }
    
    def __init__(self):
        self.scenes: List[SceneData] = []
        self.characters_found: set = set()
        
    def parse_screenplay(self, script_text: str) -> List[SceneData]:
        """
        Main parsing method - extracts scenes from screenplay text
        """
        self.scenes = []
        self.characters_found = set()
        
        try:
            lines = self._clean_and_split_script(script_text)
            current_scene = None
            current_characters = set()
            line_number = 0
            
            for line in lines:
                line_number += 1
                line_clean = line.strip()
                
                if not line_clean:
                    continue
                
                # Check for scene header
                scene_match = self._parse_scene_header(line_clean)
                if scene_match:
                    # Save previous scene if exists
                    if current_scene:
                        current_scene.characters_present = list(current_characters)
                        self.scenes.append(current_scene)
                    
                    # Create new scene
                    current_scene = SceneData(
                        scene_number=len(self.scenes) + 1,
                        title=scene_match['title'],
                        location=scene_match['location'],
                        time_of_day=scene_match['time_of_day'],
                        description="",
                        characters_present=[],
                        page_start=self._estimate_page_number(line_number),
                        action_lines=[]
                    )
                    current_characters = set()
                    continue
                
                if current_scene is None:
                    # Create a default scene if script doesn't start with scene header
                    current_scene = SceneData(
                        scene_number=1,
                        title="SCENE 1",
                        location="UNSPECIFIED",
                        time_of_day="DAY",
                        description="",
                        characters_present=[],
                        action_lines=[]
                    )
                    current_characters = set()
                
                # Parse different screenplay elements
                if self._is_character_name(line_clean):
                    character_name = self._clean_character_name(line_clean)
                    current_characters.add(character_name)
                    self.characters_found.add(character_name)
                    
                elif self._is_action_line(line_clean):
                    current_scene.action_lines.append(line_clean)
                    if len(current_scene.description) < 200:  # Limit description length
                        current_scene.description += f" {line_clean}"
                        
                elif self._is_dialogue(line_clean):
                    current_scene.dialogue_count += 1
            
            # Don't forget the last scene
            if current_scene:
                current_scene.characters_present = list(current_characters)
                self.scenes.append(current_scene)
            
            # Clean up scene descriptions
            for scene in self.scenes:
                scene.description = scene.description.strip()[:300]  # Limit length
                scene.page_end = scene.page_start  # Simple estimation
            
            logger.info(f"Parsed {len(self.scenes)} scenes with {len(self.characters_found)} characters")
            return self.scenes
            
        except Exception as e:
            logger.error(f"Screenplay parsing failed: {e}")
            return self._create_fallback_scenes(script_text)
    
    def _clean_and_split_script(self, script_text: str) -> List[str]:
        """Clean script text and split into lines"""
        # Remove excessive whitespace but preserve formatting
        lines = script_text.replace('\r\n', '\n').replace('\r', '\n').split('\n')
        return [line.rstrip() for line in lines]
    
    def _parse_scene_header(self, line: str) -> Optional[Dict[str, str]]:
        """Parse scene header line (INT./EXT. LOCATION - TIME)"""
        
        # Try standard format first
        match = re.match(self.SCENE_HEADER_PATTERN, line.upper())
        if match:
            interior_exterior = match.group(1)
            location = match.group(2).strip()
            time_of_day = match.group(3).strip()
            
            # Map time variations to standard times
            time_of_day = self.TIME_MAPPINGS.get(time_of_day, time_of_day)
            
            title = f"{interior_exterior} {location} - {time_of_day}"
            
            return {
                'title': title,
                'location': location,
                'time_of_day': time_of_day
            }
        
        # Try alternative formats
        alt_patterns = [
            r'^(INTERIOR|EXTERIOR)[\s\.]+(.+?)[\s\-–—]+(DAY|NIGHT|DAWN|DUSK).*$',
            r'^(INT|EXT)[\s\.]+(.+)$',  # No time specified
        ]
        
        for pattern in alt_patterns:
            match = re.match(pattern, line.upper())
            if match:
                interior_exterior = "INT." if match.group(1).startswith('INT') else "EXT."
                location = match.group(2).strip() if len(match.groups()) > 1 else "UNKNOWN LOCATION"
                time_of_day = match.group(3).strip() if len(match.groups()) > 2 else "DAY"
                
                title = f"{interior_exterior} {location} - {time_of_day}"
                
                return {
                    'title': title,
                    'location': location,
                    'time_of_day': time_of_day
                }
        
        return None
    
    def _is_character_name(self, line: str) -> bool:
        """Identify character name lines"""
        # Character names are typically ALL CAPS, centered, and alone on a line
        return (
            re.match(self.CHARACTER_NAME_PATTERN, line) and
            len(line.strip()) > 1 and
            len(line.strip()) < 40 and
            not self._is_scene_header_line(line) and
            not self._is_transition_line(line)
        )
    
    def _is_action_line(self, line: str) -> bool:
        """Identify action/description lines"""
        return (
            not self._is_character_name(line) and
            not self._is_parenthetical(line) and
            not self._is_scene_header_line(line) and
            not self._is_transition_line(line) and
            len(line.strip()) > 10 and
            re.match(r'^[A-Z].*', line)  # Starts with capital letter
        )
    
    def _is_dialogue(self, line: str) -> bool:
        """Identify dialogue lines"""
        return (
            not self._is_character_name(line) and
            not self._is_action_line(line) and
            not self._is_parenthetical(line) and
            not self._is_scene_header_line(line) and
            len(line.strip()) > 0 and
            re.match(r'^[a-zA-Z].*', line)  # Starts with letter (usually lowercase)
        )
    
    def _is_parenthetical(self, line: str) -> bool:
        """Identify parenthetical lines (actor directions)"""
        return re.match(self.PARENTHETICAL_PATTERN, line) is not None
    
    def _is_scene_header_line(self, line: str) -> bool:
        """Check if line is a scene header"""
        return self._parse_scene_header(line) is not None
    
    def _is_transition_line(self, line: str) -> bool:
        """Identify transition lines"""
        return re.match(self.TRANSITION_PATTERN, line.upper()) is not None
    
    def _clean_character_name(self, line: str) -> str:
        """Clean character name from line"""
        name = line.strip().upper()
        
        # Remove common suffixes
        suffixes = ['(CONT\'D)', '(CONT)', '(O.S.)', '(V.O.)', '(OFF)', '(VOICE OVER)']
        for suffix in suffixes:
            name = name.replace(suffix, '').strip()
        
        return name
    
    def _estimate_page_number(self, line_number: int) -> int:
        """Estimate page number based on line number (rough approximation)"""
        # Typical screenplay: ~55 lines per page
        return max(1, line_number // 55)
    
    def _create_fallback_scenes(self, script_text: str) -> List[SceneData]:
        """Create basic scene structure if parsing fails"""
        logger.warning("Using fallback scene parsing")
        
        # Split script into rough sections
        sections = script_text.split('\n\n')
        scenes = []
        
        for i, section in enumerate(sections):
            if len(section.strip()) > 50:  # Skip very short sections
                scene = SceneData(
                    scene_number=i + 1,
                    title=f"SCENE {i + 1}",
                    location="UNSPECIFIED",
                    time_of_day="DAY",
                    description=section.strip()[:200],
                    characters_present=self._extract_basic_characters(section),
                    action_lines=[section.strip()]
                )
                scenes.append(scene)
        
        return scenes if scenes else [SceneData(
            scene_number=1,
            title="FULL SCRIPT",
            location="VARIOUS",
            time_of_day="DAY",
            description=script_text[:200],
            characters_present=[],
            action_lines=[script_text]
        )]
    
    def _extract_basic_characters(self, text: str) -> List[str]:
        """Basic character extraction as fallback"""
        # Look for all-caps words that might be character names
        potential_characters = re.findall(r'\b[A-Z]{2,}(?:[A-Z\s]*[A-Z])?\b', text)
        
        # Filter out common non-character words
        excluded_words = {
            'THE', 'AND', 'BUT', 'FOR', 'WITH', 'FROM', 'INTO', 'OVER', 
            'UNDER', 'THROUGH', 'DURING', 'BEFORE', 'AFTER', 'ABOVE',
            'INT', 'EXT', 'DAY', 'NIGHT', 'FADE', 'CUT', 'DISSOLVE'
        }
        
        characters = []
        for char in potential_characters:
            if (char not in excluded_words and 
                len(char) > 2 and 
                len(char) < 20 and
                char not in characters):
                characters.append(char)
        
        return characters[:10]  # Limit to reasonable number
    
    def get_character_list(self) -> List[str]:
        """Get list of all characters found during parsing"""
        return sorted(list(self.characters_found))
    
    def get_location_list(self) -> List[str]:
        """Get list of all locations found during parsing"""
        locations = set()
        for scene in self.scenes:
            if scene.location and scene.location != "UNSPECIFIED":
                locations.add(scene.location)
        return sorted(list(locations))
    
    def get_scene_statistics(self) -> Dict[str, Any]:
        """Get statistics about parsed scenes"""
        if not self.scenes:
            return {}
        
        total_scenes = len(self.scenes)
        day_scenes = len([s for s in self.scenes if s.time_of_day == "DAY"])
        night_scenes = len([s for s in self.scenes if s.time_of_day == "NIGHT"])
        interior_scenes = len([s for s in self.scenes if s.title.startswith("INT.")])
        exterior_scenes = len([s for s in self.scenes if s.title.startswith("EXT.")])
        
        avg_characters_per_scene = sum(len(s.characters_present) for s in self.scenes) / total_scenes
        total_dialogue_lines = sum(s.dialogue_count for s in self.scenes)
        
        return {
            "total_scenes": total_scenes,
            "day_scenes": day_scenes,
            "night_scenes": night_scenes,
            "interior_scenes": interior_scenes,
            "exterior_scenes": exterior_scenes,
            "total_characters": len(self.characters_found),
            "average_characters_per_scene": round(avg_characters_per_scene, 1),
            "total_dialogue_lines": total_dialogue_lines,
            "locations": len(self.get_location_list())
        }

# Factory function for easy use
def parse_screenplay(script_text: str) -> Tuple[List[SceneData], Dict[str, Any]]:
    """
    Parse screenplay and return scenes with statistics
    """
    parser = ScreenplayParser()
    scenes = parser.parse_screenplay(script_text)
    stats = parser.get_scene_statistics()
    
    return scenes, stats