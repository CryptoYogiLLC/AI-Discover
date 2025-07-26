"""Project management endpoints"""

from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from structlog import get_logger

from app.core.database import get_db
from app.api.v1.endpoints.auth import get_current_user
from app.models.user import User, UserRole
from app.models.project import Project, ProjectMember
from app.schemas.project import (
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    ProjectListResponse,
    ProjectMemberCreate,
    ProjectMemberUpdate,
    ProjectMemberResponse,
)

logger = get_logger()
router = APIRouter()


async def get_project_or_404(
    project_id: UUID,
    db: AsyncSession,
    current_user: User,
    required_permission: Optional[str] = None,
) -> Project:
    """Get project by ID with permission check"""
    # Get project with members
    result = await db.execute(
        select(Project)
        .options(
            selectinload(Project.members).selectinload(ProjectMember.user),
            selectinload(Project.created_by_user),
        )
        .where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )

    # Check permissions
    if current_user.role != UserRole.ADMIN:
        # Check if user is a member
        member = next(
            (m for m in project.members if m.user_id == current_user.id), None
        )

        if not member:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this project",
            )

        # Check specific permission if required
        if required_permission:
            if required_permission == "admin" and member.role != "admin":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Admin permission required for this project",
                )
            elif required_permission == "collaborator" and member.role == "viewer":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Collaborator permission required for this project",
                )

    return project


