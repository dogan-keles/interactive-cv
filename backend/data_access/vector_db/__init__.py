"""
Vector database module for RAG (Retrieval-Augmented Generation).

Provides vector storage, embedding generation, and semantic search capabilities.
"""

from .vector_store import (
    VectorStore,
    EmbeddingProvider,
    VectorChunk,
    RetrievedChunk,
    ChunkMetadata,
    SourceType,
)
from .ingestion import DocumentIngestion
from .retrieval import RAGRetrievalPipeline

__all__ = [
    "VectorStore",
    "EmbeddingProvider",
    "VectorChunk",
    "RetrievedChunk",
    "ChunkMetadata",
    "SourceType",
    "DocumentIngestion",
    "RAGRetrievalPipeline",
]