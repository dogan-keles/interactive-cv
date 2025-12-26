"""
Vector database abstraction for RAG (Retrieval-Augmented Generation).

Provides an abstract interface for vector storage and retrieval,
supporting multiple vector DB backends (pgvector, FAISS, Chroma, etc.).
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional

import numpy as np


class SourceType(str, Enum):
    """Source types for vector store metadata."""
    CV = "cv"
    GITHUB = "github"
    EXPERIENCE = "experience"
    PROJECT = "project"
    SUMMARY = "summary"
    SKILL = "skill"


@dataclass
class ChunkMetadata:
    """Metadata associated with a vector chunk."""
    profile_id: int
    source_type: SourceType
    source_id: Optional[int] = None  # e.g., project_id, experience_id
    chunk_index: Optional[int] = None  # Position within source document


@dataclass
class VectorChunk:
    """A chunk of text with its embedding and metadata."""
    text: str
    embedding: np.ndarray
    metadata: ChunkMetadata


@dataclass
class RetrievedChunk:
    """A retrieved chunk with similarity score."""
    text: str
    metadata: ChunkMetadata
    similarity_score: float


class VectorStore(ABC):
    """
    Abstract interface for vector database operations.
    
    Concrete implementations can use pgvector, FAISS, Chroma, etc.
    All methods must be profile-aware (profile_id filtering).
    """

    @abstractmethod
    async def upsert_chunks(
        self,
        chunks: List[VectorChunk],
        profile_id: int,
    ) -> None:
        """
        Insert or update chunks in the vector store.
        
        Args:
            chunks: List of chunks with embeddings and metadata
            profile_id: Profile ID for filtering/namespace
        """
        pass

    @abstractmethod
    async def delete_profile_chunks(
        self,
        profile_id: int,
        source_type: Optional[SourceType] = None,
    ) -> None:
        """
        Delete all chunks for a profile, optionally filtered by source_type.
        
        Useful for re-ingestion (idempotent operations).
        
        Args:
            profile_id: Profile to delete chunks for
            source_type: Optional filter by source type
        """
        pass

    @abstractmethod
    async def search(
        self,
        query_embedding: np.ndarray,
        profile_id: int,
        top_k: int = 5,
        source_type: Optional[SourceType] = None,
        min_score: float = 0.0,
    ) -> List[RetrievedChunk]:
        """
        Search for similar chunks by embedding similarity.
        
        Args:
            query_embedding: Query vector
            profile_id: Filter results to this profile
            top_k: Number of results to return
            source_type: Optional filter by source type
            min_score: Minimum similarity score threshold
            
        Returns:
            List of retrieved chunks sorted by similarity (highest first)
        """
        pass

    @abstractmethod
    async def get_embedding_dimension(self) -> int:
        """Return the expected embedding dimension for this store."""
        pass


class EmbeddingProvider(ABC):
    """
    Abstract interface for embedding generation.
    
    Decouples embedding logic from vector store implementation.
    """

    @abstractmethod
    async def generate_embedding(self, text: str) -> np.ndarray:
        """Generate embedding vector for a text string."""
        pass

    @abstractmethod
    async def generate_embeddings_batch(
        self,
        texts: List[str],
    ) -> List[np.ndarray]:
        """Generate embeddings for multiple texts (may be batched)."""
        pass

    @abstractmethod
    def get_dimension(self) -> int:
        """Return the embedding dimension."""
        pass


# Placeholder for concrete implementation
# Example: PgVectorStore, FAISSVectorStore, ChromaVectorStore
class ConcreteVectorStore(VectorStore):
    """
    Placeholder for concrete vector store implementation.
    
    Replace with actual implementation (pgvector, FAISS, Chroma, etc.).
    """
    
    def __init__(
        self,
        embedding_provider: EmbeddingProvider,
        connection_string: Optional[str] = None,
    ):
        self.embedding_provider = embedding_provider
        # Initialize actual vector DB connection here
        
    async def upsert_chunks(
        self,
        chunks: List[VectorChunk],
        profile_id: int,
    ) -> None:
        # Implementation: Store chunks with metadata
        raise NotImplementedError("Concrete implementation required")
    
    async def delete_profile_chunks(
        self,
        profile_id: int,
        source_type: Optional[SourceType] = None,
    ) -> None:
        # Implementation: Delete chunks matching profile_id and optional source_type
        raise NotImplementedError("Concrete implementation required")
    
    async def search(
        self,
        query_embedding: np.ndarray,
        profile_id: int,
        top_k: int = 5,
        source_type: Optional[SourceType] = None,
        min_score: float = 0.0,
    ) -> List[RetrievedChunk]:
        # Implementation: Vector similarity search with filters
        raise NotImplementedError("Concrete implementation required")
    
    async def get_embedding_dimension(self) -> int:
        return self.embedding_provider.get_dimension()


