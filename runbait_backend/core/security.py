"""
Security utilities:
- JWT creation / decoding
- FastAPI dependency for authenticated routes
- authlib OAuth client factory for GitHub
"""
from datetime import datetime, timedelta, timezone
from typing import Optional

from authlib.integrations.starlette_client import OAuth
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt

from core.config import get_settings

settings = get_settings()

# ---------------------------------------------------------------------------
# JWT helpers
# ---------------------------------------------------------------------------

_bearer_scheme = HTTPBearer(auto_error=False)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a signed JWT containing `data` as claims."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    """Decode and validate a JWT. Raises HTTPException on failure."""
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer_scheme),
) -> dict:
    """
    FastAPI dependency. Extracts the Bearer token from the Authorization header
    and returns the decoded JWT payload.
    Usage: `user = Depends(get_current_user)`
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return decode_access_token(credentials.credentials)


# ---------------------------------------------------------------------------
# GitHub OAuth client (authlib)
# ---------------------------------------------------------------------------

_GITHUB_OAUTH_CONFIG = {
    "name": "github",
    "client_id": settings.GITHUB_CLIENT_ID,
    "client_secret": settings.GITHUB_CLIENT_SECRET,
    "access_token_url": "https://github.com/login/oauth/access_token",
    "authorize_url": "https://github.com/login/oauth/authorize",
    "api_base_url": "https://api.github.com/",
    # Scopes: user email + repo + GitHub Actions workflow
    "client_kwargs": {"scope": "user:email repo workflow"},
}


def create_oauth() -> OAuth:
    """Create and return a configured authlib OAuth instance."""
    oauth = OAuth()
    oauth.register(**_GITHUB_OAUTH_CONFIG)
    return oauth
