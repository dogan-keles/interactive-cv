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


class ChunkingConfig:
    """Configuration for text chunking strategy."""
    
    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap


def chunk_text(
    text: str,
    config: ChunkingConfig,
) -> List[str]:
    """
    Split text into overlapping chunks.
    
    Simple character-based chunking. Can be extended with
    sentence-aware or token-aware chunking.
    
    Args:
        text: Input text to chunk
        config: Chunking configuration
        
    Returns:
        List of text chunks
    """
    if not text or len(text) <= config.chunk_size:
        return [text] if text else []
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + config.chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        
        if end >= len(text):
            break
            
        # Move start position with overlap
        start = end - config.chunk_overlap
    
    return chunks


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
    
    async def _create_chunks_from_text(
        self,
        text: str,
        profile_id: int,
        source_type: SourceType,
        source_id: Optional[int] = None,
    ) -> List[VectorChunk]:
        """
        Create vector chunks from text with embeddings.
        
        Args:
            text: Input text to chunk and embed
            profile_id: Profile identifier
            source_type: Source type for metadata
            source_id: Optional source identifier
            
        Returns:
            List of vector chunks with embeddings
        """
        if not text:
            return []
        
        text_chunks = chunk_text(text, self.chunking_config)
        if not text_chunks:
            return []
        
        chunks = []
        for idx, chunk_text in enumerate(text_chunks):
            metadata = ChunkMetadata(
                profile_id=profile_id,
                source_type=source_type,
                source_id=source_id,
                chunk_index=idx,
            )
            embedding = await self.embedding_provider.generate_embedding(chunk_text)
            chunks.append(
                VectorChunk(
                    text=chunk_text,
                    embedding=embedding,
                    metadata=metadata,
                )
            )
        
        return chunks
    
    async def _create_chunks_from_text_batch(
        self,
        text: str,
        profile_id: int,
        source_type: SourceType,
        source_id: Optional[int] = None,
    ) -> List[VectorChunk]:
        """
        Create vector chunks from text using batch embedding generation.
        
        More efficient for large documents.
        
        Args:
            text: Input text to chunk and embed
            profile_id: Profile identifier
            source_type: Source type for metadata
            source_id: Optional source identifier
            
        Returns:
            List of vector chunks with embeddings
        """
        if not text:
            return []
        
        text_chunks = chunk_text(text, self.chunking_config)
        chunk_texts = [chunk for chunk in text_chunks if chunk]
        if not chunk_texts:
            return []
        
        # Generate embeddings in batch
        embeddings = await self.embedding_provider.generate_embeddings_batch(chunk_texts)
        
        chunks = []
        for idx, (chunk_text, embedding) in enumerate(zip(chunk_texts, embeddings)):
            metadata = ChunkMetadata(
                profile_id=profile_id,
                source_type=source_type,
                source_id=source_id,
                chunk_index=idx,
            )
            chunks.append(
                VectorChunk(
                    text=chunk_text,
                    embedding=embedding,
                    metadata=metadata,
                )
            )
        
        return chunks
    
    async def ingest_profile_data(
        self,
        profile_id: int,
        profile_summary: Optional[str] = None,
        experiences: Optional[List[dict]] = None,
        projects: Optional[List[dict]] = None,
        skills: Optional[List[dict]] = None,
    ) -> None:
        """
        Ingest structured profile data from PostgreSQL.
        
        Args:
            profile_id: Profile identifier
            profile_summary: Profile summary text
            experiences: List of experience dicts with 'id', 'company', 'role', 'description'
            projects: List of project dicts with 'id', 'title', 'description', 'tech_stack'
            skills: List of skill dicts with 'name', 'category', 'proficiency_level'
        """
        chunks_to_store = []
        
        # Ingest profile summary
        if profile_summary:
            chunks = await self._create_chunks_from_text(
                text=profile_summary,
                profile_id=profile_id,
                source_type=SourceType.SUMMARY,
            )
            chunks_to_store.extend(chunks)
        
        # Ingest experiences
        if experiences:
            for exp in experiences:
                exp_text = self._format_experience(exp)
                chunks = await self._create_chunks_from_text(
                    text=exp_text,
                    profile_id=profile_id,
                    source_type=SourceType.EXPERIENCE,
                    source_id=exp.get("id"),
                )
                chunks_to_store.extend(chunks)
        
        # Ingest projects
        if projects:
            for project in projects:
                project_text = self._format_project(project)
                chunks = await self._create_chunks_from_text(
                    text=project_text,
                    profile_id=profile_id,
                    source_type=SourceType.PROJECT,
                    source_id=project.get("id"),
                )
                chunks_to_store.extend(chunks)
        
        # Ingest skills (as structured text)
        if skills:
            skills_text = self._format_skills(skills)
            chunks = await self._create_chunks_from_text(
                text=skills_text,
                profile_id=profile_id,
                source_type=SourceType.SKILL,
            )
            chunks_to_store.extend(chunks)
        
        # Batch upsert all chunks
        if chunks_to_store:
            await self.vector_store.upsert_chunks(chunks_to_store, profile_id)
    
    async def ingest_document(
        self,
        profile_id: int,
        document_text: str,
        source_type: SourceType,
        source_id: Optional[int] = None,
    ) -> None:
        """
        Ingest unstructured document (CV PDF, markdown, README, etc.).
        
        Args:
            profile_id: Profile identifier
            document_text: Full document text
            source_type: Type of document (CV, GITHUB, etc.)
            source_id: Optional source identifier
        """
        chunks_to_store = await self._create_chunks_from_text_batch(
            text=document_text,
            profile_id=profile_id,
            source_type=source_type,
            source_id=source_id,
        )
        
        if chunks_to_store:
            await self.vector_store.upsert_chunks(chunks_to_store, profile_id)
    
    async def reingest_profile(
        self,
        profile_id: int,
        **kwargs,
    ) -> None:
        """
        Re-ingest profile data (idempotent operation).
        
        Deletes existing chunks for the profile, then ingests fresh data.
        """
        # Delete existing chunks
        await self.vector_store.delete_profile_chunks(profile_id)
        
        # Ingest fresh data
        await self.ingest_profile_data(profile_id, **kwargs)
    
    def _format_experience(self, exp: dict) -> str:
        """Format experience dict into searchable text."""
        parts = [
            f"Role: {exp.get('role', '')}",
            f"Company: {exp.get('company', '')}",
        ]
        if exp.get("description"):
            parts.append(f"Description: {exp['description']}")
        return "\n".join(parts)
    
    def _format_project(self, project: dict) -> str:
        """Format project dict into searchable text."""
        parts = [
            f"Project: {project.get('title', '')}",
        ]
        if project.get("description"):
            parts.append(f"Description: {project['description']}")
        if project.get("tech_stack"):
            tech_stack = project["tech_stack"]
            if isinstance(tech_stack, list):
                parts.append(f"Technologies: {', '.join(tech_stack)}")
        return "\n".join(parts)
    
    def _format_skills(self, skills: List[dict]) -> str:
        """Format skills list into searchable text."""
        skill_parts = []
        for skill in skills:
            skill_str = f"{skill.get('name', '')} ({skill.get('category', '')}) - {skill.get('proficiency_level', '')}"
            skill_parts.append(skill_str)
        return "\n".join(skill_parts)


