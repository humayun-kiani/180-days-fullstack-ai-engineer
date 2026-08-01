# ============================================================
# app/api/deps.py — Updated with real JWT auth
# ============================================================

from typing import Annotated, Optional
from fastapi import Depends, HTTPException, status, Query
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError

from app.core.security import decode_token
from app.core.token_blacklist import is_token_revoked
from app.db.session import get_db
from app.db.models.user import User
from app.core.config import settings

# ─── Database ───────────────────────────────────────────────

DB = Annotated[Session, Depends(get_db)]

# ─── OAuth2 ─────────────────────────────────────────────────

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login",
    auto_error=False    # False allows optional auth
)

oauth2_required = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login",
    auto_error=True    # True raises 401 if no token
)

# ─── User Dependencies ───────────────────────────────────────

def get_current_user(
    token: str = Depends(oauth2_required),
    db: Session = Depends(get_db)
) -> User:
    """
    Extract and validate the current user from JWT token.

    This dependency:
    1. Extracts Bearer token from Authorization header
    2. Decodes and verifies JWT signature
    3. Checks token expiry
    4. Checks token blacklist (logout)
    5. Loads user from database
    6. Verifies user is active

    Inject into any endpoint that requires authentication.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"}
    )

    try:
        payload = decode_token(token)

        # Verify this is an access token (not a refresh token)
        if payload.get("type") != "access":
            raise credentials_exception

        # Check blacklist
        jti = payload.get("jti")
        if jti and is_token_revoked(jti):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked (logged out)",
                headers={"WWW-Authenticate": "Bearer"}
            )

        user_id: str = payload.get("sub")
        if not user_id:
            raise credentials_exception

    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.id == int(user_id)).first()

    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account is deactivated"
        )

    return user


def get_current_user_optional(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Like get_current_user but returns None if no token provided.
    Useful for endpoints that behave differently when authenticated.
    """
    if not token:
        return None
    try:
        return get_current_user(token, db)
    except HTTPException:
        return None


# ─── Role-Based Access ───────────────────────────────────────

ROLE_HIERARCHY = {
    "reader": 0,
    "user": 1,
    "editor": 2,
    "admin": 3
}


def require_role(minimum_role: str):
    """
    Dependency factory for role-based access control.

    Args:
        minimum_role: The minimum role required ('reader', 'user', 'editor', 'admin').

    Returns:
        FastAPI dependency function.

    Usage:
        @router.delete("/{id}")
        def delete(user = Depends(require_role("admin"))):
            ...
    """
    def check_role(
        current_user: User = Depends(get_current_user)
    ) -> User:
        user_level = ROLE_HIERARCHY.get(current_user.role, 0)
        required_level = ROLE_HIERARCHY.get(minimum_role, 0)

        if user_level < required_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"This action requires '{minimum_role}' role or higher. "
                    f"Your current role: '{current_user.role}'"
                )
            )
        return current_user

    return check_role


# ─── Pagination ──────────────────────────────────────────────

class Pagination:
    def __init__(
        self,
        page: int = Query(1, ge=1),
        per_page: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE)
    ):
        self.page = page
        self.per_page = per_page

    @property
    def skip(self) -> int:
        return (self.page - 1) * self.per_page

    @property
    def limit(self) -> int:
        return self.per_page


# ─── Type Aliases ────────────────────────────────────────────

PageParams = Annotated[Pagination, Depends(Pagination)]
CurrentUser = Annotated[User, Depends(get_current_user)]
OptionalUser = Annotated[Optional[User], Depends(get_current_user_optional)]
AdminUser = Annotated[User, Depends(require_role("admin"))]
EditorUser = Annotated[User, Depends(require_role("editor"))]