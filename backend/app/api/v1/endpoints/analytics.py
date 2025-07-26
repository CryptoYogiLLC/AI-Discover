"""Analytics endpoints for assessment data"""

from typing import Optional, Dict, List
from uuid import UUID
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from structlog import get_logger

from app.core.database import get_db
from app.api.v1.endpoints.auth import get_current_user
from app.api.v1.endpoints.projects import get_project_or_404
from app.models.user import User, UserRole
from app.models.project import Project, ProjectMember
from app.models.assessment import ApplicationAssessment
from app.schemas.analytics import (
    ProjectAnalytics,
    AssessmentAnalyticsSummary,
    FieldCompletionMetrics,
    TimeMetrics,
    DataQualityMetrics,
)

logger = get_logger()
router = APIRouter()


@router.get("/projects/{project_id}/analytics", response_model=ProjectAnalytics)
async def get_project_analytics(
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get comprehensive analytics for a project

    Includes completion rates, recommendation distribution, and progress metrics.
    """
    # Check project access
    project = await get_project_or_404(project_id, db, current_user)

    # Get all assessments for the project
    result = await db.execute(
        select(ApplicationAssessment)
        .where(ApplicationAssessment.project_id == project_id)
        .options(selectinload(ApplicationAssessment.assessed_by_user))
    )
    assessments = result.scalars().all()

    if not assessments:
        return ProjectAnalytics(
            project_id=project_id,
            project_name=project.name,
            total_assessments=0,
            completed_assessments=0,
            in_progress_assessments=0,
            average_completion_rate=0,
            recommendation_distribution={},
            criticality_distribution={},
            average_scores={},
            top_incomplete_fields=[],
            time_metrics=TimeMetrics(
                average_time_to_complete=0,
                last_activity=None,
                assessments_last_week=0,
                assessments_last_month=0,
            ),
        )

    # Calculate metrics
    total_assessments = len(assessments)
    completed_assessments = 0
    in_progress_assessments = 0

    # Recommendation and criticality distribution
    recommendation_dist = {}
    criticality_dist = {}

    # Score aggregation
    risk_scores = []
    debt_scores = []
    quality_scores = []
    experience_scores = []

    # Field completion tracking
    field_completion_counts = {}

    # Time metrics
    now = datetime.now(timezone.utc)
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)
    assessments_last_week = 0
    assessments_last_month = 0
    last_activity = None

    for assessment in assessments:
        # Check completion status
        completion_rate = calculate_completion_rate(assessment)
        if completion_rate >= 90:  # Consider 90% as completed
            completed_assessments += 1
        else:
            in_progress_assessments += 1

        # Recommendation distribution
        if assessment.recommendation:
            rec = assessment.recommendation.value
            recommendation_dist[rec] = recommendation_dist.get(rec, 0) + 1

        # Criticality distribution
        if assessment.business_criticality:
            crit = assessment.business_criticality
            criticality_dist[crit] = criticality_dist.get(crit, 0) + 1

        # Collect scores
        if assessment.migration_risk_score:
            risk_scores.append(assessment.migration_risk_score)
        if assessment.technical_debt_score:
            debt_scores.append(assessment.technical_debt_score)
        if assessment.code_quality_score:
            quality_scores.append(assessment.code_quality_score)
        if assessment.team_cloud_experience_score:
            experience_scores.append(assessment.team_cloud_experience_score)

        # Track field completion
        track_field_completion(assessment, field_completion_counts)

        # Time metrics
        if assessment.last_updated:
            if not last_activity or assessment.last_updated > last_activity:
                last_activity = assessment.last_updated

            if assessment.last_updated >= week_ago:
                assessments_last_week += 1
            if assessment.last_updated >= month_ago:
                assessments_last_month += 1

    # Calculate averages
    average_scores = {
        "risk_score": sum(risk_scores) / len(risk_scores) if risk_scores else 0,
        "technical_debt": sum(debt_scores) / len(debt_scores) if debt_scores else 0,
        "code_quality": (
            sum(quality_scores) / len(quality_scores) if quality_scores else 0
        ),
        "team_experience": (
            sum(experience_scores) / len(experience_scores) if experience_scores else 0
        ),
    }

    # Find top incomplete fields
    incomplete_fields = sorted(
        [
            (field, count)
            for field, count in field_completion_counts.items()
            if count < total_assessments
        ],
        key=lambda x: x[1],
    )
    top_incomplete_fields = [
        {"field": field, "completion_rate": (count / total_assessments * 100)}
        for field, count in incomplete_fields[:10]
    ]

    # Calculate average completion rate
    total_completion = sum(calculate_completion_rate(a) for a in assessments)
    average_completion_rate = (
        total_completion / total_assessments if total_assessments > 0 else 0
    )

    return ProjectAnalytics(
        project_id=project_id,
        project_name=project.name,
        total_assessments=total_assessments,
        completed_assessments=completed_assessments,
        in_progress_assessments=in_progress_assessments,
        average_completion_rate=average_completion_rate,
        recommendation_distribution=recommendation_dist,
        criticality_distribution=criticality_dist,
        average_scores=average_scores,
        top_incomplete_fields=top_incomplete_fields,
        time_metrics=TimeMetrics(
            average_time_to_complete=0,  # Would need to track start time to calculate
            last_activity=last_activity,
            assessments_last_week=assessments_last_week,
            assessments_last_month=assessments_last_month,
        ),
    )


@router.get("/assessments/analytics/summary", response_model=AssessmentAnalyticsSummary)
async def get_assessment_analytics_summary(
    project_id: Optional[UUID] = None,
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get analytics summary for assessments

    Can be filtered by project and time period.
    """
    # Base query
    query = select(ApplicationAssessment)

    # Apply filters
    if project_id:
        await get_project_or_404(project_id, db, current_user)
        query = query.where(ApplicationAssessment.project_id == project_id)
    else:
        # Get accessible projects
        if current_user.role != UserRole.ADMIN:
            project_query = (
                select(Project.id)
                .join(ProjectMember)
                .where(ProjectMember.user_id == current_user.id)
            )
            accessible_projects = await db.execute(project_query)
            project_ids = [p[0] for p in accessible_projects]

            if not project_ids:
                return AssessmentAnalyticsSummary(
                    total_assessments=0,
                    assessments_by_status={},
                    assessments_by_recommendation={},
                    assessments_by_criticality={},
                    field_completion_metrics=FieldCompletionMetrics(
                        most_completed_fields=[],
                        least_completed_fields=[],
                        average_fields_completed=0,
                    ),
                    data_quality_metrics=DataQualityMetrics(
                        assessments_with_ai_recommendations=0,
                        assessments_validated=0,
                        average_data_quality_score=0,
                    ),
                    time_period_days=days,
                )

            query = query.where(ApplicationAssessment.project_id.in_(project_ids))

    # Apply time filter
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
    query = query.where(ApplicationAssessment.last_updated >= cutoff_date)

    # Execute query
    result = await db.execute(query)
    assessments = result.scalars().all()

    # Calculate metrics
    total_assessments = len(assessments)

    # Status distribution
    status_dist = {
        "completed": 0,
        "in_progress": 0,
        "not_started": 0,
    }

    # Recommendation distribution
    recommendation_dist = {}

    # Criticality distribution
    criticality_dist = {}

    # Field completion tracking
    field_completion_totals = {}
    field_counts = {}

    # Data quality metrics
    assessments_with_recommendations = 0
    assessments_validated = 0
    quality_scores = []

    for assessment in assessments:
        # Status
        completion_rate = calculate_completion_rate(assessment)
        if completion_rate >= 90:
            status_dist["completed"] += 1
        elif completion_rate > 10:
            status_dist["in_progress"] += 1
        else:
            status_dist["not_started"] += 1

        # Recommendations
        if assessment.recommendation:
            rec = assessment.recommendation.value
            recommendation_dist[rec] = recommendation_dist.get(rec, 0) + 1
            assessments_with_recommendations += 1

        # Criticality
        if assessment.business_criticality:
            crit = assessment.business_criticality
            criticality_dist[crit] = criticality_dist.get(crit, 0) + 1

        # Field completion
        for field in get_assessment_fields():
            if field not in field_counts:
                field_counts[field] = 0
                field_completion_totals[field] = 0

            field_counts[field] += 1
            if is_field_completed(assessment, field):
                field_completion_totals[field] += 1

        # Data quality
        quality_score = calculate_data_quality_score(assessment)
        quality_scores.append(quality_score)

        # Check if validated (has all critical fields)
        if has_critical_fields_completed(assessment):
            assessments_validated += 1

    # Calculate field completion rates
    field_completion_rates = [
        {
            "field": field,
            "completion_rate": (
                field_completion_totals[field] / field_counts[field] * 100
            ),
        }
        for field in field_counts
    ]

    # Sort for most/least completed
    field_completion_rates.sort(key=lambda x: x["completion_rate"], reverse=True)
    most_completed = field_completion_rates[:10]
    least_completed = field_completion_rates[-10:]

    # Calculate average fields completed
    total_possible_fields = len(get_assessment_fields()) * total_assessments
    total_completed_fields = sum(count_completed_fields(a) for a in assessments)
    average_fields_completed = (
        (total_completed_fields / total_possible_fields * 100)
        if total_possible_fields > 0
        else 0
    )

    return AssessmentAnalyticsSummary(
        total_assessments=total_assessments,
        assessments_by_status=status_dist,
        assessments_by_recommendation=recommendation_dist,
        assessments_by_criticality=criticality_dist,
        field_completion_metrics=FieldCompletionMetrics(
            most_completed_fields=most_completed,
            least_completed_fields=least_completed,
            average_fields_completed=average_fields_completed,
        ),
        data_quality_metrics=DataQualityMetrics(
            assessments_with_ai_recommendations=assessments_with_recommendations,
            assessments_validated=assessments_validated,
            average_data_quality_score=(
                sum(quality_scores) / len(quality_scores) if quality_scores else 0
            ),
        ),
        time_period_days=days,
    )


def calculate_completion_rate(assessment: ApplicationAssessment) -> float:
    """Calculate completion percentage for an assessment"""
    fields = get_assessment_fields()
    completed = sum(1 for field in fields if is_field_completed(assessment, field))
    return (completed / len(fields) * 100) if fields else 0


def count_completed_fields(assessment: ApplicationAssessment) -> int:
    """Count number of completed fields in an assessment"""
    fields = get_assessment_fields()
    return sum(1 for field in fields if is_field_completed(assessment, field))


def is_field_completed(assessment: ApplicationAssessment, field_name: str) -> bool:
    """Check if a field is completed"""
    value = getattr(assessment, field_name, None)

    if value is None:
        return False

    if isinstance(value, bool):
        return True  # Boolean fields are always considered complete

    if isinstance(value, (list, dict)):
        return bool(value)  # Check if not empty

    if isinstance(value, str):
        return bool(value.strip())  # Check if not empty string

    return True  # Other types (numbers, dates, etc.)


def track_field_completion(
    assessment: ApplicationAssessment, completion_counts: Dict[str, int]
) -> None:
    """Track field completion for analytics"""
    for field in get_assessment_fields():
        if is_field_completed(assessment, field):
            completion_counts[field] = completion_counts.get(field, 0) + 1


def calculate_data_quality_score(assessment: ApplicationAssessment) -> float:
    """Calculate data quality score for an assessment (0-100)"""
    score = 0
    max_score = 100

    # Completion rate (40 points)
    completion_rate = calculate_completion_rate(assessment)
    score += completion_rate * 0.4

    # Has recommendation (20 points)
    if assessment.recommendation:
        score += 20

    # Critical fields completed (20 points)
    critical_fields = [
        "application_name",
        "business_criticality",
        "architecture_type",
        "technical_debt_score",
        "migration_risk_score",
    ]
    critical_completed = sum(
        1 for field in critical_fields if is_field_completed(assessment, field)
    )
    score += (critical_completed / len(critical_fields)) * 20

    # Has financial data (10 points)
    financial_fields = [
        "current_licensing_cost_annual",
        "expected_cost_savings_percent",
        "expected_roi_months",
    ]
    financial_completed = sum(
        1 for field in financial_fields if is_field_completed(assessment, field)
    )
    if financial_completed > 0:
        score += 10

    # Has technical assessment (10 points)
    technical_fields = [
        "code_quality_score",
        "containerization_ready",
        "cloud_native_services_used",
    ]
    technical_completed = sum(
        1 for field in technical_fields if is_field_completed(assessment, field)
    )
    if technical_completed >= 2:
        score += 10

    return min(score, max_score)


def has_critical_fields_completed(assessment: ApplicationAssessment) -> bool:
    """Check if all critical fields are completed"""
    critical_fields = [
        "application_name",
        "business_criticality",
        "architecture_type",
        "technical_debt_score",
        "migration_risk_score",
    ]

    return all(is_field_completed(assessment, field) for field in critical_fields)


def get_assessment_fields() -> List[str]:
    """Get all assessment field names"""
    return [
        "application_name",
        "application_description",
        "business_owner",
        "technical_owner",
        "business_criticality",
        "revenue_impact",
        "user_count",
        "architecture_type",
        "technology_stack",
        "programming_languages",
        "server_count",
        "database_types",
        "storage_requirements_gb",
        "integration_count",
        "integration_types",
        "external_dependencies",
        "peak_load_users",
        "response_time_sla_ms",
        "availability_sla_percent",
        "compliance_requirements",
        "data_sensitivity",
        "authentication_methods",
        "technical_debt_score",
        "code_quality_score",
        "documentation_quality",
        "containerization_ready",
        "stateless_architecture",
        "cloud_native_services_used",
        "data_volume_gb",
        "transaction_volume_per_day",
        "batch_processing_required",
        "real_time_processing_required",
        "current_licensing_cost_annual",
        "infrastructure_cost_annual",
        "support_cost_annual",
        "migration_deadline",
        "blackout_windows",
        "business_peak_periods",
        "migration_risk_score",
        "business_impact_if_failed",
        "rollback_complexity",
        "team_cloud_experience_score",
        "training_required",
        "external_support_needed",
        "last_major_update",
        "expected_retirement_date",
        "modernization_planned",
        "data_residency_requirements",
        "data_retention_requirements",
        "backup_recovery_requirements",
        "bandwidth_requirements_mbps",
        "latency_requirements_ms",
        "vpn_requirements",
        "monitoring_tools",
        "logging_requirements",
        "support_hours",
        "preferred_migration_strategy",
        "acceptable_downtime_hours",
        "data_migration_approach",
        "success_metrics",
        "acceptance_criteria",
        "dependent_applications",
        "shared_infrastructure",
        "regulatory_constraints",
        "expected_cost_savings_percent",
        "expected_performance_improvement_percent",
        "expected_roi_months",
    ]
