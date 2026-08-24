"""
Character Bible Generator Service
Creates comprehensive character profiles and continuity tracking for film production
"""

import logging
from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass
from collections import defaultdict, Counter
import json

from .character_extractor import CharacterProfile, CharacterExtractor
from .scene_parser import SceneData

logger = logging.getLogger(__name__)

@dataclass
class CharacterBible:
    """Complete character bible with all production information"""
    characters: Dict[str, CharacterProfile]
    character_relationships: Dict[str, Dict[str, str]]
    scene_matrix: Dict[str, List[int]]  # character -> scenes they appear in
    continuity_tracker: Dict[str, List[Dict[str, Any]]]
    production_notes: Dict[str, List[str]]
    casting_suggestions: Dict[str, Dict[str, Any]]
    costume_notes: Dict[str, List[str]]
    makeup_notes: Dict[str, List[str]]

@dataclass 
class CharacterArc:
    """Character development arc across the script"""
    character_name: str
    introduction_scene: int
    key_moments: List[Dict[str, Any]]
    character_growth: List[str]
    relationships_evolution: Dict[str, List[str]]
    emotional_journey: List[Dict[str, str]]

class CharacterBibleGenerator:
    """
    Generates comprehensive character bibles for production use
    """
    
    def __init__(self):
        self.character_extractor = CharacterExtractor()
    
    def generate_character_bible(
        self, 
        scenes: List[SceneData], 
        script_text: str,
        production_level: str = "standard"  # "basic", "standard", "premium"
    ) -> CharacterBible:
        """
        Generate a comprehensive character bible
        """
        try:
            logger.info("Starting character bible generation")
            
            # Extract characters using the enhanced extractor
            characters = self.character_extractor.extract_characters(scenes, script_text)
            
            # Build character relationships
            relationships = self._build_character_relationships(characters, scenes)
            
            # Create scene matrix
            scene_matrix = self._create_scene_matrix(characters, scenes)
            
            # Track continuity across scenes
            continuity_tracker = self._track_character_continuity(characters, scenes, script_text)
            
            # Generate production notes
            production_notes = self._generate_production_notes(characters, scenes)
            
            # Generate casting suggestions
            casting_suggestions = self._generate_casting_suggestions(characters)
            
            # Generate costume notes
            costume_notes = self._generate_costume_notes(characters, scenes)
            
            # Generate makeup notes
            makeup_notes = self._generate_makeup_notes(characters, scenes)
            
            bible = CharacterBible(
                characters=characters,
                character_relationships=relationships,
                scene_matrix=scene_matrix,
                continuity_tracker=continuity_tracker,
                production_notes=production_notes,
                casting_suggestions=casting_suggestions,
                costume_notes=costume_notes,
                makeup_notes=makeup_notes
            )
            
            logger.info(f"Generated character bible with {len(characters)} characters")
            return bible
            
        except Exception as e:
            logger.error(f"Character bible generation failed: {e}")
            return self._create_fallback_bible(scenes)
    
    def _build_character_relationships(
        self, 
        characters: Dict[str, CharacterProfile], 
        scenes: List[SceneData]
    ) -> Dict[str, Dict[str, str]]:
        """Build detailed character relationship map"""
        relationships = defaultdict(dict)
        
        # Co-appearance analysis
        character_coappearances = defaultdict(lambda: defaultdict(int))
        
        for scene in scenes:
            scene_chars = scene.characters_present
            for char1 in scene_chars:
                for char2 in scene_chars:
                    if char1 != char2:
                        character_coappearances[char1][char2] += 1
        
        # Analyze relationship strength and type
        for char1, coappears in character_coappearances.items():
            if char1 in characters:
                char_profile = characters[char1]
                
                for char2, count in coappears.items():
                    if char2 in characters:
                        # Determine relationship strength
                        strength = "weak"
                        if count >= 5:
                            strength = "strong"
                        elif count >= 3:
                            strength = "moderate"
                        
                        # Try to determine relationship type from existing data
                        relationship_type = char_profile.relationships.get(char2, "colleague")
                        
                        relationships[char1][char2] = f"{relationship_type} ({strength})"
        
        return dict(relationships)
    
    def _create_scene_matrix(
        self, 
        characters: Dict[str, CharacterProfile], 
        scenes: List[SceneData]
    ) -> Dict[str, List[int]]:
        """Create matrix showing which characters appear in which scenes"""
        scene_matrix = {}
        
        for char_name, char_profile in characters.items():
            scene_matrix[char_name] = char_profile.scene_appearances
        
        return scene_matrix
    
    def _track_character_continuity(
        self, 
        characters: Dict[str, CharacterProfile], 
        scenes: List[SceneData],
        script_text: str
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Track character continuity issues and notes across scenes"""
        continuity_tracker = defaultdict(list)
        
        for char_name, char_profile in characters.items():
            continuity_notes = []
            
            # Track physical descriptions across scenes
            physical_descriptions = {}
            for i, scene_num in enumerate(char_profile.scene_appearances):
                scene = next((s for s in scenes if s.scene_number == scene_num), None)
                if scene:
                    # Look for character descriptions in this scene
                    scene_text = f"{scene.description} {' '.join(scene.action_lines)}"
                    
                    if char_name.lower() in scene_text.lower():
                        # Extract any new descriptions
                        description = self._extract_scene_specific_description(
                            scene_text, char_name
                        )
                        if description:
                            physical_descriptions[scene_num] = description
            
            # Check for inconsistencies
            if len(physical_descriptions) > 1:
                continuity_notes.append({
                    "type": "physical_description",
                    "issue": "Multiple physical descriptions found",
                    "details": physical_descriptions,
                    "severity": "medium"
                })
            
            # Track age consistency
            age_refs = char_profile.age_references
            if len(set(age_refs)) > 1:
                continuity_notes.append({
                    "type": "age_consistency",
                    "issue": "Conflicting age references",
                    "details": age_refs,
                    "severity": "high"
                })
            
            # Track prop/costume continuity
            costume_mentions = self._track_costume_mentions(char_name, scenes)
            if costume_mentions:
                continuity_notes.append({
                    "type": "costume_continuity",
                    "issue": "Costume changes noted",
                    "details": costume_mentions,
                    "severity": "low"
                })
            
            continuity_tracker[char_name] = continuity_notes
        
        return dict(continuity_tracker)
    
    def _generate_production_notes(
        self, 
        characters: Dict[str, CharacterProfile], 
        scenes: List[SceneData]
    ) -> Dict[str, List[str]]:
        """Generate production notes for each character"""
        production_notes = {}
        
        for char_name, char_profile in characters.items():
            notes = []
            
            # Character importance
            if char_profile.character_type == "lead":
                notes.append("LEAD CHARACTER - Primary casting priority")
                notes.append("Requires experienced actor with strong presence")
            elif char_profile.character_type == "supporting":
                notes.append("SUPPORTING CHARACTER - Important to story")
                notes.append("Requires skilled actor for key scenes")
            elif char_profile.character_type == "recurring":
                notes.append("RECURRING CHARACTER - Multiple appearances")
            else:
                notes.append("BACKGROUND CHARACTER - Can be cast locally")
            
            # Scene load
            total_scenes = char_profile.total_scenes
            if total_scenes > 20:
                notes.append(f"HIGH AVAILABILITY REQUIRED - Appears in {total_scenes} scenes")
            elif total_scenes > 10:
                notes.append(f"MODERATE AVAILABILITY - Appears in {total_scenes} scenes")
            
            # Dialogue intensity
            if char_profile.dialogue_count > 50:
                notes.append("DIALOGUE-HEAVY ROLE - Strong speaking ability required")
            
            # Age requirements
            if char_profile.age_references:
                age_note = f"AGE REQUIREMENTS: {', '.join(char_profile.age_references)}"
                notes.append(age_note)
            
            # Physical requirements
            if char_profile.physical_descriptions:
                physical_note = f"PHYSICAL: {', '.join(char_profile.physical_descriptions[:3])}"
                notes.append(physical_note)
            
            # Personality traits
            if char_profile.personality_traits:
                personality_note = f"PERSONALITY: {', '.join(char_profile.personality_traits[:3])}"
                notes.append(personality_note)
            
            # Relationship dynamics
            if char_profile.relationships:
                relationships_note = "KEY RELATIONSHIPS: " + ", ".join([
                    f"{other} ({rel})" for other, rel in list(char_profile.relationships.items())[:3]
                ])
                notes.append(relationships_note)
            
            production_notes[char_name] = notes
        
        return production_notes
    
    def _generate_casting_suggestions(
        self, 
        characters: Dict[str, CharacterProfile]
    ) -> Dict[str, Dict[str, Any]]:
        """Generate casting suggestions and requirements"""
        casting_suggestions = {}
        
        for char_name, char_profile in characters.items():
            suggestions = {
                "priority_level": self._get_casting_priority(char_profile),
                "union_status": self._get_union_requirements(char_profile),
                "special_skills": self._extract_special_skills(char_profile),
                "budget_tier": self._suggest_budget_tier(char_profile),
                "casting_notes": self._generate_casting_notes(char_profile)
            }
            
            casting_suggestions[char_name] = suggestions
        
        return casting_suggestions
    
    def _generate_costume_notes(
        self, 
        characters: Dict[str, CharacterProfile], 
        scenes: List[SceneData]
    ) -> Dict[str, List[str]]:
        """Generate costume department notes"""
        costume_notes = {}
        
        for char_name, char_profile in characters.items():
            notes = []
            
            # Extract costume mentions from descriptions
            costume_items = []
            for desc in char_profile.descriptions:
                costume_items.extend(self._extract_costume_items(desc))
            
            if costume_items:
                notes.append(f"COSTUME ITEMS: {', '.join(set(costume_items))}")
            
            # Scene count considerations
            if char_profile.total_scenes > 10:
                notes.append("MULTIPLE COSTUME CHANGES LIKELY")
                notes.append("Consider durability and backup options")
            
            # Character type considerations
            if char_profile.character_type == "lead":
                notes.append("HERO COSTUMES - High quality materials required")
            
            # Time period considerations
            if any(period in " ".join(char_profile.descriptions).lower() 
                   for period in ["period", "historical", "vintage"]):
                notes.append("PERIOD ACCURATE COSTUMES REQUIRED")
            
            costume_notes[char_name] = notes if notes else ["Standard wardrobe requirements"]
        
        return costume_notes
    
    def _generate_makeup_notes(
        self, 
        characters: Dict[str, CharacterProfile], 
        scenes: List[SceneData]
    ) -> Dict[str, List[str]]:
        """Generate makeup department notes"""
        makeup_notes = {}
        
        for char_name, char_profile in characters.items():
            notes = []
            
            # Age makeup requirements
            age_refs = char_profile.age_references
            if any("elderly" in ref.lower() or "old" in ref.lower() for ref in age_refs):
                notes.append("AGE MAKEUP REQUIRED")
                notes.append("Consider prosthetics for advanced aging")
            
            # Special makeup from descriptions
            descriptions = " ".join(char_profile.descriptions).lower()
            if "scar" in descriptions or "tattoo" in descriptions:
                notes.append("SPECIAL MAKEUP/PROSTHETICS REQUIRED")
            
            if "injury" in descriptions or "bruise" in descriptions:
                notes.append("INJURY MAKEUP - Plan for continuity across scenes")
            
            # Character type considerations
            if char_profile.character_type == "lead":
                notes.append("LEAD CHARACTER - High definition makeup required")
            
            # Scene count considerations
            if char_profile.total_scenes > 15:
                notes.append("LONG SHOOTING SCHEDULE - Touch-up materials needed")
            
            makeup_notes[char_name] = notes if notes else ["Standard makeup requirements"]
        
        return makeup_notes
    
    def create_character_arcs(
        self, 
        characters: Dict[str, CharacterProfile], 
        scenes: List[SceneData]
    ) -> Dict[str, CharacterArc]:
        """Create character development arcs"""
        character_arcs = {}
        
        for char_name, char_profile in characters.items():
            if char_profile.character_type in ["lead", "supporting"]:
                arc = CharacterArc(
                    character_name=char_name,
                    introduction_scene=char_profile.first_appearance,
                    key_moments=self._identify_key_moments(char_name, scenes),
                    character_growth=self._analyze_character_growth(char_profile),
                    relationships_evolution=self._track_relationship_evolution(char_name, scenes),
                    emotional_journey=self._map_emotional_journey(char_name, scenes)
                )
                character_arcs[char_name] = arc
        
        return character_arcs
    
    def generate_bible_export(self, bible: CharacterBible, format: str = "json") -> Dict[str, Any]:
        """Export character bible in specified format"""
        export_data = {
            "characters": {
                name: {
                    "name": profile.name,
                    "descriptions": profile.descriptions,
                    "first_appearance": profile.first_appearance,
                    "total_scenes": profile.total_scenes,
                    "character_type": profile.character_type,
                    "age_references": profile.age_references,
                    "physical_descriptions": profile.physical_descriptions,
                    "personality_traits": profile.personality_traits,
                    "relationships": profile.relationships,
                    "scene_appearances": profile.scene_appearances
                }
                for name, profile in bible.characters.items()
            },
            "relationships": bible.character_relationships,
            "scene_matrix": bible.scene_matrix,
            "production_notes": bible.production_notes,
            "casting_suggestions": bible.casting_suggestions,
            "costume_notes": bible.costume_notes,
            "makeup_notes": bible.makeup_notes,
            "continuity_tracker": bible.continuity_tracker
        }
        
        return export_data
    
    # Helper methods
    def _extract_scene_specific_description(self, scene_text: str, char_name: str) -> Optional[str]:
        """Extract character description from specific scene"""
        # Simple implementation - could be enhanced with NLP
        sentences = scene_text.split('.')
        for sentence in sentences:
            if char_name.lower() in sentence.lower() and len(sentence) > 20:
                return sentence.strip()
        return None
    
    def _track_costume_mentions(self, char_name: str, scenes: List[SceneData]) -> Dict[int, List[str]]:
        """Track costume mentions for character across scenes"""
        costume_mentions = {}
        
        for scene in scenes:
            if char_name in scene.characters_present:
                scene_text = f"{scene.description} {' '.join(scene.action_lines)}"
                costumes = self._extract_costume_items(scene_text)
                if costumes:
                    costume_mentions[scene.scene_number] = costumes
        
        return costume_mentions
    
    def _extract_costume_items(self, text: str) -> List[str]:
        """Extract costume items from text"""
        costume_keywords = [
            "dress", "suit", "shirt", "jacket", "coat", "hat", "shoes", "boots",
            "uniform", "costume", "outfit", "wearing", "dressed in"
        ]
        
        items = []
        text_lower = text.lower()
        for keyword in costume_keywords:
            if keyword in text_lower:
                items.append(keyword)
        
        return items
    
    def _get_casting_priority(self, char_profile: CharacterProfile) -> str:
        """Determine casting priority level"""
        if char_profile.character_type == "lead":
            return "high"
        elif char_profile.character_type == "supporting":
            return "medium"
        else:
            return "low"
    
    def _get_union_requirements(self, char_profile: CharacterProfile) -> str:
        """Determine union status requirements"""
        if char_profile.character_type in ["lead", "supporting"]:
            return "SAG-AFTRA required"
        else:
            return "non-union acceptable"
    
    def _extract_special_skills(self, char_profile: CharacterProfile) -> List[str]:
        """Extract special skills from character profile"""
        skills = []
        descriptions = " ".join(char_profile.descriptions + char_profile.personality_traits).lower()
        
        skill_keywords = {
            "driving": ["driving", "driver", "car", "motorcycle"],
            "fighting": ["fight", "martial arts", "boxing", "combat"],
            "singing": ["sing", "singer", "music", "voice"],
            "dancing": ["dance", "dancer", "choreography"],
            "languages": ["accent", "foreign", "bilingual", "speaks"]
        }
        
        for skill, keywords in skill_keywords.items():
            if any(keyword in descriptions for keyword in keywords):
                skills.append(skill)
        
        return skills
    
    def _suggest_budget_tier(self, char_profile: CharacterProfile) -> str:
        """Suggest budget tier for character"""
        if char_profile.character_type == "lead" and char_profile.total_scenes > 20:
            return "A-list"
        elif char_profile.character_type == "lead":
            return "name actor"
        elif char_profile.character_type == "supporting" and char_profile.total_scenes > 10:
            return "experienced supporting"
        else:
            return "day player"
    
    def _generate_casting_notes(self, char_profile: CharacterProfile) -> List[str]:
        """Generate specific casting notes"""
        notes = []
        
        if char_profile.dialogue_count > 30:
            notes.append("Strong dialogue delivery required")
        
        if len(char_profile.scene_appearances) > 15:
            notes.append("Long-term availability needed")
        
        if char_profile.personality_traits:
            notes.append(f"Must embody: {', '.join(char_profile.personality_traits[:2])}")
        
        return notes
    
    def _identify_key_moments(self, char_name: str, scenes: List[SceneData]) -> List[Dict[str, Any]]:
        """Identify key character moments"""
        # Simplified implementation
        return [{"scene": scenes[0].scene_number, "moment": "Character introduction"}]
    
    def _analyze_character_growth(self, char_profile: CharacterProfile) -> List[str]:
        """Analyze character growth arc"""
        return ["Character development to be analyzed"]
    
    def _track_relationship_evolution(self, char_name: str, scenes: List[SceneData]) -> Dict[str, List[str]]:
        """Track how relationships evolve"""
        return {}
    
    def _map_emotional_journey(self, char_name: str, scenes: List[SceneData]) -> List[Dict[str, str]]:
        """Map emotional journey"""
        return []
    
    def _create_fallback_bible(self, scenes: List[SceneData]) -> CharacterBible:
        """Create basic bible if generation fails"""
        return CharacterBible(
            characters={},
            character_relationships={},
            scene_matrix={},
            continuity_tracker={},
            production_notes={},
            casting_suggestions={},
            costume_notes={},
            makeup_notes={}
        )

# Factory function
def generate_character_bible(
    scenes: List[SceneData], 
    script_text: str,
    production_level: str = "standard"
) -> CharacterBible:
    """Generate character bible for production"""
    generator = CharacterBibleGenerator()
    return generator.generate_character_bible(scenes, script_text, production_level)