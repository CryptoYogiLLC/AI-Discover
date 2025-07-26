"""Application Assessment schemas for request/response validation"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, field_validator
from uuid import UUID

from app.models.assessment import MigrationRecommendation


class ApplicationAssessmentBase(BaseModel):
    """Base application assessment schema"""
    # Basic Information
    application_name: str = Field(..., min_length=1, max_length=255)
    application_description: Optional[str] = None
    business_owner: Optional[str] = Field(None, max_length=255)
    technical_owner: Optional[str] = Field(None, max_length=255)
    
    # Business Criticality
    business_criticality: Optional[str] = Field(None, pattern="^(Critical|High|Medium|Low)$")
    revenue_impact: Optional[float] = Field(None, ge=0)
    user_count: Optional[int] = Field(None, ge=0)
    
    # Technical Architecture
    architecture_type: Optional[str] = None
    technology_stack: Optional[List[str]] = None
    programming_languages: Optional[List[str]] = None
    
    # Infrastructure Dependencies
    server_count: Optional[int] = Field(None, ge=0)
    database_types: Optional[List[str]] = None
    storage_requirements_gb: Optional[float] = Field(None, ge=0)
    
    # Integration Complexity
    integration_count: Optional[int] = Field(None, ge=0)
    integration_types: Optional[List[str]] = None
    external_dependencies: Optional[List[str]] = None
    
    # Performance Requirements
    peak_load_users: Optional[int] = Field(None, ge=0)
    response_time_sla_ms: Optional[int] = Field(None, ge=0)
    availability_sla_percent: Optional[float] = Field(None, ge=0, le=100)
    
    # Compliance and Security
    compliance_requirements: Optional[List[str]] = None
    data_sensitivity: Optional[str] = Field(None, pattern="^(Public|Internal|Confidential|Restricted)$")
    authentication_methods: Optional[List[str]] = None
    
    # Current State Assessment
    technical_debt_score: Optional[int] = Field(None, ge=1, le=10)
    code_quality_score: Optional[int] = Field(None, ge=1, le=10)
    documentation_quality: Optional[str] = Field(None, pattern="^(Excellent|Good|Fair|Poor)$")
    
    # Cloud Readiness
    containerization_ready: bool = False
    stateless_architecture: bool = False
    cloud_native_services_used: Optional[List[str]] = None
    
    # Migration Complexity Factors
    data_volume_gb: Optional[float] = Field(None, ge=0)
    transaction_volume_per_day: Optional[int] = Field(None, ge=0)
    batch_processing_required: bool = False
    real_time_processing_required: bool = False
    
    # Licensing and Costs
    current_licensing_cost_annual: Optional[float] = Field(None, ge=0)
    infrastructure_cost_annual: Optional[float] = Field(None, ge=0)
    support_cost_annual: Optional[float] = Field(None, ge=0)
    
    # Migration Timeline Constraints
    migration_deadline: Optional[datetime] = None
    blackout_windows: Optional[List[Dict[str, str]]] = None
    business_peak_periods: Optional[List[Dict[str, str]]] = None
    
    # Risk Assessment
    migration_risk_score: Optional[int] = Field(None, ge=1, le=10)
    business_impact_if_failed: Optional[str] = Field(None, pattern="^(Critical|High|Medium|Low)$")
    rollback_complexity: Optional[str] = Field(None, pattern="^(Simple|Moderate|Complex)$")
    
    # Team Readiness
    team_cloud_experience_score: Optional[int] = Field(None, ge=1, le=10)
    training_required: bool = True
    external_support_needed: bool = False
    
    # Application Lifecycle
    last_major_update: Optional[datetime] = None
    expected_retirement_date: Optional[datetime] = None
    modernization_planned: bool = False
    
    # Data Characteristics
    data_residency_requirements: Optional[List[str]] = None
    data_retention_requirements: Optional[str] = None
    backup_recovery_requirements: Optional[Dict[str, Any]] = None
    
    # Network Requirements
    bandwidth_requirements_mbps: Optional[float] = Field(None, ge=0)
    latency_requirements_ms: Optional[int] = Field(None, ge=0)
    vpn_requirements: bool = False
    
    # Operational Requirements
    monitoring_tools: Optional[List[str]] = None
    logging_requirements: Optional[Dict[str, Any]] = None
    support_hours: Optional[str] = None
    
    # Migration Approach Preferences
    preferred_migration_strategy: Optional[str] = None
    acceptable_downtime_hours: Optional[float] = Field(None, ge=0)
    data_migration_approach: Optional[str] = None
    
    # Success Criteria
    success_metrics: Optional[List[Dict[str, Any]]] = None
    acceptance_criteria: Optional[List[str]] = None
    
    # Dependencies and Constraints
    dependent_applications: Optional[List[str]] = None
    shared_infrastructure: Optional[List[str]] = None
    regulatory_constraints: Optional[List[str]] = None
    
    # Cost-Benefit Analysis
    expected_cost_savings_percent: Optional[float] = Field(None, ge=0, le=100)
    expected_performance_improvement_percent: Optional[float] = Field(None, ge=0)
    expected_roi_months: Optional[int] = Field(None, ge=0)
    
    # Notes
    notes: Optional[str] = None


class ApplicationAssessmentCreate(ApplicationAssessmentBase):
    """Application assessment creation schema"""
    project_id: UUID


class ApplicationAssessmentUpdate(ApplicationAssessmentBase):
    """Application assessment update schema"""
    application_name: Optional[str] = Field(None, min_length=1, max_length=255)


class ApplicationAssessmentInDB(ApplicationAssessmentBase):
    """Application assessment in database schema"""
    id: UUID
    project_id: UUID
    assessment_date: datetime
    assessed_by: Optional[UUID] = None
    last_updated: datetime
    
    # AI Recommendations
    recommendation: Optional[MigrationRecommendation] = None
    recommendation_score: Optional[float] = None
    recommendation_reasoning: Optional[str] = None
    alternative_recommendations: Optional[List[Dict[str, Any]]] = None
    
    class Config:
        from_attributes = True
        use_enum_values = True


class ApplicationAssessmentResponse(ApplicationAssessmentInDB):
    """Application assessment response schema"""
    project_name: Optional[str] = None
    assessed_by_username: Optional[str] = None


class AssessmentListResponse(BaseModel):
    """Assessment list response schema"""
    assessments: List[ApplicationAssessmentResponse]
    total: int
    page: int
    size: int


class AssessmentSummary(BaseModel):
    """Assessment summary for dashboard"""
    total_assessments: int
    by_recommendation: Dict[str, int]
    by_criticality: Dict[str, int]
    average_risk_score: float
    average_technical_debt: float
    total_cost_savings_potential: float