"""
GitHub tools for agents.

Fetches real GitHub repository data via GitHub API with intelligent filtering.
"""

import os
import logging
import datetime
from typing import List, Optional
from github import Github, GithubException

from sqlalchemy.orm import Session
from sqlalchemy import select

from backend.data_access.knowledge_base.postgres import Profile, Project

logger = logging.getLogger(__name__)


def _get_github_client() -> Optional[Github]:
    """
    Get authenticated GitHub client.
    
    Returns:
        Github client or None if token not available
    """
    # Force reload environment variables
    from dotenv import load_dotenv
    load_dotenv(override=True)  # override=True forces refresh
    
    token = os.getenv("GITHUB_TOKEN")
    
    if not token:
        logger.warning("GITHUB_TOKEN not found in environment")
        return None
    
    logger.info(f"GitHub token found (starts with: {token[:15]}...)")
    
    try:
        return Github(token)
    except Exception as e:
        logger.error(f"Failed to create GitHub client: {e}")
        return None


def _calculate_repo_score(repo) -> float:
    """
    Calculate relevance score for a repository.
    
    Factors:
    - Stars (weighted 3x)
    - Forks (weighted 2x)
    - Size (bigger = more substantial)
    - Recency (updated recently = more relevant)
    - Has description (shows effort)
    - Has topics/tags (shows organization)
    
    Args:
        repo: PyGithub Repository object
        
    Returns:
        Relevance score (higher = more important)
    """
    score = 0.0
    
    # Stars (major factor)
    score += repo.stargazers_count * 3
    
    # Forks (moderate factor)
    score += repo.forks_count * 2
    
    # Size (substantial projects score higher)
    # Normalize: 1 point per 100KB
    score += (repo.size / 100)
    
    # Recency bonus (updated in last 6 months)
    if repo.updated_at:
        days_since_update = (datetime.datetime.now(datetime.timezone.utc) - repo.updated_at).days
        if days_since_update < 180:  # 6 months
            # More recent = higher score
            recency_bonus = max(0, (180 - days_since_update) / 30)  # Up to 6 points
            score += recency_bonus
    
    # Has good description
    if repo.description and len(repo.description) > 20:
        score += 2
    
    # Has topics/tags
    topics = repo.get_topics()
    if topics:
        score += len(topics) * 0.5  # 0.5 points per topic
    
    # Larger projects (likely has README and good structure)
    if repo.size > 50:  # Projects > 50KB
        score += 1
    
    return score


async def get_github_repositories(
    profile_id: int,
    db_session: Session,
    max_repos: int = 15,
    min_stars: int = 0,
    include_forks: bool = False,
) -> List[dict]:
    """
    Get GitHub repositories for a profile with intelligent filtering.
    
    Fetches from GitHub API if username is available, filters and sorts
    by relevance to show most important projects.
    Falls back to database projects with github_url.
    
    Args:
        profile_id: Profile identifier
        db_session: SQLAlchemy database session
        max_repos: Maximum number of repos to return (default 15)
        min_stars: Minimum star count (default 0)
        include_forks: Whether to include forked repos (default False)
        
    Returns:
        List of repository dictionaries (most important first)
    """
    # Get GitHub username from profile
    username = await get_profile_github_username(profile_id, db_session)
    
    if not username:
        logger.info("No GitHub username found, returning empty list")
        return []
    
    logger.info(f"Found GitHub username: {username}")
    
    # Try to fetch from GitHub API
    github_client = _get_github_client()
    
    if github_client:
        try:
            logger.info(f"Attempting to fetch repos from GitHub for user: {username}")
            repos = await _fetch_repos_from_github(
                github_client, 
                username,
                max_repos=max_repos,
                min_stars=min_stars,
                include_forks=include_forks,
            )
            if repos:
                logger.info(f"✅ Fetched {len(repos)} repositories from GitHub API")
                return repos
        except Exception as e:
            logger.warning(f"Failed to fetch from GitHub API: {e}")
    
    # Fallback: Get from database
    logger.info("Falling back to database for repository info")
    return await _get_repos_from_database(profile_id, db_session)


