"""
Profile tools for agents.

Agents use these tools to query structured profile data from PostgreSQL.
Agents must NOT access the database directly.
"""

from typing import List, Optional
from datetime import date

from sqlalchemy.orm import Session
from sqlalchemy import select

from data_access.knowledge_base.postgres import Profile, Skill, Experience, Project


async def get_profile_summary(
    profile_id: int,
    db_session: Session,
) -> Optional[str]:
    """
    Get profile summary text.
    
    Args:
        profile_id: Profile identifier
        db_session: SQLAlchemy database session
        
    Returns:
        Profile summary text or None
    """
    result = db_session.execute(
        select(Profile).where(Profile.id == profile_id)
    )
    profile = result.scalar_one_or_none()
    
    if not profile:
        return None
    
    return profile.summary


async def get_profile_skills(
    profile_id: int,
    db_session: Session,
) -> List[dict]:
    """
    Get all skills for a profile.
    
    Args:
        profile_id: Profile identifier
        db_session: SQLAlchemy database session
        
    Returns:
        List of skill dictionaries with 'id', 'name', 'category', 'proficiency_level'
    """
    result = db_session.execute(
        select(Skill).where(Skill.profile_id == profile_id)
    )
    skills = result.scalars().all()
    
    return [
        {
            "id": skill.id,
            "name": skill.name,
            "category": skill.category,
            "proficiency_level": skill.proficiency_level,
        }
        for skill in skills
    ]


async def get_profile_experiences(
    profile_id: int,
    db_session: Session,
) -> List[dict]:
    """
    Get all work experiences for a profile.
    
    Args:
        profile_id: Profile identifier
        db_session: SQLAlchemy database session
        
    Returns:
        List of experience dictionaries with 'id', 'company', 'role', 'start_date',
        'end_date', 'description', 'location'
    """
    result = db_session.execute(
        select(Experience)
        .where(Experience.profile_id == profile_id)
        .order_by(Experience.start_date.desc())
    )
    experiences = result.scalars().all()
    
    return [
        {
            "id": exp.id,
            "company": exp.company,
            "role": exp.role,
            "start_date": exp.start_date.isoformat() if exp.start_date else None,
            "end_date": exp.end_date.isoformat() if exp.end_date else None,
            "description": exp.description,
            "location": exp.location,
        }
        for exp in experiences
    ]


async def get_profile_projects(
    profile_id: int,
    db_session: Session,
) -> List[dict]:
    """
    Get all projects for a profile.
    
    Args:
        profile_id: Profile identifier
        db_session: SQLAlchemy database session
        
    Returns:
        List of project dictionaries with 'id', 'title', 'description', 'tech_stack',
        'relevance_tags', 'github_url', 'demo_url'
    """
    result = db_session.execute(
        select(Project).where(Project.profile_id == profile_id)
    )
    projects = result.scalars().all()
    
    return [
        {
            "id": project.id,
            "title": project.title,
            "description": project.description,
            "tech_stack": project.tech_stack if project.tech_stack else [],
            "relevance_tags": project.relevance_tags if project.relevance_tags else [],
            "github_url": project.github_url,
            "demo_url": project.demo_url,
        }
        for project in projects
    ]


async def get_profile_basic_info(
    profile_id: int,
    db_session: Session,
) -> Optional[dict]:
    """
    Get basic profile information (name, email, location, etc.).
    
    Args:
        profile_id: Profile identifier
        db_session: SQLAlchemy database session
        
    Returns:
        Dictionary with basic profile info or None
    """
    result = db_session.execute(
        select(Profile).where(Profile.id == profile_id)
    )
    profile = result.scalar_one_or_none()
    
    if not profile:
        return None
    
    return {
        "id": profile.id,
        "name": profile.name,
        "email": profile.email,
        "location": profile.location,
        "linkedin_url": profile.linkedin_url,
        "github_username": profile.github_username,
    }





