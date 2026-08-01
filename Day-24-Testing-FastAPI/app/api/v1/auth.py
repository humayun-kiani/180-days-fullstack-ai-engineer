# ============================================================
# app/api/v1/auth.py
# Authentication endpoints: register, login, refresh, logout
# ============================================================

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.security import (
    hash_password, verify_password,
    create_access_token, create_refresh_token,
    decode_token, get_token_expires_in
)
from app.core.token_blacklist import revoke_token, is_token_revoked
from app.core.config import settings
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.auth import (
    RegisterRequest, TokenResponse, RefreshRequest,
    PasswordChangeRequest, MessageResponse, UserProfileResponse,
    LoginRequest
)
from jose import JWTError
from fastapi.security import OAuth2PasswordBearer

router = APIRouter(prefix="/auth", tags=["Authentication"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


# ─── Helpers ────────────────────────────────────────────────

def get_user_by_username(db: Session, username: str) -> User | None:
    return db.query(User).filter(User.username == username.lower()).first()


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == email.lower()).first()


def authenticate_user(
    db: Session, username: str, password: str
) -> User | None:
    """
    Verify username and password.

    Returns User if credentials are valid, None otherwise.
    Timing-safe: takes the same time whether user exists or not.
    """
    user = get_user_by_username(db, username)

    # Even if user doesn't exist, still run verify_password
    # to prevent timing attacks that reveal which usernames exist
    dummy_hash = "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/lewdBenqQJmaBxRq"
    hash_to_check = user.hashed_password if user else dummy_hash

    password_correct = verify_password(password, hash_to_check)

    if not user or not password_correct:
        return None

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account is deactivated. Contact admin."
        )

    return user


def build_token_response(user: User) -> dict:
    """Create access + refresh tokens for a user."""
    token_data = {
        "username": user.username,
        "role": user.role,
        "email": user.email
    }

    access_token = create_access_token(
        subject=user.id,
        extra_data=token_data
    )
    refresh_token = create_refresh_token(subject=user.id)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


def log_auth_event(username: str, event: str, success: bool):
    """Background task for security audit logging."""
    status_str = "✅ SUCCESS" if success else "❌ FAILED"
    print(f"  🔐 [Auth Audit] {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} | "
          f"{status_str} | {event} | user: {username}")


# ─── ENDPOINTS ──────────────────────────────────────────────

@router.post(
    "/register",
    response_model=UserProfileResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Create a new account. Passwords are hashed with bcrypt."
)
def register(
    request: RegisterRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    # Check email uniqueness
    if get_user_by_email(db, request.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Email '{request.email}' is already registered"
        )

    # Check username uniqueness
    if get_user_by_username(db, request.username):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Username '{request.username}' is already taken"
        )

    # Create user with hashed password
    user = User(
        username=request.username,
        email=request.email,
        hashed_password=hash_password(request.password),    # ← bcrypt hash
        full_name=request.full_name,
        role="user"    # new users are always 'user' role
    )
    db.add(user)
    db.flush()
    db.refresh(user)

    background_tasks.add_task(
        log_auth_event, request.username, "REGISTER", True
    )

    return user


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login with username and password",
    description="""
    Authenticate with username and password.
    Returns access token (30 min) and refresh token (7 days).

    **Access token**: Include in `Authorization: Bearer <token>` header.
    **Refresh token**: Use at `POST /auth/refresh` to get new access token.

    This endpoint also accepts form data (OAuth2 standard format).
    """
)
def login(
    background_tasks: BackgroundTasks,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = authenticate_user(db, form_data.username, form_data.password)

    if not user:
        background_tasks.add_task(
            log_auth_event, form_data.username, "LOGIN", False
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"}
        )

    background_tasks.add_task(
        log_auth_event, user.username, "LOGIN", True
    )

    return build_token_response(user)


@router.post(
    "/login/json",
    response_model=TokenResponse,
    summary="Login with JSON body",
    description="Alternative login endpoint accepting JSON body instead of form data."
)
def login_json(
    request: LoginRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    user = authenticate_user(db, request.username, request.password)

    if not user:
        background_tasks.add_task(
            log_auth_event, request.username, "LOGIN_JSON", False
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"}
        )

    background_tasks.add_task(
        log_auth_event, user.username, "LOGIN_JSON", True
    )

    return build_token_response(user)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh access token",
    description="""
    Use a valid refresh token to get a new access token.
    The refresh token itself must still be valid (not expired, not revoked).
    """
)
def refresh_token(
    request: RefreshRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired refresh token"
    )

    try:
        payload = decode_token(request.refresh_token)

        # Must be a refresh token, not an access token
        if payload.get("type") != "refresh":
            raise credentials_exception

        # Check if revoked
        jti = payload.get("jti")
        if jti and is_token_revoked(jti):
            raise credentials_exception

        user_id = payload.get("sub")
        if not user_id:
            raise credentials_exception

    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(
        User.id == int(user_id),
        User.is_active == True
    ).first()

    if not user:
        raise credentials_exception

    # Revoke old refresh token (one-time use)
    if jti:
        from jose import jwt as _jwt
        exp = payload.get("exp", 0)
        remaining = int(exp - datetime.utcnow().timestamp())
        revoke_token(jti, max(remaining, 0))

    background_tasks.add_task(
        log_auth_event, user.username, "REFRESH", True
    )

    return build_token_response(user)


@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="Logout",
    description="Revoke the current access token. It will no longer be accepted."
)
def logout(
    background_tasks: BackgroundTasks,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    try:
        payload = decode_token(token)
        jti = payload.get("jti")
        exp = payload.get("exp", 0)

        if jti:
            remaining = int(exp - datetime.utcnow().timestamp())
            revoke_token(jti, max(remaining, 0))

        user_id = payload.get("sub")
        if user_id:
            user = db.query(User).filter(User.id == int(user_id)).first()
            if user:
                background_tasks.add_task(
                    log_auth_event, user.username, "LOGOUT", True
                )
    except JWTError:
        pass    # token already invalid — logout is fine

    return MessageResponse(message="Successfully logged out")


@router.get(
    "/me",
    response_model=UserProfileResponse,
    summary="Get current user profile",
    description="Returns the profile of the currently authenticated user."
)
def get_me(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    try:
        payload = decode_token(token)

        # Check blacklist
        jti = payload.get("jti")
        if jti and is_token_revoked(jti):
            raise HTTPException(401, "Token has been revoked")

        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(401, "Invalid token")

    except JWTError:
        raise HTTPException(401, "Invalid or expired token")

    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(404, "User not found")

    return user


@router.put(
    "/change-password",
    response_model=MessageResponse,
    summary="Change password",
    description="Change the current user's password. Requires current password."
)
def change_password(
    request: PasswordChangeRequest,
    background_tasks: BackgroundTasks,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    try:
        payload = decode_token(token)
        user_id = payload.get("sub")
    except JWTError:
        raise HTTPException(401, "Invalid token")

    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(404, "User not found")

    # Verify current password
    if not verify_password(request.current_password, user.hashed_password):
        raise HTTPException(400, "Current password is incorrect")

    # Update to new password
    user.hashed_password = hash_password(request.new_password)
    db.flush()

    background_tasks.add_task(
        log_auth_event, user.username, "PASSWORD_CHANGE", True
    )

    return MessageResponse(
        message="Password changed successfully",
        detail="All existing sessions remain valid until they expire"
    )