async def _fetch_repos_from_github(
    github_client: Github,
    username: str,
    max_repos: int = 15,
    min_stars: int = 0,
    include_forks: bool = False,
) -> List[dict]:
    """
    Fetch repositories from GitHub API with intelligent filtering.
    
    Filters for important/relevant repositories:
    - Sorts by stars + recent activity + size
    - Excludes forks (unless requested)
    - Excludes archived repos
    - Excludes tiny repos (< 10KB)
    - Prioritizes substantial projects
    
    Args:
        github_client: Authenticated GitHub client
        username: GitHub username
        max_repos: Maximum number of repos to return
        min_stars: Minimum star count
        include_forks: Whether to include forked repos
        
    Returns:
        List of repository dictionaries (most important first)
    """
    try:
        user = github_client.get_user(username)
        all_repos = []
        
        logger.info(f"Fetching all public repositories for {username}...")
        
        # Get all public repositories
        for repo in user.get_repos(type='public'):
            # Skip forks unless specifically requested
            if repo.fork and not include_forks:
                continue
            
            # Skip archived repos (not actively maintained)
            if repo.archived:
                continue
            
            # Skip very small repos (likely tests/demos)
            if repo.size < 10:  # Less than 10KB
                continue
            
            # Calculate relevance score
            score = _calculate_repo_score(repo)
            
            all_repos.append({
                "name": repo.name,
                "full_name": repo.full_name,
                "description": repo.description or "No description",
                "html_url": repo.html_url,
                "language": repo.language or "Not specified",
                "languages": list(repo.get_languages().keys()),  # All languages used
                "stargazers_count": repo.stargazers_count,
                "forks_count": repo.forks_count,
                "open_issues_count": repo.open_issues_count,
                "topics": repo.get_topics(),
                "created_at": repo.created_at.isoformat() if repo.created_at else None,
                "updated_at": repo.updated_at.isoformat() if repo.updated_at else None,
                "size": repo.size,
                "default_branch": repo.default_branch,
                "is_fork": repo.fork,
                "archived": repo.archived,
                "_relevance_score": score,  # Internal use for sorting
            })
        
        logger.info(f"Found {len(all_repos)} repos after filtering")
        
        # Sort by relevance score (highest first)
        all_repos.sort(key=lambda r: r["_relevance_score"], reverse=True)
        
        # Filter by stars if specified
        if min_stars > 0:
            all_repos = [r for r in all_repos if r["stargazers_count"] >= min_stars]
            logger.info(f"After star filter (>={min_stars}): {len(all_repos)} repos")
        
        # Return top N most relevant repos
        top_repos = all_repos[:max_repos]
        
        logger.info(f"Returning top {len(top_repos)} most relevant repositories")
        
        # Remove internal score field before returning
        for repo in top_repos:
            repo.pop("_relevance_score", None)
        
        return top_repos
    
    except GithubException as e:
        logger.error(f"GitHub API error: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error fetching repos: {e}")
        return []


async def _get_repos_from_database(
    profile_id: int,
    db_session: Session,
) -> List[dict]:
    """
    Get repositories from database (fallback).
    
    Args:
        profile_id: Profile identifier
        db_session: Database session
        
    Returns:
        List of repository dictionaries
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
            "name": project.title,
            "description": project.description or "No description",
            "html_url": project.github_url,
            "languages": project.tech_stack if project.tech_stack else [],
            "topics": project.relevance_tags if project.relevance_tags else [],
            "stargazers_count": 0,
            "forks_count": 0,
        })
    
    return repos


async def get_repository_details(
    repo_name: str,
    profile_id: int,
    db_session: Session,
) -> Optional[dict]:
    """
    Get details for a specific repository.
    
    Args:
        repo_name: Repository name
        profile_id: Profile identifier
        db_session: Database session
        
    Returns:
        Repository details dictionary or None
    """
    # Get GitHub username
    username = await get_profile_github_username(profile_id, db_session)
    
    if not username:
        return None
    
    github_client = _get_github_client()
    
    if github_client:
        try:
            # Try full name first (username/repo)
            if '/' in repo_name:
                repo = github_client.get_repo(repo_name)
            else:
                repo = github_client.get_repo(f"{username}/{repo_name}")
            
            # Get detailed info
            languages = repo.get_languages()
            
            return {
                "name": repo.name,
                "full_name": repo.full_name,
                "description": repo.description or "No description",
                "html_url": repo.html_url,
                "language": repo.language or "Not specified",
                "languages": languages,
                "stargazers_count": repo.stargazers_count,
                "forks_count": repo.forks_count,
                "open_issues_count": repo.open_issues_count,
                "topics": repo.get_topics(),
                "created_at": repo.created_at.isoformat() if repo.created_at else None,
                "updated_at": repo.updated_at.isoformat() if repo.updated_at else None,
                "size": repo.size,
                "default_branch": repo.default_branch,
                "homepage": repo.homepage,
                "has_issues": repo.has_issues,
                "has_wiki": repo.has_wiki,
                "archived": repo.archived,
            }
        
        except GithubException as e:
            logger.error(f"GitHub API error for repo {repo_name}: {e}")
    
    # Fallback to database
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
        "name": project.title,
        "description": project.description,
        "html_url": project.github_url,
        "languages": project.tech_stack if project.tech_stack else [],
        "topics": project.relevance_tags if project.relevance_tags else [],
    }


async def get_profile_github_username(
    profile_id: int,
    db_session: Session,
) -> Optional[str]:
    """
    Get GitHub username for a profile.
    
    Args:
        profile_id: Profile identifier
        db_session: Database session
        
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