"""Security utilities for authentication and authorization."""

import hashlib
import logging
import re
import secrets
from datetime import UTC, datetime, timedelta
from typing import Annotated, Any

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from app.config import get_settings

logger = logging.getLogger(__name__)

# JWT Configuration
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7
API_KEY_PREFIX = "gha_"

# Security schemes
bearer_scheme = HTTPBearer(auto_error=False)


class TokenPayload(BaseModel):
    """JWT token payload."""

    sub: str  # Subject (user ID or API key ID)
    exp: datetime
    iat: datetime
    type: str  # "access", "refresh", or "api_key"
    scopes: list[str] = []


class User(BaseModel):
    """User model for authentication."""

    id: str
    username: str
    is_active: bool = True
    is_admin: bool = False
    scopes: list[str] = []


class APIKey(BaseModel):
    """API key model."""

    id: str
    name: str
    key_hash: str
    is_active: bool = True
    scopes: list[str] = []
    created_at: datetime
    last_used_at: datetime | None = None


# Scope definitions for RBAC
class Scopes:
    """Available permission scopes."""

    READ_REPOSITORIES = "repositories:read"
    WRITE_REPOSITORIES = "repositories:write"
    READ_WORKFLOWS = "workflows:read"
    WRITE_WORKFLOWS = "workflows:write"
    READ_RUNS = "runs:read"
    WRITE_RUNS = "runs:write"
    READ_ANALYSIS = "analysis:read"
    WRITE_ANALYSIS = "analysis:write"
    READ_LOGS = "logs:read"
    READ_METRICS = "metrics:read"
    ADMIN = "admin"

    # Predefined scope sets
    READ_ALL = [
        READ_REPOSITORIES,
        READ_WORKFLOWS,
        READ_RUNS,
        READ_ANALYSIS,
        READ_LOGS,
        READ_METRICS,
    ]
    WRITE_ALL = [WRITE_REPOSITORIES, WRITE_WORKFLOWS, WRITE_RUNS, WRITE_ANALYSIS]
    ALL = READ_ALL + WRITE_ALL + [ADMIN]


def create_access_token(
    subject: str,
    scopes: list[str] | None = None,
    expires_delta: timedelta | None = None,
) -> str:
    """Create a JWT access token."""
    settings = get_settings()

    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    payload = {
        "sub": subject,
        "exp": expire,
        "iat": datetime.now(UTC),
        "type": "access",
        "scopes": scopes or [],
    }

    return jwt.encode(payload, settings.secret_key, algorithm=JWT_ALGORITHM)


def create_refresh_token(subject: str) -> str:
    """Create a JWT refresh token."""
    settings = get_settings()

    expire = datetime.now(UTC) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    payload = {
        "sub": subject,
        "exp": expire,
        "iat": datetime.now(UTC),
        "type": "refresh",
    }

    return jwt.encode(payload, settings.secret_key, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> TokenPayload:
    """Decode and validate a JWT token."""
    settings = get_settings()

    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[JWT_ALGORITHM])
        return TokenPayload(**payload)
    except jwt.ExpiredSignatureError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid token: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e


def generate_api_key() -> tuple[str, str]:
    """Generate a new API key. Returns (key, key_hash)."""
    # Generate a secure random key
    key = API_KEY_PREFIX + secrets.token_urlsafe(32)

    # Hash the key for storage
    key_hash = hashlib.sha256(key.encode()).hexdigest()

    return key, key_hash


def verify_api_key(key: str, key_hash: str) -> bool:
    """Verify an API key against its hash."""
    computed_hash = hashlib.sha256(key.encode()).hexdigest()
    return secrets.compare_digest(computed_hash, key_hash)


async def get_current_user(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> User | None:
    """
    Get the current authenticated user from the request.

    Supports both JWT Bearer tokens and API keys.
    Returns None if no authentication is provided (for optional auth).
    """
    settings = get_settings()

    # Check for Bearer token
    if credentials:
        token = credentials.credentials

        # Check if it's an API key
        if token.startswith(API_KEY_PREFIX):
            # API key authentication
            # In production, look up the API key in the database
            # For now, we'll validate against a configured API key
            if settings.api_keys:
                for api_key_config in settings.api_keys:
                    if verify_api_key(token, api_key_config.key_hash):
                        return User(
                            id=api_key_config.id,
                            username=f"api_key:{api_key_config.name}",
                            scopes=list(api_key_config.scopes),
                        )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # JWT token authentication
        payload = decode_token(token)

        if payload.type not in ("access", "api_key"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # In production, look up the user in the database
        return User(
            id=payload.sub,
            username=payload.sub,
            scopes=payload.scopes,
        )

    return None


async def get_current_user_required(
    user: Annotated[User | None, Depends(get_current_user)],
) -> User:
    """Require authentication - raises 401 if not authenticated."""
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


class RequireScopes:
    """Dependency for requiring specific scopes."""

    def __init__(self, required_scopes: list[str]) -> None:
        self.required_scopes = required_scopes

    async def __call__(
        self, user: Annotated[User, Depends(get_current_user_required)]
    ) -> User:
        """Check if user has required scopes."""
        # Admin has all permissions
        if Scopes.ADMIN in user.scopes:
            return user

        # Check for required scopes
        missing_scopes = set(self.required_scopes) - set(user.scopes)
        if missing_scopes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required scopes: {', '.join(missing_scopes)}",
            )

        return user


def require_scopes(*scopes: str) -> Any:
    """Create a dependency that requires specific scopes."""
    return Depends(RequireScopes(list(scopes)))


# Input validation helpers
GITHUB_REPO_NAME_PATTERN = re.compile(r"^[a-zA-Z0-9._-]+$")
GITHUB_OWNER_PATTERN = re.compile(r"^[a-zA-Z0-9](?:[a-zA-Z0-9._-]*[a-zA-Z0-9])?$")


def validate_github_owner(owner: str) -> str:
    """Validate GitHub owner/org name."""
    if not owner or len(owner) > 39:
        raise ValueError("Invalid GitHub owner name length")
    if not GITHUB_OWNER_PATTERN.match(owner):
        raise ValueError("Invalid GitHub owner name format")
    return owner


def validate_github_repo(repo: str) -> str:
    """Validate GitHub repository name."""
    if not repo or len(repo) > 100:
        raise ValueError("Invalid GitHub repository name length")
    if not GITHUB_REPO_NAME_PATTERN.match(repo):
        raise ValueError("Invalid GitHub repository name format")
    return repo


def escape_like_pattern(pattern: str) -> str:
    """Escape special characters for SQL LIKE patterns."""
    # Escape %, _, and \ characters
    return pattern.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
