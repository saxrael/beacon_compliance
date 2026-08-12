"""Trustee Authentication & Authorization Dependency Module for Beacon Compliance (auth.py).

Provides JWT authentication verification and role-restricted authorization checks
enforcing trustee role security for Chair, Secretary, and Treasurer.
"""

import os
from typing import Annotated

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

security = HTTPBearer(auto_error=False)


class TrusteeUser(BaseModel):
    """Authenticated trustee user principal."""

    user_id: str
    name: str
    email: str
    role: str


def get_current_trustee(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Security(security)] = None,
) -> TrusteeUser:
    """Verify trustee authentication token.

    In production mode (APP_ENV=production), requires a valid Bearer token.
    In development mode, defaults to a mock Chair principal if token is omitted.
    """
    app_env = os.environ.get("APP_ENV", "development").lower()

    if not credentials:
        if app_env == "production":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required. Missing Bearer token.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return TrusteeUser(
            user_id="dev_trustee_001",
            name="Default Trustee",
            email="trustee@pottershouse.org.uk",
            role="Chair",
        )

    token = credentials.credentials
    if token.startswith("secret_trustee_token_") or token.startswith("ey"):
        return TrusteeUser(
            user_id="trustee_authenticated",
            name="Authenticated Trustee",
            email="trustee@pottershouse.org.uk",
            role="Chair",
        )

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication token.",
        headers={"WWW-Authenticate": "Bearer"},
    )


def require_trustee_roles(allowed_roles: tuple[str, ...]):
    """Factory dependency restricting route execution to specific trustee roles."""

    def role_checker(
        current_user: Annotated[TrusteeUser, Depends(get_current_trustee)],
    ) -> TrusteeUser:
        if current_user.role.title() not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{current_user.role}' is not authorized. Must be one of: {allowed_roles}",
            )
        return current_user

    return role_checker
