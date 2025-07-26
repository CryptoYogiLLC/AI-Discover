"""Seed data script for development"""

import asyncio
import uuid
from datetime import datetime, timedelta, timezone
from typing import List
import random

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import AsyncSessionLocal, init_db
from app.core.auth import get_password_hash
from app.models.user import User, UserRole
from app.models.project import Project, ProjectMember
from app.models.assessment import ApplicationAssessment, MigrationRecommendation


async def create_users(db: AsyncSession) -> List[User]:
    """Create sample users"""
    users_data = [
        {
            "email": "admin@example.com",
            "username": "admin",
            "full_name": "Admin User",
            "role": UserRole.ADMIN,
            "hashed_password": get_password_hash("admin123"),
        },
        {
            "email": "john.doe@example.com",
            "username": "johndoe",
            "full_name": "John Doe",
            "role": UserRole.COLLABORATOR,
            "hashed_password": get_password_hash("password123"),
        },
        {
            "email": "jane.smith@example.com",
            "username": "janesmith",
            "full_name": "Jane Smith",
            "role": UserRole.COLLABORATOR,
            "hashed_password": get_password_hash("password123"),
        },
        {
            "email": "viewer@example.com",
            "username": "viewer",
            "full_name": "Viewer User",
            "role": UserRole.VIEWER,
            "hashed_password": get_password_hash("viewer123"),
        },
        {
            "email": "ldap.user@example.com",
            "username": "ldapuser",
            "full_name": "LDAP User",
            "role": UserRole.COLLABORATOR,
            "is_ldap_user": True,
            "ldap_dn": "CN=LDAP User,OU=Users,DC=example,DC=com",
        },
    ]
    
    users = []
    for user_data in users_data:
        # Check if user already exists
        result = await db.execute(
            select(User).where(User.username == user_data["username"])
        )
        existing_user = result.scalar_one_or_none()
        
        if not existing_user:
            user = User(**user_data)
            db.add(user)
            users.append(user)
            print(f"Created user: {user.username}")
        else:
            users.append(existing_user)
            print(f"User already exists: {existing_user.username}")
    
    await db.commit()
    return users


async def create_projects(db: AsyncSession, users: List[User]) -> List[Project]:
    """Create sample projects"""
    projects_data = [
        {
            "name": "Digital Transformation Initiative",
            "description": "Modernizing legacy applications for cloud migration",
            "organization": "Acme Corporation",
            "department": "IT Operations",
            "created_by": users[0].id,  # Admin
        },
        {
            "name": "E-Commerce Platform Migration",
            "description": "Migrating e-commerce platform from on-premise to AWS",
            "organization": "Retail Corp",
            "department": "Digital Commerce",
            "created_by": users[1].id,  # John Doe
        },
        {
            "name": "Healthcare System Modernization",
            "description": "Modernizing healthcare management systems",
            "organization": "MedTech Solutions",
            "department": "Healthcare IT",
            "created_by": users[2].id,  # Jane Smith
        },
    ]
    
    projects = []
    for i, project_data in enumerate(projects_data):
        # Check if project already exists
        result = await db.execute(
            select(Project).where(Project.name == project_data["name"])
        )
        existing_project = result.scalar_one_or_none()
        
        if not existing_project:
            project = Project(**project_data)
            db.add(project)
            await db.flush()
            
            # Add project members
            # Creator is admin
            member = ProjectMember(
                project_id=project.id,
                user_id=project.created_by,
                role="admin"
            )
            db.add(member)
            
            # Add other members
            if i == 0:  # First project gets all users
                for user in users[1:]:
                    member = ProjectMember(
                        project_id=project.id,
                        user_id=user.id,
                        role="collaborator" if user.role != UserRole.VIEWER else "viewer"
                    )
                    db.add(member)
            elif i == 1:  # Second project
                member = ProjectMember(
                    project_id=project.id,
                    user_id=users[2].id,  # Jane
                    role="collaborator"
                )
                db.add(member)
                member = ProjectMember(
                    project_id=project.id,
                    user_id=users[3].id,  # Viewer
                    role="viewer"
                )
                db.add(member)
            
            projects.append(project)
            print(f"Created project: {project.name}")
        else:
            projects.append(existing_project)
            print(f"Project already exists: {existing_project.name}")
    
    await db.commit()
    return projects


