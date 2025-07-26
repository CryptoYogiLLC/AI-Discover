"""Analytics schemas for assessment data analysis"""

from typing import Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from uuid import UUID


class TimeMetrics(BaseModel):
    """Time-based metrics for assessments"""

    average_time_to_complete: float = Field(
        ..., description="Average hours to complete assessment"
    )
    last_activity: Optional[datetime] = Field(
        None, description="Timestamp of last activity"
    )
    assessments_last_week: int = Field(
        ..., description="Number of assessments updated in last 7 days"
    )
    assessments_last_month: int = Field(
        ..., description="Number of assessments updated in last 30 days"
    )


class FieldMetric(BaseModel):
    """Metric for a single field"""

    field: str
    completion_rate: float = Field(..., ge=0, le=100)


class ProjectAnalytics(BaseModel):
    """Analytics for a specific project"""

    project_id: UUID
    project_name: str
    total_assessments: int
    completed_assessments: int
    in_progress_assessments: int
    average_completion_rate: float = Field(..., ge=0, le=100)
    recommendation_distribution: Dict[str, int]
    criticality_distribution: Dict[str, int]
    average_scores: Dict[str, float]
    top_incomplete_fields: List[FieldMetric]
    time_metrics: TimeMetrics


class FieldCompletionMetrics(BaseModel):
    """Metrics about field completion across assessments"""

    most_completed_fields: List[FieldMetric]
    least_completed_fields: List[FieldMetric]
    average_fields_completed: float = Field(..., ge=0, le=100)


class DataQualityMetrics(BaseModel):
    """Metrics about data quality"""

    assessments_with_ai_recommendations: int
    assessments_validated: int
    average_data_quality_score: float = Field(..., ge=0, le=100)


class AssessmentAnalyticsSummary(BaseModel):
    """Summary analytics for assessments"""

    total_assessments: int
    assessments_by_status: Dict[str, int]
    assessments_by_recommendation: Dict[str, int]
    assessments_by_criticality: Dict[str, int]
    field_completion_metrics: FieldCompletionMetrics
    data_quality_metrics: DataQualityMetrics
    time_period_days: int


class CompletionTrend(BaseModel):
    """Completion trend over time"""

    date: datetime
    completed_count: int
    in_progress_count: int
    completion_rate: float


class UserActivityMetrics(BaseModel):
    """Metrics about user activity"""

    user_id: UUID
    username: str
    assessments_created: int
    assessments_updated: int
    last_activity: Optional[datetime]
    average_completion_rate: float


class CostAnalytics(BaseModel):
    """Cost-related analytics"""

    total_current_annual_cost: float
    projected_annual_savings: float
    average_savings_percentage: float
    total_migration_investment: float
    average_roi_months: float
    applications_by_savings_range: Dict[str, int]


class RiskAnalytics(BaseModel):
    """Risk-related analytics"""

    high_risk_applications: int
    medium_risk_applications: int
    low_risk_applications: int
    average_risk_score: float
    risk_factors_distribution: Dict[str, int]
    applications_needing_mitigation: int


class CloudReadinessAnalytics(BaseModel):
    """Cloud readiness analytics"""

    cloud_ready_applications: int
    containerized_applications: int
    stateless_applications: int
    applications_using_cloud_services: int
    readiness_percentage: float
    blockers_distribution: Dict[str, int]
