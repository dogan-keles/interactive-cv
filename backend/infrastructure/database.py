"""
Database session management with Neon DB support.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
import os
import logging

# Load .env FIRST before anything else
from dotenv import load_dotenv
load_dotenv()

from backend.data_access.knowledge_base.postgres import Base

logger = logging.getLogger(__name__)

# Get DATABASE_URL from environment (after load_dotenv)
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    logger.warning("⚠️  DATABASE_URL not set, using fallback (won't work in production)")
    DATABASE_URL = "postgresql://user:password@localhost/interactive_cv"
else:
    logger.info(f"✅ DATABASE_URL loaded: {DATABASE_URL[:30]}...")

# Create engine with Neon-friendly settings
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,      # Verify connections before using
    pool_recycle=3600,       # Recycle connections after 1 hour (good for serverless)
    echo=False,              # Set to True for SQL logging (debugging)
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Session:
    """Get database session (FastAPI dependency)."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context():
    """Context manager for database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """Create all database tables."""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database tables created successfully")
    except Exception as e:
        logger.error(f"❌ Error creating database tables: {e}")
        raise


def check_connection():
    """Check if database connection is working."""
    try:
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("✅ Database connection successful")
        return True
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        return False