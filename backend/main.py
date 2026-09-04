"""
Greenlit AI FastAPI Backend
Multi-agent script analysis system for film production
"""

import logging
import asyncio
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings, CORS_ORIGINS
from app.routers import analyze, health, automation, webhooks
from app.agents.orchestrator import AgentOrchestrator
from app.automation.file_watcher import FileWatcher

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global instances
orchestrator = None
file_watcher = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    global orchestrator, file_watcher
    
    # Startup
    logger.info("🎬 Starting Greenlit AI backend...")
    
    try:
        # Initialize multi-agent orchestrator
        orchestrator = AgentOrchestrator()
        logger.info("✅ Multi-agent orchestrator initialized")
        
        # Initialize file watcher if enabled
        if settings.WATCH_FOLDER_ENABLED:
            file_watcher = FileWatcher(orchestrator)
            # Start file watcher in background
            asyncio.create_task(file_watcher.start_watching())
            logger.info("✅ File watcher started")
        
        # Store in app state for access in routes
        app.state.orchestrator = orchestrator
        app.state.file_watcher = file_watcher
        
        logger.info("🚀 Greenlit AI backend ready!")
        
        yield
        
    except Exception as e:
        logger.error(f"❌ Startup failed: {str(e)}")
        raise
    
    # Shutdown
    logger.info("🛑 Shutting down Greenlit AI backend...")
    
    if file_watcher:
        file_watcher.stop_watching()
    
    # Close API clients properly
    try:
        from app.agent.gemini_client import close_gemini_client
        from app.research.parallel_client import close_parallel_client
        await close_gemini_client()
        await close_parallel_client()
        logger.info("✅ API clients closed")
    except Exception as e:
        logger.warning(f"Cleanup warning: {str(e)}")
    
    logger.info("✅ Shutdown complete")


# Create FastAPI app with lifespan management
app = FastAPI(
    title="Greenlit AI Backend",
    description="Multi-agent script analysis system for film and TV production",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/health", tags=["Health"])
app.include_router(analyze.router, prefix="/api", tags=["Analysis"]) 
app.include_router(automation.router, prefix="/automation", tags=["Automation"])
app.include_router(webhooks.router, prefix="/webhooks", tags=["Webhooks"])

# Add dashboard router
try:
    from app.routers import dashboard
    app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"])
except ImportError:
    logger.warning("Dashboard router not available yet")

# Add enhanced analysis router
try:
    from app.routers import enhanced_analysis
    app.include_router(enhanced_analysis.router, prefix="/api", tags=["Enhanced Analysis"])
except ImportError:
    logger.warning("Enhanced analysis router not available yet")

# Add collaboration router (WebSocket + REST)
try:
    from app.routers import collaboration
    app.include_router(collaboration.router, prefix="/api", tags=["Collaboration"])
except ImportError:
    logger.warning("Collaboration router not available yet")

# Add export and sharing router
try:
    from app.routers import export
    app.include_router(export.router, prefix="/api", tags=["Export"])
except ImportError:
    logger.warning("Export router not available yet")

# Add analytics router
try:
    from app.routers import analytics
    app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics"])
except ImportError:
    logger.warning("Analytics router not available yet")

# Add version control router
try:
    from app.routers import version_control
    app.include_router(version_control.router, prefix="/api", tags=["Version Control"])
except ImportError:
    logger.warning("Version control router not available yet")

# Add monitoring router
try:
    from app.routers import monitoring
    app.include_router(monitoring.router, prefix="/api", tags=["Monitoring"])
except ImportError:
    logger.warning("Monitoring router not available yet")

# Add chat router ("Ask the Script")
try:
    from app.routers import chat
    app.include_router(chat.router, prefix="/api", tags=["Chat"])
except ImportError:
    logger.warning("Chat router not available yet")

# Add scene risk router (Heatmap)
try:
    from app.routers import scene_risk
    app.include_router(scene_risk.router, prefix="/api", tags=["Scene Risk"])
except ImportError:
    logger.warning("Scene risk router not available yet")

# Add budget estimation router
try:
    from app.routers import budget
    app.include_router(budget.router, prefix="/api", tags=["Budget"])
except ImportError:
    logger.warning("Budget router not available yet")

# Add cultural sensitivity router
try:
    from app.routers import cultural
    app.include_router(cultural.router, prefix="/api", tags=["Cultural"])
except ImportError:
    logger.warning("Cultural sensitivity router not available yet")

# Add storyboard generation router
try:
    from app.routers import storyboard
    app.include_router(storyboard.router, prefix="/api", tags=["Storyboard"])
except ImportError:
    logger.warning("Storyboard router not available yet")

# Add TTS / Table Read router
try:
    from app.routers import tts
    app.include_router(tts.router, prefix="/api", tags=["TTS"])
except ImportError:
    logger.warning("TTS router not available yet")

# Add Production Schedule router
try:
    from app.routers import schedule
    app.include_router(schedule.router, prefix="/api", tags=["Schedule"])
except ImportError:
    logger.warning("Schedule router not available yet")

# Add Multi-Stakeholder Analysis router
try:
    from app.routers import stakeholder
    app.include_router(stakeholder.router, prefix="/api", tags=["Stakeholder"])
except ImportError:
    logger.warning("Stakeholder router not available yet")


# Add Character Relationship Graph router
try:
    from app.routers import relationship
    app.include_router(relationship.router, prefix="/api", tags=["Relationship"])
except ImportError:
    logger.warning("Relationship router not available yet")


# Add Script Comparison router
try:
    from app.routers import script_compare
    app.include_router(script_compare.router, prefix="/api", tags=["Script Compare"])
except ImportError:
    logger.warning("Script comparison router not available yet")


# Add Pitch Deck router
try:
    from app.routers import pitch_deck
    app.include_router(pitch_deck.router, prefix="/api", tags=["Pitch Deck"])
except ImportError:
    logger.warning("Pitch deck router not available yet")


# Add Scene-to-Location Matching router
try:
    from app.routers import location
    app.include_router(location.router, prefix="/api", tags=["Location"])
except ImportError:
    logger.warning("Location router not available yet")


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": "Greenlit AI Backend",
        "version": "1.0.0",
        "description": "Multi-agent script analysis for film production",
        "status": "operational",
        "agents": settings.AGENTS_ENABLED,
        "features": {
            "multi_agent_orchestration": True,
            "file_watching": settings.WATCH_FOLDER_ENABLED,
            "auto_notifications": settings.AUTO_NOTIFICATIONS_ENABLED,
            "parallel_execution": settings.PARALLEL_AGENT_EXECUTION
        },
        "docs": "/docs",
        "health": "/health"
    }


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for unhandled errors"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": "An unexpected error occurred. Please try again." if not settings.DEBUG else str(exc)
        }
    )


if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"🎬 Starting Greenlit AI on {settings.HOST}:{settings.PORT}")
    
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )