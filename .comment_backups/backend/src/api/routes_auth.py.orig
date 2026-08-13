"""Google OAuth 2.0 & Session Authentication API Routes (routes_auth.py).

Provides endpoints for Google OAuth consent flow, OAuth callback with pre-approved
trustee email verification, email/password fallback, first-login password resets,
and authenticated session profile management.
"""

import hashlib
import hmac
import os
import secrets
import urllib.parse

import httpx

try:
    import pyotp
except Exception:
    pyotp = None

from backend.src.api.auth import (
    TrusteeUser,
    create_jwt_token,
    decode_jwt_token,
    get_current_trustee,
)
from backend.src.api.dependencies import get_d1_db
from backend.src.db.d1_client import D1DatabaseClient
from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, EmailStr

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class FirstLoginResetRequest(BaseModel):
    email: EmailStr
    current_password: str
    new_password: str


class UserProfileResponse(BaseModel):
    user_id: str
    email: str
    name: str
    role: str
    first_login_complete: bool
    google_linked: bool


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserProfileResponse
    requires_2fa: bool = False


class GoogleLoginUrlResponse(BaseModel):
    auth_url: str
    state: str


@router.get("/google/login", response_model=GoogleLoginUrlResponse)
async def google_login_initiate() -> GoogleLoginUrlResponse:
    """Generate CSRF state and return Google OAuth 2.0 authorization URL."""
    client_id = os.environ.get(
        "GOOGLE_CLIENT_ID", "mock_google_client_id_beacon_2026.apps.googleusercontent.com"
    )
    redirect_uri = os.environ.get("GOOGLE_REDIRECT_URI", "http://localhost:3000/auth/callback")

    state = secrets.token_urlsafe(16)
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "prompt": "select_account",
    }

    auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urllib.parse.urlencode(params)}"
    return GoogleLoginUrlResponse(auth_url=auth_url, state=state)


@router.get("/google/callback", response_model=AuthResponse)
async def google_oauth_callback(
    code: str,
    state: str | None = None,
    response: Response = Response(),
    db: D1DatabaseClient = Depends(get_d1_db),
) -> AuthResponse:
    """Exchange authorization code with Google token endpoint and verify pre-approved trustee identity."""
    client_id = os.environ.get(
        "GOOGLE_CLIENT_ID", "mock_google_client_id_beacon_2026.apps.googleusercontent.com"
    )
    client_secret = os.environ.get("GOOGLE_CLIENT_SECRET", "mock_google_client_secret_beacon_2026")
    redirect_uri = os.environ.get("GOOGLE_REDIRECT_URI", "http://localhost:3000/auth/callback")

    # In test/mock mode or production code exchange
    google_email = None
    google_name = None
    google_sub = None

    if os.environ.get("MOCK_GOOGLE_OAUTH", "false").lower() == "true" or client_id.startswith(
        "mock_"
    ):
        # Test mock credentials
        google_email = os.environ.get("MOCK_GOOGLE_EMAIL", "chair@pottershouse.org.uk")
        google_name = os.environ.get("MOCK_GOOGLE_NAME", "Mock Google Trustee")
        google_sub = f"google_sub_{hashlib.md5(google_email.encode()).hexdigest()[:10]}"
    else:
        # Live Google OAuth API Code Exchange
        async with httpx.AsyncClient(timeout=10.0) as client:
            token_res = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "code": code,
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "redirect_uri": redirect_uri,
                    "grant_type": "authorization_code",
                },
            )

            if token_res.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Google OAuth token exchange failed: {token_res.text}",
                )

            token_data = token_res.json()
            access_token = token_data.get("access_token")

            userinfo_res = await client.get(
                "https://www.googleapis.com/oauth2/v3/userinfo",
                headers={"Authorization": f"Bearer {access_token}"},
            )

            if userinfo_res.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Failed to fetch user profile from Google.",
                )

            user_info = userinfo_res.json()
            google_email = user_info.get("email")
            google_name = user_info.get("name", "Trustee User")
            google_sub = user_info.get("sub")

    if not google_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="No email returned from Google OAuth."
        )

    # Pre-approved Trustee Verification Gate
    user = db.fetchone("SELECT * FROM users WHERE LOWER(email) = LOWER(?)", (google_email,))

    if not user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied for email '{google_email}'. Only pre-provisioned trustees can log in.",
        )

    # Link google_id if not already linked
    if not user.get("google_id"):
        db.execute(
            "UPDATE users SET google_id = ? WHERE user_id = ?", (google_sub, user["user_id"])
        )

    user_role = user["role"].title()
    first_complete = bool(user.get("first_login_complete", 0))

    # Issue PyJWT session token
    jwt_token = create_jwt_token(user_id=user["user_id"], role=user_role, email=user["email"])

    # Set secure HttpOnly session cookie
    response.set_cookie(
        key="session_token",
        value=jwt_token,
        httponly=True,
        secure=os.environ.get("APP_ENV") == "production",
        samesite="lax",
        max_age=86400,  # 24 hours
    )

    user_profile = UserProfileResponse(
        user_id=user["user_id"],
        email=user["email"],
        name=user["name"] or google_name,
        role=user_role,
        first_login_complete=first_complete,
        google_linked=True,
    )

    return AuthResponse(access_token=jwt_token, user=user_profile)


