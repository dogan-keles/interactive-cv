"""
Document ingestion for RAG pipeline.

Chunks and embeds profile data for semantic search.
"""

import logging
from typing import List
from sqlalchemy.orm import Session

from backend.data_access.vector_db.vector_store import (
    VectorStore,
    VectorChunk,
    ChunkMetadata,
    SourceType,
    EmbeddingProvider,
)
from backend.data_access.knowledge_base.postgres import (
    Profile,
    Skill,
    Experience,
    Project,
)

logger = logging.getLogger(__name__)


class DocumentIngestion:
    """
    Handles ingestion of profile data into vector store.
    """
    
    def __init__(
        self,
        vector_store: VectorStore,
        embedding_provider: EmbeddingProvider,
    ):
        """
        Initialize document ingestion.
        
        Args:
            vector_store: Vector store for saving embeddings
            embedding_provider: Provider for generating embeddings
        """
        self.vector_store = vector_store
        self.embedding_provider = embedding_provider
    
    async def ingest_profile(
        self,
        profile_id: int,
        db_session: Session,
    ) -> int:
        """
        Ingest complete profile data into vector store.
        
        Args:
            profile_id: Profile ID to ingest
            db_session: Database session
            
        Returns:
            Number of chunks created
        """
        logger.info(f"Starting ingestion for profile {profile_id}")
        
        # Delete existing chunks for this profile (idempotent)
        await self.vector_store.delete_profile_chunks(profile_id)
        
        # Fetch profile data
        profile = db_session.query(Profile).filter(Profile.id == profile_id).first()
        if not profile:
            logger.warning(f"Profile {profile_id} not found")
            return 0
        
        all_chunks = []
        
        # 1. Ingest summary
        if profile.summary:
            chunks = await self._chunk_and_embed_text(
                text=profile.summary,
                profile_id=profile_id,
                source_type=SourceType.SUMMARY,
            )
            all_chunks.extend(chunks)
        
        # 2. Ingest skills
        skills = db_session.query(Skill).filter(Skill.profile_id == profile_id).all()
        for skill in skills:
            text = f"{skill.name} ({skill.category}, {skill.proficiency_level})"
            chunks = await self._chunk_and_embed_text(
                text=text,
                profile_id=profile_id,
                source_type=SourceType.SKILL,
                source_id=skill.id,
            )
            all_chunks.extend(chunks)
        
        # 3. Ingest experiences
        experiences = db_session.query(Experience).filter(Experience.profile_id == profile_id).all()
        for exp in experiences:
            text = f"{exp.role} at {exp.company}. {exp.description or ''}"
            chunks = await self._chunk_and_embed_text(
                text=text,
                profile_id=profile_id,
                source_type=SourceType.EXPERIENCE,
                source_id=exp.id,
            )
            all_chunks.extend(chunks)
        
        # 4. Ingest projects
        projects = db_session.query(Project).filter(Project.profile_id == profile_id).all()
        for proj in projects:
            tech_stack = ', '.join(proj.tech_stack) if proj.tech_stack else ''
            text = f"{proj.title}. {proj.description or ''}. Technologies: {tech_stack}"
            chunks = await self._chunk_and_embed_text(
                text=text,
                profile_id=profile_id,
                source_type=SourceType.PROJECT,
                source_id=proj.id,
            )
            all_chunks.extend(chunks)
        
        # Store all chunks
        if all_chunks:
            await self.vector_store.upsert_chunks(all_chunks, profile_id)
        
        logger.info(f"Ingestion complete. Created {len(all_chunks)} chunks for profile {profile_id}")
        return len(all_chunks)
    
    async def _chunk_and_embed_text(
        self,
        text: str,
        profile_id: int,
        source_type: SourceType,
        source_id: int = None,
    ) -> List[VectorChunk]:
        """
        Chunk text and generate embeddings.
        
        Args:
            text: Text to chunk and embed
            profile_id: Profile ID
            source_type: Type of source document
            source_id: Optional source document ID
            
        Returns:
            List of vector chunks with embeddings
        """
        # Simple chunking strategy: Split on sentences if text is long
        chunks_text = self._chunk_text(text, max_chunk_size=500)
        
        # Generate embeddings for all chunks
        embeddings = await self.embedding_provider.generate_embeddings_batch(chunks_text)
        
        # Create VectorChunk objects
        vector_chunks = []
        for idx, (chunk_text, embedding) in enumerate(zip(chunks_text, embeddings)):
            metadata = ChunkMetadata(
                profile_id=profile_id,
                source_type=source_type,
                source_id=source_id,
                chunk_index=idx,
            )
            vector_chunks.append(
                VectorChunk(
                    text=chunk_text,
                    embedding=embedding,
                    metadata=metadata,
                )
            )
        
        return vector_chunks
    
    def _chunk_text(self, text: str, max_chunk_size: int = 500) -> List[str]:
        """
        Split text into chunks.
        
        Simple strategy: Keep chunks under max_chunk_size characters.
        Split on periods if possible.
        
        Args:
            text: Text to chunk
            max_chunk_size: Maximum characters per chunk
            
        Returns:
            List of text chunks
        """
        if len(text) <= max_chunk_size:
            return [text]
        
        # Split on sentences (periods followed by space)
        sentences = text.replace('. ', '.|').split('|')
        
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) <= max_chunk_size:
                current_chunk += sentence + " "
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + " "
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks if chunks else [text]