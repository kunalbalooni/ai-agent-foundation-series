import os
import httpx
import asyncio
from functools import lru_cache

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pydantic import BaseModel

TENANT_ID = os.environ["AZURE_AD_TENANT_ID"]
BACKEND_CLIENT_ID = os.environ["AZURE_AD_CLIENT_ID"]  # Backend API client ID

# Token issuer — must match exactly what Entra ID puts in the 'iss' claim.
# MSAL v3 (used by the React frontend) requests tokens from the v2.0 endpoint,
# which sets iss to the v2.0 format below. The v1.0 STS format
# (https://sts.windows.net/<tenant>/) would cause a validation failure.
ISSUER = f"https://login.microsoftonline.com/{TENANT_ID}/v2.0"

# JWKS endpoint — Entra ID's public keys for token signature verification
JWKS_URL = f"https://login.microsoftonline.com/{TENANT_ID}/discovery/v2.0/keys"

# HTTPBearer extracts the token from the Authorization: Bearer <token> header
bearer_scheme = HTTPBearer()


class CurrentUser(BaseModel):
    """Typed representation of the authenticated user, extracted from the JWT."""
    object_id: str            # Entra ID user object ID (stable unique identifier)
    upn: str                  # User principal name (email address)
    display_name: str         # Display name
    groups: list[str]         # List of group object IDs the user belongs to
    scopes: list[str]         # API scopes granted in this token (e.g. ["agent.query"])


# Module-level JWKS cache (populated on first request, shared across all requests)
_jwks_cache: dict | None = None


def _fetch_jwks_sync() -> dict:
    """Synchronous JWKS fetch — run in a thread pool to avoid blocking the event loop."""
    response = httpx.get(JWKS_URL, timeout=10)
    response.raise_for_status()
    return response.json()


async def _get_jwks() -> dict:
    """Return cached JWKS, fetching from Entra ID on first call.

    Uses asyncio.to_thread so the blocking httpx.get runs in a thread pool
    and does not block the async event loop.
    """
    global _jwks_cache
    if _jwks_cache is None:
        _jwks_cache = await asyncio.to_thread(_fetch_jwks_sync)
    return _jwks_cache


async def _validate_token(token: str) -> dict:
    """Validate a JWT access token issued by Entra ID.

    Performs full validation:
    - Signature verification using Entra ID public keys
    - Issuer check: must be this tenant's STS
    - Audience check: must be this backend API's client ID
    - Expiry check: token must not be expired

    Returns the decoded token claims on success.
    Raises HTTPException 401 on any validation failure.
    """
    try:
        jwks = await _get_jwks()

        # Decode and validate the token.
        # python-jose verifies signature, issuer, audience, and expiry automatically.
        claims = jwt.decode(
            token,
            jwks,
            algorithms=["RS256"],
            audience=BACKEND_CLIENT_ID,
            issuer=ISSUER,
            options={"verify_at_hash": False},  # Not required for access tokens
        )
        return claims

    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token validation failed: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> CurrentUser:
    """FastAPI dependency that validates the bearer token and returns the current user.

    Usage:
        @app.post("/ask")
        async def ask(query: Query, user: CurrentUser = Depends(get_current_user)):
            ...

    Every protected endpoint receives a fully validated CurrentUser.
    If the token is invalid or absent, FastAPI returns 401 before the handler runs.
    """
    claims = await _validate_token(credentials.credentials)

    # Extract claims — use .get() with defaults to handle optional claims gracefully
    return CurrentUser(
        object_id=claims.get("oid", ""),
        upn=claims.get("upn") or claims.get("preferred_username", ""),
        display_name=claims.get("name", ""),
        groups=claims.get("groups", []),          # Group object IDs
        scopes=claims.get("scp", "").split(),     # Space-separated scope string → list
    )


# ── Group-Based Access Control ────────────────────────────────────────────────

GROUP_IDS = {
    "agent_users": os.environ.get("GROUP_ID_AGENT_USERS", ""),
    "agent_admins": os.environ.get("GROUP_ID_AGENT_ADMINS", ""),
}


def require_group(group_name: str):
    """Dependency factory that enforces group membership.

    Usage:
        @app.post("/admin/reset")
        async def reset(user: CurrentUser = Depends(require_group("agent_admins"))):
            ...

    Returns the CurrentUser if they are in the required group.
    Returns 403 Forbidden if they are not.
    """
    required_group_id = GROUP_IDS.get(group_name)
    if not required_group_id:
        raise ValueError(
            f"Unknown group: {group_name}. "
            f"Check GROUP_ID_{group_name.upper()} env var."
        )

    def _check_group(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if required_group_id not in user.groups:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access requires membership in the '{group_name}' group.",
            )
        return user

    return _check_group
