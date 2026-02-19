"""
Vector database abstraction for RAG.
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
    source_id: Optional[int] = None
    chunk_index: Optional[int] = None


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
    """Abstract interface for vector database operations."""

    @abstractmethod
    async def upsert_chunks(
        self,
        chunks: List[VectorChunk],
        profile_id: int,
    ) -> None:
        """Insert or update chunks in the vector store."""
        pass

    @abstractmethod
    async def delete_profile_chunks(
        self,
        profile_id: int,
        source_type: Optional[SourceType] = None,
    ) -> None:
        """Delete all chunks for a profile."""
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
        """Search for similar chunks by embedding similarity."""
        pass

    @abstractmethod
    async def get_embedding_dimension(self) -> int:
        """Return the expected embedding dimension."""
        pass


class EmbeddingProvider(ABC):
    """Abstract interface for embedding generation."""

    @abstractmethod
    async def generate_embedding(self, text: str) -> np.ndarray:
        """Generate embedding vector for text."""
        pass

    @abstractmethod
    async def generate_embeddings_batch(
        self,
        texts: List[str],
    ) -> List[np.ndarray]:
        """Generate embeddings for multiple texts."""
        pass

    @abstractmethod
    def get_dimension(self) -> int:
        """Return the embedding dimension."""
        pass