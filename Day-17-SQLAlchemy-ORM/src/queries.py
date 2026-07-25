# ============================================================
# src/queries.py
# Demonstrate ORM query capabilities
# ============================================================

from sqlalchemy.orm import Session, selectinload, joinedload
from sqlalchemy import func, and_, or_, desc, text
from src.models import User, Post, Category, Tag, Comment, PostLike
from src.repositories.user_repo import UserRepository
from src.repositories.post_repo import PostRepository


def run_demo_queries(session: Session) -> dict:
    """Run all demonstration queries."""
    user_repo = UserRepository(session)
    post_repo = PostRepository(session)
    results = {}

    # ── Overview ──
    results["overview"] = {
        "users": user_repo.count(),
        "posts": post_repo.count(),
        "published": session.query(Post).filter(Post.status == "published").count(),
        "comments": session.query(Comment).count(),
        "likes": session.query(PostLike).count(),
        "categories": session.query(Category).count(),
        "tags": session.query(Tag).count(),
    }

    # ── Top authors ──
    results["top_authors"] = user_repo.get_top_authors(limit=8)

    # ── Popular posts ──
    popular = post_repo.get_popular(limit=8)
    results["popular_posts"] = [
        {
            "title": p.title,
            "author": p.author.username if p.author else "unknown",
            "category": p.category.name if p.category else "uncategorized",
            "views": p.views,
            "likes": p.like_count,
            "comments": p.comment_count,
            "tags": [t.name for t in p.tags],
            "reading_time": p.reading_time
        }
        for p in popular
    ]

    # ── Category statistics ──
    results["category_stats"] = post_repo.get_category_stats()

    # ── Post statistics ──
    results["post_stats"] = post_repo.get_statistics()

    # ── Users by role ──
    results["users_by_role"] = user_repo.count_by_role()

    # ── Search demo ──
    search_results = post_repo.search("python", limit=5)
    results["search_python"] = [
        {"title": p.title, "views": p.views}
        for p in search_results
    ]

    # ── Tag breakdown ──
    tag_stats = (
        session.query(
            Tag.name,
            func.count(Post.id).label("post_count"),
            func.coalesce(func.sum(Post.views), 0).label("total_views")
        )
        .join(Tag.posts)
        .filter(Post.status == "published")
        .group_by(Tag.name)
        .order_by(func.count(Post.id).desc())
        .limit(10)
        .all()
    )
    results["tag_stats"] = [
        {"tag": r.name, "posts": r.post_count, "views": int(r.total_views)}
        for r in tag_stats
    ]

    # ── Comment threads demo ──
    comments_with_replies = (
        session.query(Comment)
        .options(
            joinedload(Comment.author),
            selectinload(Comment.replies).joinedload(Comment.author)
        )
        .filter(Comment.parent_id.is_(None))
        .limit(5)
        .all()
    )
    results["comment_threads"] = [
        {
            "author": c.author.username if c.author else "unknown",
            "content": c.content[:80] + "..." if len(c.content) > 80 else c.content,
            "replies": len(c.replies)
        }
        for c in comments_with_replies
    ]

    # ── N+1 demonstration ──
    # Without eager loading — counts queries needed
    results["eager_loading_demo"] = {
        "note": "With joinedload/selectinload, loading 15 posts with authors = 2 queries",
        "naive_approach": "Without eager loading = 1 + 15 = 16 queries (N+1 problem)"
    }

    return results