async def create_assessments(db: AsyncSession, projects: List[Project], users: List[User]) -> None:
    """Create sample application assessments"""
    
    # Sample applications for assessment
    applications = [
        {
            "name": "Customer Portal",
            "description": "Web-based customer self-service portal",
            "criticality": "Critical",
            "architecture": "Monolithic",
            "tech_stack": ["Java", "Spring Boot", "Oracle DB", "Apache Tomcat"],
            "recommendation": MigrationRecommendation.REPLATFORM,
        },
        {
            "name": "Inventory Management System",
            "description": "Legacy inventory tracking system",
            "criticality": "High",
            "architecture": "Client-Server",
            "tech_stack": [".NET Framework", "SQL Server", "Windows Server"],
            "recommendation": MigrationRecommendation.REFACTOR,
        },
        {
            "name": "HR Management Portal",
            "description": "Human resources management application",
            "criticality": "Medium",
            "architecture": "Microservices",
            "tech_stack": ["Node.js", "MongoDB", "React", "Docker"],
            "recommendation": MigrationRecommendation.REHOST,
        },
        {
            "name": "Legacy Reporting Tool",
            "description": "Outdated reporting system scheduled for replacement",
            "criticality": "Low",
            "architecture": "Desktop Application",
            "tech_stack": ["VB6", "Access Database"],
            "recommendation": MigrationRecommendation.RETIRE,
        },
        {
            "name": "Mobile Banking App Backend",
            "description": "API backend for mobile banking application",
            "criticality": "Critical",
            "architecture": "Microservices",
            "tech_stack": ["Python", "FastAPI", "PostgreSQL", "Redis", "Kubernetes"],
            "recommendation": MigrationRecommendation.REHOST,
        },
        {
            "name": "Document Management System",
            "description": "Enterprise document storage and workflow",
            "criticality": "High",
            "architecture": "SOA",
            "tech_stack": ["Java EE", "IBM WebSphere", "DB2"],
            "recommendation": MigrationRecommendation.REPURCHASE,
        },
    ]
    
    for i, app_data in enumerate(applications):
        # Assign to different projects
        project = projects[i % len(projects)]
        
        # Check if assessment already exists
        result = await db.execute(
            select(ApplicationAssessment).where(
                ApplicationAssessment.application_name == app_data["name"],
                ApplicationAssessment.project_id == project.id
            )
        )
        existing_assessment = result.scalar_one_or_none()
        
        if not existing_assessment:
            assessment = ApplicationAssessment(
                project_id=project.id,
                application_name=app_data["name"],
                application_description=app_data["description"],
                business_owner=f"Business Owner {i + 1}",
                technical_owner=f"Tech Owner {i + 1}",
                business_criticality=app_data["criticality"],
                revenue_impact=random.randint(100000, 5000000),
                user_count=random.randint(100, 10000),
                architecture_type=app_data["architecture"],
                technology_stack=app_data["tech_stack"],
                programming_languages=app_data["tech_stack"][:2],
                server_count=random.randint(1, 20),
                database_types=["Oracle", "PostgreSQL", "MongoDB"][: random.randint(1, 3)],
                storage_requirements_gb=random.randint(100, 5000),
                integration_count=random.randint(2, 15),
                integration_types=["REST API", "SOAP", "File Transfer", "Message Queue"][: random.randint(2, 4)],
                external_dependencies=["Payment Gateway", "Email Service", "SMS Service"][: random.randint(1, 3)],
                peak_load_users=random.randint(500, 5000),
                response_time_sla_ms=random.choice([100, 200, 500, 1000]),
                availability_sla_percent=random.choice([99.0, 99.5, 99.9, 99.99]),
                compliance_requirements=random.choice([["HIPAA"], ["PCI-DSS"], ["SOX"], ["GDPR"], []]),
                data_sensitivity=random.choice(["Public", "Internal", "Confidential", "Restricted"]),
                authentication_methods=["LDAP", "OAuth2", "SAML"][: random.randint(1, 2)],
                technical_debt_score=random.randint(3, 8),
                code_quality_score=random.randint(4, 9),
                documentation_quality=random.choice(["Excellent", "Good", "Fair", "Poor"]),
                containerization_ready=random.choice([True, False]),
                stateless_architecture=random.choice([True, False]),
                cloud_native_services_used=["S3", "SQS", "Lambda"][: random.randint(0, 3)],
                data_volume_gb=random.randint(50, 2000),
                transaction_volume_per_day=random.randint(1000, 100000),
                batch_processing_required=random.choice([True, False]),
                real_time_processing_required=random.choice([True, False]),
                current_licensing_cost_annual=random.randint(10000, 200000),
                infrastructure_cost_annual=random.randint(20000, 300000),
                support_cost_annual=random.randint(5000, 50000),
                migration_deadline=datetime.now(timezone.utc) + timedelta(days=random.randint(90, 365)),
                migration_risk_score=random.randint(3, 8),
                business_impact_if_failed=random.choice(["Critical", "High", "Medium", "Low"]),
                rollback_complexity=random.choice(["Simple", "Moderate", "Complex"]),
                team_cloud_experience_score=random.randint(4, 9),
                training_required=random.choice([True, False]),
                external_support_needed=random.choice([True, False]),
                last_major_update=datetime.now(timezone.utc) - timedelta(days=random.randint(180, 1080)),
                modernization_planned=random.choice([True, False]),
                bandwidth_requirements_mbps=random.randint(10, 1000),
                latency_requirements_ms=random.randint(10, 200),
                vpn_requirements=random.choice([True, False]),
                monitoring_tools=["Datadog", "New Relic", "CloudWatch"][: random.randint(1, 3)],
                support_hours=random.choice(["24x7", "Business Hours", "Extended Hours"]),
                preferred_migration_strategy=random.choice(["Big Bang", "Phased", "Hybrid"]),
                acceptable_downtime_hours=random.uniform(0.5, 8.0),
                data_migration_approach=random.choice(["Online", "Offline", "CDC"]),
                expected_cost_savings_percent=random.uniform(10, 40),
                expected_performance_improvement_percent=random.uniform(15, 50),
                expected_roi_months=random.randint(6, 24),
                recommendation=app_data["recommendation"],
                recommendation_score=random.uniform(0.7, 0.95),
                recommendation_reasoning=f"Based on the assessment, {app_data['recommendation'].value} is recommended due to {app_data['architecture']} architecture and {app_data['criticality']} criticality.",
                assessed_by=users[1].id if i % 2 == 0 else users[2].id,
                assessment_date=datetime.now(timezone.utc) - timedelta(days=random.randint(1, 30)),
                notes=f"Initial assessment for {app_data['name']} migration planning."
            )
            
            db.add(assessment)
            print(f"Created assessment: {assessment.application_name}")
        else:
            print(f"Assessment already exists: {existing_assessment.application_name}")
    
    await db.commit()


async def main():
    """Run seed data script"""
    print("Starting seed data creation...")
    
    # Initialize database
    await init_db()
    
    async with AsyncSessionLocal() as db:
        # Create users
        users = await create_users(db)
        
        # Create projects
        projects = await create_projects(db, users)
        
        # Create assessments
        await create_assessments(db, projects, users)
    
    print("\nSeed data creation completed!")
    print("\nLogin credentials:")
    print("  Admin: admin@example.com / admin123")
    print("  Collaborator: john.doe@example.com / password123")
    print("  Collaborator: jane.smith@example.com / password123")
    print("  Viewer: viewer@example.com / viewer123")


if __name__ == "__main__":
    asyncio.run(main())