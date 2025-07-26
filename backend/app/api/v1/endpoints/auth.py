"""Authentication endpoints"""

from typing import Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from structlog import get_logger

from app.core.database import get_db
from app.core.auth import decode_token, check_user_permissions
from app.models.user import User, UserRole
from app.schemas.auth import (
    LoginRequest, Token, TokenData, UserResponse, 
    UserCreate, UserUpdate
)
from app.services.auth import AuthService

logger = get_logger()
router = APIRouter()

# Security scheme for JWT bearer tokens
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Get current authenticated user from JWT token"""
    token = credentials.credentials
    
    # Decode token
    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user from database
    auth_service = AuthService(db)
    user = await auth_service.get_user_by_id(payload.get("sub"))
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


def require_role(required_role: UserRole):
    """Dependency to require specific role"""
    async def role_checker(current_user: User = Depends(get_current_user)):
        if not check_user_permissions(current_user.role, required_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return current_user
    return role_checker


@router.post("/login", response_model=Token)
async def login(
    response: Response,
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Login with username/password
    
    Supports both LDAP and local authentication based on configuration.
    Returns JWT access and refresh tokens.
    """
    auth_service = AuthService(db)
    
    # Authenticate user
    user = await auth_service.authenticate_user(
        login_data.username, 
        login_data.password
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    # Create tokens
    tokens = await auth_service.create_tokens(user)
    
    # Set cookies for tokens (httpOnly for security)
    response.set_cookie(
        key="access_token",
        value=tokens.access_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=1800  # 30 minutes
    )
    response.set_cookie(
        key="refresh_token",
        value=tokens.refresh_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=604800  # 7 days
    )
    
    logger.info("User logged in", user_id=str(user.id), username=user.username)
    return tokens


@router.post("/logout")
async def logout(response: Response, current_user: User = Depends(get_current_user)):
    """
    Logout current user
    
    Clears authentication cookies.
    """
    # Clear cookies
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    
    logger.info("User logged out", user_id=str(current_user.id), username=current_user.username)
    return {"message": "Successfully logged out"}


@router.post("/refresh", response_model=Token)
async def refresh_token(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db)
):
    """
    Refresh access token using refresh token
    
    Requires valid refresh token in cookie or Authorization header.
    """
    # Try to get refresh token from cookie first, then header
    refresh_token = request.cookies.get("refresh_token")
    
    if not refresh_token:
        # Try Authorization header
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            refresh_token = auth_header.split(" ")[1]
    
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not provided"
        )
    
    # Decode refresh token
    payload = decode_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    # Get user
    auth_service = AuthService(db)
    user = await auth_service.get_user_by_id(payload.get("sub"))
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    # Refresh user role from LDAP if applicable
    if user.is_ldap_user:
        await auth_service.refresh_user_role(str(user.id))
    
    # Create new tokens
    tokens = await auth_service.create_tokens(user)
    
    # Update cookies
    response.set_cookie(
        key="access_token",
        value=tokens.access_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=1800  # 30 minutes
    )
    response.set_cookie(
        key="refresh_token",
        value=tokens.refresh_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=604800  # 7 days
    )
    
    logger.info("Tokens refreshed", user_id=str(user.id), username=user.username)
    return tokens


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    Get current user information
    
    Returns the authenticated user's profile information.
    """
    return current_user


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Register new local user
    
    Only available when LDAP is disabled or for creating local admin accounts.
    Requires admin role in production.
    """
    auth_service = AuthService(db)
    
    try:
        user = await auth_service.create_user(user_data, is_ldap_user=False)
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    user_update: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN))
):
    """
    Update user information
    
    Requires admin role.
    """
    auth_service = AuthService(db)
    
    try:
        user = await auth_service.update_user(user_id, user_update)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/test-ldap")
async def test_ldap_connection(
    current_user: User = Depends(require_role(UserRole.ADMIN))
):
    """
    Test LDAP connection
    
    Requires admin role. Tests the LDAP service account connection.
    """
    from app.services.ldap import get_ldap_service
    from app.core.config import settings
    
    if not settings.LDAP_ENABLED:
        return {"status": "disabled", "message": "LDAP is not enabled"}
    
    ldap_service = get_ldap_service()
    success = await ldap_service.test_connection()
    
    return {
        "status": "success" if success else "failed",
        "message": "LDAP connection successful" if success else "LDAP connection failed"
    }
