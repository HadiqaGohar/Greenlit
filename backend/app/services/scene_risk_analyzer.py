"""
Scene-Level Risk Assessment Service
Analyzes individual scenes for production risks and costs
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from collections import Counter

from .scene_parser import SceneData
from ..models.production_schemas import RiskLevel

logger = logging.getLogger(__name__)

@dataclass
class SceneRiskAnalysis:
    """Risk analysis data for a single scene"""
    scene_id: str
    scene_number: int
    overall_risk_score: float
    risk_factors: List[Dict[str, Any]]
    cost_estimates: Dict[str, float]
    complexity_level: str
    production_notes: List[str]
    required_clearances: List[str]
    
class SceneRiskAnalyzer:
    """
    Analyzes individual scenes for production risks and planning
    """
    
    # Risk weights for different factors
    RISK_WEIGHTS = {
        "location_complexity": 0.3,
        "cast_size": 0.2,
        "technical_requirements": 0.25,
        "legal_concerns": 0.15,
        "continuity_issues": 0.1
    }
    
    # Location complexity scoring
    LOCATION_COMPLEXITY = {
        "studio": {"score": 10, "cost_multiplier": 1.0},
        "simple_interior": {"score": 20, "cost_multiplier": 1.2},
        "complex_interior": {"score": 40, "cost_multiplier": 1.8},
        "simple_exterior": {"score": 30, "cost_multiplier": 1.5},
        "complex_exterior": {"score": 60, "cost_multiplier": 2.5},
        "vehicle": {"score": 50, "cost_multiplier": 2.2},
        "water": {"score": 70, "cost_multiplier": 3.0},
        "aerial": {"score": 80, "cost_multiplier": 3.5},
        "dangerous": {"score": 90, "cost_multiplier": 4.0}
    }
    
    def __init__(self):
        pass
    
    def analyze_scene_risks(
        self, 
        scene: SceneData, 
        agent_findings: Dict[str, Any] = None,
        budget_tier: str = "medium"
    ) -> SceneRiskAnalysis:
        """
        Analyze a single scene for production risks and requirements
        """
        try:
            risk_factors = []
            cost_estimates = {"location": 0, "cast": 0, "equipment": 0, "legal": 0, "total": 0}
            production_notes = []
            required_clearances = []
            
            # Analyze location complexity
            location_analysis = self._analyze_location_complexity(scene)
            risk_factors.append(location_analysis)
            cost_estimates["location"] = location_analysis["estimated_cost"]
            
            # Analyze cast requirements
            cast_analysis = self._analyze_cast_complexity(scene)
            risk_factors.append(cast_analysis)
            cost_estimates["cast"] = cast_analysis["estimated_cost"]
            
            # Analyze technical requirements
            technical_analysis = self._analyze_technical_requirements(scene)
            risk_factors.append(technical_analysis)
            cost_estimates["equipment"] = technical_analysis["estimated_cost"]
            
            # Analyze legal/clearance requirements
            if agent_findings:
                legal_analysis = self._analyze_legal_requirements(scene, agent_findings)
                risk_factors.append(legal_analysis)
                cost_estimates["legal"] = legal_analysis["estimated_cost"]
                required_clearances.extend(legal_analysis.get("clearances", []))
            
            # Calculate overall risk score
            overall_risk_score = self._calculate_overall_risk_score(risk_factors)
            
            # Generate production notes
            production_notes = self._generate_production_notes(scene, risk_factors, overall_risk_score)
            
            # Calculate total cost
            cost_estimates["total"] = sum(cost_estimates.values()) - cost_estimates["total"]
            
            # Determine complexity level
            complexity_level = self._determine_complexity_level(overall_risk_score)
            
            return SceneRiskAnalysis(
                scene_id=f"scene_{scene.scene_number}",
                scene_number=scene.scene_number,
                overall_risk_score=overall_risk_score,
                risk_factors=risk_factors,
                cost_estimates=cost_estimates,
                complexity_level=complexity_level,
                production_notes=production_notes,
                required_clearances=required_clearances
            )
            
        except Exception as e:
            logger.error(f"Scene risk analysis failed for scene {scene.scene_number}: {e}")
            return self._create_fallback_analysis(scene)
    
    def _analyze_location_complexity(self, scene: SceneData) -> Dict[str, Any]:
        """Analyze location complexity and associated risks"""
        location = scene.location.lower()
        time_of_day = scene.time_of_day.lower()
        
        # Determine location type
        location_type = "simple_interior"
        
        if "ext" in scene.title.lower():
            if any(keyword in location for keyword in ["street", "park", "beach", "forest"]):
                location_type = "simple_exterior"
            elif any(keyword in location for keyword in ["highway", "rooftop", "mountain", "bridge"]):
                location_type = "complex_exterior"
            elif any(keyword in location for keyword in ["water", "ocean", "lake", "river"]):
                location_type = "water"
            elif any(keyword in location for keyword in ["helicopter", "plane", "aerial"]):
                location_type = "aerial"
        else:
            if any(keyword in location for keyword in ["hospital", "police", "court", "bank"]):
                location_type = "complex_interior"
            elif any(keyword in location for keyword in ["car", "truck", "bus", "train"]):
                location_type = "vehicle"
        
        # Check for dangerous elements
        if any(keyword in scene.description.lower() for keyword in ["fire", "explosion", "fight", "crash", "gun"]):
            location_type = "dangerous"
        
        complexity_data = self.LOCATION_COMPLEXITY.get(location_type, self.LOCATION_COMPLEXITY["simple_interior"])
        
        # Night shooting adds complexity
        night_multiplier = 1.3 if time_of_day in ["night", "dusk"] else 1.0
        
        risk_score = complexity_data["score"] * night_multiplier
        estimated_cost = 5000 * complexity_data["cost_multiplier"] * night_multiplier
        
        concerns = []
        if location_type in ["complex_exterior", "water", "aerial", "dangerous"]:
            concerns.append("Requires specialized crew and equipment")
        if time_of_day in ["night", "dusk"]:
            concerns.append("Night shooting increases complexity and costs")
        if "weather" in scene.description.lower():
            concerns.append("Weather-dependent shooting")
        
        return {
            "category": "location_complexity",
            "type": location_type,
            "risk_score": min(risk_score, 100),
            "estimated_cost": estimated_cost,
            "concerns": concerns,
            "mitigation": self._get_location_mitigation(location_type)
        }
    
    def _analyze_cast_complexity(self, scene: SceneData) -> Dict[str, Any]:
        """Analyze cast size and complexity"""
        cast_count = len(scene.characters_present)
        dialogue_count = scene.dialogue_count
        
        # Calculate cast complexity
        if cast_count <= 2:
            complexity = "simple"
            risk_score = 10
            cost_multiplier = 1.0
        elif cast_count <= 5:
            complexity = "moderate"
            risk_score = 30
            cost_multiplier = 1.5
        elif cast_count <= 10:
            complexity = "complex"
            risk_score = 60
            cost_multiplier = 2.5
        else:
            complexity = "crowd"
            risk_score = 80
            cost_multiplier = 4.0
        
        # Dialogue intensity adds complexity
        if dialogue_count > 20:
            risk_score += 15
            cost_multiplier *= 1.2
        
        estimated_cost = cast_count * 500 * cost_multiplier
        
        concerns = []
        if cast_count > 5:
            concerns.append("Large cast requires careful scheduling")
        if dialogue_count > 15:
            concerns.append("Dialogue-heavy scene may require multiple takes")
        
        return {
            "category": "cast_complexity",
            "cast_count": cast_count,
            "complexity": complexity,
            "risk_score": min(risk_score, 100),
            "estimated_cost": estimated_cost,
            "concerns": concerns,
            "mitigation": self._get_cast_mitigation(complexity)
        }
    
    def _analyze_technical_requirements(self, scene: SceneData) -> Dict[str, Any]:
        """Analyze technical and equipment requirements"""
        description = scene.description.lower()
        action_text = " ".join(scene.action_lines).lower()
        full_text = f"{description} {action_text}"
        
        technical_elements = []
        risk_score = 0
        estimated_cost = 1000  # Base equipment cost
        
        # Check for special equipment needs
        if any(keyword in full_text for keyword in ["car chase", "driving", "motorcycle"]):
            technical_elements.append("Vehicle work")
            risk_score += 25
            estimated_cost += 3000
        
        if any(keyword in full_text for keyword in ["fight", "action", "stunt"]):
            technical_elements.append("Stunt coordination")
            risk_score += 30
            estimated_cost += 5000
        
        if any(keyword in full_text for keyword in ["explosion", "fire", "smoke"]):
            technical_elements.append("Special effects")
            risk_score += 40
            estimated_cost += 8000
        
        if any(keyword in full_text for keyword in ["crane", "steadicam", "drone"]):
            technical_elements.append("Specialized camera work")
            risk_score += 20
            estimated_cost += 2000
        
        if any(keyword in full_text for keyword in ["rain", "snow", "fog"]):
            technical_elements.append("Weather effects")
            risk_score += 15
            estimated_cost += 1500
        
        concerns = []
        if technical_elements:
            concerns.append("Requires specialized technical crew")
            concerns.append("Additional safety protocols needed")
        
        return {
            "category": "technical_requirements",
            "elements": technical_elements,
            "risk_score": min(risk_score, 100),
            "estimated_cost": estimated_cost,
            "concerns": concerns,
            "mitigation": "Hire specialized crew and conduct thorough safety meetings"
        }
    
    def _analyze_legal_requirements(self, scene: SceneData, agent_findings: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze legal and clearance requirements"""
        legal_risks = agent_findings.get("legal", {}).get("data", {}).get("copyright_risks", [])
        
        risk_score = 0
        estimated_cost = 0
        clearances = []
        concerns = []
        
        for risk in legal_risks:
            risk_type = risk.get("type", "")
            severity = risk.get("severity", "low")
            
            if severity == "high":
                risk_score += 30
                estimated_cost += 5000
            elif severity == "medium":
                risk_score += 20
                estimated_cost += 2000
            else:
                risk_score += 10
                estimated_cost += 500
            
            if "music" in risk_type:
                clearances.append("Music licensing")
            elif "trademark" in risk_type:
                clearances.append("Trademark clearance")
            elif "person" in risk_type:
                clearances.append("Personality rights")
            
            concerns.append(risk.get("description", "Legal clearance required"))
        
        return {
            "category": "legal_requirements",
            "clearances": clearances,
            "risk_score": min(risk_score, 100),
            "estimated_cost": estimated_cost,
            "concerns": concerns,
            "mitigation": "Obtain necessary clearances before filming"
        }
    
    def _calculate_overall_risk_score(self, risk_factors: List[Dict[str, Any]]) -> float:
        """Calculate weighted overall risk score"""
        total_score = 0
        total_weight = 0
        
        for factor in risk_factors:
            category = factor.get("category", "")
            risk_score = factor.get("risk_score", 0)
            weight = self.RISK_WEIGHTS.get(category, 0.1)
            
            total_score += risk_score * weight
            total_weight += weight
        
        return min(total_score / max(total_weight, 1), 100)
    
    def _generate_production_notes(
        self, 
        scene: SceneData, 
        risk_factors: List[Dict[str, Any]], 
        overall_risk_score: float
    ) -> List[str]:
        """Generate production notes for the scene"""
        notes = []
        
        # Add scene summary
        notes.append(f"Scene {scene.scene_number}: {scene.title}")
        notes.append(f"Location: {scene.location} | Time: {scene.time_of_day}")
        notes.append(f"Characters: {len(scene.characters_present)} | Risk Score: {overall_risk_score:.1f}")
        
        # Add specific concerns
        for factor in risk_factors:
            concerns = factor.get("concerns", [])
            if concerns:
                notes.append(f"{factor['category'].replace('_', ' ').title()} concerns:")
                notes.extend([f"  • {concern}" for concern in concerns])
        
        # Add recommendations based on risk score
        if overall_risk_score > 70:
            notes.append("⚠️ HIGH RISK: Requires experienced crew and detailed planning")
        elif overall_risk_score > 40:
            notes.append("⚡ MEDIUM RISK: Consider additional preparation time")
        else:
            notes.append("✅ LOW RISK: Standard production protocols apply")
        
        return notes
    
    def _determine_complexity_level(self, risk_score: float) -> str:
        """Determine complexity level from risk score"""
        if risk_score >= 70:
            return "high"
        elif risk_score >= 40:
            return "medium"
        else:
            return "low"
    
    def _get_location_mitigation(self, location_type: str) -> str:
        """Get mitigation strategy for location type"""
        strategies = {
            "water": "Hire water safety coordinator and marine unit",
            "aerial": "Certified drone operator and flight clearances",
            "dangerous": "Safety coordinator, stunt doubles, and insurance",
            "complex_exterior": "Location permits and weather contingency",
            "vehicle": "Professional drivers and closed road permits",
        }
        return strategies.get(location_type, "Standard location preparation")
    
    def _get_cast_mitigation(self, complexity: str) -> str:
        """Get mitigation strategy for cast complexity"""
        strategies = {
            "crowd": "Assistant directors and crowd control",
            "complex": "Detailed call sheets and rehearsal time",
            "moderate": "Clear scene choreography",
            "simple": "Standard blocking and direction"
        }
        return strategies.get(complexity, "Standard direction")
    
    def _create_fallback_analysis(self, scene: SceneData) -> SceneRiskAnalysis:
        """Create basic analysis if detailed analysis fails"""
        return SceneRiskAnalysis(
            scene_id=f"scene_{scene.scene_number}",
            scene_number=scene.scene_number,
            overall_risk_score=25.0,  # Conservative estimate
            risk_factors=[{
                "category": "general",
                "risk_score": 25.0,
                "concerns": ["Unable to perform detailed risk analysis"],
                "mitigation": "Manual review recommended"
            }],
            cost_estimates={"location": 3000, "cast": 1500, "equipment": 1000, "legal": 0, "total": 5500},
            complexity_level="medium",
            production_notes=[
                f"Scene {scene.scene_number}: {scene.title}",
                "Risk analysis incomplete - manual review required"
            ],
            required_clearances=[]
        )

def analyze_scene_risks(
    scenes: List[SceneData], 
    agent_findings: Dict[str, Any] = None,
    budget_tier: str = "medium"
) -> List[SceneRiskAnalysis]:
    """
    Analyze risks for multiple scenes
    """
    analyzer = SceneRiskAnalyzer()
    analyses = []
    
    for scene in scenes:
        analysis = analyzer.analyze_scene_risks(scene, agent_findings, budget_tier)
        analyses.append(analysis)
    
    logger.info(f"Completed risk analysis for {len(analyses)} scenes")
    return analyses