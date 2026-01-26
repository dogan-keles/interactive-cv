"""
PgVector implementation for RAG vector storage.

Uses PostgreSQL with pgvector extension for vector similarity search.
"""

import logging
from typing import List, Optional
import numpy as np
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.data_access.vector_db.vector_store import (
    VectorStore,
    VectorChunk,
    RetrievedChunk,
    ChunkMetadata,
    SourceType,
    EmbeddingProvider,
)

logger = logging.getLogger(__name__)


class PgVectorStore(VectorStore):
    """
    PostgreSQL + pgvector implementation of VectorStore.
    
    Uses pgvector extension for efficient vector similarity search.
    """
    
    def __init__(
        self,
        db_session: Session,
        embedding_provider: EmbeddingProvider,
    ):
        """
        Initialize PgVectorStore.
        
        Args:
            db_session: SQLAlchemy database session
            embedding_provider: Embedding generation provider
        """
        self.db_session = db_session
        self.embedding_provider = embedding_provider
    
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
        try:
            for chunk in chunks:
                # Convert numpy array to list for pgvector
                embedding_list = chunk.embedding.tolist()
                
                # Insert into embeddings table
                query = text("""
                    INSERT INTO embeddings 
                    (profile_id, text, embedding, source_type, source_id, chunk_index, metadata)
                    VALUES 
                    (:profile_id, :text, CAST(:embedding AS vector), :source_type, :source_id, :chunk_index, CAST(:metadata AS jsonb))
                """)
                
                self.db_session.execute(
                    query,
                    {
                        "profile_id": profile_id,
                        "text": chunk.text,
                        "embedding": f"[{','.join(map(str, embedding_list))}]",
                        "source_type": chunk.metadata.source_type.value,
                        "source_id": chunk.metadata.source_id,
                        "chunk_index": chunk.metadata.chunk_index,
                        "metadata": "{}",  # Can add more metadata as JSON
                    }
                )
            
            self.db_session.commit()
            logger.info(f"Upserted {len(chunks)} chunks for profile {profile_id}")
        
        except Exception as e:
            self.db_session.rollback()
            logger.error(f"Error upserting chunks: {e}")
            raise
    
    async def delete_profile_chunks(
        self,
        profile_id: int,
        source_type: Optional[SourceType] = None,
    ) -> None:
        """
        Delete all chunks for a profile, optionally filtered by source_type.
        
        Args:
            profile_id: Profile to delete chunks for
            source_type: Optional filter by source type
        """
        try:
            if source_type:
                query = text("""
                    DELETE FROM embeddings 
                    WHERE profile_id = :profile_id 
                    AND source_type = :source_type
                """)
                self.db_session.execute(
                    query,
                    {"profile_id": profile_id, "source_type": source_type.value}
                )
            else:
                query = text("""
                    DELETE FROM embeddings 
                    WHERE profile_id = :profile_id
                """)
                self.db_session.execute(
                    query,
                    {"profile_id": profile_id}
                )
            
            self.db_session.commit()
            logger.info(f"Deleted chunks for profile {profile_id}, source_type={source_type}")
        
        except Exception as e:
            self.db_session.rollback()
            logger.error(f"Error deleting chunks: {e}")
            raise
    
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
        
        Uses cosine similarity via pgvector's <=> operator.
        
        Args:
            query_embedding: Query vector
            profile_id: Filter results to this profile
            top_k: Number of results to return
            source_type: Optional filter by source type
            min_score: Minimum similarity score threshold (0-1, where 1 is identical)
            
        Returns:
            List of retrieved chunks sorted by similarity (highest first)
        """
        try:
            # Convert numpy array to list
            embedding_list = query_embedding.tolist()
            embedding_str = f"[{','.join(map(str, embedding_list))}]"
            
            # Build query with optional source_type filter
            if source_type:
                query = text("""
                    SELECT 
                        text,
                        source_type,
                        source_id,
                        chunk_index,
                        profile_id,
                        1 - (embedding <=> :query_embedding::vector) AS similarity
                    FROM embeddings
                    WHERE profile_id = :profile_id
                    AND source_type = :source_type
                    AND 1 - (embedding <=> :query_embedding::vector) >= :min_score
                    ORDER BY embedding <=> :query_embedding::vector
                    LIMIT :top_k
                """)
                params = {
                    "query_embedding": embedding_str,
                    "profile_id": profile_id,
                    "source_type": source_type.value,
                    "min_score": min_score,
                    "top_k": top_k,
                }
            else:
                query = text("""
                    SELECT 
                        text,
                        source_type,
                        source_id,
                        chunk_index,
                        profile_id,
                        1 - (embedding <=> :query_embedding::vector) AS similarity
                    FROM embeddings
                    WHERE profile_id = :profile_id
                    AND 1 - (embedding <=> :query_embedding::vector) >= :min_score
                    ORDER BY embedding <=> :query_embedding::vector
                    LIMIT :top_k
                """)
                params = {
                    "query_embedding": embedding_str,
                    "profile_id": profile_id,
                    "min_score": min_score,
                    "top_k": top_k,
                }
            
            result = self.db_session.execute(query, params)
            rows = result.fetchall()
            
            # Convert to RetrievedChunk objects
            chunks = []
            for row in rows:
                metadata = ChunkMetadata(
                    profile_id=row.profile_id,
                    source_type=SourceType(row.source_type),
                    source_id=row.source_id,
                    chunk_index=row.chunk_index,
                )
                chunks.append(
                    RetrievedChunk(
                        text=row.text,
                        metadata=metadata,
                        similarity_score=float(row.similarity),
                    )
                )
            
            logger.info(f"Found {len(chunks)} similar chunks for profile {profile_id}")
            return chunks
        
        except Exception as e:
            logger.error(f"Error searching chunks: {e}")
            raise
    
    async def get_embedding_dimension(self) -> int:
        """Return the expected embedding dimension for this store."""
        return self.embedding_provider.get_dimension()