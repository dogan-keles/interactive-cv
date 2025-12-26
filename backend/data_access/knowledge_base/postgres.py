"""
PostgreSQL database models for the interactive-cv knowledge base.

Stores structured profile data including skills, experience, and projects.
"""

from datetime import date
from typing import Optional

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Date,
    ForeignKey,
    JSON,
    Enum as SQLEnum,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Profile(Base):
    """
    Core profile entity representing the candidate's basic information.
    
    Stores personal and professional summary data. Acts as the root entity
    for related skills, experiences, and projects.
    """
    __tablename__ = "profiles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=True)
    location = Column(String(255), nullable=True)
    summary = Column(Text, nullable=True)
    linkedin_url = Column(String(500), nullable=True)
    github_username = Column(String(100), nullable=True)

    # Relationships
    skills = relationship("Skill", back_populates="profile", cascade="all, delete-orphan")
    experiences = relationship("Experience", back_populates="profile", cascade="all, delete-orphan")
    projects = relationship("Project", back_populates="profile", cascade="all, delete-orphan")


class Skill(Base):
    """
    Represents a technical or professional skill.
    
    Skills are categorized and have a proficiency level to indicate
    the candidate's expertise in that area.
    """
    __tablename__ = "skills"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    category = Column(String(50), nullable=False)  # e.g., "Programming Language", "Framework", "Tool"
    proficiency_level = Column(String(20), nullable=False)  # e.g., "Beginner", "Intermediate", "Advanced", "Expert"

    # Relationship
    profile = relationship("Profile", back_populates="skills")


class Experience(Base):
    """
    Represents a work experience or professional position.
    
    Stores employment history with company, role, duration, and
    detailed description of responsibilities and achievements.
    """
    __tablename__ = "experiences"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False)
    company = Column(String(255), nullable=False)
    role = Column(String(255), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)  # None for current position
    description = Column(Text, nullable=True)
    location = Column(String(255), nullable=True)

    # Relationship
    profile = relationship("Profile", back_populates="experiences")


class Project(Base):
    """
    Represents a project or portfolio item.
    
    Stores project metadata including title, description, technology stack,
    and relevance tags for filtering and search purposes.
    """
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    tech_stack = Column(JSON, nullable=True)  # Array of technology names
    relevance_tags = Column(JSON, nullable=True)  # Array of tags for filtering
    github_url = Column(String(500), nullable=True)
    demo_url = Column(String(500), nullable=True)

    # Relationship
    profile = relationship("Profile", back_populates="projects")


