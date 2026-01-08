# Implementation Roadmap - Interactive CV Backend

## 📊 Mevcut Durum Analizi

### ✅ Tamamlanmış Katmanlar

#### 1. **Orchestrator Layer** ✅
- ✅ `orchestrator.py` - Routing logic implement edilmiş
- ✅ `language_detector.py` - Dil algılama çalışıyor
- ✅ `intent_detector.py` - Intent detection çalışıyor
- ✅ `types.py` - RequestContext, Intent, Language enum'ları var

#### 2. **RAG Pipeline (Vector DB)** ✅
- ✅ `vector_store.py` - Abstract interfaces tanımlı
- ✅ `ingestion.py` - Refactor edilmiş, temiz kod
- ✅ `retrieval.py` - Retrieval pipeline implement edilmiş
- ✅ `semantic_search_tools.py` - Agent'lar için tool'lar hazır

#### 3. **Knowledge Base** ✅
- ✅ `postgres.py` - SQLAlchemy modelleri tanımlı (Profile, Skill, Experience, Project)

#### 4. **Agent Prompts** ✅
- ✅ `prompts.py` - Tüm agent prompt'ları tanımlı
- ✅ `AGENT_PROMPTS.md` - Dokümantasyon hazır

---

### ❌ Eksik Implementasyonlar

#### 1. **Agent Implementations** ❌ (KRİTİK)
- ❌ `profile_agent.py` - BOŞ
- ❌ `github_agent.py` - BOŞ
- ❌ `cv_agent.py` - BOŞ
- ❌ `guardrail_agent.py` - BOŞ

**Etki**: Sistem çalışmaz, orchestrator agent'ları bekliyor.

---

#### 2. **Tool Implementations** ❌ (KRİTİK)
- ❌ `profile_tools.py` - BOŞ (SQL queries için)
- ❌ `github_tools.py` - BOŞ (GitHub API için)
- ❌ `cv_tools.py` - BOŞ (File storage için)
- ✅ `semantic_search_tools.py` - VAR ✅

**Etki**: Agent'lar veri çekemez, tool'lar olmadan çalışamaz.

---

#### 3. **LLM Provider** ❌ (KRİTİK)
- ❌ `infrastructure/llm/provider.py` - BOŞ
- ❌ Concrete implementation yok (OpenAI, Anthropic, vs.)

**Etki**: Agent'lar LLM çağrısı yapamaz, response üretemez.

---

#### 4. **Vector Store Concrete Implementation** ❌ (ÖNEMLİ)
- ❌ `vector_store.py` içinde sadece abstract class var
- ❌ Concrete implementation yok (pgvector, FAISS, Chroma, vs.)

**Etki**: RAG pipeline çalışmaz, vector search yapılamaz.

---

#### 5. **Embedding Provider Concrete Implementation** ❌ (ÖNEMLİ)
- ❌ `vector_store.py` içinde sadece abstract class var
- ❌ Concrete implementation yok (OpenAI, Sentence Transformers, vs.)

**Etki**: Embedding üretilemez, vector store'a veri yazılamaz.

---

#### 6. **API Layer** ❌ (ÖNEMLİ)
- ❌ `api/routes/chat.py` - BOŞ
- ❌ `api/routes/download.py` - Kontrol edilmeli
- ❌ `api/schemas/chat.py` - Kontrol edilmeli
- ❌ `main.py` - Kontrol edilmeli

**Etki**: HTTP endpoint'ler yok, sistem dışarıdan erişilemez.

---

#### 7. **File Storage** ❓ (KONTROL EDİLMELİ)
- ❓ `data_access/file_storage/storage.py` - Kontrol edilmeli

**Etki**: CV dosyaları saklanamaz.

---

#### 8. **Configuration & Dependencies** ❌ (ÖNEMLİ)
- ❌ `requirements.txt` veya `pyproject.toml` yok
- ❌ `infrastructure/config.py` - Kontrol edilmeli
- ❌ Environment variables yönetimi yok

**Etki**: Dependency management yok, config yönetimi eksik.

---

## 🎯 Sonraki Adımlar (Öncelik Sırasına Göre)

### PHASE 1: Core Infrastructure (KRİTİK - Sistem Çalışması İçin)

#### 1.1 LLM Provider Implementation
**Öncelik**: 🔴 EN YÜKSEK
**Süre**: 2-3 saat

```python
# infrastructure/llm/provider.py
class LLMProvider(ABC):
    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> str:
        pass

class OpenAIProvider(LLMProvider):
    # OpenAI API implementation
    pass

class AnthropicProvider(LLMProvider):
    # Claude API implementation
    pass
```

**Gereksinimler**:
- OpenAI SDK veya Anthropic SDK
- API key management
- Error handling
- Rate limiting

---

#### 1.2 Tool Implementations
**Öncelik**: 🔴 EN YÜKSEK
**Süre**: 4-5 saat

