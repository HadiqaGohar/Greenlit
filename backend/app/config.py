"""
Configuration settings for Greenlit AI backend
Loads environment variables and provides application configuration
"""

import os
from typing import List, Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # OpenRouter / Gemini Configuration
    OPENROUTER_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "google/gemini-flash-1.5"
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    GEMINI_API_KEY: Optional[str] = None  # Fallback for direct Gemini access
    
    # Parallel API Configuration
    PARALLEL_API_KEY: Optional[str] = None
    PARALLEL_API_URL: str = "https://api.parallelapi.com/v1"
    
    # Google Cloud Configuration
    GOOGLE_CLOUD_PROJECT: Optional[str] = None
    GOOGLE_APPLICATION_CREDENTIALS: Optional[str] = None
    
    # FastAPI Configuration
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # CORS Configuration
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    
    # Security
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    
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


def get_settings() -> Settings:
    """Get application settings"""
    return settings