"""
GitHub OAuth endpoints.

Flow:
  GET /api/auth/github/login
      → redirect to GitHub consent page

  GET /api/auth/github/callback
      → GitHub redirects here with `?code=...`
      → exchange code for access_token
      → fetch GitHub user profile
      → upsert user in Supabase
      → create JWT
      → redirect to Next.js API route to set HttpOnly cookie
      → Next.js API route redirects to /dashboard
"""
import logging
from urllib.parse import urlencode

from authlib.integrations.starlette_client import OAuthError
from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

from core.config import get_settings
from core.db import supabase
from core.security import create_access_token, create_oauth

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/auth", tags=["auth"])
settings = get_settings()

# Lazily created OAuth instance (authlib needs request context)
_oauth = create_oauth()
github = _oauth.github  # type: ignore[attr-defined]


@router.get("/github/login")
async def github_login(request: Request) -> RedirectResponse:
    """Redirect the browser to GitHub's OAuth consent page."""
    callback_url = f"{settings.BACKEND_URL}/api/auth/github/callback"
    return await github.authorize_redirect(request, callback_url)


@router.get("/github/callback")
async def github_callback(request: Request) -> RedirectResponse:
    """
    Handle the GitHub OAuth callback.
    Exchanges the code for a token, fetches user info, persists to Supabase,
    creates a JWT, and redirects to the Next.js set-token API route.
    """
    try:
        token = await github.authorize_access_token(request)
    except OAuthError as exc:
        logger.error("GitHub OAuth error: %s", exc)
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/signin?error=oauth_failed"
        )

    github_access_token: str = token.get("access_token", "")

    # ------------------------------------------------------------------
    # Fetch GitHub user profile
    # ------------------------------------------------------------------
    try:
        resp = await github.get("user", token=token)
        resp.raise_for_status()
        gh_user: dict = resp.json()
    except Exception as exc:
        logger.error("Failed to fetch GitHub user: %s", exc)
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/signin?error=github_api_failed"
        )

    # Fetch primary email if not public
    email: str = gh_user.get("email") or ""
    if not email:
        try:
            email_resp = await github.get("user/emails", token=token)
            email_resp.raise_for_status()
            emails = email_resp.json()
            primary = next(
                (e for e in emails if e.get("primary") and e.get("verified")),
                None,
            )
            email = primary["email"] if primary else ""
        except Exception as exc:
            logger.warning("Failed to fetch GitHub emails: %s", exc)

    github_id: int = gh_user["id"]
    login: str = gh_user.get("login", "")
    name: str = gh_user.get("name") or login
    avatar_url: str = gh_user.get("avatar_url", "")

    # ------------------------------------------------------------------
    # Upsert user in Supabase
    # ------------------------------------------------------------------
    try:
        upsert_data = {
            "github_id": github_id,
            "email": email,
            "name": name,
            "avatar_url": avatar_url,
            "github_login": login,
            "github_access_token": github_access_token,
        }
        result = (
            supabase.table("users")
            .upsert(upsert_data, on_conflict="github_id")
            .execute()
        )
        db_user = result.data[0]
    except Exception as exc:
        logger.error("Supabase upsert failed: %s", exc)
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/signin?error=db_error"
        )

    # ------------------------------------------------------------------
    # Create JWT
    # ------------------------------------------------------------------
    jwt_payload = {
        "sub": str(db_user["id"]),          # Supabase UUID
        "github_id": github_id,
        "github_login": login,
        "name": name,
        "email": email,
        "avatar_url": avatar_url,
    }
    access_token = create_access_token(jwt_payload)

    # ------------------------------------------------------------------
    # Redirect to Next.js API route — it sets the HttpOnly cookie
    # ------------------------------------------------------------------
    params = urlencode({"access_token": access_token})
    set_token_url = f"{settings.FRONTEND_URL}/api/auth/set-token?{params}"
    return RedirectResponse(url=set_token_url)
