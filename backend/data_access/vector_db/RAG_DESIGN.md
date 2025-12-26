# RAG Pipeline Design

## High-Level Architecture

The RAG (Retrieval-Augmented Generation) pipeline is split into two main flows:

### 1. Ingestion Flow
```
PostgreSQL (structured) + Documents (unstructured)
    ↓
Text Extraction & Formatting
    ↓
Text Chunking (configurable size/overlap)
    ↓
Embedding Generation (via EmbeddingProvider)
    ↓
Vector Store (with metadata: profile_id, source_type, source_id)
```

### 2. Retrieval Flow
```
User Query
    ↓
Query Embedding (via EmbeddingProvider)
    ↓
Vector Similarity Search (filtered by profile_id)
    ↓
Top-K Chunks with Metadata
    ↓
Formatted Context String
    ↓
Agent/LLM (via tools)
```

## Component Responsibilities

### `vector_store.py`
- **VectorStore (ABC)**: Abstract interface for vector database operations
  - `upsert_chunks()`: Store chunks with embeddings
  - `delete_profile_chunks()`: Delete chunks for re-ingestion
  - `search()`: Vector similarity search with profile filtering
- **EmbeddingProvider (ABC)**: Abstract interface for embedding generation
  - Decouples embedding logic (OpenAI, Sentence Transformers, etc.)
- **Data Classes**: `VectorChunk`, `RetrievedChunk`, `ChunkMetadata`, `SourceType`

### `ingestion.py`
- **RAGIngestionPipeline**: Main ingestion orchestrator
  - `ingest_profile_data()`: Converts PostgreSQL models to chunks
  - `ingest_document()`: Converts unstructured documents to chunks
  - `reingest_profile()`: Idempotent re-ingestion (delete + ingest)
- **chunk_text()**: Text chunking utility (configurable size/overlap)
- **ChunkingConfig**: Configuration for chunking strategy

### `retrieval.py`
- **RAGRetrievalPipeline**: Main retrieval orchestrator
  - `retrieve()`: Query → embedding → search → chunks
  - `format_context()`: Formats chunks into LLM-ready context string
- **No LLM calls**: Pure retrieval logic only

### `tools/semantic_search_tools.py`
- **semantic_search()**: Tool function for agents
  - Returns raw chunks with metadata
- **semantic_search_with_context()**: Convenience tool
  - Returns formatted context string ready for LLM
- **Agent Interface**: Agents call these tools, never access vector store directly

## Profile-Centric Design

Every operation is profile-aware:
- All chunks store `profile_id` in metadata
- All searches filter by `profile_id`
- Re-ingestion deletes existing chunks per profile
- Supports multiple profiles in same vector store

## Extensibility

### Adding New Vector DB Backend
1. Implement `VectorStore` interface
2. Create concrete class (e.g., `PgVectorStore`, `FAISSVectorStore`)
3. Update initialization/config

### Adding New Embedding Provider
1. Implement `EmbeddingProvider` interface
2. Create concrete class (e.g., `OpenAIEmbeddingProvider`, `SentenceTransformerProvider`)
3. Pass to pipelines via dependency injection

### Adding New Data Sources
1. Add new `SourceType` enum value
2. Extend `ingest_profile_data()` or add new ingestion method
3. Format data as text → chunk → embed → store

## Integration Points

### With Agents
- Agents import `semantic_search_tools`
- Agents call `semantic_search()` or `semantic_search_with_context()`
- Agents receive context and append to LLM prompts
- **Agents never access vector store directly**

### With Orchestrator
- Orchestrator decides which agent handles request
- Orchestrator may decide if RAG context is needed
- Orchestrator does NOT perform retrieval itself

### With Knowledge Base
- Ingestion reads from PostgreSQL models
- Retrieval is independent (no direct DB access)
- Re-ingestion can be triggered on data updates

## Data Flow Example

### Ingestion
```python
# Initialize
vector_store = ConcreteVectorStore(embedding_provider)
ingestion = RAGIngestionPipeline(vector_store, embedding_provider)

# Ingest structured data
await ingestion.ingest_profile_data(
    profile_id=1,
    profile_summary="Experienced Python developer...",
    experiences=[{...}],
    projects=[{...}],
)

# Ingest document
await ingestion.ingest_document(
    profile_id=1,
    document_text="Full CV text...",
    source_type=SourceType.CV,
)
```

### Retrieval (Agent Usage)
```python
# Initialize
retrieval = RAGRetrievalPipeline(vector_store, embedding_provider)

# Agent calls tool
chunks = await semantic_search(
    query="What is the candidate's Python experience?",
    profile_id=1,
    retrieval_pipeline=retrieval,
    top_k=5,
)

# Format for LLM
context = await retrieval.format_context(chunks, max_length=2000)
# Append context to LLM prompt
```

## Key Design Decisions

1. **Abstraction Layers**: Vector store and embedding providers are abstracted
2. **Profile Isolation**: All operations are profile-scoped
3. **Idempotent Ingestion**: Re-ingestion deletes old chunks first
4. **Agent Tools**: Agents use tools, not direct DB access
5. **No LLM in Retrieval**: Retrieval is pure search, LLM only in agents
6. **Metadata Rich**: Chunks store source_type, source_id for traceability
7. **Configurable Chunking**: Chunk size/overlap can be tuned per use case


