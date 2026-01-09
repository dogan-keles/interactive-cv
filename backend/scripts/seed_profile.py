"""
Seed profile data script.

Adds Doğan Keleş's CV data to the database.
Run this after database initialization to populate with profile data.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from dotenv import load_dotenv
load_dotenv()

from backend.infrastructure.database import SessionLocal, check_connection
from backend.data_access.knowledge_base.postgres import (
    Profile,
    Skill,
    Experience,
    Project,
)
from datetime import date
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def seed_dogan_profile():
    """Seed Doğan Keleş's profile data."""
    
    # Check database connection
    if not check_connection():
        logger.error("Cannot connect to database. Check DATABASE_URL.")
        return False
    
    db = SessionLocal()
    
    try:
        # Check if profile already exists
        existing = db.query(Profile).filter(Profile.name == "Doğan Keleş").first()
        if existing:
            logger.warning("Profile for 'Doğan Keleş' already exists. Skipping.")
            return True
        
        logger.info("Creating profile for Doğan Keleş...")
        
        # Create Profile
        profile = Profile(
            name="Doğan Keleş",
            email="dogan@example.com",  # Replace with your real email
            location="Mardin, Turkey",
            summary=(
                "Backend Engineer specializing in Python, FastAPI, and AI integration. "
                "Experienced in building scalable web applications with modern technologies. "
                "Passionate about clean architecture, agent-based systems, and LLM applications."
            ),
            linkedin_url="https://linkedin.com/in/dogankeles",  # Replace with your real LinkedIn
            github_username="dogankeles",  # Replace with your real GitHub
        )
        
        db.add(profile)
        db.flush()  # Get profile.id
        
        logger.info(f"✅ Profile created with ID: {profile.id}")
        
        # Add Skills
        skills = [
            # Programming Languages
            Skill(profile_id=profile.id, name="Python", category="Programming Language", proficiency_level="Expert"),
            Skill(profile_id=profile.id, name="JavaScript", category="Programming Language", proficiency_level="Advanced"),
            Skill(profile_id=profile.id, name="TypeScript", category="Programming Language", proficiency_level="Intermediate"),
            
            # Backend Frameworks
            Skill(profile_id=profile.id, name="FastAPI", category="Framework", proficiency_level="Expert"),
            Skill(profile_id=profile.id, name="Flask", category="Framework", proficiency_level="Advanced"),
            Skill(profile_id=profile.id, name="Django", category="Framework", proficiency_level="Intermediate"),
            
            # Databases
            Skill(profile_id=profile.id, name="PostgreSQL", category="Database", proficiency_level="Advanced"),
            Skill(profile_id=profile.id, name="SQLAlchemy", category="ORM", proficiency_level="Advanced"),
            Skill(profile_id=profile.id, name="Neon DB", category="Database", proficiency_level="Intermediate"),
            
            # Frontend
            Skill(profile_id=profile.id, name="React", category="Framework", proficiency_level="Intermediate"),
            Skill(profile_id=profile.id, name="Vite", category="Tool", proficiency_level="Intermediate"),
            
            # AI/LLM
            Skill(profile_id=profile.id, name="LLM Integration", category="AI", proficiency_level="Advanced"),
            Skill(profile_id=profile.id, name="Groq API", category="AI", proficiency_level="Advanced"),
            Skill(profile_id=profile.id, name="Agent-based Systems", category="AI", proficiency_level="Advanced"),
            Skill(profile_id=profile.id, name="RAG Pipelines", category="AI", proficiency_level="Intermediate"),
            
            # DevOps/Deployment
            Skill(profile_id=profile.id, name="Docker", category="DevOps", proficiency_level="Intermediate"),
            Skill(profile_id=profile.id, name="Git", category="Tool", proficiency_level="Advanced"),
            Skill(profile_id=profile.id, name="Koyeb", category="Cloud Platform", proficiency_level="Intermediate"),
            Skill(profile_id=profile.id, name="Vercel", category="Cloud Platform", proficiency_level="Intermediate"),
        ]
        
        for skill in skills:
            db.add(skill)
        
        logger.info(f"✅ Added {len(skills)} skills")
        
        # Add Experiences
        experiences = [
            Experience(
                profile_id=profile.id,
                company="Freelance / Personal Projects",
                role="Backend Engineer & AI Developer",
                start_date=date(2023, 1, 1),
                end_date=None,  # Current
                description=(
                    "Developing interactive AI-powered applications using FastAPI, PostgreSQL, and LLM APIs. "
                    "Built multi-agent orchestration systems for intelligent CV assistants. "
                    "Experienced in deploying serverless applications on modern cloud platforms."
                ),
                location="Remote",
            ),
            # Add more experiences here if you have them
        ]
        
        for exp in experiences:
            db.add(exp)
        
        logger.info(f"✅ Added {len(experiences)} experiences")
        
        # Add Projects
        projects = [
            Project(
                profile_id=profile.id,
                title="Interactive CV Assistant",
                description=(
                    "Multi-agent AI system for interactive CV queries. Uses ProfileAgent, "
                    "GitHubAgent, CVAgent, and GuardrailAgent with FastAPI backend, PostgreSQL "
                    "database, and Groq LLM integration. Deployed on Koyeb with Neon DB."
                ),
                tech_stack=["Python", "FastAPI", "PostgreSQL", "SQLAlchemy", "Groq API", "Neon DB", "Koyeb", "React", "Vercel"],
                relevance_tags=["AI", "Multi-Agent", "LLM", "Backend", "Full-Stack"],
                github_url="https://github.com/dogankeles/interactive-cv",  # Update if real
                demo_url=None,
            ),
            # Add more projects here
        ]
        
        for proj in projects:
            db.add(proj)
        
        logger.info(f"✅ Added {len(projects)} projects")
        
        # Commit all changes
        db.commit()
        
        logger.info("=" * 50)
        logger.info("🎉 Successfully seeded profile data!")
        logger.info(f"Profile ID: {profile.id}")
        logger.info(f"Name: {profile.name}")
        logger.info(f"Skills: {len(skills)}")
        logger.info(f"Experiences: {len(experiences)}")
        logger.info(f"Projects: {len(projects)}")
        logger.info("=" * 50)
        
        return True
    
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to seed profile: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        db.close()


if __name__ == "__main__":
    success = seed_dogan_profile()
    sys.exit(0 if success else 1)