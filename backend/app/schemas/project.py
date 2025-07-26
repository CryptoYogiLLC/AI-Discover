"""Project schemas for request/response validation"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field
from uuid import UUID



class ProjectBase(BaseModel):
    """Base project schema"""

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    organization: Optional[str] = Field(None, max_length=255)
    department: Optional[str] = Field(None, max_length=255)


class ProjectCreate(ProjectBase):
    """Project creation schema"""

    pass


class ProjectUpdate(BaseModel):
    """Project update schema"""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    organization: Optional[str] = Field(None, max_length=255)
    department: Optional[str] = Field(None, max_length=255)


class ProjectMemberBase(BaseModel):
    """Base project member schema"""

    user_id: UUID
    role: str = "viewer"  # admin, collaborator, viewer


class ProjectMemberCreate(ProjectMemberBase):
    """Add member to project schema"""

    pass


class ProjectMemberUpdate(BaseModel):
    """Update project member schema"""

    role: str


class ProjectMemberResponse(ProjectMemberBase):
    """Project member response schema"""

    id: UUID
    project_id: UUID
    joined_at: datetime

    # User info
    username: Optional[str] = None
    email: Optional[str] = None
    full_name: Optional[str] = None

    class Config:
        from_attributes = True


class ProjectInDB(ProjectBase):
    """Project in database schema"""

    id: UUID
    created_by: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProjectResponse(ProjectInDB):
    """Project response schema"""

    created_by_username: Optional[str] = None
    member_count: int = 0
    assessment_count: int = 0
    members: Optional[List[ProjectMemberResponse]] = None


class ProjectListResponse(BaseModel):
    """Project list response schema"""

    projects: List[ProjectResponse]
    total: int
    page: int
    size: int
