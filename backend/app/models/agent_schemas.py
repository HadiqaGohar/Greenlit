"""
Pydantic models for multi-agent communication and orchestration
Defines data structures for agent tasks, results, and coordination
"""

from typing import Dict, List, Any, Optional, Literal
from datetime import datetime, timezone
from pydantic import BaseModel, Field
from uuid import uuid4


def _utcnow():
    return datetime.now(timezone.utc)


class AgentTask(BaseModel):
    """Task specification for individual agents"""
    task_id: str = Field(default_factory=lambda: str(uuid4()))
    agent_type: Literal["director", "research", "legal", "continuity", "storyboard", "tts", "schedule", "stakeholder", "budget", "relationship", "pitch_deck", "location", "cultural"]
    task_data: Dict[str, Any]
    priority: Literal["low", "normal", "high"] = "normal"
    created_at: datetime = Field(default_factory=_utcnow)


class AgentResult(BaseModel):
    """Standardized result format from any agent"""
    agent_type: str
    task_id: str
    success: bool = True
    confidence_score: float = Field(ge=0.0, le=1.0)
    processing_time: float
    data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    completed_at: datetime = Field(default_factory=_utcnow)


class AgentTimelineStep(BaseModel):
    """Single step in the agent replay timeline"""
    agent: str
    status: Literal["queued", "running", "complete", "error"] = "queued"
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    summary: str = ""
    claims_count: Optional[int] = None
    issues_found: Optional[int] = None
    confidence: Optional[float] = None
    phase: Literal["sequential", "parallel"] = "sequential"


class ReadinessScore(BaseModel):
    """Production readiness scores across 5 dimensions"""
    legal_clearance: float = Field(ge=0.0, le=100.0, default=0.0)
    historical_accuracy: float = Field(ge=0.0, le=100.0, default=0.0)
    continuity: float = Field(ge=0.0, le=100.0, default=0.0)
    budget_feasibility: float = Field(ge=0.0, le=100.0, default=0.0)
    overall: float = Field(ge=0.0, le=100.0, default=0.0)
    grade: str = "F"


class AgentFlowStep(BaseModel):
    """Data flowing between agents for the flow diagram"""
    agent: str
    claims_in: int = 0
    claims_out: int = 0
    verified: int = 0
    flagged: int = 0
    uncertain: int = 0
    issues_high: int = 0
    issues_medium: int = 0
    issues_low: int = 0


class Suggestion(BaseModel):
    """AI-generated fix suggestion for a flagged issue"""
    issue_id: str
    issue_type: str
    severity: str
    original_text: str
    suggested_text: str
    rationale: str


class ProductionIssue(BaseModel):
    """Represents a potential production problem identified by agents"""
    type: Literal["legal", "continuity", "factual", "technical", "licensing"]
    severity: Literal["low", "medium", "high", "critical"]
    description: str
    location_in_script: Optional[str] = None
    suggested_action: Optional[str] = None
    estimated_cost_impact: Optional[str] = None
    urgency: Literal["immediate", "before_production", "nice_to_fix"] = "before_production"


class RiskAssessment(BaseModel):
    """Overall production risk assessment from multi-agent analysis"""
    overall_risk_score: float = Field(ge=0.0, le=100.0)
    risk_level: Literal["low", "medium", "high", "critical"]
    risk_factors: List[str]
    critical_issues: List[ProductionIssue]
    recommended_actions: List[str]
    confidence: float = Field(ge=0.0, le=1.0, default=0.8)


class AutomationAction(BaseModel):
    """Represents an automated action triggered by agent findings"""
    action_type: Literal["notification", "checklist", "alert", "export", "schedule"]
    trigger_condition: str
    action_data: Dict[str, Any]
    status: Literal["pending", "completed", "failed"] = "pending"
    scheduled_for: Optional[datetime] = None
    executed_at: Optional[datetime] = None


class OrchestratorReport(BaseModel):
    """Comprehensive report from multi-agent orchestration"""
    report_id: str
    timestamp: datetime
    script_length: int
    script_text: str = Field(default="", description="Original script text")
    agent_results: Dict[str, AgentResult]
    risk_assessment: RiskAssessment
    processing_time: float
    automation_actions: Dict[str, Any]
    agent_timeline: List[AgentTimelineStep] = Field(default_factory=list)
    readiness_scores: ReadinessScore = Field(default_factory=ReadinessScore)
    agent_flow: List[AgentFlowStep] = Field(default_factory=list)
    suggestions: List[Suggestion] = Field(default_factory=list)
    scenes: List[Dict[str, Any]] = Field(default_factory=list)
    characters: List[Dict[str, Any]] = Field(default_factory=list)
    scene_statistics: Dict[str, Any] = Field(default_factory=dict)
    character_statistics: Dict[str, Any] = Field(default_factory=dict)
    continuity_issues: List[Dict[str, Any]] = Field(default_factory=list)

    @property
    def successful_agents(self) -> List[str]:
        return [name for name, result in self.agent_results.items() if result.success]

    @property
    def failed_agents(self) -> List[str]:
        return [name for name, result in self.agent_results.items() if not result.success]

    @property
    def average_confidence(self) -> float:
        successful = [r for r in self.agent_results.values() if r.success]
        if not successful:
            return 0.0
        return sum(r.confidence_score for r in successful) / len(successful)


# Agent-specific result schemas
class DirectorAgentResult(BaseModel):
    """Results from Director Agent - claims extraction and script analysis"""
    claims_extracted: int
    claims: List[Dict[str, Any]]
    script_sections: List[Dict[str, str]]
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ResearchAgentResult(BaseModel):
    """Results from Research Agent - fact verification via Parallel API"""
    claims_researched: int
    verified_claims: List[Dict[str, Any]]
    flagged_claims: List[Dict[str, Any]]
    uncertain_claims: List[Dict[str, Any]]
    sources: List[Dict[str, str]]
    parallel_api_calls: int
    metadata: Dict[str, Any] = Field(default_factory=dict)


class LegalAgentResult(BaseModel):
    """Results from Legal Agent - copyright and licensing assessment"""
    copyright_risks: List[Dict[str, Any]]
    trademark_issues: List[Dict[str, Any]]
    clearance_required: List[Dict[str, Any]]
    real_person_mentions: List[Dict[str, Any]]
    licensing_checklist: List[str]
    estimated_clearance_cost: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ContinuityAgentResult(BaseModel):
    """Results from Continuity Agent - consistency checking across script"""
    character_inconsistencies: List[Dict[str, Any]]
    timeline_issues: List[Dict[str, Any]]
    location_continuity: List[Dict[str, Any]]
    prop_tracking: List[Dict[str, Any]]
    scene_transitions: List[Dict[str, Any]]
    metadata: Dict[str, Any] = Field(default_factory=dict)


# Automation-specific schemas
class FileWatcherEvent(BaseModel):
    """Event triggered by file monitoring system"""
    event_type: Literal["created", "modified", "deleted"]
    file_path: str
    file_name: str
    timestamp: datetime = Field(default_factory=_utcnow)
    file_size: Optional[int] = None
    trigger_analysis: bool = True


class BatchProcessRequest(BaseModel):
    """Request for batch processing multiple script sections"""
    scenes: List[str]
    priority: Literal["low", "normal", "high"] = "normal"
    agents_to_run: List[str] = Field(default=["director", "research", "legal", "continuity"])
    notification_webhook: Optional[str] = None
    auto_export: bool = False


class NotificationRequest(BaseModel):
    """Request to send automated notification"""
    notification_type: Literal["slack", "email", "webhook"]
    recipient: str
    subject: str
    message: str
    priority: Literal["low", "medium", "high", "urgent"] = "medium"
    data: Optional[Dict[str, Any]] = None
