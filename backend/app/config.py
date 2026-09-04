"""
Configuration settings for Greenlit AI backend
Loads environment variables and provides application configuration
"""

import os
import json
import warnings
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


def _parse_cors_origins() -> List[str]:
    raw = os.environ.get("CORS_ORIGINS", "")
    if not raw:
        return ["http://localhost:3000", "http://127.0.0.1:3000"]
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, list):
            return parsed
        return [str(parsed)]
    except (json.JSONDecodeError, TypeError):
        return [origin.strip() for origin in raw.split(",") if origin.strip()]


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True, extra="ignore")
    
    # Gemini Configuration (Google Cloud Gen AI SDK)
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-2.5-flash"
    GOOGLE_CLOUD_PROJECT: Optional[str] = None
    GOOGLE_CLOUD_LOCATION: str = "global"
    USE_ENTERPRISE_GEMINI: bool = False  # Set True for Agent Platform
    
    # Parallel API Configuration
    PARALLEL_API_KEY: Optional[str] = None
    
    # FastAPI Configuration
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # CORS Configuration - parsed manually to avoid pydantic_settings JSON parsing issues
    CORS_ORIGINS: List[str] = _parse_cors_origins()
    
    # Security
    SECRET_KEY: str = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")
    
    # File Watcher Configuration
    WATCH_FOLDER_ENABLED: bool = True
    WATCH_CHECK_INTERVAL: int = 30
    
    # Automation Configuration
    AUTO_NOTIFICATIONS_ENABLED: bool = True
    SLACK_WEBHOOK_URL: Optional[str] = None
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_PERIOD: int = 60
    
    # Multi-Agent Configuration
    AGENTS_ENABLED: List[str] = ["director", "research", "legal", "continuity", "storyboard", "tts", "schedule", "stakeholder", "budget", "relationship", "pitch_deck", "location"]
    PARALLEL_AGENT_EXECUTION: bool = True
    MAX_CONCURRENT_AGENTS: int = 4
    
    # Monitoring
    SENTRY_DSN: Optional[str] = None
    ENABLE_MONITORING: bool = False


# Create global settings instance
settings = Settings()

# Check for default SECRET_KEY and warn
if settings.SECRET_KEY == "dev-secret-key-change-in-production":
    warnings.warn("⚠️ Using default SECRET_KEY - set SECRET_KEY environment variable for production", UserWarning)

# Validate required API keys
if not settings.GEMINI_API_KEY:
    warnings.warn("⚠️ GEMINI_API_KEY not set - Gemini agents will fail", UserWarning)
if not settings.PARALLEL_API_KEY:
    warnings.warn("⚠️ PARALLEL_API_KEY not set - Research agent will use fallback mode", UserWarning)


def get_settings() -> Settings:
    """Get application settings"""
    return settings
