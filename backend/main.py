"""
FastAPI main application entry point.
Initializes LLM provider, database, agents, and orchestrator.
"""

import os
import logging
from contextlib import asynccontextmanager
from dotenv import load_dotenv

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Load env vars
load_dotenv()

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

# Middleware
from backend.middleware.error_logger import ErrorLoggingMiddleware

# Routes
from backend.api.routes import chat, profile, cv


# -------------------------------------------------------------------
# Logging Configuration
# -------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(name)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


# -------------------------------------------------------------------
# Globals
# -------------------------------------------------------------------
_orchestrator: Orchestrator | None = None
_db_session = None


# -------------------------------------------------------------------
# Lifespan
# -------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    global _orchestrator, _db_session

    logger.info("🚀 Initializing application...")

    # 1. Database
    if check_connection():
        logger.info("✅ Database connected (Neon DB)")
        _db_session = SessionLocal()
    else:
        logger.warning("⚠️ Database connection failed - running without DB")
        _db_session = None

    # 2. LLM Provider
    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key:
        raise RuntimeError("❌ GROQ_API_KEY is required")

    llm_provider = GroqProvider(
        api_key=groq_api_key,
        model=os.getenv("LLM_MODEL", "llama-3.3-70b-versatile"),
    )
    logger.info("✅ Groq LLM provider initialized")

    # 3. RAG (optional)
    retrieval_pipeline = None
    if _db_session:
        try:
            from backend.data_access.vector_db.pgvector_store import PgVectorStore
            from backend.data_access.vector_db.sklearn_embedding import SklearnTfidfEmbedding
            from backend.data_access.vector_db.retrieval import RAGRetrievalPipeline
            
            logger.info("📥 Initializing RAG components...")
            
            # Initialize embedding provider (lightweight TF-IDF)
            embedding_provider = SklearnTfidfEmbedding(max_features=384)
            logger.info(f"✅ Embedding provider initialized (dimension: {embedding_provider.get_dimension()})")

            vector_store = PgVectorStore(
                db_session=_db_session,
                embedding_provider=embedding_provider,
            )

            retrieval_pipeline = RAGRetrievalPipeline(
                vector_store=vector_store,
                embedding_provider=embedding_provider,
            )

            logger.info("✅ RAG retrieval pipeline initialized")

        except Exception as e:
            logger.warning(f"⚠️ RAG initialization failed: {e}")
            retrieval_pipeline = None

    # 4. Agents
    profile_agent = ProfileAgent(
        llm_provider=llm_provider,
        db_session=_db_session,
        retrieval_pipeline=retrieval_pipeline,
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

    # 5. Orchestrator
    _orchestrator = Orchestrator(
        profile_agent=profile_agent,
        github_agent=github_agent,
        cv_agent=cv_agent,
        guardrail_agent=guardrail_agent,
    )

    logger.info("🎉 Application startup complete")

    yield

    # Shutdown
    logger.info("🛑 Shutting down application...")
    if _db_session:
        _db_session.close()
        logger.info("✅ Database session closed")


# -------------------------------------------------------------------
# FastAPI App
# -------------------------------------------------------------------
app = FastAPI(
    title="Interactive CV API",
    description="AI-powered interactive CV with multi-agent architecture",
    version="1.0.0",
    lifespan=lifespan,
)


# -------------------------------------------------------------------
# CORS Configuration - Environment-based
# -------------------------------------------------------------------
environment = os.getenv("ENVIRONMENT", "development")

allowed_origins = []

if environment == "production":
    # Production: Only allow production domain
    production_url = os.getenv("FRONTEND_URL")
    if production_url:
        allowed_origins.append(production_url)
    logger.info(f"🔐 Production mode - CORS allowed origins: {allowed_origins}")
else:
    # Development: Allow localhost ports
    local_urls = os.getenv("LOCAL_FRONTEND_URLS", "http://localhost:3000,http://localhost:5173")
    allowed_origins = local_urls.split(",")
    logger.info(f"🔐 Development mode - CORS allowed origins: {allowed_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Error Logging Middleware
app.add_middleware(ErrorLoggingMiddleware)


# -------------------------------------------------------------------
# Dependencies
# -------------------------------------------------------------------
def get_orchestrator() -> Orchestrator:
    if _orchestrator is None:
        raise RuntimeError("Orchestrator not initialized")
    return _orchestrator


# -------------------------------------------------------------------
# Routes
# -------------------------------------------------------------------
chat.set_orchestrator_dependency(get_orchestrator)
app.include_router(chat.router, prefix="/api")
app.include_router(profile.router)
app.include_router(cv.router)


@app.get("/")
def root():
    return {
        "message": "Interactive CV API is running 🚀",
        "version": "1.0.0",
        "docs": "/docs",
        "environment": environment,
    }


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "environment": environment,
        "llm_provider": "groq",
        "database": "connected" if check_connection() else "disconnected",
        "mode": "production" if _db_session else "no-database",
    }


@app.post("/admin/ingest-vectors")
async def ingest_vectors_endpoint():
    """
    Admin endpoint to trigger vector ingestion in production.
    Run this once after deployment to populate embeddings.
    """
    try:
        from backend.data_access.vector_db.pgvector_store import PgVectorStore
        from backend.data_access.vector_db.sklearn_embedding import SklearnTfidfEmbedding
        from backend.data_access.vector_db.ingestion import DocumentIngestion
        
        if not _db_session:
            return {
                "success": False,
                "error": "Database not connected"
            }
        
        logger.info("Starting vector ingestion via admin endpoint...")
        
        # Initialize embedding provider (lightweight TF-IDF)
        embedding_provider = SklearnTfidfEmbedding(max_features=384)
        logger.info("Embedding provider initialized")
        
        # Initialize vector store
        vector_store = PgVectorStore(
            db_session=_db_session,
            embedding_provider=embedding_provider,
        )
        logger.info("Vector store initialized")
        
        # Initialize ingestion pipeline
        ingestion = DocumentIngestion(
            vector_store=vector_store,
            embedding_provider=embedding_provider,
        )
        logger.info("Ingestion pipeline initialized")
        
        # Ingest profile
        num_chunks = await ingestion.ingest_profile(
            profile_id=1,
            db_session=_db_session,
        )
        
        logger.info(f"Ingestion complete: {num_chunks} chunks created")
        
        return {
            "success": True,
            "chunks_created": num_chunks,
            "message": f"Successfully created {num_chunks} vector embeddings",
            "profile_id": 1
        }
    
    except Exception as e:
        logger.error(f"Ingestion failed: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }