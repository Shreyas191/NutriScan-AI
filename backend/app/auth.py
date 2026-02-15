"""
Authentication — Clerk JWT verification for FastAPI.

Validates Bearer tokens issued by Clerk using JWKS (JSON Web Key Set).
Provides FastAPI dependencies for extracting the current user and enforcing roles.
"""

from __future__ import annotations

import time
from enum import Enum
from typing import Any

import httpx
import jwt as pyjwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from app.config import settings

# ---------------------------------------------------------------------------
# Security scheme
# ---------------------------------------------------------------------------
_bearer = HTTPBearer(auto_error=False)


# ---------------------------------------------------------------------------
# JWKS cache — fetched once, refreshed every hour
# ---------------------------------------------------------------------------
_jwks_cache: dict[str, Any] | None = None
_jwks_fetched_at: float = 0
_JWKS_TTL = 3600  # 1 hour


async def _get_jwks() -> dict[str, Any]:
    """Fetch and cache the JWKS from Clerk."""
    global _jwks_cache, _jwks_fetched_at

    now = time.time()
    if _jwks_cache and (now - _jwks_fetched_at) < _JWKS_TTL:
        return _jwks_cache

    jwks_url = settings.CLERK_JWKS_URL
    if not jwks_url:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="CLERK_JWKS_URL is not configured",
        )

    async with httpx.AsyncClient() as client:
        resp = await client.get(jwks_url)
        resp.raise_for_status()
        _jwks_cache = resp.json()
        _jwks_fetched_at = now
        return _jwks_cache


# ---------------------------------------------------------------------------
# User model
# ---------------------------------------------------------------------------
class Role(str, Enum):
    """Application roles for RBAC."""

    USER = "user"
    ADMIN = "admin"


class CurrentUser(BaseModel):
    """Authenticated user extracted from a Clerk JWT."""

    user_id: str
    email: str | None = None
    role: Role = Role.USER


# ---------------------------------------------------------------------------
# Core dependency — get_current_user
# ---------------------------------------------------------------------------
async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> CurrentUser:
    """
    Verify the Bearer token and return the authenticated user.

    Raises 401 if the token is missing, invalid, or expired.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    try:
        # Fetch signing keys
        jwks = await _get_jwks()
        signing_keys = {
            k["kid"]: k for k in jwks.get("keys", []) if k.get("use") == "sig"
        }

        # Decode header to find the right key
        unverified_header = pyjwt.get_unverified_header(token)
        kid = unverified_header.get("kid")
        if not kid or kid not in signing_keys:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token signing key",
            )

        # Build public key from JWK
        key_data = signing_keys[kid]
        public_key = pyjwt.algorithms.RSAAlgorithm.from_jwk(key_data)

        # Verify and decode
        payload = pyjwt.decode(
            token,
            public_key,
            algorithms=["RS256"],
            options={
                "verify_aud": False,  # Clerk tokens may not always have an audience
                "verify_iss": True,
                "verify_exp": True,
            },
            issuer=settings.CLERK_ISSUER,
        )

    except pyjwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        )
    except pyjwt.InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {e}",
        )

    # Extract user info from Clerk JWT claims
    user_id = payload.get("sub", "")
    email = payload.get("email")

    # Role: Check Clerk metadata for admin flag, default to "user"
    metadata = payload.get("public_metadata", {}) or {}
    role = Role.ADMIN if metadata.get("role") == "admin" else Role.USER

    return CurrentUser(user_id=user_id, email=email, role=role)


# ---------------------------------------------------------------------------
# RBAC dependency — require_role
# ---------------------------------------------------------------------------
def require_role(required: Role):
    """
    FastAPI dependency factory that enforces a minimum role.

    Usage:
        @app.get("/admin", dependencies=[Depends(require_role(Role.ADMIN))])
    """

    async def _check(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if required == Role.ADMIN and user.role != Role.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required",
            )
        return user

    return _check
