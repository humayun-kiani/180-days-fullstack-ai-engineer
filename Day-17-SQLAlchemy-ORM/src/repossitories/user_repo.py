# ============================================================
# src/repositories/user_repo.py
# User repository — all database operations for User model
# ============================================================

from datetime import datetime
from sqlalchemy.orm import Session, selectinload, joinedload
from sqlalchemy import func, and_
from src.models import User, Post, Comment, PostLike


class UserRepository:
    """
    Repository for User database operations.

    Following the Repository Pattern:
    - All SQL/ORM logic lives here
    - Business logic stays in service layer
    - Easy to test by mocking this class
    """

    def __init__(self, session: Session):
        self.session = session

    # ─── READ ─────────────────────────────────────────────────

    def get_by_id(self, user_id: int) -> User | None:
        """Get user by primary key."""
        return self.session.get(User, user_id)

    def get_by_email(self, email: str) -> User | None:
        """Get user by email (case-insensitive)."""
        return self.session.query(User).filter(
            func.lower(User.email) == email.lower()
        ).first()

    def get_by_username(self, username: str) -> User | None:
        """Get user by username."""
        return self.session.query(User).filter(
            User.username == username.lower()
        ).first()

    def get_all_active(self, limit: int = 50) -> list[User]:
        """Get all active users."""
        return (
            self.session.query(User)
            .filter(User.is_active == True)
            .order_by(User.created_at.desc())
            .limit(limit)
            .all()
        )

    def get_with_posts(self, user_id: int) -> User | None:
        """Get user with their posts eagerly loaded (avoids N+1)."""
        return (
            self.session.query(User)
            .options(selectinload(User.posts))
            .filter(User.id == user_id)
            .first()
        )

    def get_with_full_profile(self, user_id: int) -> User | None:
        """Get user with posts, comments, and followers eagerly loaded."""
        return (
            self.session.query(User)
            .options(
                selectinload(User.posts).selectinload(Post.tags),
                selectinload(User.comments),
                selectinload(User.followers),
                selectinload(User.following)
            )
            .filter(User.id == user_id)
            .first()
        )

    def get_top_authors(self, limit: int = 10) -> list[dict]:
        """Get top authors by total post views."""
        results = (
            self.session.query(
                User.id,
                User.username,
                User.display_name,
                func.count(Post.id).label("post_count"),
                func.coalesce(func.sum(Post.views), 0).label("total_views"),
                func.coalesce(func.avg(Post.views), 0).label("avg_views")
            )
            .outerjoin(Post, and_(
                Post.author_id == User.id,
                Post.status == "published"
            ))
            .filter(User.is_active == True)
            .group_by(User.id, User.username, User.display_name)
            .order_by(func.coalesce(func.sum(Post.views), 0).desc())
            .limit(limit)
            .all()
        )
        return [
            {
                "id": r.id,
                "username": r.username,
                "display_name": r.display_name,
                "post_count": r.post_count,
                "total_views": int(r.total_views),
                "avg_views": round(float(r.avg_views), 1)
            }
            for r in results
        ]

    def count_by_role(self) -> dict[str, int]:
        """Count users by role."""
        results = (
            self.session.query(User.role, func.count(User.id))
            .group_by(User.role)
            .all()
        )
        return {role: count for role, count in results}

    def search(self, query: str, limit: int = 20) -> list[User]:
        """Search users by username or display name."""
        search_term = f"%{query.lower()}%"
        return (
            self.session.query(User)
            .filter(
                User.is_active == True,
                (User.username.ilike(search_term)) |
                (User.display_name.ilike(search_term))
            )
            .limit(limit)
            .all()
        )

    # ─── WRITE ────────────────────────────────────────────────

    def create(
        self,
        username: str,
        email: str,
        password_hash: str,
        display_name: str | None = None,
        role: str = "reader"
    ) -> User:
        """Create a new user."""
        user = User(
            username=username.lower().strip(),
            email=email.lower().strip(),
            password_hash=password_hash,
            display_name=display_name or username,
            role=role
        )
        self.session.add(user)
        self.session.flush()   # get the ID without committing
        return user

    def update_last_login(self, user: User) -> None:
        """Update user's last login timestamp."""
        user.last_login_at = datetime.utcnow()

    def deactivate(self, user: User) -> None:
        """Deactivate a user account."""
        user.is_active = False

    def follow(self, follower: User, target: User) -> bool:
        """Follow another user. Returns False if already following."""
        if target in follower.following:
            return False
        follower.following.append(target)
        return True

    def unfollow(self, follower: User, target: User) -> bool:
        """Unfollow a user. Returns False if not following."""
        if target not in follower.following:
            return False
        follower.following.remove(target)
        return True

    def count(self) -> int:
        """Count total users."""
        return self.session.query(User).count()