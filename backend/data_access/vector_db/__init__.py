"""
Vector database module for RAG pipeline.

Exports:
- VectorStore: Abstract interface for vector storage
- EmbeddingProvider: Abstract interface for embeddings
- RAGIngestionPipeline: Ingestion pipeline
- RAGRetrievalPipeline: Retrieval pipeline
- SourceType: Enum for source types
"""

from .ingestion import ChunkingConfig, RAGIngestionPipeline
from .retrieval import RAGRetrievalPipeline
from .vector_store import (
    ChunkMetadata,
    EmbeddingProvider,
    RetrievedChunk,
    SourceType,
    VectorChunk,
    VectorStore,
)

__all__ = [
    "VectorStore",
    "EmbeddingProvider",
    "VectorChunk",
    "RetrievedChunk",
    "ChunkMetadata",
    "SourceType",
    "RAGIngestionPipeline",
    "RAGRetrievalPipeline",
    "ChunkingConfig",
]


