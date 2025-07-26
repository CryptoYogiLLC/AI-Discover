"""Initial schema with users, projects, and assessments

Revision ID: 001
Revises:
Create Date: 2025-01-26 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create user role enum
    op.execute("CREATE TYPE userrole AS ENUM ('admin', 'collaborator', 'viewer')")

    # Create migration recommendation enum
    op.execute(
        "CREATE TYPE migrationrecommendation AS ENUM ('rehost', 'replatform', 'repurchase', 'refactor', 'retire', 'retain')"
    )

    # Create users table
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("username", sa.String(), nullable=False),
        sa.Column("hashed_password", sa.String(), nullable=True),
        sa.Column("full_name", sa.String(), nullable=True),
        sa.Column(
            "role",
            postgresql.ENUM("admin", "collaborator", "viewer", name="userrole"),
            nullable=False,
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("is_ldap_user", sa.Boolean(), nullable=False),
        sa.Column("ldap_dn", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("last_login_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    op.create_index(op.f("ix_users_username"), "users", ["username"], unique=True)

    # Create projects table
    op.create_table(
        "projects",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("organization", sa.String(length=255), nullable=True),
        sa.Column("department", sa.String(length=255), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_projects_name"), "projects", ["name"], unique=False)

    # Create project_members table
    op.create_table(
        "project_members",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role", sa.String(length=50), nullable=True),
        sa.Column("joined_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create application_assessments table
    op.create_table(
        "application_assessments",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("application_name", sa.String(length=255), nullable=False),
        sa.Column("application_description", sa.Text(), nullable=True),
        sa.Column("business_owner", sa.String(length=255), nullable=True),
        sa.Column("technical_owner", sa.String(length=255), nullable=True),
        sa.Column("business_criticality", sa.String(length=50), nullable=True),
        sa.Column("revenue_impact", sa.Float(), nullable=True),
        sa.Column("user_count", sa.Integer(), nullable=True),
        sa.Column("architecture_type", sa.String(length=100), nullable=True),
        sa.Column("technology_stack", sa.JSON(), nullable=True),
        sa.Column("programming_languages", sa.JSON(), nullable=True),
        sa.Column("server_count", sa.Integer(), nullable=True),
        sa.Column("database_types", sa.JSON(), nullable=True),
        sa.Column("storage_requirements_gb", sa.Float(), nullable=True),
        sa.Column("integration_count", sa.Integer(), nullable=True),
        sa.Column("integration_types", sa.JSON(), nullable=True),
        sa.Column("external_dependencies", sa.JSON(), nullable=True),
        sa.Column("peak_load_users", sa.Integer(), nullable=True),
        sa.Column("response_time_sla_ms", sa.Integer(), nullable=True),
        sa.Column("availability_sla_percent", sa.Float(), nullable=True),
        sa.Column("compliance_requirements", sa.JSON(), nullable=True),
        sa.Column("data_sensitivity", sa.String(length=50), nullable=True),
        sa.Column("authentication_methods", sa.JSON(), nullable=True),
        sa.Column("technical_debt_score", sa.Integer(), nullable=True),
        sa.Column("code_quality_score", sa.Integer(), nullable=True),
        sa.Column("documentation_quality", sa.String(length=50), nullable=True),
        sa.Column("containerization_ready", sa.Boolean(), nullable=True),
        sa.Column("stateless_architecture", sa.Boolean(), nullable=True),
        sa.Column("cloud_native_services_used", sa.JSON(), nullable=True),
        sa.Column("data_volume_gb", sa.Float(), nullable=True),
        sa.Column("transaction_volume_per_day", sa.Integer(), nullable=True),
        sa.Column("batch_processing_required", sa.Boolean(), nullable=True),
        sa.Column("real_time_processing_required", sa.Boolean(), nullable=True),
        sa.Column("current_licensing_cost_annual", sa.Float(), nullable=True),
        sa.Column("infrastructure_cost_annual", sa.Float(), nullable=True),
        sa.Column("support_cost_annual", sa.Float(), nullable=True),
        sa.Column("migration_deadline", sa.DateTime(), nullable=True),
        sa.Column("blackout_windows", sa.JSON(), nullable=True),
        sa.Column("business_peak_periods", sa.JSON(), nullable=True),
        sa.Column("migration_risk_score", sa.Integer(), nullable=True),
        sa.Column("business_impact_if_failed", sa.String(length=50), nullable=True),
        sa.Column("rollback_complexity", sa.String(length=50), nullable=True),
        sa.Column("team_cloud_experience_score", sa.Integer(), nullable=True),
        sa.Column("training_required", sa.Boolean(), nullable=True),
        sa.Column("external_support_needed", sa.Boolean(), nullable=True),
        sa.Column("last_major_update", sa.DateTime(), nullable=True),
        sa.Column("expected_retirement_date", sa.DateTime(), nullable=True),
        sa.Column("modernization_planned", sa.Boolean(), nullable=True),
        sa.Column("data_residency_requirements", sa.JSON(), nullable=True),
        sa.Column("data_retention_requirements", sa.String(length=100), nullable=True),
        sa.Column("backup_recovery_requirements", sa.JSON(), nullable=True),
        sa.Column("bandwidth_requirements_mbps", sa.Float(), nullable=True),
        sa.Column("latency_requirements_ms", sa.Integer(), nullable=True),
        sa.Column("vpn_requirements", sa.Boolean(), nullable=True),
        sa.Column("monitoring_tools", sa.JSON(), nullable=True),
        sa.Column("logging_requirements", sa.JSON(), nullable=True),
        sa.Column("support_hours", sa.String(length=50), nullable=True),
        sa.Column("preferred_migration_strategy", sa.String(length=100), nullable=True),
        sa.Column("acceptable_downtime_hours", sa.Float(), nullable=True),
        sa.Column("data_migration_approach", sa.String(length=100), nullable=True),
        sa.Column("success_metrics", sa.JSON(), nullable=True),
        sa.Column("acceptance_criteria", sa.JSON(), nullable=True),
        sa.Column("dependent_applications", sa.JSON(), nullable=True),
        sa.Column("shared_infrastructure", sa.JSON(), nullable=True),
        sa.Column("regulatory_constraints", sa.JSON(), nullable=True),
        sa.Column("expected_cost_savings_percent", sa.Float(), nullable=True),
        sa.Column(
            "expected_performance_improvement_percent", sa.Float(), nullable=True
        ),
        sa.Column("expected_roi_months", sa.Integer(), nullable=True),
        sa.Column(
            "recommendation",
            postgresql.ENUM(
                "rehost",
                "replatform",
                "repurchase",
                "refactor",
                "retire",
                "retain",
                name="migrationrecommendation",
            ),
            nullable=True,
        ),
        sa.Column("recommendation_score", sa.Float(), nullable=True),
        sa.Column("recommendation_reasoning", sa.Text(), nullable=True),
        sa.Column("alternative_recommendations", sa.JSON(), nullable=True),
        sa.Column("assessment_date", sa.DateTime(), nullable=True),
        sa.Column("assessed_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("last_updated", sa.DateTime(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(
            ["assessed_by"],
            ["users.id"],
        ),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_application_assessments_application_name"),
        "application_assessments",
        ["application_name"],
        unique=False,
    )

    # Keep existing tables
    # applications table
    op.create_table(
        "applications",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("environment", sa.String(), nullable=False),
        sa.Column("target_type", sa.String(), nullable=False),
        sa.Column("target_id", sa.String(), nullable=False),
        sa.Column("attributes", sa.JSON(), nullable=True),
        sa.Column("recommendation", sa.String(), nullable=True),
        sa.Column("confidence_score", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    # collection_flows table
    op.create_table(
        "collection_flows",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("provider", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table("collection_flows")
    op.drop_table("applications")
    op.drop_index(
        op.f("ix_application_assessments_application_name"),
        table_name="application_assessments",
    )
    op.drop_table("application_assessments")
    op.drop_table("project_members")
    op.drop_index(op.f("ix_projects_name"), table_name="projects")
    op.drop_table("projects")
    op.drop_index(op.f("ix_users_username"), table_name="users")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")

    # Drop enums
    op.execute("DROP TYPE IF EXISTS migrationrecommendation")
    op.execute("DROP TYPE IF EXISTS userrole")
