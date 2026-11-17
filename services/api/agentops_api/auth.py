"""Security, Token Hashing, JWT, and Project-Level RBAC."""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
import jwt
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from agentops_api.config import settings
from agentops_api.database import get_db
from agentops_api.models import User, Project, ApiKey, Organization

# Security schemes
bearer_scheme = HTTPBearer(auto_error=False)
api_key_header = APIKeyHeader(name="X-AgentOps-Api-Key", auto_error=False)


def hash_password(password: str) -> str:
    """Hash password using SHA-256 with salt."""
    salt = settings.SECRET_KEY[:16]
    return hashlib.sha256(f"{salt}{password}".encode("utf-8")).hexdigest()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against stored hash."""
    return hash_password(plain_password) == hashed_password


def hash_api_key(raw_key: str) -> str:
    """Produce SHA-256 hex digest of an API key."""
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()


def generate_api_key_pair(prefix: str = "aop_live_") -> Tuple[str, str, str]:
    """
    Generate a new API key pair.
    Returns (raw_key, key_prefix, hashed_key).
    Only the raw_key is returned once to the caller; hashed_key is stored.
    """
    random_part = secrets.token_urlsafe(32)
    raw_key = f"{prefix}{random_part}"
    key_prefix = raw_key[:12]
    hashed_key = hash_api_key(raw_key)
    return raw_key, key_prefix, hashed_key


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Generate JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """Retrieve authenticated user from JWT bearer token."""
    if not credentials:
        return None
    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if not user_id:
            return None
    except jwt.PyJWTError:
        return None

    query = select(User).where(User.id == user_id, User.is_active == True)
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def get_project_by_api_key(
    raw_key: Optional[str] = Security(api_key_header),
    db: AsyncSession = Depends(get_db)
) -> Optional[Project]:
    """Authenticate and retrieve Project associated with the X-AgentOps-Api-Key header."""
    if not raw_key:
        return None
    
    hashed = hash_api_key(raw_key)
    query = (
        select(ApiKey)
        .where(ApiKey.hashed_key == hashed, ApiKey.is_active == True)
    )
    result = await db.execute(query)
    api_key = result.scalar_one_or_none()
    
    if not api_key:
        return None
    
    # Update last_used_at
    api_key.last_used_at = datetime.now(timezone.utc)
    await db.commit()
    
    project_query = select(Project).where(Project.id == api_key.project_id)
    project_result = await db.execute(project_query)
    return project_result.scalar_one_or_none()


async def get_authenticated_context(
    user: Optional[User] = Depends(get_current_user),
    api_project: Optional[Project] = Depends(get_project_by_api_key)
) -> Tuple[Optional[User], Optional[Project]]:
    """Context resolver returning either authenticated user or authenticated project."""
    if not user and not api_project:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Provide a valid Bearer JWT or X-AgentOps-Api-Key."
        )
    return user, api_project


async def verify_project_access(
    project_id: str,
    user: Optional[User] = Depends(get_current_user),
    api_project: Optional[Project] = Depends(get_project_by_api_key),
    db: AsyncSession = Depends(get_db)
) -> Project:
    """
    Enforce strict tenant isolation:
    Verify that the user or API key is authorized to access the requested project_id.
    """
    # 1. API Key Auth: Must match project exactly
    if api_project:
        if api_project.id != project_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="API Key is not authorized for this project."
            )
        return api_project

    # 2. User JWT Auth: User's organization must own the project
    if user:
        query = select(Project).where(
            Project.id == project_id,
            Project.organization_id == user.organization_id
        )
        result = await db.execute(query)
        project = result.scalar_one_or_none()
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found or access denied."
            )
        return project

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required."
    )
