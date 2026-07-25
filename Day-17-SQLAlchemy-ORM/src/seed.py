# ============================================================
# src/seed.py
# Seed the database with realistic blog data
# ============================================================

import random
import hashlib
from datetime import datetime, timedelta
from faker import Faker

from src.models import User, Category, Tag, Post, Comment, PostLike

fake = Faker()
random.seed(42)


def fake_password(pw="password123"):
    return hashlib.sha256(pw.encode()).hexdigest()


CATEGORIES_DATA = [
    ("Technology", "technology", "#3B82F6"),
    ("AI & Machine Learning", "ai-machine-learning", "#8B5CF6"),
    ("Web Development", "web-development", "#10B981"),
    ("Data Science", "data-science", "#F59E0B"),
    ("DevOps", "devops", "#EF4444"),
    ("Career", "career", "#EC4899"),
]

TAGS_DATA = [
    "python", "javascript", "sql", "docker", "postgresql",
    "fastapi", "react", "machine-learning", "ai", "tutorial",
    "beginner", "advanced", "devops", "career", "tips",
]

TITLES = [
    "Getting Started with FastAPI: A Complete Guide",
    "PostgreSQL Performance Tuning Tips",
    "Docker for Python Developers",
    "Building AI Applications with LangChain",
    "SQLAlchemy ORM: Relationships Explained",
    "Async Python: asyncio vs Threading",
    "React Hooks: useState and useEffect",
    "Machine Learning Model Deployment",
    "CI/CD Pipeline with GitHub Actions",
    "Redis Caching Best Practices",
    "Understanding Vector Embeddings",
    "Python Testing with pytest",
    "Database Migrations with Alembic",
    "Building REST APIs with FastAPI",
    "Kubernetes for Beginners",
]

ROLES = ["author"] * 6 + ["editor"] * 2 + ["admin"] * 1 + ["reader"] * 3


def seed_all(session) -> dict:
    """Seed all data and return created object counts."""

    print("\n  Seeding blog ORM database...")
    counts = {}

    # ── Categories ──
    categories = []
    for name, slug, color in CATEGORIES_DATA:
        cat = Category(name=name, slug=slug, color=color,
                       description=f"Articles about {name}")
        session.add(cat)
        categories.append(cat)
    session.flush()
    counts["categories"] = len(categories)
    print(f"  ✅ {len(categories)} categories")

    # ── Tags ──
    tags = []
    for tag_name in TAGS_DATA:
        tag = Tag(name=tag_name, slug=tag_name.replace(" ", "-"))
        session.add(tag)
        tags.append(tag)
    session.flush()
    counts["tags"] = len(tags)
    print(f"  ✅ {len(tags)} tags")

    # ── Users ──
    users = []
    for i, role in enumerate(ROLES):
        first = fake.first_name()
        last = fake.last_name()
        username = f"{first.lower()}{i}"
        user = User(
            username=username,
            email=f"{username}@blog.example.com",
            password_hash=fake_password(),
            display_name=f"{first} {last}",
            bio=fake.paragraph(nb_sentences=2),
            role=role,
            is_active=True,
            email_verified=True
        )
        session.add(user)
        users.append(user)
    session.flush()
    counts["users"] = len(users)
    print(f"  ✅ {len(users)} users")

    # ── Posts ──
    author_users = [u for u in users if u.role in ("author", "editor", "admin")]
    posts = []

    for i, title in enumerate(TITLES):
        author = random.choice(author_users)
        category = random.choice(categories)
        post_tags = random.sample(tags, random.randint(2, 5))
        status = random.choice(["published"] * 8 + ["draft"] * 2)
        content = "\n\n".join([fake.paragraph(nb_sentences=6) for _ in range(4)])

        post = Post(
            author_id=author.id,
            category_id=category.id,
            title=title,
            slug=f"{title.lower().replace(' ', '-').replace(':', '').replace(',', '')}-{i}",
            excerpt=fake.paragraph(nb_sentences=2),
            content=content,
            status=status,
            views=random.randint(0, 5000) if status == "published" else 0,
            reading_time=max(1, len(content.split()) // 200),
            published_at=(
                datetime.utcnow() - timedelta(days=random.randint(1, 90))
                if status == "published" else None
            ),
            tags=post_tags
        )
        session.add(post)
        posts.append(post)

    session.flush()
    counts["posts"] = len(posts)
    print(f"  ✅ {len(posts)} posts")

    # ── Comments ──
    comment_count = 0
    for post in posts[:12]:
        num_comments = random.randint(1, 6)
        root_comments = []
        for _ in range(num_comments):
            commenter = random.choice(users)
            parent = random.choice(root_comments) if root_comments and random.random() < 0.3 else None
            comment = Comment(
                post_id=post.id,
                author_id=commenter.id,
                parent_id=parent.id if parent else None,
                content=fake.paragraph(nb_sentences=random.randint(1, 3))
            )
            session.add(comment)
            root_comments.append(comment)
            comment_count += 1
    session.flush()
    counts["comments"] = comment_count
    print(f"  ✅ {comment_count} comments")

    # ── Likes ──
    like_count = 0
    for post in posts:
        likers = random.sample(users, min(random.randint(0, 10), len(users)))
        for user in likers:
            like = PostLike(user_id=user.id, post_id=post.id)
            session.add(like)
            like_count += 1
    session.flush()
    counts["likes"] = like_count
    print(f"  ✅ {like_count} likes")

    # ── Follows ──
    follow_count = 0
    for user in users:
        targets = [u for u in users if u.id != user.id]
        following = random.sample(targets, min(3, len(targets)))
        for target in following:
            if target not in user.following:
                user.following.append(target)
                follow_count += 1
    session.flush()
    counts["follows"] = follow_count
    print(f"  ✅ {follow_count} follows")

    print(f"\n  🎉 Database seeded!")
    return counts