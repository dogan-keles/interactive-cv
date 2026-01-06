"""
CV tools for agents.

Agents use these tools to generate and manage CV files.
"""

from typing import Optional
import logging

from sqlalchemy.orm import Session

from data_access.file_storage.storage import FileStorage
from tools.profile_tools import (
    get_profile_basic_info,
    get_profile_summary,
    get_profile_skills,
    get_profile_experiences,
    get_profile_projects,
)

logger = logging.getLogger(__name__)


def _format_cv_text(
    basic_info: dict,
    summary: Optional[str],
    skills: list,
    experiences: list,
    projects: list,
    language: str = "en",
) -> str:
    """
    Format profile data into CV text format.
    
    Args:
        basic_info: Basic profile information
        summary: Profile summary
        skills: List of skills
        experiences: List of experiences
        projects: List of projects
        language: Language for CV ("en" or "tr")
        
    Returns:
        Formatted CV text
    """
    lines = []
    
    if language == "tr":
        lines.append(f"İSİM: {basic_info.get('name', '')}")
        lines.append(f"E-POSTA: {basic_info.get('email', '')}")
        lines.append(f"KONUM: {basic_info.get('location', '')}")
        if basic_info.get('linkedin_url'):
            lines.append(f"LinkedIn: {basic_info['linkedin_url']}")
        if basic_info.get('github_username'):
            lines.append(f"GitHub: {basic_info['github_username']}")
        lines.append("")
        
        if summary:
            lines.append("ÖZET")
            lines.append("=" * 50)
            lines.append(summary)
            lines.append("")
        
        if skills:
            lines.append("YETENEKLER")
            lines.append("=" * 50)
            for skill in skills:
                lines.append(f"- {skill['name']} ({skill['category']}) - {skill['proficiency_level']}")
            lines.append("")
        
        if experiences:
            lines.append("DENEYİM")
            lines.append("=" * 50)
            for exp in experiences:
                lines.append(f"{exp['role']} - {exp['company']}")
                if exp.get('start_date') and exp.get('end_date'):
                    lines.append(f"{exp['start_date']} - {exp['end_date']}")
                elif exp.get('start_date'):
                    lines.append(f"{exp['start_date']} - Devam ediyor")
                if exp.get('description'):
                    lines.append(exp['description'])
                lines.append("")
        
        if projects:
            lines.append("PROJELER")
            lines.append("=" * 50)
            for project in projects:
                lines.append(f"{project['title']}")
                if project.get('description'):
                    lines.append(project['description'])
                if project.get('tech_stack'):
                    lines.append(f"Teknolojiler: {', '.join(project['tech_stack'])}")
                if project.get('github_url'):
                    lines.append(f"GitHub: {project['github_url']}")
                lines.append("")
    else:
        lines.append(f"NAME: {basic_info.get('name', '')}")
        lines.append(f"EMAIL: {basic_info.get('email', '')}")
        lines.append(f"LOCATION: {basic_info.get('location', '')}")
        if basic_info.get('linkedin_url'):
            lines.append(f"LinkedIn: {basic_info['linkedin_url']}")
        if basic_info.get('github_username'):
            lines.append(f"GitHub: {basic_info['github_username']}")
        lines.append("")
        
        if summary:
            lines.append("SUMMARY")
            lines.append("=" * 50)
            lines.append(summary)
            lines.append("")
        
        if skills:
            lines.append("SKILLS")
            lines.append("=" * 50)
            for skill in skills:
                lines.append(f"- {skill['name']} ({skill['category']}) - {skill['proficiency_level']}")
            lines.append("")
        
        if experiences:
            lines.append("EXPERIENCE")
            lines.append("=" * 50)
            for exp in experiences:
                lines.append(f"{exp['role']} - {exp['company']}")
                if exp.get('start_date') and exp.get('end_date'):
                    lines.append(f"{exp['start_date']} - {exp['end_date']}")
                elif exp.get('start_date'):
                    lines.append(f"{exp['start_date']} - Present")
                if exp.get('description'):
                    lines.append(exp['description'])
                lines.append("")
        
        if projects:
            lines.append("PROJECTS")
            lines.append("=" * 50)
            for project in projects:
                lines.append(f"{project['title']}")
                if project.get('description'):
                    lines.append(project['description'])
                if project.get('tech_stack'):
                    lines.append(f"Technologies: {', '.join(project['tech_stack'])}")
                if project.get('github_url'):
                    lines.append(f"GitHub: {project['github_url']}")
                lines.append("")
    
    return "\n".join(lines)


async def generate_cv(
    profile_id: int,
    db_session: Session,
    file_storage: FileStorage,
    format: str = "txt",
    language: str = "en",
) -> str:
    """
    Generate CV file and return download URL.
    
    Args:
        profile_id: Profile identifier
        db_session: SQLAlchemy database session
        file_storage: File storage instance
        format: File format ("txt" for now, can extend to "pdf")
        language: Language for CV ("en" or "tr")
        
    Returns:
        URL or path to download the CV file
    """
    basic_info = await get_profile_basic_info(profile_id, db_session)
    if not basic_info:
        raise ValueError(f"Profile {profile_id} not found")
    
    summary = await get_profile_summary(profile_id, db_session)
    skills = await get_profile_skills(profile_id, db_session)
    experiences = await get_profile_experiences(profile_id, db_session)
    projects = await get_profile_projects(profile_id, db_session)
    
    cv_text = _format_cv_text(
        basic_info=basic_info,
        summary=summary,
        skills=skills,
        experiences=experiences,
        projects=projects,
        language=language,
    )
    
    file_path = f"cv/{profile_id}/cv_{language}.{format}"
    file_url = await file_storage.save_file(
        content=cv_text.encode("utf-8"),
        file_path=file_path,
        content_type="text/plain" if format == "txt" else "application/pdf",
    )
    
    logger.info(f"Generated CV for profile {profile_id}: {file_url}")
    return file_url


async def get_cv_download_link(
    profile_id: int,
    file_storage: FileStorage,
    format: str = "txt",
    language: str = "en",
) -> Optional[str]:
    """
    Get download link for existing CV file.
    
    If CV doesn't exist, returns None.
    
    Args:
        profile_id: Profile identifier
        file_storage: File storage instance
        format: File format ("txt" or "pdf")
        language: Language for CV ("en" or "tr")
        
    Returns:
        URL or path to download the CV, or None if not found
    """
    file_path = f"cv/{profile_id}/cv_{language}.{format}"
    
    if await file_storage.file_exists(file_path):
        return await file_storage.get_file_url(file_path)
    
    return None



