"""
GitHub tools for agents.

Agents use these tools to retrieve GitHub repository information.
Can fetch from database (if stored) or GitHub API.
"""

from typing import List, Optional
import logging

from sqlalchemy.orm import Session
from sqlalchemy import select

from data_access.knowledge_base.postgres import Profile, Project

logger = logging.getLogger(__name__)


async def get_github_repositories(
    profile_id: int,
    db_session: Session,
) -> List[dict]:
    """
    Get GitHub repositories for a profile.
    
    Currently fetches from database (projects with github_url).
    Can be extended to use GitHub API if needed.
    
    Args:
        profile_id: Profile identifier
        db_session: SQLAlchemy database session
        
    Returns:
        List of repository dictionaries with project info and GitHub URL
    """
    result = db_session.execute(
        select(Project)
        .where(Project.profile_id == profile_id)
        .where(Project.github_url.isnot(None))
    )
    projects = result.scalars().all()
    
    repos = []
    for project in projects:
        repos.append({
            "id": project.id,
            "title": project.title,
            "description": project.description,
            "github_url": project.github_url,
            "tech_stack": project.tech_stack if project.tech_stack else [],
            "demo_url": project.demo_url,
        })
    
    return repos


async def get_repository_details(
    repo_name: str,
    profile_id: int,
    db_session: Session,
) -> Optional[dict]:
    """
    Get details for a specific repository.
    
    Searches projects by title or GitHub URL containing repo_name.
    
    Args:
        repo_name: Repository name or identifier
        profile_id: Profile identifier
        db_session: SQLAlchemy database session
        
    Returns:
        Repository details dictionary or None
    """
    result = db_session.execute(
        select(Project)
        .where(Project.profile_id == profile_id)
        .where(
            (Project.title.ilike(f"%{repo_name}%")) |
            (Project.github_url.ilike(f"%{repo_name}%"))
        )
    )
    project = result.scalar_one_or_none()
    
    if not project:
        return None
    
    return {
        "id": project.id,
        "title": project.title,
        "description": project.description,
        "github_url": project.github_url,
        "tech_stack": project.tech_stack if project.tech_stack else [],
        "relevance_tags": project.relevance_tags if project.relevance_tags else [],
        "demo_url": project.demo_url,
    }


async def get_profile_github_username(
    profile_id: int,
    db_session: Session,
) -> Optional[str]:
    """
    Get GitHub username for a profile.
    
    Args:
        profile_id: Profile identifier
        db_session: SQLAlchemy database session
        
    Returns:
        GitHub username or None
    """
    result = db_session.execute(
        select(Profile).where(Profile.id == profile_id)
    )
    profile = result.scalar_one_or_none()
    
    if not profile:
        return None
    
    return profile.github_username