@router.get("/", response_model=ProjectListResponse)
async def list_projects(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List projects accessible to current user

    - Admins see all projects
    - Other users see only projects they're members of
    """
    # Base query
    query = select(Project).options(
        selectinload(Project.created_by_user),
        selectinload(Project.members),
        selectinload(Project.assessments),
    )

    # Apply access control
    if current_user.role != UserRole.ADMIN:
        # Only show projects where user is a member
        query = query.join(ProjectMember).where(
            ProjectMember.user_id == current_user.id
        )

    # Apply search
    if search:
        query = query.where(Project.name.ilike(f"%{search}%"))

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)

    # Apply pagination
    query = query.offset((page - 1) * size).limit(size)

    # Execute query
    result = await db.execute(query)
    projects = result.scalars().all()

    # Format response
    project_responses = []
    for project in projects:
        response = ProjectResponse(
            **project.__dict__,
            created_by_username=(
                project.created_by_user.username if project.created_by_user else None
            ),
            member_count=len(project.members),
            assessment_count=len(project.assessments),
        )
        project_responses.append(response)

    return ProjectListResponse(
        projects=project_responses, total=total or 0, page=page, size=size
    )


@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_data: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create new project

    The creating user automatically becomes a project admin.
    """
    # Create project
    project = Project(**project_data.model_dump(), created_by=current_user.id)
    db.add(project)
    await db.flush()

    # Add creator as admin member
    member = ProjectMember(project_id=project.id, user_id=current_user.id, role="admin")
    db.add(member)

    await db.commit()
    await db.refresh(project)

    # Load relationships
    await db.execute(
        select(Project)
        .options(selectinload(Project.created_by_user), selectinload(Project.members))
        .where(Project.id == project.id)
    )

    logger.info(
        "Project created", project_id=str(project.id), user_id=str(current_user.id)
    )

    return ProjectResponse(
        **project.__dict__,
        created_by_username=current_user.username,
        member_count=1,
        assessment_count=0,
    )


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get project details"""
    project = await get_project_or_404(project_id, db, current_user)

    # Get member details
    member_responses = []
    for member in project.members:
        member_resp = ProjectMemberResponse(
            **member.__dict__,
            username=member.user.username if member.user else None,
            email=member.user.email if member.user else None,
            full_name=member.user.full_name if member.user else None,
        )
        member_responses.append(member_resp)

    return ProjectResponse(
        **project.__dict__,
        created_by_username=(
            project.created_by_user.username if project.created_by_user else None
        ),
        member_count=len(project.members),
        assessment_count=(
            len(project.assessments) if hasattr(project, "assessments") else 0
        ),
        members=member_responses,
    )


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: UUID,
    project_update: ProjectUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update project

    Requires project admin or collaborator permission.
    """
    project = await get_project_or_404(project_id, db, current_user, "collaborator")

    # Update fields
    update_data = project_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(project, field, value)

    await db.commit()
    await db.refresh(project)

    logger.info(
        "Project updated", project_id=str(project_id), user_id=str(current_user.id)
    )

    return ProjectResponse(
        **project.__dict__,
        created_by_username=(
            project.created_by_user.username if project.created_by_user else None
        ),
        member_count=len(project.members),
        assessment_count=(
            len(project.assessments) if hasattr(project, "assessments") else 0
        ),
    )


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete project

    Requires project admin permission or system admin role.
    """
    project = await get_project_or_404(project_id, db, current_user, "admin")

    await db.delete(project)
    await db.commit()

    logger.info(
        "Project deleted", project_id=str(project_id), user_id=str(current_user.id)
    )


@router.post(
    "/{project_id}/members",
    response_model=ProjectMemberResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_project_member(
    project_id: UUID,
    member_data: ProjectMemberCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Add member to project

    Requires project admin permission.
    """
    project = await get_project_or_404(project_id, db, current_user, "admin")

    # Check if user exists
    result = await db.execute(select(User).where(User.id == member_data.user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    # Check if already a member
    existing_member = next(
        (m for m in project.members if m.user_id == member_data.user_id), None
    )

    if existing_member:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User is already a member of this project",
        )

    # Add member
    member = ProjectMember(
        project_id=project_id, user_id=member_data.user_id, role=member_data.role
    )
    db.add(member)
    await db.commit()
    await db.refresh(member)

    logger.info(
        "Member added to project",
        project_id=str(project_id),
        user_id=str(member_data.user_id),
        role=member_data.role,
    )

    return ProjectMemberResponse(
        **member.__dict__,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
    )


@router.put("/{project_id}/members/{user_id}", response_model=ProjectMemberResponse)
async def update_project_member(
    project_id: UUID,
    user_id: UUID,
    member_update: ProjectMemberUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update project member role

    Requires project admin permission.
    """
    project = await get_project_or_404(project_id, db, current_user, "admin")

    # Find member
    member = next((m for m in project.members if m.user_id == user_id), None)

    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Member not found in project"
        )

    # Prevent last admin from changing role
    if member.role == "admin" and member_update.role != "admin":
        admin_count = sum(1 for m in project.members if m.role == "admin")
        if admin_count == 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot remove last admin from project",
            )

    # Update role
    member.role = member_update.role
    await db.commit()
    await db.refresh(member)

    # Get user info
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    logger.info(
        "Member role updated",
        project_id=str(project_id),
        user_id=str(user_id),
        new_role=member_update.role,
    )

    return ProjectMemberResponse(
        **member.__dict__,
        username=user.username if user else None,
        email=user.email if user else None,
        full_name=user.full_name if user else None,
    )


@router.delete(
    "/{project_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def remove_project_member(
    project_id: UUID,
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Remove member from project

    Requires project admin permission.
    Users can also remove themselves from a project.
    """
    # Allow users to remove themselves
    required_permission = None if user_id == current_user.id else "admin"
    project = await get_project_or_404(
        project_id, db, current_user, required_permission
    )

    # Find member
    member = next((m for m in project.members if m.user_id == user_id), None)

    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Member not found in project"
        )

    # Prevent last admin from being removed
    if member.role == "admin":
        admin_count = sum(1 for m in project.members if m.role == "admin")
        if admin_count == 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot remove last admin from project",
            )

    # Remove member
    await db.delete(member)
    await db.commit()

    logger.info(
        "Member removed from project",
        project_id=str(project_id),
        user_id=str(user_id),
        removed_by=str(current_user.id),
    )
