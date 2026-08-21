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

from app.config import settings
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
    
    # Close any async resources
    if orchestrator:
        # Close agent clients if they have cleanup methods
        try:
            if hasattr(orchestrator.director, 'gemini_client'):
                await orchestrator.director.gemini_client.close()
            if hasattr(orchestrator.researcher, 'parallel_client'):
                await orchestrator.researcher.parallel_client.close()
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
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/health", tags=["Health"])
app.include_router(analyze.router, prefix="/api", tags=["Analysis"]) 
app.include_router(automation.router, prefix="/automation", tags=["Automation"])
app.include_router(webhooks.router, prefix="/webhooks", tags=["Webhooks"])


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