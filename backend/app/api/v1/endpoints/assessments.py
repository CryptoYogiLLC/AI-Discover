"""Application Assessment endpoints"""

from typing import Optional
from uuid import UUID
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, func, or_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from structlog import get_logger

from app.core.database import get_db
from app.api.v1.endpoints.auth import get_current_user
from app.api.v1.endpoints.projects import get_project_or_404
from app.models.user import User, UserRole
from app.models.project import Project, ProjectMember
from app.models.assessment import ApplicationAssessment, MigrationRecommendation
from app.schemas.assessment import (
    ApplicationAssessmentCreate,
    ApplicationAssessmentUpdate,
    ApplicationAssessmentResponse,
    AssessmentListResponse,
    AssessmentSummary,
)

logger = get_logger()
router = APIRouter()


async def get_assessment_or_404(
    assessment_id: UUID,
    db: AsyncSession,
    current_user: User,
    required_permission: Optional[str] = None,
) -> ApplicationAssessment:
    """Get assessment by ID with permission check"""
    # Get assessment with project
    result = await db.execute(
        select(ApplicationAssessment)
        .options(
            selectinload(ApplicationAssessment.project).selectinload(Project.members),
            selectinload(ApplicationAssessment.assessed_by_user),
        )
        .where(ApplicationAssessment.id == assessment_id)
    )
    assessment = result.scalar_one_or_none()

    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found"
        )

    # Check project permissions
    await get_project_or_404(
        assessment.project_id, db, current_user, required_permission
    )

    return assessment


