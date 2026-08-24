"""
Character Extraction and Analysis Service
Builds character profiles from screenplay content for continuity tracking
"""

import re
import logging
from typing import List, Dict, Any, Set, Optional
from collections import defaultdict, Counter
from dataclasses import dataclass

from .scene_parser import SceneData

logger = logging.getLogger(__name__)

@dataclass
class CharacterProfile:
    """Character profile data structure"""
    name: str
    descriptions: List[str]
    first_appearance: int
    total_scenes: int
    character_type: str
    age_references: List[str]
    physical_descriptions: List[str]
    personality_traits: List[str]
    relationships: Dict[str, str]  # character_name -> relationship_type
    dialogue_count: int
    scene_appearances: List[int]
    
    def __post_init__(self):
        self.descriptions = list(dict.fromkeys(self.descriptions))  # Remove duplicates
        self.age_references = list(dict.fromkeys(self.age_references))
        self.physical_descriptions = list(dict.fromkeys(self.physical_descriptions))
        self.personality_traits = list(dict.fromkeys(self.personality_traits))

class CharacterExtractor:
    """
    Extracts and analyzes character information from screenplay content
    """
    
    # Patterns for character analysis
    AGE_PATTERNS = [
        r'(\d+)[\s\-]*(?:year[s]?\s*old|yr[s]?\s*old|years?\s*of\s*age)',
        r'(?:aged?|age)\s*(\d+)',
        r'(?:in\s*(?:his|her|their))\s*(early|mid|late)?\s*(teens|twenties|thirties|forties|fifties|sixties|seventies|eighties|nineties)',
        r'(?:teenager|teen|child|kid|baby|toddler|elderly|senior)'
    ]
    
    PHYSICAL_PATTERNS = [
        r'(?:tall|short|fat|thin|slim|muscular|athletic|overweight|underweight)',
        r'(?:blonde?|brunette|redhead|gray\s*haired?|bald)',
        r'(?:blue|brown|green|hazel|gray)\s*eyes?',
        r'(?:wearing|dressed\s*in|has\s*on)\s*([^.!?]+)',
        r'(?:beautiful|handsome|attractive|ugly|plain|stunning|gorgeous)'
    ]
    
    PERSONALITY_PATTERNS = [
        r'(?:is|seems|appears)\s*(?:very\s*)?([a-z]+(?:\s+and\s+[a-z]+)*)',
        r'(?:nervous|confident|shy|outgoing|aggressive|gentle|kind|mean|smart|stupid|wise|foolish)',
        r'(?:leader|follower|rebel|conformist|introvert|extrovert)'
    ]
    
    RELATIONSHIP_KEYWORDS = {
        'family': ['mother', 'father', 'son', 'daughter', 'brother', 'sister', 'wife', 'husband', 'parent', 'child'],
        'romantic': ['boyfriend', 'girlfriend', 'lover', 'partner', 'spouse', 'fiancé', 'fiancée'],
        'professional': ['boss', 'employee', 'colleague', 'partner', 'client', 'doctor', 'lawyer', 'teacher', 'student'],
        'friendship': ['friend', 'best friend', 'buddy', 'pal', 'roommate', 'neighbor']
    }
    
    def __init__(self):
        self.characters: Dict[str, CharacterProfile] = {}
        self.character_networks: Dict[str, Set[str]] = defaultdict(set)
        
    def extract_characters(self, scenes: List[SceneData], script_text: str) -> Dict[str, CharacterProfile]:
        """
        Main character extraction method
        """
        self.characters = {}
        self.character_networks = defaultdict(set)
        
        try:
            # First pass: identify all characters from scenes
            self._identify_characters_from_scenes(scenes)
            
            # Second pass: analyze character descriptions in full script
            self._analyze_character_descriptions(script_text)
            
            # Third pass: analyze relationships
            self._analyze_character_relationships(script_text, scenes)
            
            # Final pass: classify characters and calculate stats
            self._classify_characters(scenes)
            
            logger.info(f"Extracted {len(self.characters)} characters")
            return self.characters
            
        except Exception as e:
            logger.error(f"Character extraction failed: {e}")
            return self._create_basic_character_list(scenes)
    
    def _identify_characters_from_scenes(self, scenes: List[SceneData]):
        """Identify characters from scene data"""
        for scene in scenes:
            for character_name in scene.characters_present:
                if character_name not in self.characters:
                    self.characters[character_name] = CharacterProfile(
                        name=character_name,
                        descriptions=[],
                        first_appearance=scene.scene_number,
                        total_scenes=0,
                        character_type="supporting",
                        age_references=[],
                        physical_descriptions=[],
                        personality_traits=[],
                        relationships={},
                        dialogue_count=0,
                        scene_appearances=[]
                    )
                
                # Update appearance tracking
                self.characters[character_name].scene_appearances.append(scene.scene_number)
                self.characters[character_name].total_scenes += 1
                
                # Track character networks (who appears with whom)
                for other_char in scene.characters_present:
                    if other_char != character_name:
                        self.character_networks[character_name].add(other_char)
    
    def _analyze_character_descriptions(self, script_text: str):
        """Analyze script text for character descriptions"""
        lines = script_text.split('\n')
        
        for character_name in self.characters.keys():
            character_profile = self.characters[character_name]
            
            # Find lines mentioning this character
            for line in lines:
                line_clean = line.strip()
                if not line_clean:
                    continue
                
                # Check if line mentions the character
                if self._line_mentions_character(line_clean, character_name):
                    # Extract age information
                    age_info = self._extract_age_info(line_clean)
                    if age_info:
                        character_profile.age_references.extend(age_info)
                    
                    # Extract physical descriptions
                    physical_info = self._extract_physical_info(line_clean)
                    if physical_info:
                        character_profile.physical_descriptions.extend(physical_info)
                    
                    # Extract personality traits
                    personality_info = self._extract_personality_info(line_clean)
                    if personality_info:
                        character_profile.personality_traits.extend(personality_info)
                    
                    # Store full description if substantial
                    if len(line_clean) > 20 and len(line_clean) < 200:
                        character_profile.descriptions.append(line_clean)
    
    def _analyze_character_relationships(self, script_text: str, scenes: List[SceneData]):
        """Analyze relationships between characters"""
        for character_name in self.characters.keys():
            character_profile = self.characters[character_name]
            
            # Analyze relationship keywords in context
            for relationship_type, keywords in self.RELATIONSHIP_KEYWORDS.items():
                for keyword in keywords:
                    pattern = rf'\b{re.escape(character_name)}\b.*\b{keyword}\b|\b{keyword}\b.*\b{re.escape(character_name)}\b'
                    matches = re.finditer(pattern, script_text, re.IGNORECASE)
                    
                    for match in matches:
                        context = match.group(0)
                        # Try to identify the other person in relationship
                        other_chars = [name for name in self.characters.keys() 
                                     if name != character_name and name.lower() in context.lower()]
                        if other_chars:
                            character_profile.relationships[other_chars[0]] = relationship_type
    
    def _classify_characters(self, scenes: List[SceneData]):
        """Classify characters by importance and calculate final stats"""
        total_scenes = len(scenes)
        
        for character_name, profile in self.characters.items():
            # Calculate appearance percentage
            appearance_percentage = profile.total_scenes / total_scenes if total_scenes > 0 else 0
            
            # Classify character importance
            if appearance_percentage > 0.7:
                profile.character_type = "lead"
            elif appearance_percentage > 0.3:
                profile.character_type = "supporting"
            elif appearance_percentage > 0.1:
                profile.character_type = "recurring" 
            else:
                profile.character_type = "background"
            
            # Estimate dialogue count (rough approximation)
            profile.dialogue_count = profile.total_scenes * 5  # Rough estimate
            
            # Clean up lists
            profile.descriptions = profile.descriptions[:5]  # Keep top 5
            profile.age_references = profile.age_references[:3]
            profile.physical_descriptions = profile.physical_descriptions[:5]
            profile.personality_traits = profile.personality_traits[:5]
    
    def _line_mentions_character(self, line: str, character_name: str) -> bool:
        """Check if a line mentions a specific character"""
        # Simple name matching - could be enhanced with NLP
        return character_name.lower() in line.lower()
    
    def _extract_age_info(self, text: str) -> List[str]:
        """Extract age-related information from text"""
        age_info = []
        text_lower = text.lower()
        
        for pattern in self.AGE_PATTERNS:
            matches = re.finditer(pattern, text_lower, re.IGNORECASE)
            for match in matches:
                age_info.append(match.group(0))
        
        return age_info
    
    def _extract_physical_info(self, text: str) -> List[str]:
        """Extract physical description information"""
        physical_info = []
        text_lower = text.lower()
        
        for pattern in self.PHYSICAL_PATTERNS:
            matches = re.finditer(pattern, text_lower, re.IGNORECASE)
            for match in matches:
                physical_info.append(match.group(0))
        
        return physical_info
    
    def _extract_personality_info(self, text: str) -> List[str]:
        """Extract personality trait information"""
        personality_info = []
        text_lower = text.lower()
        
        for pattern in self.PERSONALITY_PATTERNS:
            matches = re.finditer(pattern, text_lower, re.IGNORECASE)
            for match in matches:
                personality_info.append(match.group(0))
        
        return personality_info
    
    def _create_basic_character_list(self, scenes: List[SceneData]) -> Dict[str, CharacterProfile]:
        """Create basic character list as fallback"""
        logger.warning("Using basic character extraction fallback")
        
        character_counts = Counter()
        first_appearances = {}
        
        for scene in scenes:
            for char in scene.characters_present:
                character_counts[char] += 1
                if char not in first_appearances:
                    first_appearances[char] = scene.scene_number
        
        characters = {}
        for char_name, count in character_counts.items():
            characters[char_name] = CharacterProfile(
                name=char_name,
                descriptions=[f"Character appears in {count} scenes"],
                first_appearance=first_appearances[char_name],
                total_scenes=count,
                character_type="supporting" if count > 3 else "background",
                age_references=[],
                physical_descriptions=[],
                personality_traits=[],
                relationships={},
                dialogue_count=count * 3,  # Rough estimate
                scene_appearances=list(range(first_appearances[char_name], 
                                           first_appearances[char_name] + count))
            )
        
        return characters
    
    def detect_continuity_issues(self) -> List[Dict[str, Any]]:
        """Detect potential continuity issues in character descriptions"""
        issues = []
        
        for character_name, profile in self.characters.items():
            # Check for conflicting age references
            ages = profile.age_references
            if len(ages) > 1:
                # Simple check for obvious conflicts
                age_numbers = []
                for age_ref in ages:
                    numbers = re.findall(r'\d+', age_ref)
                    age_numbers.extend([int(n) for n in numbers if 0 < int(n) < 100])
                
                if len(set(age_numbers)) > 1:
                    issues.append({
                        "type": "age_inconsistency",
                        "character": character_name,
                        "description": f"Conflicting age references: {ages}",
                        "severity": "medium",
                        "suggested_fix": "Review character age references for consistency"
                    })
            
            # Check for conflicting physical descriptions
            physical_descs = profile.physical_descriptions
            if len(physical_descs) > 1:
                # Look for obvious conflicts (simplified)
                hair_colors = []
                for desc in physical_descs:
                    if any(color in desc.lower() for color in ['blonde', 'brunette', 'redhead', 'black hair']):
                        hair_colors.append(desc)
                
                if len(hair_colors) > 1:
                    issues.append({
                        "type": "physical_inconsistency",
                        "character": character_name,
                        "description": f"Conflicting physical descriptions: {hair_colors}",
                        "severity": "low",
                        "suggested_fix": "Standardize character physical descriptions"
                    })
        
        return issues
    
    def get_character_statistics(self) -> Dict[str, Any]:
        """Get statistics about extracted characters"""
        if not self.characters:
            return {}
        
        total_characters = len(self.characters)
        character_types = Counter(profile.character_type for profile in self.characters.values())
        
        avg_scenes_per_character = sum(p.total_scenes for p in self.characters.values()) / total_characters
        
        most_connected = max(self.character_networks.items(), 
                           key=lambda x: len(x[1]), default=(None, set()))[0]
        
        return {
            "total_characters": total_characters,
            "character_types": dict(character_types),
            "average_scenes_per_character": round(avg_scenes_per_character, 1),
            "most_connected_character": most_connected,
            "characters_with_descriptions": len([p for p in self.characters.values() if p.descriptions]),
            "characters_with_relationships": len([p for p in self.characters.values() if p.relationships])
        }

# Factory function for easy use
def extract_characters(scenes: List[SceneData], script_text: str) -> tuple[Dict[str, CharacterProfile], List[Dict[str, Any]], Dict[str, Any]]:
    """
    Extract characters and return profiles with continuity issues and statistics
    """
    extractor = CharacterExtractor()
    characters = extractor.extract_characters(scenes, script_text)
    continuity_issues = extractor.detect_continuity_issues()
    stats = extractor.get_character_statistics()
    
    return characters, continuity_issues, stats