**1.2.1 Profile Tools** (SQL queries)
```python
# tools/profile_tools.py
async def get_profile_skills(profile_id: int) -> List[dict]:
    # SQLAlchemy query
    pass

async def get_profile_experiences(profile_id: int) -> List[dict]:
    pass

async def get_profile_projects(profile_id: int) -> List[dict]:
    pass

async def get_profile_summary(profile_id: int) -> Optional[str]:
    pass
```

**1.2.2 GitHub Tools** (GitHub API veya DB)
```python
# tools/github_tools.py
async def get_github_repositories(profile_id: int) -> List[dict]:
    # GitHub API veya DB query
    pass

async def get_repository_details(repo_name: str, profile_id: int) -> dict:
    pass
```

**1.2.3 CV Tools** (File storage)
```python
# tools/cv_tools.py
async def generate_cv(profile_id: int, format: str) -> str:
    # Generate CV from profile data
    pass

async def get_cv_download_link(profile_id: int, format: str) -> str:
    # Return file storage link
    pass
```

**Gereksinimler**:
- SQLAlchemy session management
- GitHub API client (opsiyonel)
- File storage integration

---

#### 1.3 Agent Implementations
**Öncelik**: 🔴 EN YÜKSEK
**Süre**: 6-8 saat

**1.3.1 ProfileAgent**
```python
# agents/profile_agent.py
class ProfileAgent:
    def __init__(self, llm_provider, retrieval_pipeline, db_session):
        self.llm = llm_provider
        self.retrieval = retrieval_pipeline
        self.db = db_session
    
    async def process(self, context: RequestContext) -> str:
        # 1. Build prompt from prompts.py
        # 2. Use profile_tools or semantic_search_tools
        # 3. Call LLM with prompt + context
        # 4. Return response in context.language
        pass
```

**1.3.2 GitHubAgent**
```python
# agents/github_agent.py
class GitHubAgent:
    # Similar structure, uses github_tools
    pass
```

**1.3.3 CVAgent**
```python
# agents/cv_agent.py
class CVAgent:
    # Uses cv_tools and profile_tools
    pass
```

**1.3.4 GuardrailAgent**
```python
# agents/guardrail_agent.py
class GuardrailAgent:
    async def check_response(self, response: str, context: RequestContext) -> str:
        # Validate response safety
        pass
    
    async def handle_out_of_scope(self, context: RequestContext) -> str:
        # Use guardrail prompt
        pass
```

**Gereksinimler**:
- LLM provider (Phase 1.1)
- Tools (Phase 1.2)
- Prompt templates (✅ VAR)

---

### PHASE 2: Vector DB & Embeddings (ÖNEMLİ - RAG İçin)

#### 2.1 Embedding Provider Implementation
**Öncelik**: 🟡 YÜKSEK
**Süre**: 2-3 saat

```python
# infrastructure/embeddings/provider.py (yeni dosya)
class OpenAIEmbeddingProvider(EmbeddingProvider):
    async def generate_embedding(self, text: str) -> np.ndarray:
        # OpenAI embeddings API
        pass

class SentenceTransformerProvider(EmbeddingProvider):
    # Local model, no API needed
    pass
```

**Gereksinimler**:
- OpenAI embeddings API veya sentence-transformers library

---

#### 2.2 Vector Store Implementation
**Öncelik**: 🟡 YÜKSEK
**Süre**: 4-6 saat

**Seçenek 1: pgvector (PostgreSQL extension)**
```python
# data_access/vector_db/pgvector_store.py
class PgVectorStore(VectorStore):
    # PostgreSQL + pgvector implementation
    pass
```

**Seçenek 2: FAISS (Local)**
```python
# data_access/vector_db/faiss_store.py
class FAISSVectorStore(VectorStore):
    # FAISS in-memory implementation
    pass
```

**Seçenek 3: Chroma (Embedded)**
```python
# data_access/vector_db/chroma_store.py
class ChromaVectorStore(VectorStore):
    # ChromaDB implementation
    pass
```

**Öneri**: pgvector (PostgreSQL zaten var, extension eklemek kolay)

**Gereksinimler**:
- Vector DB library (pgvector, FAISS, Chroma)
- Database connection management

---

### PHASE 3: API Layer (ÖNEMLİ - HTTP Endpoints)

#### 3.1 API Routes
**Öncelik**: 🟡 YÜKSEK
**Süre**: 3-4 saat

```python
# api/routes/chat.py
@router.post("/chat")
async def chat(request: ChatRequest):
    # 1. Get orchestrator from dependency injection
    # 2. Call orchestrator.process_request()
    # 3. Return response
    pass

# api/routes/download.py
@router.get("/cv/{profile_id}")
async def download_cv(profile_id: int, format: str):
    # CV download endpoint
    pass
```

**3.2 API Schemas**
```python
# api/schemas/chat.py
class ChatRequest(BaseModel):
    query: str
    profile_id: int

class ChatResponse(BaseModel):
    response: str
    language: str
```

