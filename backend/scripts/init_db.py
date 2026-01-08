"""
Database initialization script.

Run this to create all tables in Neon DB.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.infrastructure.database import create_tables, check_connection
from backend.data_access.knowledge_base.postgres import Base
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init_database():
    """Initialize database tables."""
    logger.info("🔄 Checking database connection...")
    
    if not check_connection():
        logger.error("❌ Cannot connect to database. Check your DATABASE_URL.")
        return False
    
    logger.info("🔄 Creating database tables...")
    
    try:
        create_tables()
        logger.info("✅ Database initialized successfully!")
        
        # Print created tables
        table_names = list(Base.metadata.tables.keys())
        logger.info(f"📋 Created tables: {', '.join(table_names)}")
        
        return True
    
    except Exception as e:
        logger.error(f"❌ Failed to initialize database: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = init_database()
    sys.exit(0 if success else 1)