@router.get("/", response_model=AssessmentListResponse)
async def list_assessments(
    project_id: Optional[UUID] = None,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    recommendation: Optional[MigrationRecommendation] = None,
    criticality: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List assessments accessible to current user

    Can filter by project, recommendation, criticality, and search term.
    """
    # Base query
    query = select(ApplicationAssessment).options(
        selectinload(ApplicationAssessment.project),
        selectinload(ApplicationAssessment.assessed_by_user),
    )

    # Filter by project if specified
    if project_id:
        # Check project access
        await get_project_or_404(project_id, db, current_user)
        query = query.where(ApplicationAssessment.project_id == project_id)
    else:
        # Get all accessible projects
        if current_user.role != UserRole.ADMIN:
            # Get projects where user is a member
            project_query = (
                select(Project.id)
                .join(ProjectMember)
                .where(ProjectMember.user_id == current_user.id)
            )
            accessible_projects = await db.execute(project_query)
            project_ids = [p[0] for p in accessible_projects]

            if not project_ids:
                return AssessmentListResponse(
                    assessments=[], total=0, page=page, size=size
                )

            query = query.where(ApplicationAssessment.project_id.in_(project_ids))

    # Apply filters
    if search:
        query = query.where(
            or_(
                ApplicationAssessment.application_name.ilike(f"%{search}%"),
                ApplicationAssessment.application_description.ilike(f"%{search}%"),
            )
        )

    if recommendation:
        query = query.where(ApplicationAssessment.recommendation == recommendation)

    if criticality:
        query = query.where(ApplicationAssessment.business_criticality == criticality)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)

    # Apply pagination
    query = (
        query.offset((page - 1) * size)
        .limit(size)
        .order_by(ApplicationAssessment.assessment_date.desc())
    )

    # Execute query
    result = await db.execute(query)
    assessments = result.scalars().all()

    # Format response
    assessment_responses = []
    for assessment in assessments:
        response = ApplicationAssessmentResponse(
            **assessment.__dict__,
            project_name=assessment.project.name if assessment.project else None,
            assessed_by_username=(
                assessment.assessed_by_user.username
                if assessment.assessed_by_user
                else None
            ),
        )
        assessment_responses.append(response)

    return AssessmentListResponse(
        assessments=assessment_responses, total=total or 0, page=page, size=size
    )


@router.post(
    "/",
    response_model=ApplicationAssessmentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_assessment(
    assessment_data: ApplicationAssessmentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create new application assessment

    Requires collaborator permission on the project.
    """
    # Check project access
    project = await get_project_or_404(
        assessment_data.project_id, db, current_user, "collaborator"
    )

    # Create assessment
    assessment = ApplicationAssessment(
        **assessment_data.model_dump(),
        assessed_by=current_user.id,
        assessment_date=datetime.now(timezone.utc),
    )

    db.add(assessment)
    await db.commit()
    await db.refresh(assessment)

    logger.info(
        "Assessment created",
        assessment_id=str(assessment.id),
        project_id=str(assessment.project_id),
        user_id=str(current_user.id),
    )

    return ApplicationAssessmentResponse(
        **assessment.__dict__,
        project_name=project.name,
        assessed_by_username=current_user.username,
    )


@router.get("/summary", response_model=AssessmentSummary)
async def get_assessment_summary(
    project_id: Optional[UUID] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get assessment summary statistics

    Can be filtered by project.
    """
    # Base query
    query = select(ApplicationAssessment)

    # Filter by project if specified
    if project_id:
        await get_project_or_404(project_id, db, current_user)
        query = query.where(ApplicationAssessment.project_id == project_id)
    else:
        # Get all accessible projects
        if current_user.role != UserRole.ADMIN:
            project_query = (
                select(Project.id)
                .join(ProjectMember)
                .where(ProjectMember.user_id == current_user.id)
            )
            accessible_projects = await db.execute(project_query)
            project_ids = [p[0] for p in accessible_projects]

            if not project_ids:
                return AssessmentSummary(
                    total_assessments=0,
                    by_recommendation={},
                    by_criticality={},
                    average_risk_score=0,
                    average_technical_debt=0,
                    total_cost_savings_potential=0,
                )

            query = query.where(ApplicationAssessment.project_id.in_(project_ids))

    # Get assessments
    result = await db.execute(query)
    assessments = result.scalars().all()

    # Calculate summary
    total = len(assessments)

    by_recommendation = {}
    by_criticality = {}
    total_risk = 0
    total_debt = 0
    total_savings = 0
    risk_count = 0
    debt_count = 0

    for assessment in assessments:
        # Recommendation counts
        if assessment.recommendation:
            by_recommendation[assessment.recommendation.value] = (
                by_recommendation.get(assessment.recommendation.value, 0) + 1
            )

        # Criticality counts
        if assessment.business_criticality:
            by_criticality[assessment.business_criticality] = (
                by_criticality.get(assessment.business_criticality, 0) + 1
            )

        # Risk score average
        if assessment.migration_risk_score:
            total_risk += assessment.migration_risk_score
            risk_count += 1

        # Technical debt average
        if assessment.technical_debt_score:
            total_debt += assessment.technical_debt_score
            debt_count += 1

        # Cost savings
        if (
            assessment.expected_cost_savings_percent
            and assessment.current_licensing_cost_annual
        ):
            savings = (
                assessment.expected_cost_savings_percent / 100
            ) * assessment.current_licensing_cost_annual
            total_savings += savings

    return AssessmentSummary(
        total_assessments=total,
        by_recommendation=by_recommendation,
        by_criticality=by_criticality,
        average_risk_score=total_risk / risk_count if risk_count > 0 else 0,
        average_technical_debt=total_debt / debt_count if debt_count > 0 else 0,
        total_cost_savings_potential=total_savings,
    )


@router.get("/{assessment_id}", response_model=ApplicationAssessmentResponse)
async def get_assessment(
    assessment_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get assessment details"""
    assessment = await get_assessment_or_404(assessment_id, db, current_user)

    return ApplicationAssessmentResponse(
        **assessment.__dict__,
        project_name=assessment.project.name if assessment.project else None,
        assessed_by_username=(
            assessment.assessed_by_user.username
            if assessment.assessed_by_user
            else None
        ),
    )


@router.put("/{assessment_id}", response_model=ApplicationAssessmentResponse)
async def update_assessment(
    assessment_id: UUID,
    assessment_update: ApplicationAssessmentUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update application assessment

    Requires collaborator permission on the project.
    """
    assessment = await get_assessment_or_404(
        assessment_id, db, current_user, "collaborator"
    )

    # Update fields
    update_data = assessment_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(assessment, field, value)

    assessment.last_updated = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(assessment)

    # Reload with relationships
    assessment = await get_assessment_or_404(assessment_id, db, current_user)

    logger.info(
        "Assessment updated",
        assessment_id=str(assessment_id),
        user_id=str(current_user.id),
    )

    return ApplicationAssessmentResponse(
        **assessment.__dict__,
        project_name=assessment.project.name if assessment.project else None,
        assessed_by_username=(
            assessment.assessed_by_user.username
            if assessment.assessed_by_user
            else None
        ),
    )


@router.delete("/{assessment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_assessment(
    assessment_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete application assessment

    Requires admin permission on the project.
    """
    assessment = await get_assessment_or_404(assessment_id, db, current_user, "admin")

    await db.delete(assessment)
    await db.commit()

    logger.info(
        "Assessment deleted",
        assessment_id=str(assessment_id),
        user_id=str(current_user.id),
    )


@router.post("/{assessment_id}/analyze", response_model=ApplicationAssessmentResponse)
async def analyze_assessment(
    assessment_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Run AI analysis on assessment to generate 6R recommendation

    Requires collaborator permission on the project.
    """
    assessment = await get_assessment_or_404(
        assessment_id, db, current_user, "collaborator"
    )

    # TODO: Integrate with CrewAI service for analysis
    # For now, return a mock recommendation
    assessment.recommendation = MigrationRecommendation.REPLATFORM
    assessment.recommendation_score = 0.85
    assessment.recommendation_reasoning = (
        "Based on the assessment data, this application is a good candidate for replatforming. "
        "The application has moderate technical debt but good documentation. "
        "The architecture supports containerization with minimal changes."
    )
    assessment.alternative_recommendations = [
        {
            "recommendation": MigrationRecommendation.REFACTOR.value,
            "score": 0.72,
            "reasoning": "Refactoring could provide better long-term benefits but requires more investment.",
        },
        {
            "recommendation": MigrationRecommendation.REHOST.value,
            "score": 0.65,
            "reasoning": "Simple lift-and-shift is possible but won't leverage cloud-native features.",
        },
    ]

    assessment.last_updated = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(assessment)

    # Reload with relationships
    assessment = await get_assessment_or_404(assessment_id, db, current_user)

    logger.info(
        "Assessment analyzed",
        assessment_id=str(assessment_id),
        recommendation=assessment.recommendation.value,
        score=assessment.recommendation_score,
    )

    return ApplicationAssessmentResponse(
        **assessment.__dict__,
        project_name=assessment.project.name if assessment.project else None,
        assessed_by_username=(
            assessment.assessed_by_user.username
            if assessment.assessed_by_user
            else None
        ),
    )


@router.get("/export")
async def export_assessments(
    format: str = Query("csv", regex="^(csv|excel|json)$"),
    project_id: Optional[UUID] = None,
    recommendation: Optional[MigrationRecommendation] = None,
    criticality: Optional[str] = None,
    include_metadata: bool = Query(True),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Export assessments in various formats

    Can filter by project, recommendation, or criticality.

    Supported formats:
    - csv: Comma-separated values
    - excel: Excel workbook with multiple sheets
    - json: JSON format with metadata
    """
    from app.services.export import ExportService
    from fastapi.responses import StreamingResponse
    import io

    # Base query
    query = select(ApplicationAssessment).options(
        selectinload(ApplicationAssessment.project),
        selectinload(ApplicationAssessment.assessed_by_user),
    )

    # Apply filters
    if project_id:
        # Check project access
        await get_project_or_404(project_id, db, current_user)
        query = query.where(ApplicationAssessment.project_id == project_id)
    else:
        # Get all accessible projects
        if current_user.role != UserRole.ADMIN:
            # Get projects where user is a member
            project_query = (
                select(Project.id)
                .join(ProjectMember)
                .where(ProjectMember.user_id == current_user.id)
            )
            accessible_projects = await db.execute(project_query)
            project_ids = [p[0] for p in accessible_projects]

            if not project_ids:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="No assessments found",
                )

            query = query.where(ApplicationAssessment.project_id.in_(project_ids))

    if recommendation:
        query = query.where(ApplicationAssessment.recommendation == recommendation)

    if criticality:
        query = query.where(ApplicationAssessment.business_criticality == criticality)

    # Execute query
    result = await db.execute(query)
    assessments = result.scalars().all()

    if not assessments:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No assessments found matching criteria",
        )

    # Initialize export service
    export_service = ExportService()

    # Generate export based on format
    if format == "csv":
        content = await export_service.export_assessments_csv(
            assessments, include_metadata
        )
        media_type = "text/csv"
        filename = "assessments_export.csv"

    elif format == "excel":
        content = await export_service.export_assessments_excel(
            assessments, None, include_analytics=True
        )
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        filename = "assessments_export.xlsx"

    else:  # json
        content = await export_service.export_assessments_json(
            assessments, include_metadata
        )
        media_type = "application/json"
        filename = "assessments_export.json"

    logger.info(
        "Assessments exported",
        format=format,
        count=len(assessments),
        user_id=str(current_user.id),
    )

    # Return file response
    return StreamingResponse(
        io.BytesIO(content),
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
