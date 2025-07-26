"""User model with role-based access control"""

from sqlalchemy import Column, String, DateTime, Boolean, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.core.database import Base


class UserRole(str, enum.Enum):
    """User role enumeration"""

    ADMIN = "admin"
    COLLABORATOR = "collaborator"
    VIEWER = "viewer"


class User(Base):
    """User database model with RBAC support"""

    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=True)  # Nullable for LDAP users
    full_name = Column(String)
    role = Column(SQLEnum(UserRole), default=UserRole.VIEWER, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_ldap_user = Column(Boolean, default=False, nullable=False)
    ldap_dn = Column(String, nullable=True)  # Distinguished Name for LDAP users
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login_at = Column(DateTime, nullable=True)

    # Relationships
    project_memberships = relationship(
        "ProjectMember", back_populates="user", cascade="all, delete-orphan"
    )
    created_projects = relationship(
        "Project", back_populates="created_by_user", foreign_keys="Project.created_by"
    )
