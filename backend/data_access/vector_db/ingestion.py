"""
RAG ingestion pipeline.

Converts structured and unstructured data into chunked, embedded vectors
for storage in the vector database.
"""

from typing import List, Optional

from .vector_store import (
    ChunkMetadata,
    EmbeddingProvider,
    SourceType,
    VectorChunk,
    VectorStore,
)


# ============================================================================
# Chunking Configuration and Utilities
# ============================================================================

class ChunkingConfig:
    """Configuration for text chunking strategy."""
    
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap


def chunk_text(text: str, config: ChunkingConfig) -> List[str]:
    """Split text into overlapping chunks."""
    if not text or len(text) <= config.chunk_size:
        return [text] if text else []
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + config.chunk_size
        chunks.append(text[start:end])
        
        if end >= len(text):
            break
            
        start = end - config.chunk_overlap
    
    return chunks


# ============================================================================
# Data Formatters
# ============================================================================

def _format_dict(data: dict, fields: dict) -> str:
    """
    Generic formatter for dict data.
    
    Args:
        data: Source dictionary
        fields: Mapping of {label: key} for formatting
    
    Returns:
        Formatted string
    """
    parts = []
    for label, key in fields.items():
        value = data.get(key)
        if value:
            if isinstance(value, list):
                value = ', '.join(str(v) for v in value)
            parts.append(f"{label}: {value}")
    return "\n".join(parts)


def _format_experience(exp: dict) -> str:
    """Format experience dict into searchable text."""
    return _format_dict(exp, {
        "Role": "role",
        "Company": "company",
        "Description": "description"
    })


def _format_project(project: dict) -> str:
    """Format project dict into searchable text."""
    return _format_dict(project, {
        "Project": "title",
        "Description": "description",
        "Technologies": "tech_stack"
    })


def _format_skills(skills: List[dict]) -> str:
    """Format skills list into searchable text."""
    return "\n".join(
        f"{s.get('name', '')} ({s.get('category', '')}) - {s.get('proficiency_level', '')}"
        for s in skills
    )


# ============================================================================
# RAG Ingestion Pipeline
# ============================================================================

class RAGIngestionPipeline:
    """
    Ingestion pipeline for converting data sources into vector chunks.
    
    Handles both structured (PostgreSQL) and unstructured (documents) data.
    """
    
    def __init__(
        self,
        vector_store: VectorStore,
        embedding_provider: EmbeddingProvider,
        chunking_config: Optional[ChunkingConfig] = None,
    ):
        self.vector_store = vector_store
        self.embedding_provider = embedding_provider
        self.chunking_config = chunking_config or ChunkingConfig()
    
    async def _create_chunks(
        self,
        text: str,
        profile_id: int,
        source_type: SourceType,
        source_id: Optional[int] = None,
        use_batch: bool = True,
    ) -> List[VectorChunk]:
        """Create vector chunks from text with embeddings."""
        text_chunks = chunk_text(text, self.chunking_config)
        if not text_chunks:
            return []
        
        # Generate embeddings (batch or individual)
        if use_batch and len(text_chunks) > 1:
            embeddings = await self.embedding_provider.generate_embeddings_batch(text_chunks)
        else:
            embeddings = [
                await self.embedding_provider.generate_embedding(chunk)
                for chunk in text_chunks
            ]
        
        # Create vector chunks with metadata
        return [
            VectorChunk(
                text=chunk_text,
                embedding=embedding,
                metadata=ChunkMetadata(
                    profile_id=profile_id,
                    source_type=source_type,
                    source_id=source_id,
                    chunk_index=idx,
                )
            )
            for idx, (chunk_text, embedding) in enumerate(zip(text_chunks, embeddings))
        ]
    
    async def _ingest_items(
        self,
        items: List[dict],
        profile_id: int,
        source_type: SourceType,
        formatter,
    ) -> List[VectorChunk]:
        """Generic method to ingest list of items."""
        chunks = []
        for item in items:
            text = formatter(item)
            item_chunks = await self._create_chunks(
                text=text,
                profile_id=profile_id,
                source_type=source_type,
                source_id=item.get("id"),
            )
            chunks.extend(item_chunks)
        return chunks
    
    async def ingest_profile_data(
        self,
        profile_id: int,
        profile_summary: Optional[str] = None,
        experiences: Optional[List[dict]] = None,
        projects: Optional[List[dict]] = None,
        skills: Optional[List[dict]] = None,
    ) -> None:
        """Ingest structured profile data from PostgreSQL."""
        chunks_to_store = []
        
        # Ingest summary
        if profile_summary:
            chunks = await self._create_chunks(
                text=profile_summary,
                profile_id=profile_id,
                source_type=SourceType.SUMMARY,
            )
            chunks_to_store.extend(chunks)
        
        # Ingest experiences
        if experiences:
            chunks = await self._ingest_items(
                experiences, profile_id, SourceType.EXPERIENCE, _format_experience
            )
            chunks_to_store.extend(chunks)
        
        # Ingest projects
        if projects:
            chunks = await self._ingest_items(
                projects, profile_id, SourceType.PROJECT, _format_project
            )
            chunks_to_store.extend(chunks)
        
        # Ingest skills
        if skills:
            skills_text = _format_skills(skills)
            chunks = await self._create_chunks(
                text=skills_text,
                profile_id=profile_id,
                source_type=SourceType.SKILL,
            )
            chunks_to_store.extend(chunks)
        
        if chunks_to_store:
            await self.vector_store.upsert_chunks(chunks_to_store, profile_id)
    
    async def ingest_document(
        self,
        profile_id: int,
        document_text: str,
        source_type: SourceType,
        source_id: Optional[int] = None,
    ) -> None:
        """Ingest unstructured document (CV PDF, markdown, README, etc.)."""
        chunks = await self._create_chunks(
            text=document_text,
            profile_id=profile_id,
            source_type=source_type,
            source_id=source_id,
            use_batch=True,
        )
        
        if chunks:
            await self.vector_store.upsert_chunks(chunks, profile_id)
    
    async def reingest_profile(self, profile_id: int, **kwargs) -> None:
        """
        Re-ingest profile data (idempotent operation).
        
        Deletes existing chunks for the profile, then ingests fresh data.
        """
        await self.vector_store.delete_profile_chunks(profile_id)
        await self.ingest_profile_data(profile_id, **kwargs)