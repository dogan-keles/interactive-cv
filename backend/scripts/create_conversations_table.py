"""
Create conversations table for chat history.
"""

import os
from dotenv import load_dotenv

load_dotenv()

from backend.infrastructure.database import SessionLocal, engine
from sqlalchemy import text


def create_table():
    """Create conversations table."""
    
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS conversations (
        id SERIAL PRIMARY KEY,
        profile_id INTEGER NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
        session_id VARCHAR(255),
        user_query TEXT NOT NULL,
        agent_response TEXT NOT NULL,
        agent_type VARCHAR(50),
        language VARCHAR(10),
        response_time_ms INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE INDEX IF NOT EXISTS idx_conversations_profile ON conversations(profile_id);
    CREATE INDEX IF NOT EXISTS idx_conversations_session ON conversations(session_id);
    CREATE INDEX IF NOT EXISTS idx_conversations_created ON conversations(created_at DESC);
    """
    
    with engine.connect() as conn:
        conn.execute(text(create_table_sql))
        conn.commit()
    
    print("✅ Table conversations created successfully!")


if __name__ == "__main__":
    create_table()