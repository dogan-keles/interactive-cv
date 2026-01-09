"""
FastAPI main application entry point.
Initializes LLM provider, database, agents, and orchestrator.
"""

import os
import logging
from contextlib import asynccontextmanager
from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Database
from backend.infrastructure.database import SessionLocal, check_connection

# LLM Provider
from backend.infrastructure.llm.provider import GroqProvider

# Agents
from backend.agents.profile_agent import ProfileAgent
from backend.agents.github_agent import GitHubAgent
from backend.agents.cv_agent import CVAgent
from backend.agents.guardrail_agent import GuardrailAgent

# Orchestrator
from backend.orchestrator.orchestrator import Orchestrator

# API Routes
from backend.api.routes import chat, profile  # ← CHANGED: Added profile

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global instances
_orchestrator: Orchestrator | None = None
_db_session = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan: startup and shutdown logic.
    
    Startup:
    - Check database connection
    - Create database session
    - Initialize LLM provider
    - Create agents with real database sessions
    - Initialize orchestrator
    
    Shutdown:
    - Close database session
    """
    global _orchestrator, _db_session

    logger.info("🚀 Initializing application...")

    # 1. Check database connection
    if check_connection():
        logger.info("✅ Database connected (Neon DB)")
        _db_session = SessionLocal()
    else:
        logger.warning("⚠️  Database connection failed - running without DB")
        _db_session = None

    # 2. Initialize LLM Provider (Groq)
    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key:
        logger.error("❌ GROQ_API_KEY not found in environment variables!")
        raise ValueError("GROQ_API_KEY is required")
    
    llm_provider = GroqProvider(
        api_key=groq_api_key,
        model=os.getenv("LLM_MODEL", "llama-3.3-70b-versatile"),
    )
    logger.info("✅ Groq LLM provider initialized")

    # 3. Create agents with database sessions
    profile_agent = ProfileAgent(
        llm_provider=llm_provider,
        db_session=_db_session,
    )
    
    github_agent = GitHubAgent(
        llm_provider=llm_provider,
        db_session=_db_session,
    )
    
    cv_agent = CVAgent(
        llm_provider=llm_provider,
        db_session=_db_session,
    )
    
    guardrail_agent = GuardrailAgent(llm_provider)
    
    logger.info("✅ Agents initialized")

    # 4. Create orchestrator
    _orchestrator = Orchestrator(
        profile_agent=profile_agent,
        github_agent=github_agent,
        cv_agent=cv_agent,
        guardrail_agent=guardrail_agent,
    )
    
    logger.info("✅ Orchestrator initialized")
    logger.info("🎉 Application startup complete!")
    
    yield
    
    # Shutdown: cleanup resources
    logger.info("🛑 Shutting down application...")
    if _db_session:
        _db_session.close()
        logger.info("✅ Database session closed")


# Create FastAPI app
app = FastAPI(
    title="Interactive CV API",
    description="AI-powered interactive CV with multi-agent architecture",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_orchestrator() -> Orchestrator:
    """
    Dependency injection: Get orchestrator instance.
    
    Returns:
        Orchestrator instance
        
    Raises:
        RuntimeError: If orchestrator not initialized
    """
    if _orchestrator is None:
        raise RuntimeError("Orchestrator not initialized")
    return _orchestrator


# Register routes
chat.set_orchestrator_dependency(get_orchestrator)
app.include_router(chat.router)
app.include_router(profile.router)  # ← ADDED: Profile router


@app.get("/")
def root():
    """Root endpoint - API status."""
    return {
        "message": "Interactive CV API is running 🚀",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    """
    Health check endpoint.
    
    Returns service status including:
    - Overall health status
    - LLM provider status
    - Database connection status
    """
    db_status = "connected" if check_connection() else "disconnected"
    
    return {
        "status": "healthy",
        "llm_provider": "groq",
        "database": db_status,
        "mode": "production" if _db_session else "no-database",
    }