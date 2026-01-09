"""
Profile data access tools.

Functions for retrieving structured profile data from PostgreSQL.
Used by ProfileAgent to answer questions about skills, experience, etc.
"""

from typing import List, Dict, Optional
from sqlalchemy.orm import Session
import logging

from backend.data_access.knowledge_base.postgres import (
    Profile,
    Skill,
    Experience,
    Project,
)

logger = logging.getLogger(__name__)


async def get_profile_basic_info(
    profile_id: int,
    db_session: Session,
) -> Optional[Dict]:
    """
    Get basic profile information.
    
    Args:
        profile_id: Profile ID
        db_session: Database session
        
    Returns:
        Dictionary with basic info or None if not found
    """
    try:
        profile = db_session.query(Profile).filter(Profile.id == profile_id).first()
        
        if not profile:
            logger.warning(f"Profile {profile_id} not found")
            return None
        
        return {
            "id": profile.id,
            "name": profile.name,
            "email": profile.email,
            "location": profile.location,
            "summary": profile.summary,
            "linkedin_url": profile.linkedin_url,
            "github_username": profile.github_username,
        }
    
    except Exception as e:
        logger.error(f"Error fetching profile basic info: {e}")
        return None


async def get_profile_summary(
    profile_id: int,
    db_session: Session,
) -> Optional[str]:
    """
    Get profile summary text.
    
    Args:
        profile_id: Profile ID
        db_session: Database session
        
    Returns:
        Summary text or None
    """
    try:
        profile = db_session.query(Profile).filter(Profile.id == profile_id).first()
        return profile.summary if profile else None
    
    except Exception as e:
        logger.error(f"Error fetching profile summary: {e}")
        return None


async def get_profile_skills(
    profile_id: int,
    db_session: Session,
) -> List[Dict]:
    """
    Get all skills for a profile.
    
    Args:
        profile_id: Profile ID
        db_session: Database session
        
    Returns:
        List of skill dictionaries
    """
    try:
        skills = db_session.query(Skill).filter(Skill.profile_id == profile_id).all()
        
        return [
            {
                "id": skill.id,
                "name": skill.name,
                "category": skill.category,
                "proficiency_level": skill.proficiency_level,
            }
            for skill in skills
        ]
    
    except Exception as e:
        logger.error(f"Error fetching skills: {e}")
        return []


async def get_profile_experiences(
    profile_id: int,
    db_session: Session,
) -> List[Dict]:
    """
    Get all work experiences for a profile.
    
    Args:
        profile_id: Profile ID
        db_session: Database session
        
    Returns:
        List of experience dictionaries
    """
    try:
        experiences = db_session.query(Experience).filter(
            Experience.profile_id == profile_id
        ).order_by(Experience.start_date.desc()).all()
        
        return [
            {
                "id": exp.id,
                "company": exp.company,
                "role": exp.role,
                "start_date": exp.start_date.isoformat() if exp.start_date else None,
                "end_date": exp.end_date.isoformat() if exp.end_date else "Present",
                "description": exp.description,
                "location": exp.location,
            }
            for exp in experiences
        ]
    
    except Exception as e:
        logger.error(f"Error fetching experiences: {e}")
        return []


async def get_profile_projects(
    profile_id: int,
    db_session: Session,
) -> List[Dict]:
    """
    Get all projects for a profile.
    
    Args:
        profile_id: Profile ID
        db_session: Database session
        
    Returns:
        List of project dictionaries
    """
    try:
        projects = db_session.query(Project).filter(
            Project.profile_id == profile_id
        ).all()
        
        return [
            {
                "id": proj.id,
                "title": proj.title,
                "description": proj.description,
                "tech_stack": proj.tech_stack,
                "relevance_tags": proj.relevance_tags,
                "github_url": proj.github_url,
                "demo_url": proj.demo_url,
            }
            for proj in projects
        ]
    
    except Exception as e:
        logger.error(f"Error fetching projects: {e}")
        return []


async def get_full_profile(
    profile_id: int,
    db_session: Session,
) -> Optional[Dict]:
    """
    Get complete profile data (all information).
    
    Args:
        profile_id: Profile ID
        db_session: Database session
        
    Returns:
        Complete profile dictionary or None
    """
    try:
        basic_info = await get_profile_basic_info(profile_id, db_session)
        
        if not basic_info:
            return None
        
        return {
            "basic_info": basic_info,
            "skills": await get_profile_skills(profile_id, db_session),
            "experiences": await get_profile_experiences(profile_id, db_session),
            "projects": await get_profile_projects(profile_id, db_session),
        }
    
    except Exception as e:
        logger.error(f"Error fetching full profile: {e}")
        return None