"""
Main FastAPI application for Alert Monitoring System
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import logging
import sys
from pathlib import Path

# Add the app directory to Python path
sys.path.append(str(Path(__file__).parent))

from api.v1 import alerts, groups
from core.config import settings
from core.database import init_database
from services.vector_store import VectorStore
from services.llm_service import LLMService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="AI Alert Monitoring System",
    description="Intelligent alert grouping and RCA generation using AI",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Global exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    try:
        logger.info("Starting Alert Monitoring System...")
        
        # Initialize database
        await init_database()
        logger.info("Database initialized")
        
        # Initialize vector store
        vector_store = VectorStore()
        await vector_store.initialize()
        logger.info("Vector store initialized")
        
        # Initialize LLM service
        llm_service = LLMService()
        await llm_service.initialize()
        logger.info("LLM service initialized")
        
        logger.info("Alert Monitoring System started successfully!")
        
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        raise

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down Alert Monitoring System...")

# Include API routers
app.include_router(
    alerts.router,
    prefix="/api/v1/alerts",
    tags=["alerts"]
)

app.include_router(
    groups.router,
    prefix="/api/v1/groups",
    tags=["groups"]
)

# Root endpoints
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "AI Alert Monitoring System API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "alert-monitoring-system"
    }

@app.get("/info")
async def system_info():
    """System information endpoint"""
    return {
        "system": "Alert Monitoring System",
        "version": "1.0.0",
        "settings": {
            "ollama_host": settings.OLLAMA_HOST,
            "ollama_model": settings.OLLAMA_MODEL,
            "chromadb_collection": settings.CHROMADB_COLLECTION
        }
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
