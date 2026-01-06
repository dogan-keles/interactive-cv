"""
Semantic search tools for agents.

Agents use these tools to retrieve context from the vector database.
Agents must NOT access the vector store directly.
"""

from typing import List, Optional

from data_access.vector_db.retrieval import RAGRetrievalPipeline
from data_access.vector_db.vector_store import RetrievedChunk, SourceType


async def semantic_search(
    query: str,
    profile_id: int,
    retrieval_pipeline: RAGRetrievalPipeline,
    top_k: int = 5,
    source_type: Optional[SourceType] = None,
) -> List[RetrievedChunk]:
    """
    Semantic search tool for agents.
    
    Retrieves relevant chunks from vector store based on query similarity.
    
    Args:
        query: User query text
        profile_id: Profile to search within
        retrieval_pipeline: RAG retrieval pipeline instance
        top_k: Number of results to return
        source_type: Optional filter by source type
        
    Returns:
        List of retrieved chunks with metadata and similarity scores
        
    Example usage in agent:
        chunks = await semantic_search(
            query="What is the candidate's experience with Python?",
            profile_id=1,
            retrieval_pipeline=retrieval_pipeline,
            top_k=3,
        )
    """
    results = await retrieval_pipeline.retrieve(
        query=query,
        profile_id=profile_id,
        top_k=top_k,
        source_type=source_type,
    )
    return results


async def semantic_search_with_context(
    query: str,
    profile_id: int,
    retrieval_pipeline: RAGRetrievalPipeline,
    top_k: int = 5,
    source_type: Optional[SourceType] = None,
    max_context_length: Optional[int] = 2000,
) -> str:
    """
    Semantic search tool that returns formatted context string.
    
    Convenience function for agents that need ready-to-use context
    for LLM prompts.
    
    Args:
        query: User query text
        profile_id: Profile to search within
        retrieval_pipeline: RAG retrieval pipeline instance
        top_k: Number of results to return
        source_type: Optional filter by source type
        max_context_length: Maximum character length for context
        
    Returns:
        Formatted context string ready for LLM prompt
    """
    chunks = await semantic_search(
        query=query,
        profile_id=profile_id,
        retrieval_pipeline=retrieval_pipeline,
        top_k=top_k,
        source_type=source_type,
    )
    
    context = await retrieval_pipeline.format_context(
        chunks=chunks,
        max_length=max_context_length,
    )
    
    return context