@router.post("/login", response_model=AuthResponse)
async def login_with_password(
    req: LoginRequest,
    response: Response,
    db: D1DatabaseClient = Depends(get_d1_db),
) -> AuthResponse:
    """Authenticate trustee using email and password."""
    user = db.fetchone("SELECT * FROM users WHERE LOWER(email) = LOWER(?)", (req.email,))

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password."
        )

    salt = os.environ.get("TRUSTEE_SIGNATURE_SALT", "default_salt_beacon_2026")
    input_pwd_hash = hmac.new(salt.encode(), f"{req.password}:{salt}".encode(), hashlib.sha256).hexdigest()

    if input_pwd_hash != user["password_hash"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password."
        )

    user_role = user["role"].title()
    first_complete = bool(user.get("first_login_complete", 0))

    user_profile = UserProfileResponse(
        user_id=user["user_id"],
        email=user["email"],
        name=user["name"],
        role=user_role,
        first_login_complete=first_complete,
        google_linked=bool(user.get("google_id")),
    )

    if user.get("totp_enabled"):
        jwt_token = create_jwt_token(
            user_id=user["user_id"], role="2FA_PENDING", email=user["email"]
        )
        return AuthResponse(access_token=jwt_token, user=user_profile, requires_2fa=True)

    jwt_token = create_jwt_token(user_id=user["user_id"], role=user_role, email=user["email"])

    response.set_cookie(
        key="session_token",
        value=jwt_token,
        httponly=True,
        secure=os.environ.get("APP_ENV") == "production",
        samesite="lax",
        max_age=86400,
    )

    return AuthResponse(access_token=jwt_token, user=user_profile)


class Login2FARequest(BaseModel):
    temp_token: str
    totp_code: str


@router.post("/login/2fa", response_model=AuthResponse)
async def login_with_2fa(
    req: Login2FARequest,
    response: Response,
    db: D1DatabaseClient = Depends(get_d1_db),
) -> AuthResponse:
    if pyotp is None:
        raise HTTPException(status_code=500, detail="pyotp library not available on server")

    payload = decode_jwt_token(req.temp_token)
    if payload.get("role") != "2FA_PENDING":
        raise HTTPException(status_code=401, detail="Invalid temporary token.")

    user = db.fetchone("SELECT * FROM users WHERE user_id = ?", (payload["sub"],))
    if not user or not user.get("totp_secret"):
        raise HTTPException(status_code=401, detail="Invalid user or 2FA not enabled.")

    totp = pyotp.TOTP(user["totp_secret"])
    if not totp.verify(req.totp_code):
        raise HTTPException(status_code=401, detail="Invalid 2FA code.")

    user_role = user["role"].title()
    jwt_token = create_jwt_token(user_id=user["user_id"], role=user_role, email=user["email"])

    response.set_cookie(
        key="session_token",
        value=jwt_token,
        httponly=True,
        secure=os.environ.get("APP_ENV") == "production",
        samesite="lax",
        max_age=86400,
    )

    user_profile = UserProfileResponse(
        user_id=user["user_id"],
        email=user["email"],
        name=user["name"],
        role=user_role,
        first_login_complete=bool(user.get("first_login_complete", 0)),
        google_linked=bool(user.get("google_id")),
    )
    return AuthResponse(access_token=jwt_token, user=user_profile)


@router.post("/first-login-reset", response_model=UserProfileResponse)
async def first_login_password_reset(
    req: FirstLoginResetRequest,
    db: D1DatabaseClient = Depends(get_d1_db),
) -> UserProfileResponse:
    """Execute forced password reset for temporary credentials on first login."""
    user = db.fetchone("SELECT * FROM users WHERE LOWER(email) = LOWER(?)", (req.email,))

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User account not found.")

    salt = os.environ.get("TRUSTEE_SIGNATURE_SALT", "default_salt_beacon_2026")
    curr_pwd_hash = hmac.new(salt.encode(), f"{req.current_password}:{salt}".encode(), hashlib.sha256).hexdigest()

    if curr_pwd_hash != user["password_hash"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Current temporary password incorrect."
        )

    if len(req.new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be at least 8 characters long.",
        )

    new_pwd_hash = hmac.new(salt.encode(), f"{req.new_password}:{salt}".encode(), hashlib.sha256).hexdigest()

    db.execute(
        "UPDATE users SET password_hash = ?, first_login_complete = 1 WHERE user_id = ?",
        (new_pwd_hash, user["user_id"]),
    )

    return UserProfileResponse(
        user_id=user["user_id"],
        email=user["email"],
        name=user["name"],
        role=user["role"].title(),
        first_login_complete=True,
        google_linked=bool(user.get("google_id")),
    )


@router.get("/me", response_model=UserProfileResponse)
async def get_current_user_profile(
    current_user: TrusteeUser = Depends(get_current_trustee),
    db: D1DatabaseClient = Depends(get_d1_db),
) -> UserProfileResponse:
    """Return authenticated user profile derived directly from session token."""
    user = db.fetchone("SELECT * FROM users WHERE user_id = ?", (current_user.user_id,))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Authenticated user record not found."
        )

    return UserProfileResponse(
        user_id=user["user_id"],
        email=user["email"],
        name=user["name"],
        role=user["role"].title(),
        first_login_complete=bool(user.get("first_login_complete", 0)),
        google_linked=bool(user.get("google_id")),
    )


@router.post("/logout")
async def logout(response: Response) -> dict[str, str]:
    """Clear session token cookie and log out user."""
    response.delete_cookie(key="session_token")
    return {"status": "logged_out"}
