"""Authentication service combining LDAP and local authentication"""

from typing import Optional, Dict, Any
from datetime import datetime, timezone
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from structlog import get_logger

from app.core.auth import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
)
from app.core.config import settings
from app.models.user import User, UserRole
from app.schemas.auth import UserCreate, UserUpdate, Token
from app.services.ldap import get_ldap_service

logger = get_logger()


class AuthService:
    """Service for handling authentication operations"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.ldap_service = get_ldap_service() if settings.LDAP_ENABLED else None

    async def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """
        Authenticate user with LDAP or local credentials

        Args:
            username: Username or email
            password: User password

        Returns:
            User object if authentication successful, None otherwise
        """
        # First try to find user in database
        user = await self.get_user_by_username_or_email(username)

        # If LDAP is enabled and user is LDAP user or doesn't exist
        if settings.LDAP_ENABLED and (not user or user.is_ldap_user):
            ldap_info = await self.ldap_service.authenticate_user(username, password)

            if ldap_info:
                # Create or update user from LDAP
                user = await self._sync_ldap_user(ldap_info)
                if user:
                    # Update last login
                    user.last_login_at = datetime.now(timezone.utc)
                    await self.db.commit()
                    return user
            elif user and user.is_ldap_user:
                # LDAP auth failed for LDAP user
                return None

        # Try local authentication if user exists and is not LDAP user
        if user and not user.is_ldap_user and user.hashed_password:
            if verify_password(password, user.hashed_password):
                # Update last login
                user.last_login_at = datetime.now(timezone.utc)
                await self.db.commit()
                return user

        return None

    async def create_user(
        self, user_create: UserCreate, is_ldap_user: bool = False
    ) -> User:
        """
        Create new user

        Args:
            user_create: User creation data
            is_ldap_user: Whether user is from LDAP

        Returns:
            Created user object
        """
        # Check if user already exists
        existing_user = await self.get_user_by_username_or_email(
            user_create.username, user_create.email
        )
        if existing_user:
            raise ValueError("User with this username or email already exists")

        # Create user
        user = User(
            email=user_create.email,
            username=user_create.username,
            full_name=user_create.full_name,
            role=user_create.role,
            is_active=user_create.is_active,
            is_ldap_user=is_ldap_user,
            hashed_password=(
                get_password_hash(user_create.password) if not is_ldap_user else None
            ),
        )

        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)

        logger.info("User created", user_id=str(user.id), username=user.username)
        return user

    async def update_user(
        self, user_id: str, user_update: UserUpdate
    ) -> Optional[User]:
        """
        Update user information

        Args:
            user_id: User ID
            user_update: Update data

        Returns:
            Updated user or None if not found
        """
        user = await self.get_user_by_id(user_id)
        if not user:
            return None

        # Update fields
        update_data = user_update.model_dump(exclude_unset=True)

        # Handle password update
        if "password" in update_data and update_data["password"]:
            if user.is_ldap_user:
                raise ValueError("Cannot update password for LDAP user")
            update_data["hashed_password"] = get_password_hash(
                update_data.pop("password")
            )

        for field, value in update_data.items():
            setattr(user, field, value)

        user.updated_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(user)

        logger.info("User updated", user_id=user_id)
        return user

    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_user_by_username_or_email(
        self, username: str, email: Optional[str] = None
    ) -> Optional[User]:
        """Get user by username or email"""
        conditions = [User.username == username]
        if email:
            conditions.append(User.email == email)
        else:
            # If only username provided, also check email field
            conditions.append(User.email == username)

        result = await self.db.execute(select(User).where(or_(*conditions)))
        return result.scalar_one_or_none()

    async def create_tokens(self, user: User) -> Token:
        """
        Create access and refresh tokens for user

        Args:
            user: User object

        Returns:
            Token object with access and refresh tokens
        """
        token_data = {
            "sub": str(user.id),
            "role": user.role.value,
            "username": user.username,
        }

        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)

        return Token(access_token=access_token, refresh_token=refresh_token)

    async def refresh_user_role(self, user_id: str) -> Optional[UserRole]:
        """
        Refresh user role from LDAP

        Args:
            user_id: User ID

        Returns:
            Updated role or None if update failed
        """
        if not settings.LDAP_ENABLED:
            return None

        user = await self.get_user_by_id(user_id)
        if not user or not user.is_ldap_user:
            return None

        # Sync role from LDAP
        new_role = await self.ldap_service.sync_user_groups(user.username)
        if new_role and new_role != user.role:
            user.role = new_role
            user.updated_at = datetime.now(timezone.utc)
            await self.db.commit()

            logger.info(
                "User role updated from LDAP", user_id=user_id, new_role=new_role.value
            )
            return new_role

        return user.role

    async def _sync_ldap_user(self, ldap_info: Dict[str, Any]) -> Optional[User]:
        """
        Create or update user from LDAP information

        Args:
            ldap_info: User information from LDAP

        Returns:
            User object or None if sync failed
        """
        try:
            # Find existing user
            user = await self.get_user_by_username_or_email(
                ldap_info["username"], ldap_info.get("email")
            )

            if user:
                # Update existing user
                user.email = ldap_info.get("email", user.email)
                user.full_name = ldap_info.get("full_name", user.full_name)
                user.role = ldap_info.get("role", user.role)
                user.ldap_dn = ldap_info.get("ldap_dn", user.ldap_dn)
                user.is_ldap_user = True
                user.updated_at = datetime.now(timezone.utc)
            else:
                # Create new user
                user = User(
                    email=ldap_info.get(
                        "email", f"{ldap_info['username']}@example.com"
                    ),
                    username=ldap_info["username"],
                    full_name=ldap_info.get("full_name"),
                    role=ldap_info.get("role", UserRole.VIEWER),
                    is_active=True,
                    is_ldap_user=True,
                    ldap_dn=ldap_info.get("ldap_dn"),
                )
                self.db.add(user)

            await self.db.commit()
            await self.db.refresh(user)

            logger.info(
                "LDAP user synced", user_id=str(user.id), username=user.username
            )
            return user

        except Exception as e:
            logger.error("Failed to sync LDAP user", error=str(e), ldap_info=ldap_info)
            await self.db.rollback()
            return None
