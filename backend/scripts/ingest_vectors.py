"""
Script to ingest profile data into vector database.

Run this after seeding profile data to enable semantic search.
"""

import asyncio
import logging
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from backend.infrastructure.database import SessionLocal, check_connection
from backend.data_access.vector_db.pgvector_store import PgVectorStore
from backend.data_access.vector_db.sklearn_embedding import SklearnTfidfEmbedding
from backend.data_access.vector_db.ingestion import DocumentIngestion

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    """Ingest profile data into vector database."""
    
    logger.info("=" * 70)
    logger.info("VECTOR DATABASE INGESTION")
    logger.info("=" * 70)
    
    # 1. Check database connection
    if not check_connection():
        logger.error("❌ Database connection failed")
        logger.error("Make sure DATABASE_URL is set in .env")
        return
    
    logger.info("✅ Database connected")
    
    # 2. Create database session
    db_session = SessionLocal()
    
    try:
        # 3. Initialize embedding provider
        logger.info("📥 Loading TF-IDF embedding provider...")
        embedding_provider = SklearnTfidfEmbedding(max_features=384)
        logger.info(f"✅ TF-IDF provider loaded (dimension: {embedding_provider.get_dimension()})")
        
        # 4. Initialize vector store
        vector_store = PgVectorStore(
            db_session=db_session,
            embedding_provider=embedding_provider,
        )
        logger.info("✅ Vector store initialized")
        
        # 5. Initialize ingestion pipeline
        ingestion = DocumentIngestion(
            vector_store=vector_store,
            embedding_provider=embedding_provider,
        )
        logger.info("✅ Ingestion pipeline initialized")
        
        # 6. Ingest profile (default profile_id=1)
        profile_id = 1
        logger.info(f"📝 Ingesting profile {profile_id}...")
        
        num_chunks = await ingestion.ingest_profile(
            profile_id=profile_id,
            db_session=db_session,
        )
        
        logger.info("=" * 70)
        logger.info(f"🎉 Ingestion complete!")
        logger.info(f"📊 Created {num_chunks} vector embeddings")
        logger.info("=" * 70)
        logger.info("")
        logger.info("✅ Semantic search is now enabled!")
        logger.info("Your ProfileAgent can now understand context and meaning.")
        
    except Exception as e:
        logger.error(f"❌ Ingestion failed: {e}", exc_info=True)
    
    finally:
        db_session.close()
        logger.info("✅ Database session closed")


if __name__ == "__main__":
    asyncio.run(main())


