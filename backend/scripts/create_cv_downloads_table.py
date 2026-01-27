"""
Create cv_download_requests table for tracking CV downloads.
"""

import os
from dotenv import load_dotenv

load_dotenv()

from backend.infrastructure.database import SessionLocal, engine
from sqlalchemy import text

def create_table():
    """Create cv_download_requests table."""
    
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS cv_download_requests (
        id SERIAL PRIMARY KEY,
        profile_id INTEGER NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
        user_name VARCHAR(255) NOT NULL,
        user_email VARCHAR(255) NOT NULL,
        user_company VARCHAR(255),
        download_token VARCHAR(255) UNIQUE NOT NULL,
        downloaded BOOLEAN DEFAULT FALSE,
        downloaded_at TIMESTAMP,
        ip_address VARCHAR(50),
        user_agent TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE INDEX IF NOT EXISTS idx_cv_downloads_token ON cv_download_requests(download_token);
    CREATE INDEX IF NOT EXISTS idx_cv_downloads_profile ON cv_download_requests(profile_id);
    CREATE INDEX IF NOT EXISTS idx_cv_downloads_email ON cv_download_requests(user_email);
    """
    
    with engine.connect() as conn:
        conn.execute(text(create_table_sql))
        conn.commit()
    
    print("✅ Table cv_download_requests created successfully!")

if __name__ == "__main__":
    create_table()