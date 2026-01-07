import os
import logging
from contextlib import asynccontextmanager
from dotenv import load_dotenv

# .env dosyasındaki değişkenleri yükle
load_dotenv()


from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Provider ve Ajanlar - İsmi GroqProvider (q ile) olarak güncelledik
from infrastructure.llm.provider import GroqProvider
from agents.profile_agent import ProfileAgent
from agents.github_agent import GitHubAgent
from agents.cv_agent import CVAgent
from agents.guardrail_agent import GuardrailAgent
from orchestrator.orchestrator import Orchestrator
from api.routes import chat

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global orkestratör nesnesi
_orchestrator: Orchestrator | None = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Uygulama başladığında ve kapandığında çalışacak mantık."""
    global _orchestrator

    logger.info("🚀 Initializing application (Using Groq AI - Free Tier)...")

    # 1. LLM Provider'ı Groq API anahtarı ile oluşturuyoruz
    # Not: os.getenv("GROQ_API_KEY") kullanıyoruz, .env dosyanı buna göre güncelle!
    llm_provider = GroqProvider(
        api_key=os.getenv("GROQ_API_KEY"),
        model=os.getenv("LLM_MODEL", "llama-3.3-70b-versatile"),
    )

    # 2. Ajanları oluşturuyoruz
    profile_agent = ProfileAgent(
        llm_provider=llm_provider,
        db_session=None
    )
    
    github_agent = GitHubAgent(
        llm_provider=llm_provider,
        db_session=None
    )
    
    cv_agent = CVAgent(
        llm_provider=llm_provider,
        db_session=None
    )
    
    guardrail_agent = GuardrailAgent(llm_provider)

    # 3. Orkestratörü kuruyoruz
    _orchestrator = Orchestrator(
        profile_agent=profile_agent,
        github_agent=github_agent,
        cv_agent=cv_agent,
        guardrail_agent=guardrail_agent,
    )

    logger.info("✅ Application initialized with Groq Provider")
    yield
    logger.info("🛑 Shutting down application...")

app = FastAPI(
    title="Interactive CV API",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_orchestrator() -> Orchestrator:
    """Dependency injection için orkestratörü döndürür."""
    if _orchestrator is None:
        raise RuntimeError("Orchestrator not initialized")
    return _orchestrator

# Router ayarları
chat.set_orchestrator_dependency(get_orchestrator)
app.include_router(chat.router)

@app.get("/health")
async def health():
    return {
        "status": "healthy", 
        "llm_provider": "groq",
        "mode": "mock_data_enabled"
    }