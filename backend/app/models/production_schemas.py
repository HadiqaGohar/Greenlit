"""
Enhanced production-focused data models for Greenlit AI
Includes scene analysis, character tracking, collaboration, and analytics
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field
from uuid import uuid4

class ScriptStatus(str, Enum):
    DRAFT = "draft"
    IN_REVIEW = "in_review" 
    PRODUCTION_READY = "production_ready"
    ARCHIVED = "archived"

class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ProductionRole(str, Enum):
    DIRECTOR = "director"
    PRODUCER = "producer"
    SCRIPT_SUPERVISOR = "script_supervisor"
    LINE_PRODUCER = "line_producer"
    LEGAL_AFFAIRS = "legal_affairs"
    RESEARCHER = "researcher"

# Enhanced Script Models
class Script(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str
    title: str
    content: str
    status: ScriptStatus = ScriptStatus.DRAFT
    risk_score: float = 0.0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    version: int = 1
    genre: Optional[str] = None
    budget_range: Optional[str] = None  # "low", "medium", "high"
    total_scenes: int = 0

class ScriptVersion(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    script_id: str
    version_number: int
    content: str
    changes_summary: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str

# Scene Analysis Models
class Scene(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    script_id: str
    scene_number: int
    title: str  # e.g., "INT. COFFEE SHOP - DAY"
    location: str
    time_of_day: str  # DAY, NIGHT, DAWN, DUSK
    description: str
    characters_present: List[str] = []
    risk_score: float = 0.0
    estimated_cost: float = 0.0
    page_start: Optional[int] = None
    page_end: Optional[int] = None

class SceneRiskAnalysis(BaseModel):
    scene_id: str
    legal_risks: List[Dict[str, Any]] = []
    continuity_issues: List[Dict[str, Any]] = []
    research_flags: List[Dict[str, Any]] = []
    location_complexity: str = "simple"  # simple, moderate, complex
    cast_size: int = 0
    special_requirements: List[str] = []

# Character Tracking Models
class Character(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    script_id: str
    name: str
    descriptions: List[str] = []  # Various descriptions found in script
    first_appearance: int = 1  # Scene number
    total_scenes: int = 0
    character_type: str = "supporting"  # lead, supporting, background, extra
    age_range: Optional[str] = None
    gender: Optional[str] = None
    notes: str = ""

class CharacterAppearance(BaseModel):
    character_id: str
    scene_id: str
    description_in_scene: str
    action_lines: List[str] = []
    dialogue_count: int = 0

class ContinuityIssue(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    script_id: str
    character_id: Optional[str] = None
    scene_ids: List[str] = []
    issue_type: str  # "character_description", "timeline", "props", "location"
    severity: RiskLevel
    description: str
    suggested_fix: str = ""
    resolved: bool = False

# Collaboration Models
class Comment(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    report_id: str
    claim_id: Optional[str] = None  # Can comment on specific claims
    scene_id: Optional[str] = None   # Can comment on scenes
    user_id: str
    user_name: str
    user_role: ProductionRole
    content: str
    parent_id: Optional[str] = None  # For threaded replies
    resolved: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class TeamMember(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str
    script_id: str
    role: ProductionRole
    permissions: List[str] = []  # "view", "comment", "resolve", "admin"
    added_at: datetime = Field(default_factory=datetime.utcnow)

class ReviewStatus(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    script_id: str
    reviewer_id: str
    status: str  # "pending", "approved", "rejected", "needs_changes"
    comments: str = ""
    reviewed_at: Optional[datetime] = None

# Analytics Models
class ProjectSummary(BaseModel):
    id: str
    title: str
    status: ScriptStatus
    risk_score: float
    last_analyzed: datetime
    scenes_count: int
    characters_count: int
    issues: Dict[str, int] = {
        "critical": 0,
        "high": 0, 
        "medium": 0,
        "low": 0
    }
    team_size: int = 0
    progress_percentage: float = 0.0

class TrendPoint(BaseModel):
    date: datetime
    value: float
    metric: str  # "risk_score", "scripts_analyzed", "issues_resolved"

class AnalyticsSummary(BaseModel):
    total_scripts: int = 0
    average_risk_score: float = 0.0
    scripts_this_month: int = 0
    active_collaborators: int = 0
    trends: List[TrendPoint] = []
    top_risk_categories: Dict[str, int] = {}
    recent_activity: List[Dict[str, Any]] = []

# Notification Models
class NotificationSettings(BaseModel):
    user_id: str
    email_enabled: bool = True
    slack_enabled: bool = False
    slack_webhook: Optional[str] = None
    high_risk_threshold: float = 70.0
    notify_on_comments: bool = True
    notify_on_completion: bool = True
    digest_frequency: str = "weekly"  # "daily", "weekly", "monthly", "never"

class Notification(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str
    type: str  # "high_risk", "analysis_complete", "comment_added", "review_request"
    title: str
    message: str
    script_id: Optional[str] = None
    read: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    action_url: Optional[str] = None

# Export Models
class ExportRequest(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str
    script_id: str
    format: str  # "pdf", "json", "csv", "docx"
    sections: List[str] = []  # "overview", "scenes", "characters", "risks"
    include_comments: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = "pending"  # "pending", "processing", "completed", "failed"
    download_url: Optional[str] = None

# Cost Estimation Models
class CostEstimate(BaseModel):
    scene_id: str
    location_cost: float = 0.0
    cast_cost: float = 0.0
    equipment_cost: float = 0.0
    legal_clearance_cost: float = 0.0
    total_estimated_cost: float = 0.0
    confidence_level: float = 0.5
    cost_factors: List[str] = []
    notes: str = ""

class BudgetImpact(BaseModel):
    script_id: str
    total_estimated_cost: float = 0.0
    cost_by_category: Dict[str, float] = {}
    high_cost_scenes: List[str] = []
    cost_saving_suggestions: List[str] = []
    budget_risk_level: RiskLevel = RiskLevel.MEDIUM

# File Management Models  
class UploadedFile(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str
    filename: str
    file_size: int
    file_type: str
    storage_path: str
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    processed: bool = False
    script_id: Optional[str] = None

# API Response Models
class DashboardResponse(BaseModel):
    projects: List[ProjectSummary]
    analytics: AnalyticsSummary
    notifications: List[Notification]
    recent_exports: List[ExportRequest]

class SceneAnalysisResponse(BaseModel):
    scenes: List[Scene]
    scene_risks: List[SceneRiskAnalysis]
    characters: List[Character]
    continuity_issues: List[ContinuityIssue]
    total_estimated_cost: float
    recommendations: List[str]

class CharacterBibleResponse(BaseModel):
    characters: List[Character]
    character_appearances: Dict[str, List[CharacterAppearance]]
    continuity_issues: List[ContinuityIssue]
    character_network: Dict[str, List[str]]  # Which characters appear together

class CollaborationResponse(BaseModel):
    comments: List[Comment]
    team_members: List[TeamMember]
    review_status: List[ReviewStatus]
    activity_feed: List[Dict[str, Any]]
    unresolved_issues: int

# Request Models
class ScriptAnalysisRequest(BaseModel):
    script_text: str
    title: str
    options: Dict[str, Any] = {}
    analyze_scenes: bool = True
    extract_characters: bool = True
    estimate_costs: bool = False

class CommentRequest(BaseModel):
    content: str
    claim_id: Optional[str] = None
    scene_id: Optional[str] = None
    parent_id: Optional[str] = None

class TeamInviteRequest(BaseModel):
    email: str
    role: ProductionRole
    permissions: List[str] = ["view", "comment"]

class NotificationUpdateRequest(BaseModel):
    settings: NotificationSettings