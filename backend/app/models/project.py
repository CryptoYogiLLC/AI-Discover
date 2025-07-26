"""Project model for grouping application assessments"""

from sqlalchemy import Column, String, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.core.database import Base


class Project(Base):
    """Project database model for organizing application assessments"""

    __tablename__ = "projects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    organization = Column(String(255))
    department = Column(String(255))

    # Metadata
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    created_by_user = relationship(
        "User", back_populates="created_projects", foreign_keys=[created_by]
    )
    members = relationship(
        "ProjectMember", back_populates="project", cascade="all, delete-orphan"
    )
    assessments = relationship(
        "ApplicationAssessment", back_populates="project", cascade="all, delete-orphan"
    )


class ProjectMember(Base):
    """Association table for project members with roles"""

    __tablename__ = "project_members"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    role = Column(String(50), default="viewer")  # admin, collaborator, viewer
    joined_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    project = relationship("Project", back_populates="members")
    user = relationship("User", back_populates="project_memberships")
