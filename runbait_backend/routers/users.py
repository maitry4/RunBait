"""
User endpoints.

GET /api/users/me  — returns the currently authenticated user's profile.
"""
from fastapi import APIRouter, Depends

from core.security import get_current_user

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("/me")
async def get_me(user: dict = Depends(get_current_user)) -> dict:
    """
    Returns the JWT claims of the currently authenticated user.
    The frontend calls this server-side to validate the session cookie.
    """
    return {
        "id": user.get("sub"),
        "github_id": user.get("github_id"),
        "github_login": user.get("github_login"),
        "name": user.get("name"),
        "email": user.get("email"),
        "avatar_url": user.get("avatar_url"),
    }
