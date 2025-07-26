"""Application Assessment model with 22 critical attributes"""

from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Integer, Float, Boolean, JSON, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.core.database import Base


class MigrationRecommendation(str, enum.Enum):
    """6R Migration recommendations"""
    REHOST = "rehost"           # Lift and shift
    REPLATFORM = "replatform"   # Lift, tinker, and shift
    REPURCHASE = "repurchase"   # Drop and shop
    REFACTOR = "refactor"       # Re-architect
    RETIRE = "retire"           # Decommission
    RETAIN = "retain"           # Keep as-is


class ApplicationAssessment(Base):
    """Application assessment with 22 critical attributes for 6R analysis"""
    
    __tablename__ = "application_assessments"
    
    # Primary key and relationships
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    
    # 1. Basic Application Information
    application_name = Column(String(255), nullable=False, index=True)
    application_description = Column(Text)
    business_owner = Column(String(255))
    technical_owner = Column(String(255))
    
    # 2. Business Criticality
    business_criticality = Column(String(50))  # Critical, High, Medium, Low
    revenue_impact = Column(Float)  # Annual revenue impact in dollars
    user_count = Column(Integer)  # Number of users
    
    # 3. Technical Architecture
    architecture_type = Column(String(100))  # Monolithic, Microservices, SOA, etc.
    technology_stack = Column(JSON)  # List of technologies used
    programming_languages = Column(JSON)  # List of programming languages
    
    # 4. Infrastructure Dependencies
    server_count = Column(Integer)
    database_types = Column(JSON)  # List of database types (Oracle, MySQL, etc.)
    storage_requirements_gb = Column(Float)
    
    # 5. Integration Complexity
    integration_count = Column(Integer)  # Number of integrations
    integration_types = Column(JSON)  # API, File, Database, Message Queue, etc.
    external_dependencies = Column(JSON)  # List of external systems
    
    # 6. Performance Requirements
    peak_load_users = Column(Integer)
    response_time_sla_ms = Column(Integer)  # SLA in milliseconds
    availability_sla_percent = Column(Float)  # e.g., 99.9
    
    # 7. Compliance and Security
    compliance_requirements = Column(JSON)  # HIPAA, PCI-DSS, SOX, etc.
    data_sensitivity = Column(String(50))  # Public, Internal, Confidential, Restricted
    authentication_methods = Column(JSON)  # LDAP, OAuth, SAML, etc.
    
    # 8. Current State Assessment
    technical_debt_score = Column(Integer)  # 1-10 scale
    code_quality_score = Column(Integer)  # 1-10 scale
    documentation_quality = Column(String(50))  # Excellent, Good, Fair, Poor
    
    # 9. Cloud Readiness
    containerization_ready = Column(Boolean, default=False)
    stateless_architecture = Column(Boolean, default=False)
    cloud_native_services_used = Column(JSON)  # S3, SQS, etc.
    
    # 10. Migration Complexity Factors
    data_volume_gb = Column(Float)
    transaction_volume_per_day = Column(Integer)
    batch_processing_required = Column(Boolean, default=False)
    real_time_processing_required = Column(Boolean, default=False)
    
    # 11. Licensing and Costs
    current_licensing_cost_annual = Column(Float)
    infrastructure_cost_annual = Column(Float)
    support_cost_annual = Column(Float)
    
    # 12. Migration Timeline Constraints
    migration_deadline = Column(DateTime)
    blackout_windows = Column(JSON)  # Periods when migration cannot occur
    business_peak_periods = Column(JSON)  # High business activity periods
    
    # 13. Risk Assessment
    migration_risk_score = Column(Integer)  # 1-10 scale
    business_impact_if_failed = Column(String(50))  # Critical, High, Medium, Low
    rollback_complexity = Column(String(50))  # Simple, Moderate, Complex
    
    # 14. Team Readiness
    team_cloud_experience_score = Column(Integer)  # 1-10 scale
    training_required = Column(Boolean, default=True)
    external_support_needed = Column(Boolean, default=False)
    
    # 15. Application Lifecycle
    last_major_update = Column(DateTime)
    expected_retirement_date = Column(DateTime)
    modernization_planned = Column(Boolean, default=False)
    
    # 16. Data Characteristics
    data_residency_requirements = Column(JSON)  # Geographic constraints
    data_retention_requirements = Column(String(100))  # Retention policy
    backup_recovery_requirements = Column(JSON)  # RTO, RPO
    
    # 17. Network Requirements
    bandwidth_requirements_mbps = Column(Float)
    latency_requirements_ms = Column(Integer)
    vpn_requirements = Column(Boolean, default=False)
    
    # 18. Operational Requirements
    monitoring_tools = Column(JSON)  # Current monitoring stack
    logging_requirements = Column(JSON)  # Log types and retention
    support_hours = Column(String(50))  # 24x7, Business hours, etc.
    
    # 19. Migration Approach Preferences
    preferred_migration_strategy = Column(String(100))  # Big bang, Phased, Hybrid
    acceptable_downtime_hours = Column(Float)
    data_migration_approach = Column(String(100))  # Online, Offline, CDC
    
    # 20. Success Criteria
    success_metrics = Column(JSON)  # KPIs for successful migration
    acceptance_criteria = Column(JSON)  # Specific acceptance criteria
    
    # 21. Dependencies and Constraints
    dependent_applications = Column(JSON)  # Apps that depend on this
    shared_infrastructure = Column(JSON)  # Shared resources
    regulatory_constraints = Column(JSON)  # Specific regulatory requirements
    
    # 22. Cost-Benefit Analysis
    expected_cost_savings_percent = Column(Float)
    expected_performance_improvement_percent = Column(Float)
    expected_roi_months = Column(Integer)  # Months to ROI
    
    # AI-Generated Recommendations
    recommendation = Column(SQLEnum(MigrationRecommendation))
    recommendation_score = Column(Float)  # Confidence score 0-1
    recommendation_reasoning = Column(Text)
    alternative_recommendations = Column(JSON)  # Other viable options
    
    # Metadata
    assessment_date = Column(DateTime, default=datetime.utcnow)
    assessed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    notes = Column(Text)
    
    # Relationships
    project = relationship("Project", back_populates="assessments")
    assessed_by_user = relationship("User", foreign_keys=[assessed_by])