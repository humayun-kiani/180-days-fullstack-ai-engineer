# ============================================================
# src/models.py
# SQLAlchemy ORM Models — Blog Platform
# ============================================================

from datetime import datetime
from typing import Optional
from sqlalchemy import (
    String, Integer, Float, Boolean, Text,
    DateTime, ForeignKey, Table, Column,
    UniqueConstraint, CheckConstraint, Index
)
from sqlalchemy.orm import (
    DeclarativeBase, Mapped, mapped_column,
    relationship, validates
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY, TSVECTOR
import uuid


# ─── Base Class ─────────────────────────────────────────────

class Base(DeclarativeBase):
    """Declarative base for all models."""
    pass


# ─── Mixins — Reusable Column Groups ───────────────────────

class TimestampMixin:
    """Add created_at and updated_at to any model."""
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


class SoftDeleteMixin:
    """Add soft delete support to any model."""
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    def soft_delete(self):
        self.is_deleted = True
        self.deleted_at = datetime.utcnow()


# ─── Association Tables (M2M) ───────────────────────────────

post_tags_table = Table(
    "post_tags",
    Base.metadata,
    Column("post_id", Integer, ForeignKey("posts.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True)
)

user_follows_table = Table(
    "user_follows",
    Base.metadata,
    Column("follower_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("following_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
)


# ─── USER MODEL ─────────────────────────────────────────────

class User(TimestampMixin, Base):
    """
    User model — represents registered users.

    Relationships:
        posts: posts authored by this user (one-to-many)
        comments: comments written by this user (one-to-many)
        likes: posts liked by this user (many-to-many via PostLike)
        following: users this user follows (many-to-many self-referential)
        followers: users who follow this user (many-to-many self-referential)
    """
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    display_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    bio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    role: Mapped[str] = mapped_column(String(20), default="reader", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Table constraints
    __table_args__ = (
        CheckConstraint("role IN ('reader', 'author', 'editor', 'admin')", name="valid_role"),
        CheckConstraint("LENGTH(username) >= 3", name="username_min_length"),
        Index("idx_users_email_lower", "email"),
    )

    # Relationships
    posts: Mapped[list["Post"]] = relationship(
        "Post",
        back_populates="author",
        cascade="all, delete-orphan",
        lazy="select"
    )
    comments: Mapped[list["Comment"]] = relationship(
        "Comment",
        back_populates="author",
        cascade="all, delete-orphan"
    )
    likes: Mapped[list["PostLike"]] = relationship(
        "PostLike",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    # Self-referential M2M — following/followers
    following: Mapped[list["User"]] = relationship(
        "User",
        secondary=user_follows_table,
        primaryjoin="User.id == user_follows.c.follower_id",
        secondaryjoin="User.id == user_follows.c.following_id",
        back_populates="followers"
    )
    followers: Mapped[list["User"]] = relationship(
        "User",
        secondary=user_follows_table,
        primaryjoin="User.id == user_follows.c.following_id",
        secondaryjoin="User.id == user_follows.c.follower_id",
        back_populates="following"
    )

    @validates("email")
    def validate_email(self, key, value):
        """Ensure email is lowercase."""
        return value.lower().strip()

    @validates("username")
    def validate_username(self, key, value):
        """Ensure username has no spaces."""
        return value.strip().lower()

    @property
    def post_count(self) -> int:
        return len([p for p in self.posts if p.status == "published"])

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}')>"


# ─── CATEGORY MODEL ─────────────────────────────────────────

class Category(TimestampMixin, Base):
    """
    Post category model.

    Supports nested categories via parent_id self-reference.
    """
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(120), unique=True, nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    color: Mapped[str] = mapped_column(String(7), default="#3B82F6")
    icon: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    parent_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("categories.id"), nullable=True
    )

    # Self-referential relationship for nested categories
    parent: Mapped[Optional["Category"]] = relationship(
        "Category",
        back_populates="children",
        remote_side="Category.id"
    )
    children: Mapped[list["Category"]] = relationship(
        "Category",
        back_populates="parent"
    )
    posts: Mapped[list["Post"]] = relationship(
        "Post",
        back_populates="category"
    )

    def __repr__(self):
        return f"<Category(id={self.id}, name='{self.name}')>"


# ─── TAG MODEL ──────────────────────────────────────────────

class Tag(Base):
    """Simple tag model for post tagging."""
    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(60), unique=True, nullable=False)

    # M2M with Post through post_tags_table
    posts: Mapped[list["Post"]] = relationship(
        "Post",
        secondary=post_tags_table,
        back_populates="tags"
    )

    def __repr__(self):
        return f"<Tag(name='{self.name}')>"


# ─── POST MODEL ─────────────────────────────────────────────

class Post(TimestampMixin, SoftDeleteMixin, Base):
    """
    Blog post model — the core entity.

    Has relationships to: User (author), Category, Tag (M2M),
    Comment (one-to-many), PostLike (one-to-many).
    """
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    author_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    category_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("categories.id", ondelete="SET NULL"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    slug: Mapped[str] = mapped_column(String(350), unique=True, nullable=False)
    excerpt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    cover_image: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="draft", nullable=False)
    views: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    reading_time: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    __table_args__ = (
        CheckConstraint(
            "status IN ('draft', 'published', 'archived', 'scheduled')",
            name="valid_post_status"
        ),
        CheckConstraint("views >= 0", name="non_negative_views"),
        Index("idx_posts_author", "author_id"),
        Index("idx_posts_status", "status"),
        Index(
            "idx_posts_published",
            "published_at",
            postgresql_where=text("status = 'published'")
        ),
    )

    # Relationships
    author: Mapped["User"] = relationship(
        "User",
        back_populates="posts"
    )
    category: Mapped[Optional["Category"]] = relationship(
        "Category",
        back_populates="posts"
    )
    tags: Mapped[list["Tag"]] = relationship(
        "Tag",
        secondary=post_tags_table,
        back_populates="posts",
        lazy="select"
    )
    comments: Mapped[list["Comment"]] = relationship(
        "Comment",
        back_populates="post",
        cascade="all, delete-orphan",
        order_by="Comment.created_at"
    )
    likes: Mapped[list["PostLike"]] = relationship(
        "PostLike",
        back_populates="post",
        cascade="all, delete-orphan"
    )

    @property
    def like_count(self) -> int:
        return len(self.likes)

    @property
    def comment_count(self) -> int:
        return len(self.comments)

    @property
    def is_published(self) -> bool:
        return self.status == "published"

    def calculate_reading_time(self) -> int:
        """Estimate reading time in minutes."""
        word_count = len(self.content.split())
        return max(1, round(word_count / 200))

    def __repr__(self):
        return f"<Post(id={self.id}, title='{self.title[:30]}...', status='{self.status}')>"


# ─── COMMENT MODEL ──────────────────────────────────────────

class Comment(TimestampMixin, Base):
    """
    Comment model — supports nested replies via parent_id.
    """
    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    post_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("posts.id", ondelete="CASCADE"), nullable=False
    )
    author_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    parent_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("comments.id", ondelete="CASCADE"), nullable=True
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    is_approved: Mapped[bool] = mapped_column(Boolean, default=True)
    like_count: Mapped[int] = mapped_column(Integer, default=0)

    __table_args__ = (
        CheckConstraint("LENGTH(content) >= 1", name="non_empty_comment"),
        Index("idx_comments_post", "post_id"),
        Index("idx_comments_author", "author_id"),
    )

    # Relationships
    post: Mapped["Post"] = relationship("Post", back_populates="comments")
    author: Mapped["User"] = relationship("User", back_populates="comments")

    # Self-referential for nested comments
    parent: Mapped[Optional["Comment"]] = relationship(
        "Comment",
        back_populates="replies",
        remote_side="Comment.id"
    )
    replies: Mapped[list["Comment"]] = relationship(
        "Comment",
        back_populates="parent",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Comment(id={self.id}, post_id={self.post_id})>"


# ─── POST LIKE MODEL ────────────────────────────────────────

class PostLike(Base):
    """
    Post like model — tracks which users liked which posts.
    Composite PK prevents duplicate likes.
    """
    __tablename__ = "post_likes"

    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    post_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("posts.id", ondelete="CASCADE"), primary_key=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User"] = relationship("User", back_populates="likes")
    post: Mapped["Post"] = relationship("Post", back_populates="likes")

    def __repr__(self):
        return f"<PostLike(user={self.user_id}, post={self.post_id})>"