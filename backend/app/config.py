"""
Configuration settings for Greenlit AI backend
Loads environment variables and provides application configuration
"""

import os
import warnings
from typing import List, Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
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
    
    # CORS Configuration
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    
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
    AGENTS_ENABLED: List[str] = ["director", "research", "legal", "continuity"]
    PARALLEL_AGENT_EXECUTION: bool = True
    MAX_CONCURRENT_AGENTS: int = 4
    
    # Monitoring
    SENTRY_DSN: Optional[str] = None
    ENABLE_MONITORING: bool = False
    
    class Config:
        env_file = ".env"
        case_sensitive = True


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
