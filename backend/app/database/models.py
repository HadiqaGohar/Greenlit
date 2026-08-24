"""
SQLAlchemy database models for enhanced production features
Uses String(36) for UUID columns to ensure SQLite compatibility
"""

from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid

from app.database.connection import Base


def generate_uuid():
    return str(uuid.uuid4())


class Script(Base):
    __tablename__ = "scripts"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), nullable=False)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    status = Column(String(50), default="draft")
    risk_score = Column(Float, default=0.0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    version = Column(Integer, default=1)
    genre = Column(String(100))
    budget_range = Column(String(50))
    total_scenes = Column(Integer, default=0)
    
    scenes = relationship("Scene", back_populates="script", cascade="all, delete-orphan")
    characters = relationship("Character", back_populates="script", cascade="all, delete-orphan")
    comments = relationship("Comment", back_populates="script", cascade="all, delete-orphan")
    team_members = relationship("TeamMember", back_populates="script", cascade="all, delete-orphan")


class ScriptVersion(Base):
    __tablename__ = "script_versions"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    script_id = Column(String(36), ForeignKey("scripts.id"), nullable=False)
    version_number = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    changes_summary = Column(Text, default="")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    created_by = Column(String(36), nullable=False)


class Scene(Base):
    __tablename__ = "scenes"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    script_id = Column(String(36), ForeignKey("scripts.id"), nullable=False)
    scene_number = Column(Integer, nullable=False)
    title = Column(String(255), nullable=False)
    location = Column(String(255))
    time_of_day = Column(String(50))
    description = Column(Text)
    characters_present = Column(JSON, default=list)
    risk_score = Column(Float, default=0.0)
    estimated_cost = Column(Float, default=0.0)
    page_start = Column(Integer)
    page_end = Column(Integer)
    
    script = relationship("Script", back_populates="scenes")
    risk_analysis = relationship("SceneRiskAnalysis", back_populates="scene", cascade="all, delete-orphan")


class SceneRiskAnalysis(Base):
    __tablename__ = "scene_risk_analysis"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    scene_id = Column(String(36), ForeignKey("scenes.id"), nullable=False)
    legal_risks = Column(JSON, default=list)
    continuity_issues = Column(JSON, default=list)
    research_flags = Column(JSON, default=list)
    location_complexity = Column(String(50), default="simple")
    cast_size = Column(Integer, default=0)
    special_requirements = Column(JSON, default=list)
    
    scene = relationship("Scene", back_populates="risk_analysis")


class Character(Base):
    __tablename__ = "characters"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    script_id = Column(String(36), ForeignKey("scripts.id"), nullable=False)
    name = Column(String(255), nullable=False)
    descriptions = Column(JSON, default=list)
    first_appearance = Column(Integer, default=1)
    total_scenes = Column(Integer, default=0)
    character_type = Column(String(50), default="supporting")
    age_range = Column(String(50))
    gender = Column(String(50))
    notes = Column(Text, default="")
    
    script = relationship("Script", back_populates="characters")
    appearances = relationship("CharacterAppearance", back_populates="character", cascade="all, delete-orphan")


class CharacterAppearance(Base):
    __tablename__ = "character_appearances"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    character_id = Column(String(36), ForeignKey("characters.id"), nullable=False)
    scene_id = Column(String(36), ForeignKey("scenes.id"), nullable=False)
    description_in_scene = Column(Text)
    action_lines = Column(JSON, default=list)
    dialogue_count = Column(Integer, default=0)
    
    character = relationship("Character", back_populates="appearances")


class ContinuityIssue(Base):
    __tablename__ = "continuity_issues"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    script_id = Column(String(36), ForeignKey("scripts.id"), nullable=False)
    character_id = Column(String(36), ForeignKey("characters.id"))
    scene_ids = Column(JSON, default=list)
    issue_type = Column(String(100), nullable=False)
    severity = Column(String(50), nullable=False)
    description = Column(Text, nullable=False)
    suggested_fix = Column(Text, default="")
    resolved = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class Comment(Base):
    __tablename__ = "comments"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    script_id = Column(String(36), ForeignKey("scripts.id"), nullable=False)
    claim_id = Column(String(36))
    scene_id = Column(String(36), ForeignKey("scenes.id"))
    user_id = Column(String(36), nullable=False)
    user_name = Column(String(255), nullable=False)
    user_role = Column(String(100), nullable=False)
    content = Column(Text, nullable=False)
    parent_id = Column(String(36), ForeignKey("comments.id"))
    resolved = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    script = relationship("Script", back_populates="comments")
    replies = relationship("Comment", remote_side="Comment.id")


class TeamMember(Base):
    __tablename__ = "team_members"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), nullable=False)
    script_id = Column(String(36), ForeignKey("scripts.id"), nullable=False)
    role = Column(String(100), nullable=False)
    permissions = Column(JSON, default=list)
    added_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    script = relationship("Script", back_populates="team_members")


class ReviewStatus(Base):
    __tablename__ = "review_statuses"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    script_id = Column(String(36), ForeignKey("scripts.id"), nullable=False)
    reviewer_id = Column(String(36), nullable=False)
    status = Column(String(50), default="pending")
    comments = Column(Text, default="")
    reviewed_at = Column(DateTime)


class NotificationSettings(Base):
    __tablename__ = "notification_settings"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), unique=True, nullable=False)
    email_enabled = Column(Boolean, default=True)
    slack_enabled = Column(Boolean, default=False)
    slack_webhook = Column(String(500))
    high_risk_threshold = Column(Float, default=70.0)
    notify_on_comments = Column(Boolean, default=True)
    notify_on_completion = Column(Boolean, default=True)
    digest_frequency = Column(String(50), default="weekly")


class Notification(Base):
    __tablename__ = "notifications"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), nullable=False)
    type = Column(String(100), nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    script_id = Column(String(36), ForeignKey("scripts.id"))
    read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    action_url = Column(String(500))


class ExportRequest(Base):
    __tablename__ = "export_requests"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), nullable=False)
    script_id = Column(String(36), ForeignKey("scripts.id"), nullable=False)
    format = Column(String(50), nullable=False)
    sections = Column(JSON, default=list)
    include_comments = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    status = Column(String(50), default="pending")
    download_url = Column(String(500))


class CostEstimate(Base):
    __tablename__ = "cost_estimates"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    scene_id = Column(String(36), ForeignKey("scenes.id"), nullable=False)
    location_cost = Column(Float, default=0.0)
    cast_cost = Column(Float, default=0.0)
    equipment_cost = Column(Float, default=0.0)
    legal_clearance_cost = Column(Float, default=0.0)
    total_estimated_cost = Column(Float, default=0.0)
    confidence_level = Column(Float, default=0.5)
    cost_factors = Column(JSON, default=list)
    notes = Column(Text, default="")


class UploadedFile(Base):
    __tablename__ = "uploaded_files"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), nullable=False)
    filename = Column(String(255), nullable=False)
    file_size = Column(Integer, nullable=False)
    file_type = Column(String(100), nullable=False)
    storage_path = Column(String(500), nullable=False)
    uploaded_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    processed = Column(Boolean, default=False)
    script_id = Column(String(36), ForeignKey("scripts.id"))


class Analytics(Base):
    __tablename__ = "analytics"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36))
    metric = Column(String(100), nullable=False)
    value = Column(Float, nullable=False)
    date = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    extra_data = Column(JSON, default=dict)