**3.3 Main Application**
```python
# main.py
app = FastAPI()

# Dependency injection setup
# - LLM provider
# - Vector store
# - Embedding provider
# - Agents
# - Orchestrator

app.include_router(chat_router)
app.include_router(download_router)
```

**Gereksinimler**:
- FastAPI
- Dependency injection (FastAPI Depends)
- Error handling middleware

---

### PHASE 4: Configuration & Setup (ÖNEMLİ)

#### 4.1 Configuration Management
**Öncelik**: 🟡 YÜKSEK
**Süre**: 2 saat

```python
# infrastructure/config.py
class Settings(BaseSettings):
    # Database
    database_url: str
    
    # LLM
    openai_api_key: str
    llm_model: str = "gpt-4"
    
    # Vector DB
    vector_db_type: str = "pgvector"
    
    # Embeddings
    embedding_provider: str = "openai"
    embedding_model: str = "text-embedding-3-small"
    
    class Config:
        env_file = ".env"
```

**4.2 Dependencies**
```txt
# requirements.txt
fastapi>=0.104.0
uvicorn>=0.24.0
sqlalchemy>=2.0.0
psycopg2-binary>=2.9.0
pgvector>=0.2.0
openai>=1.0.0
numpy>=1.24.0
python-dotenv>=1.0.0
pydantic>=2.0.0
pydantic-settings>=2.0.0
```

**4.3 Environment Variables**
```env
# .env.example
DATABASE_URL=postgresql://user:pass@localhost/dbname
OPENAI_API_KEY=sk-...
LLM_MODEL=gpt-4
VECTOR_DB_TYPE=pgvector
EMBEDDING_PROVIDER=openai
EMBEDDING_MODEL=text-embedding-3-small
```

---

### PHASE 5: Integration & Testing (ÖNEMLİ)

#### 5.1 Dependency Injection Setup
**Öncelik**: 🟡 ORTA
**Süre**: 3-4 saat

```python
# main.py veya infrastructure/dependencies.py
def get_llm_provider() -> LLMProvider:
    # Initialize based on config
    pass

def get_vector_store() -> VectorStore:
    # Initialize based on config
    pass

def get_orchestrator() -> Orchestrator:
    # Initialize all agents with dependencies
    pass
```

#### 5.2 Integration Testing
**Öncelik**: 🟡 ORTA
**Süre**: 4-6 saat

- End-to-end test scenarios
- Agent behavior tests
- RAG pipeline tests
- Error handling tests

---

## 📋 Implementation Checklist

### Phase 1 (KRİTİK - Sistem Çalışması)
- [ ] LLM Provider implementation
- [ ] Profile Tools implementation
- [ ] GitHub Tools implementation
- [ ] CV Tools implementation
- [ ] ProfileAgent implementation
- [ ] GitHubAgent implementation
- [ ] CVAgent implementation
- [ ] GuardrailAgent implementation

### Phase 2 (ÖNEMLİ - RAG)
- [ ] Embedding Provider implementation
- [ ] Vector Store concrete implementation
- [ ] RAG ingestion setup (test data)

### Phase 3 (ÖNEMLİ - API)
- [ ] API routes (chat, download)
- [ ] API schemas
- [ ] Main application setup
- [ ] Dependency injection

### Phase 4 (ÖNEMLİ - Config)
- [ ] Configuration management
- [ ] requirements.txt
- [ ] .env.example
- [ ] Database setup scripts

### Phase 5 (TESTING)
- [ ] Integration tests
- [ ] End-to-end tests
- [ ] Error handling tests

---

## 🚀 Hızlı Başlangıç Önerisi

**En hızlı çalışır hale getirmek için:**

1. **LLM Provider** (OpenAI) - 2 saat
2. **Profile Tools** (SQL queries) - 2 saat
3. **ProfileAgent** (basit implementasyon) - 2 saat
4. **GuardrailAgent** (basit implementasyon) - 1 saat
5. **API Route** (chat endpoint) - 1 saat
6. **Main.py setup** - 1 saat

**Toplam: ~9 saat** - Basit bir chat endpoint çalışır hale gelir.

---

## 📝 Notlar

- **Vector DB**: İlk aşamada opsiyonel, agent'lar SQL'den çalışabilir
- **GitHub Tools**: GitHub API yerine DB'den de çalışabilir (daha hızlı)
- **CV Generation**: İlk aşamada basit text format, sonra PDF
- **Testing**: Her phase'den sonra test et, büyük refactor'lardan kaçın

---

## 🔄 İteratif Yaklaşım

1. **MVP**: ProfileAgent + SQL tools + LLM (çalışır sistem)
2. **RAG Ekle**: Vector DB + embeddings (daha iyi responses)
3. **Diğer Agent'lar**: GitHubAgent, CVAgent
4. **Polish**: Error handling, logging, monitoring






