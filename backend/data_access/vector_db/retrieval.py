"""
RAG retrieval pipeline.
"""

from typing import List, Optional

from .vector_store import EmbeddingProvider, RetrievedChunk, SourceType, VectorStore


class RAGRetrievalPipeline:
    """Retrieval pipeline for semantic search over vector store."""
    
    def __init__(
        self,
        vector_store: VectorStore,
        embedding_provider: EmbeddingProvider,
    ):
        self.vector_store = vector_store
        self.embedding_provider = embedding_provider
    
    async def retrieve(
        self,
        query: str,
        profile_id: int,
        top_k: int = 5,
        source_type: Optional[SourceType] = None,
        min_score: float = 0.0,
    ) -> List[RetrievedChunk]:
        """Retrieve relevant chunks for a query."""
        query_embedding = await self.embedding_provider.generate_embedding(query)
        
        results = await self.vector_store.search(
            query_embedding=query_embedding,
            profile_id=profile_id,
            top_k=top_k,
            source_type=source_type,
            min_score=min_score,
        )
        
        return results
    
    async def format_context(
        self,
        chunks: List[RetrievedChunk],
        max_length: Optional[int] = None,
    ) -> str:
        """Format retrieved chunks into LLM context string."""
        context_parts = []
        current_length = 0
        
        for chunk in chunks:
            chunk_text = f"[{chunk.metadata.source_type.value}] {chunk.text}"
            
            if max_length:
                if current_length + len(chunk_text) > max_length:
                    break
                current_length += len(chunk_text)
            
            context_parts.append(chunk_text)
        
        return "\n\n".join(context_parts)