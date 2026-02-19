"""
PostgreSQL database models for profile data.
"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Date,
    ForeignKey,
    JSON,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Profile(Base):
    """Core profile entity with basic information."""
    __tablename__ = "profiles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=True)
    location = Column(String(255), nullable=True)
    summary = Column(Text, nullable=True)
    linkedin_url = Column(String(500), nullable=True)
    github_username = Column(String(100), nullable=True)

    skills = relationship("Skill", back_populates="profile", cascade="all, delete-orphan")
    experiences = relationship("Experience", back_populates="profile", cascade="all, delete-orphan")
    projects = relationship("Project", back_populates="profile", cascade="all, delete-orphan")


class Skill(Base):
    """Technical or professional skill."""
    __tablename__ = "skills"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    category = Column(String(50), nullable=False)
    proficiency_level = Column(String(20), nullable=False)

    profile = relationship("Profile", back_populates="skills")


class Experience(Base):
    """Work experience or professional position."""
    __tablename__ = "experiences"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False)
    company = Column(String(255), nullable=False)
    role = Column(String(255), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)
    description = Column(Text, nullable=True)
    location = Column(String(255), nullable=True)

    profile = relationship("Profile", back_populates="experiences")


class Project(Base):
    """Project or portfolio item."""
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    tech_stack = Column(JSON, nullable=True)
    relevance_tags = Column(JSON, nullable=True)
    github_url = Column(String(500), nullable=True)
    demo_url = Column(String(500), nullable=True)

    profile = relationship("Profile", back_populates="projects")  # ✅ FIX: "Project" → "Profile"