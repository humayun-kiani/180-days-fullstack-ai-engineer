# ============================================================
# src/repositories/post_repo.py
# Post repository — all database operations for Post model
# ============================================================

import re
from datetime import datetime
from sqlalchemy.orm import Session, selectinload, joinedload
from sqlalchemy import func, and_, or_, desc
from src.models import Post, User, Category, Tag, Comment, PostLike


def slugify(text: str) -> str:
    """Convert title to URL-friendly slug."""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '-', text)
    return text.strip('-')


class PostRepository:
    """Repository for Post database operations."""

    def __init__(self, session: Session):
        self.session = session

    # ─── READ ─────────────────────────────────────────────────

    def get_by_id(self, post_id: int) -> Post | None:
        """Get post by ID with author, category, and tags loaded."""
        return (
            self.session.query(Post)
            .options(
                joinedload(Post.author),
                joinedload(Post.category),
                selectinload(Post.tags)
            )
            .filter(Post.id == post_id, Post.is_deleted == False)
            .first()
        )

    def get_by_slug(self, slug: str) -> Post | None:
        """Get published post by URL slug."""
        return (
            self.session.query(Post)
            .options(
                joinedload(Post.author),
                joinedload(Post.category),
                selectinload(Post.tags),
                selectinload(Post.comments).joinedload(Comment.author)
            )
            .filter(Post.slug == slug, Post.is_deleted == False)
            .first()
        )

    def get_published(
        self,
        page: int = 1,
        per_page: int = 10,
        category_id: int | None = None
    ) -> tuple[list[Post], int]:
        """
        Get paginated published posts.

        Returns:
            tuple: (list of posts, total count)
        """
        query = (
            self.session.query(Post)
            .options(
                joinedload(Post.author),
                joinedload(Post.category),
                selectinload(Post.tags)
            )
            .filter(
                Post.status == "published",
                Post.is_deleted == False
            )
        )

        if category_id:
            query = query.filter(Post.category_id == category_id)

        total = query.count()
        posts = (
            query
            .order_by(Post.published_at.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )
        return posts, total

    def get_by_author(self, author_id: int, include_drafts: bool = False) -> list[Post]:
        """Get all posts by a specific author."""
        query = (
            self.session.query(Post)
            .options(joinedload(Post.category), selectinload(Post.tags))
            .filter(Post.author_id == author_id, Post.is_deleted == False)
        )
        if not include_drafts:
            query = query.filter(Post.status == "published")
        return query.order_by(Post.created_at.desc()).all()

    def get_popular(self, limit: int = 5) -> list[Post]:
        """Get most viewed published posts."""
        return (
            self.session.query(Post)
            .options(joinedload(Post.author))
            .filter(Post.status == "published", Post.is_deleted == False)
            .order_by(Post.views.desc())
            .limit(limit)
            .all()
        )

    def search(self, query: str, limit: int = 20) -> list[Post]:
        """Search posts by title or excerpt."""
        term = f"%{query}%"
        return (
            self.session.query(Post)
            .options(joinedload(Post.author))
            .filter(
                Post.status == "published",
                Post.is_deleted == False,
                or_(
                    Post.title.ilike(term),
                    Post.excerpt.ilike(term),
                    Post.content.ilike(term)
                )
            )
            .order_by(Post.views.desc())
            .limit(limit)
            .all()
        )

    def get_statistics(self) -> dict:
        """Get aggregate statistics about all posts."""
        result = self.session.query(
            func.count(Post.id).label("total"),
            func.count(Post.id).filter(Post.status == "published").label("published"),
            func.count(Post.id).filter(Post.status == "draft").label("drafts"),
            func.coalesce(func.sum(Post.views), 0).label("total_views"),
            func.coalesce(func.avg(Post.views), 0).label("avg_views"),
            func.coalesce(func.max(Post.views), 0).label("max_views")
        ).filter(Post.is_deleted == False).one()

        return {
            "total": result.total,
            "published": result.published,
            "drafts": result.drafts,
            "total_views": int(result.total_views),
            "avg_views": round(float(result.avg_views), 1),
            "max_views": int(result.max_views)
        }

    def get_by_tag(self, tag_name: str, limit: int = 10) -> list[Post]:
        """Get posts with a specific tag."""
        return (
            self.session.query(Post)
            .join(Post.tags)
            .options(joinedload(Post.author))
            .filter(
                Tag.name == tag_name.lower(),
                Post.status == "published",
                Post.is_deleted == False
            )
            .order_by(Post.published_at.desc())
            .limit(limit)
            .all()
        )

    def get_category_stats(self) -> list[dict]:
        """Get post statistics per category."""
        results = (
            self.session.query(
                Category.name.label("category"),
                Category.color,
                func.count(Post.id).label("post_count"),
                func.coalesce(func.sum(Post.views), 0).label("total_views"),
                func.coalesce(func.avg(Post.views), 0).label("avg_views")
            )
            .outerjoin(Post, and_(
                Post.category_id == Category.id,
                Post.status == "published",
                Post.is_deleted == False
            ))
            .group_by(Category.id, Category.name, Category.color)
            .order_by(func.coalesce(func.sum(Post.views), 0).desc())
            .all()
        )
        return [
            {
                "category": r.category,
                "color": r.color,
                "post_count": r.post_count,
                "total_views": int(r.total_views),
                "avg_views": round(float(r.avg_views), 1)
            }
            for r in results
        ]

    # ─── WRITE ────────────────────────────────────────────────

    def create(
        self,
        author_id: int,
        title: str,
        content: str,
        category_id: int | None = None,
        excerpt: str | None = None,
        status: str = "draft",
        tag_names: list[str] | None = None
    ) -> Post:
        """Create a new post with optional tags."""
        slug = slugify(title)

        # Ensure slug is unique
        existing = self.session.query(Post).filter(Post.slug == slug).first()
        if existing:
            slug = f"{slug}-{int(datetime.utcnow().timestamp())}"

        post = Post(
            author_id=author_id,
            title=title,
            slug=slug,
            content=content,
            excerpt=excerpt or content[:200],
            category_id=category_id,
            status=status,
        )
        post.reading_time = post.calculate_reading_time()

        if status == "published":
            post.published_at = datetime.utcnow()

        self.session.add(post)
        self.session.flush()

        # Handle tags
        if tag_names:
            self._set_tags(post, tag_names)

        return post

    def publish(self, post: Post) -> None:
        """Publish a draft post."""
        post.status = "published"
        post.published_at = datetime.utcnow()

    def increment_views(self, post: Post) -> None:
        """Increment view counter."""
        post.views += 1

    def toggle_like(self, post: Post, user_id: int) -> bool:
        """
        Toggle like on a post.

        Returns:
            bool: True if liked, False if unliked.
        """
        existing_like = self.session.query(PostLike).filter(
            PostLike.post_id == post.id,
            PostLike.user_id == user_id
        ).first()

        if existing_like:
            self.session.delete(existing_like)
            return False
        else:
            like = PostLike(post_id=post.id, user_id=user_id)
            self.session.add(like)
            return True

    def soft_delete(self, post: Post) -> None:
        """Soft delete a post."""
        post.soft_delete()

    def _set_tags(self, post: Post, tag_names: list[str]) -> None:
        """Set tags on a post, creating new tags as needed."""
        tags = []
        for tag_name in tag_names:
            tag_name = tag_name.lower().strip()
            tag = self.session.query(Tag).filter(Tag.name == tag_name).first()
            if not tag:
                tag = Tag(name=tag_name, slug=slugify(tag_name))
                self.session.add(tag)
                self.session.flush()
            tags.append(tag)
        post.tags = tags

    def count(self) -> int:
        """Count all non-deleted posts."""
        return self.session.query(Post).filter(Post.is_deleted == False).count()