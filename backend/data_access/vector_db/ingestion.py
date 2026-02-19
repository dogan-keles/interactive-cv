"""
Document ingestion for RAG pipeline.
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
    """Handles ingestion of profile data into vector store."""
    
    def __init__(
        self,
        vector_store: VectorStore,
        embedding_provider: EmbeddingProvider,
    ):
        self.vector_store = vector_store
        self.embedding_provider = embedding_provider
    
    async def ingest_profile(
        self,
        profile_id: int,
        db_session: Session,
    ) -> int:
        """Ingest complete profile data into vector store."""
        logger.info(f"Starting ingestion for profile {profile_id}")
        
        await self.vector_store.delete_profile_chunks(profile_id)
        
        profile = db_session.query(Profile).filter(Profile.id == profile_id).first()
        if not profile:
            logger.warning(f"Profile {profile_id} not found")
            return 0
        
        all_chunks = []
        
        if profile.summary:
            chunks = await self._chunk_and_embed_text(
                text=profile.summary,
                profile_id=profile_id,
                source_type=SourceType.SUMMARY,
            )
            all_chunks.extend(chunks)
        
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
        """Chunk text and generate embeddings."""
        chunks_text = self._chunk_text(text, max_chunk_size=500)
        embeddings = await self.embedding_provider.generate_embeddings_batch(chunks_text)
        
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
        """Split text into chunks."""
        if len(text) <= max_chunk_size:
            return [text]
        
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