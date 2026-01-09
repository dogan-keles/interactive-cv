"""
Profile API routes.

Endpoints for creating and managing profile data.
"""

from typing import List, Optional
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.infrastructure.database import get_db
from backend.data_access.knowledge_base.postgres import (
    Profile,
    Skill,
    Experience,
    Project,
)

router = APIRouter(
    prefix="/api/profile",
    tags=["profile"],
)


# ============================================================================
# Pydantic Schemas (Request/Response Models)
# ============================================================================

class SkillCreate(BaseModel):
    name: str
    category: str
    proficiency_level: str


class ExperienceCreate(BaseModel):
    company: str
    role: str
    start_date: date
    end_date: Optional[date] = None
    description: Optional[str] = None
    location: Optional[str] = None


class ProjectCreate(BaseModel):
    title: str
    description: Optional[str] = None
    tech_stack: Optional[List[str]] = None
    relevance_tags: Optional[List[str]] = None
    github_url: Optional[str] = None
    demo_url: Optional[str] = None


class ProfileCreate(BaseModel):
    name: str
    email: Optional[str] = None
    location: Optional[str] = None
    summary: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_username: Optional[str] = None
    skills: Optional[List[SkillCreate]] = None
    experiences: Optional[List[ExperienceCreate]] = None
    projects: Optional[List[ProjectCreate]] = None


class ProfileResponse(BaseModel):
    id: int
    name: str
    email: Optional[str]
    location: Optional[str]
    summary: Optional[str]
    linkedin_url: Optional[str]
    github_username: Optional[str]

    class Config:
        from_attributes = True


# ============================================================================
# API Endpoints
# ============================================================================

@router.post("", response_model=ProfileResponse, status_code=201)
def create_profile(
    profile_data: ProfileCreate,
    db: Session = Depends(get_db),
):
    """
    Create a new profile with skills, experiences, and projects.
    
    Args:
        profile_data: Profile creation data
        db: Database session
        
    Returns:
        Created profile
    """
    try:
        # Create profile
        profile = Profile(
            name=profile_data.name,
            email=profile_data.email,
            location=profile_data.location,
            summary=profile_data.summary,
            linkedin_url=profile_data.linkedin_url,
            github_username=profile_data.github_username,
        )
        
        db.add(profile)
        db.flush()  # Get profile.id without committing
        
        # Add skills
        if profile_data.skills:
            for skill_data in profile_data.skills:
                skill = Skill(
                    profile_id=profile.id,
                    name=skill_data.name,
                    category=skill_data.category,
                    proficiency_level=skill_data.proficiency_level,
                )
                db.add(skill)
        
        # Add experiences
        if profile_data.experiences:
            for exp_data in profile_data.experiences:
                experience = Experience(
                    profile_id=profile.id,
                    company=exp_data.company,
                    role=exp_data.role,
                    start_date=exp_data.start_date,
                    end_date=exp_data.end_date,
                    description=exp_data.description,
                    location=exp_data.location,
                )
                db.add(experience)
        
        # Add projects
        if profile_data.projects:
            for proj_data in profile_data.projects:
                project = Project(
                    profile_id=profile.id,
                    title=proj_data.title,
                    description=proj_data.description,
                    tech_stack=proj_data.tech_stack,
                    relevance_tags=proj_data.relevance_tags,
                    github_url=proj_data.github_url,
                    demo_url=proj_data.demo_url,
                )
                db.add(project)
        
        db.commit()
        db.refresh(profile)
        
        return profile
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create profile: {str(e)}"
        )


@router.get("/{profile_id}", response_model=ProfileResponse)
def get_profile(
    profile_id: int,
    db: Session = Depends(get_db),
):
    """
    Get profile by ID.
    
    Args:
        profile_id: Profile ID
        db: Database session
        
    Returns:
        Profile data
    """
    profile = db.query(Profile).filter(Profile.id == profile_id).first()
    
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    return profile


@router.get("/{profile_id}/full")
def get_full_profile(
    profile_id: int,
    db: Session = Depends(get_db),
):
    """
    Get complete profile data including skills, experiences, and projects.
    
    Args:
        profile_id: Profile ID
        db: Database session
        
    Returns:
        Complete profile data
    """
    profile = db.query(Profile).filter(Profile.id == profile_id).first()
    
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    # Get related data
    skills = db.query(Skill).filter(Skill.profile_id == profile_id).all()
    experiences = db.query(Experience).filter(
        Experience.profile_id == profile_id
    ).order_by(Experience.start_date.desc()).all()
    projects = db.query(Project).filter(Project.profile_id == profile_id).all()
    
    return {
        "profile": {
            "id": profile.id,
            "name": profile.name,
            "email": profile.email,
            "location": profile.location,
            "summary": profile.summary,
            "linkedin_url": profile.linkedin_url,
            "github_username": profile.github_username,
        },
        "skills": [
            {
                "id": s.id,
                "name": s.name,
                "category": s.category,
                "proficiency_level": s.proficiency_level,
            }
            for s in skills
        ],
        "experiences": [
            {
                "id": e.id,
                "company": e.company,
                "role": e.role,
                "start_date": e.start_date.isoformat(),
                "end_date": e.end_date.isoformat() if e.end_date else None,
                "description": e.description,
                "location": e.location,
            }
            for e in experiences
        ],
        "projects": [
            {
                "id": p.id,
                "title": p.title,
                "description": p.description,
                "tech_stack": p.tech_stack,
                "relevance_tags": p.relevance_tags,
                "github_url": p.github_url,
                "demo_url": p.demo_url,
            }
            for p in projects
        ],
    }


@router.get("")
def list_profiles(
    db: Session = Depends(get_db),
):
    """
    List all profiles.
    
    Args:
        db: Database session
        
    Returns:
        List of profiles
    """
    profiles = db.query(Profile).all()
    
    return {
        "profiles": [
            {
                "id": p.id,
                "name": p.name,
                "email": p.email,
            }
            for p in profiles
        ]
    }