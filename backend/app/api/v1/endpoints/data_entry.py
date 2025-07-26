"""Manual data entry endpoints for application assessments"""

from typing import Optional, Dict, List
from uuid import UUID
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.ext.asyncio import AsyncSession
from structlog import get_logger
import json

from app.core.database import get_db
from app.api.v1.endpoints.auth import get_current_user
from app.api.v1.endpoints.assessments import get_assessment_or_404
from app.models.user import User
from app.models.assessment import ApplicationAssessment
from app.schemas.data_entry import (
    FieldUpdate,
    FieldUpdateResponse,
    AIFieldSuggestion,
    ValidationResult,
    AssessmentProgress,
    FieldHistory,
)
from app.services.validation import AssessmentValidator
from app.services.ai_suggestions import AIFieldSuggestor

logger = get_logger()
router = APIRouter()


# Field versioning table (in-memory for now, should be moved to DB)
field_versions: Dict[str, List[FieldHistory]] = {}


@router.post("/{assessment_id}/fields", response_model=FieldUpdateResponse)
async def update_assessment_field(
    assessment_id: UUID,
    field_update: FieldUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update individual field in an assessment with versioning support

    Supports collaborative editing by tracking field-level changes.
    """
    # Get assessment with permission check
    assessment = await get_assessment_or_404(
        assessment_id, db, current_user, "collaborator"
    )

    # Validate field exists in the model
    if not hasattr(assessment, field_update.field_name):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Field '{field_update.field_name}' does not exist",
        )

    # Get current value
    old_value = getattr(assessment, field_update.field_name)

    # Store version history
    version_key = f"{assessment_id}:{field_update.field_name}"
    if version_key not in field_versions:
        field_versions[version_key] = []

    field_versions[version_key].append(
        FieldHistory(
            field_name=field_update.field_name,
            old_value=old_value,
            new_value=field_update.value,
            changed_by=current_user.id,
            changed_at=datetime.now(timezone.utc),
            change_reason=field_update.reason,
        )
    )

    # Update field based on type
    try:
        # Handle JSON fields
        if field_update.field_name in [
            "technology_stack",
            "programming_languages",
            "database_types",
            "integration_types",
            "external_dependencies",
            "compliance_requirements",
            "authentication_methods",
            "cloud_native_services_used",
            "blackout_windows",
            "business_peak_periods",
            "data_residency_requirements",
            "backup_recovery_requirements",
            "monitoring_tools",
            "logging_requirements",
            "success_metrics",
            "acceptance_criteria",
            "dependent_applications",
            "shared_infrastructure",
            "regulatory_constraints",
            "alternative_recommendations",
        ]:
            # These are JSON fields that should be lists or dicts
            if isinstance(field_update.value, str):
                # Try to parse as JSON if string provided
                try:
                    value = json.loads(field_update.value)
                except json.JSONDecodeError:
                    # If not valid JSON, treat as single item list
                    value = [field_update.value]
            else:
                value = field_update.value
        else:
            value = field_update.value

        setattr(assessment, field_update.field_name, value)
        assessment.last_updated = datetime.now(timezone.utc)

        await db.commit()
        await db.refresh(assessment)

        logger.info(
            "Assessment field updated",
            assessment_id=str(assessment_id),
            field=field_update.field_name,
            user_id=str(current_user.id),
        )

        return FieldUpdateResponse(
            field_name=field_update.field_name,
            value=value,
            updated_by=current_user.username,
            updated_at=assessment.last_updated,
            version=len(field_versions[version_key]),
        )

    except Exception as e:
        await db.rollback()
        logger.error(
            "Field update failed",
            assessment_id=str(assessment_id),
            field=field_update.field_name,
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update field: {str(e)}",
        )


@router.get("/{assessment_id}/suggestions", response_model=List[AIFieldSuggestion])
async def get_ai_suggestions(
    assessment_id: UUID,
    fields: Optional[List[str]] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get AI-powered suggestions for assessment fields

    Can request suggestions for specific fields or get suggestions
    for all incomplete fields.
    """
    # Get assessment
    assessment = await get_assessment_or_404(assessment_id, db, current_user)

    # Initialize AI suggestor (would be a real service in production)
    suggestor = AIFieldSuggestor()

    # Get suggestions
    suggestions = await suggestor.get_suggestions(assessment, fields)

    logger.info(
        "AI suggestions generated",
        assessment_id=str(assessment_id),
        field_count=len(suggestions),
        user_id=str(current_user.id),
    )

    return suggestions


@router.post("/{assessment_id}/validate", response_model=ValidationResult)
async def validate_assessment(
    assessment_id: UUID,
    fields: Optional[List[str]] = Body(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Validate assessment data against business rules

    Can validate specific fields or entire assessment.
    """
    # Get assessment
    assessment = await get_assessment_or_404(assessment_id, db, current_user)

    # Initialize validator
    validator = AssessmentValidator()

    # Validate assessment
    result = await validator.validate_assessment(assessment, fields)

    logger.info(
        "Assessment validated",
        assessment_id=str(assessment_id),
        is_valid=result.is_valid,
        error_count=len(result.errors),
        warning_count=len(result.warnings),
        user_id=str(current_user.id),
    )

    return result


@router.get("/{assessment_id}/progress", response_model=AssessmentProgress)
async def get_assessment_progress(
    assessment_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get completion progress for an assessment

    Returns overall progress and section-wise breakdown.
    """
    # Get assessment
    assessment = await get_assessment_or_404(assessment_id, db, current_user)

    # Calculate progress
    progress = calculate_assessment_progress(assessment)

    logger.info(
        "Assessment progress calculated",
        assessment_id=str(assessment_id),
        overall_progress=progress.overall_progress,
        user_id=str(current_user.id),
    )

    return progress


@router.get("/{assessment_id}/fields/{field_name}/history")
async def get_field_history(
    assessment_id: UUID,
    field_name: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get version history for a specific field

    Useful for tracking changes in collaborative editing.
    """
    # Check assessment access
    await get_assessment_or_404(assessment_id, db, current_user)

    # Get field history
    version_key = f"{assessment_id}:{field_name}"
    history = field_versions.get(version_key, [])

    # Convert to response format
    history_response = []
    for entry in history:
        history_response.append(
            {
                "field_name": entry.field_name,
                "old_value": entry.old_value,
                "new_value": entry.new_value,
                "changed_by": str(entry.changed_by),
                "changed_at": entry.changed_at.isoformat(),
                "change_reason": entry.change_reason,
            }
        )

    return history_response


def calculate_assessment_progress(
    assessment: ApplicationAssessment,
) -> AssessmentProgress:
    """Calculate completion progress for an assessment"""

    # Define sections and their fields
    sections = {
        "basic_information": [
            "application_name",
            "application_description",
            "business_owner",
            "technical_owner",
        ],
        "business_criticality": [
            "business_criticality",
            "revenue_impact",
            "user_count",
        ],
        "technical_architecture": [
            "architecture_type",
            "technology_stack",
            "programming_languages",
        ],
        "infrastructure": [
            "server_count",
            "database_types",
            "storage_requirements_gb",
        ],
        "integration_complexity": [
            "integration_count",
            "integration_types",
            "external_dependencies",
        ],
        "performance": [
            "peak_load_users",
            "response_time_sla_ms",
            "availability_sla_percent",
        ],
        "compliance_security": [
            "compliance_requirements",
            "data_sensitivity",
            "authentication_methods",
        ],
        "current_state": [
            "technical_debt_score",
            "code_quality_score",
            "documentation_quality",
        ],
        "cloud_readiness": [
            "containerization_ready",
            "stateless_architecture",
            "cloud_native_services_used",
        ],
        "migration_complexity": [
            "data_volume_gb",
            "transaction_volume_per_day",
            "batch_processing_required",
            "real_time_processing_required",
        ],
        "costs": [
            "current_licensing_cost_annual",
            "infrastructure_cost_annual",
            "support_cost_annual",
        ],
        "timeline": [
            "migration_deadline",
            "blackout_windows",
            "business_peak_periods",
        ],
        "risk_assessment": [
            "migration_risk_score",
            "business_impact_if_failed",
            "rollback_complexity",
        ],
        "team_readiness": [
            "team_cloud_experience_score",
            "training_required",
            "external_support_needed",
        ],
        "lifecycle": [
            "last_major_update",
            "expected_retirement_date",
            "modernization_planned",
        ],
        "data_characteristics": [
            "data_residency_requirements",
            "data_retention_requirements",
            "backup_recovery_requirements",
        ],
        "network": [
            "bandwidth_requirements_mbps",
            "latency_requirements_ms",
            "vpn_requirements",
        ],
        "operational": [
            "monitoring_tools",
            "logging_requirements",
            "support_hours",
        ],
        "migration_approach": [
            "preferred_migration_strategy",
            "acceptable_downtime_hours",
            "data_migration_approach",
        ],
        "success_criteria": [
            "success_metrics",
            "acceptance_criteria",
        ],
        "dependencies": [
            "dependent_applications",
            "shared_infrastructure",
            "regulatory_constraints",
        ],
        "cost_benefit": [
            "expected_cost_savings_percent",
            "expected_performance_improvement_percent",
            "expected_roi_months",
        ],
    }

    # Calculate progress for each section
    section_progress = {}
    total_fields = 0
    completed_fields = 0

    for section_name, fields in sections.items():
        section_total = len(fields)
        section_completed = 0
        incomplete_fields = []

        for field in fields:
            total_fields += 1
            value = getattr(assessment, field, None)

            # Check if field is completed (not None and not empty)
            if value is not None:
                if isinstance(value, (list, dict)):
                    if value:  # Not empty list/dict
                        section_completed += 1
                        completed_fields += 1
                    else:
                        incomplete_fields.append(field)
                elif isinstance(value, bool):
                    # Boolean fields are always considered complete
                    section_completed += 1
                    completed_fields += 1
                elif isinstance(value, str):
                    if value.strip():  # Not empty string
                        section_completed += 1
                        completed_fields += 1
                    else:
                        incomplete_fields.append(field)
                else:
                    # Numeric and other types
                    section_completed += 1
                    completed_fields += 1
            else:
                incomplete_fields.append(field)

        section_progress[section_name] = {
            "total_fields": section_total,
            "completed_fields": section_completed,
            "progress_percentage": (
                (section_completed / section_total * 100) if section_total > 0 else 0
            ),
            "incomplete_fields": incomplete_fields,
        }

    # Calculate overall progress
    overall_progress = (
        (completed_fields / total_fields * 100) if total_fields > 0 else 0
    )

    # Identify most incomplete sections
    incomplete_sections = sorted(
        [
            (name, data["progress_percentage"])
            for name, data in section_progress.items()
            if data["progress_percentage"] < 100
        ],
        key=lambda x: x[1],
    )

    return AssessmentProgress(
        overall_progress=overall_progress,
        total_fields=total_fields,
        completed_fields=completed_fields,
        section_progress=section_progress,
        most_incomplete_sections=[s[0] for s in incomplete_sections[:5]],
        last_updated=assessment.last_updated,
    )
