# ============================================================
# src/seed.py
# Seed the blog platform with realistic data
# ============================================================

import random
import hashlib
import re
from datetime import datetime, timedelta
from faker import Faker

fake = Faker()
random.seed(42)

CATEGORIES = [
    ("Technology", "technology", "#3B82F6", "💻"),
    ("Artificial Intelligence", "artificial-intelligence", "#8B5CF6", "🤖"),
    ("Web Development", "web-development", "#10B981", "🌐"),
    ("Data Science", "data-science", "#F59E0B", "📊"),
    ("DevOps", "devops", "#EF4444", "⚙️"),
    ("Career & Growth", "career-growth", "#EC4899", "🚀"),
    ("Python", "python", "#14B8A6", "🐍"),
    ("Tutorial", "tutorial", "#F97316", "📚"),
]

TAGS_POOL = [
    "python", "javascript", "sql", "docker", "kubernetes",
    "machine-learning", "deep-learning", "nlp", "fastapi", "react",
    "postgresql", "redis", "aws", "devops", "ci-cd",
    "tutorial", "beginner", "advanced", "tips", "best-practices",
    "ai", "llm", "gpt", "langchain", "vector-database"
]

SAMPLE_TITLES = [
    "Building a RAG System with Python and LangChain",
    "PostgreSQL Performance Tuning: 10 Essential Tips",
    "Docker Compose for Full Stack Developers",
    "Async Python: Threading vs asyncio vs Multiprocessing",
    "Building Production APIs with FastAPI",
    "Redis Caching Strategies for Web Applications",
    "Machine Learning Model Deployment Guide",
    "SQL Window Functions Explained with Examples",
    "Python Decorators: A Complete Guide",
    "Kubernetes for Beginners: From Zero to Deploy",
    "Understanding Vector Embeddings in AI",
    "Building a Real-time Chat with WebSockets",
    "Database Migrations Best Practices",
    "Python Testing with pytest: Complete Tutorial",
    "CI/CD Pipeline with GitHub Actions",
    "Building AI Agents with LangGraph",
    "FastAPI vs Flask vs Django: Which to Choose?",
    "PostgreSQL JSONB: Power of Document Storage",
    "Python Virtual Environments: Complete Guide",
    "Understanding the Transformer Architecture",
]


def slugify(text):
    """Convert text to URL-friendly slug."""
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '-', text)
    return text.strip('-')


def fake_password_hash(password="password123"):
    """Simulate a password hash."""
    return hashlib.sha256(password.encode()).hexdigest()


def seed_database(conn):
    """Seed the database with realistic blog data."""
    cursor = conn.cursor()
    print("\n  Seeding blog platform database...")

    # ── 1. Categories ──
    cat_ids = {}
    for name, slug, color, icon in CATEGORIES:
        cursor.execute("""
            INSERT INTO categories (name, slug, description, color, icon)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (slug) DO NOTHING
            RETURNING id
        """, (name, slug, f"Articles about {name}", color, icon))
        result = cursor.fetchone()
        if result:
            cat_ids[name] = result["id"]

    conn.commit()
    print(f"  ✅ Inserted {len(cat_ids)} categories.")

    # ── 2. Users ──
    user_ids = []
    roles = ["author"] * 8 + ["editor"] * 2 + ["admin"] * 1

    for i, role in enumerate(roles):
        first = fake.first_name()
        last = fake.last_name()
        username = f"{first.lower()}{last.lower()}{i}"[:30]
        email = f"{username}@{fake.domain_name()}"

        cursor.execute("""
            INSERT INTO users (username, email, password_hash, display_name,
                              bio, role, is_active, email_verified)
            VALUES (%s, %s, %s, %s, %s, %s, TRUE, TRUE)
            ON CONFLICT (email) DO NOTHING
            RETURNING id
        """, (
            username,
            email,
            fake_password_hash(),
            f"{first} {last}",
            fake.paragraph(nb_sentences=2),
            role
        ))
        result = cursor.fetchone()
        if result:
            user_ids.append(result["id"])

    conn.commit()
    print(f"  ✅ Inserted {len(user_ids)} users.")

    # ── 3. Posts ──
    post_ids = []
    cat_list = list(cat_ids.values())

    for i, title in enumerate(SAMPLE_TITLES):
        author_id = random.choice(user_ids)
        cat_id = random.choice(cat_list)
        slug = f"{slugify(title)}-{i}"
        tags = random.sample(TAGS_POOL, random.randint(3, 6))
        content = "\n\n".join([fake.paragraph(nb_sentences=8) for _ in range(5)])
        status = random.choice(["published"] * 7 + ["draft"] * 2 + ["archived"] * 1)
        views = random.randint(0, 5000) if status == "published" else 0
        reading_time = max(1, len(content.split()) // 200)

        published_at = None
        if status == "published":
            published_at = datetime.now() - timedelta(days=random.randint(1, 180))

        cursor.execute("""
            INSERT INTO posts (author_id, category_id, title, slug, excerpt,
                              content, status, tags, views, reading_time,
                              published_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (slug) DO NOTHING
            RETURNING id
        """, (
            str(author_id),
            cat_id,
            title,
            slug,
            fake.paragraph(nb_sentences=2),
            content,
            status,
            tags,
            views,
            reading_time,
            published_at
        ))
        result = cursor.fetchone()
        if result:
            post_ids.append(result["id"])

    conn.commit()
    print(f"  ✅ Inserted {len(post_ids)} posts.")

    # ── 4. Comments ──
    comment_count = 0
    for post_id in post_ids[:15]:    # comment on first 15 posts
        num_comments = random.randint(1, 8)
        parent_comments = []

        for _ in range(num_comments):
            author_id = random.choice(user_ids)
            parent_id = random.choice(parent_comments) if parent_comments and random.random() < 0.3 else None

            cursor.execute("""
                INSERT INTO comments (post_id, author_id, parent_id, content)
                VALUES (%s, %s, %s, %s)
                RETURNING id
            """, (
                str(post_id),
                str(author_id),
                str(parent_id) if parent_id else None,
                fake.paragraph(nb_sentences=random.randint(1, 4))
            ))
            result = cursor.fetchone()
            if result:
                parent_comments.append(result["id"])
                comment_count += 1

    conn.commit()
    print(f"  ✅ Inserted {comment_count} comments.")

    # ── 5. Likes ──
    like_count = 0
    for post_id in post_ids:
        num_likes = random.randint(0, 20)
        liking_users = random.sample(user_ids, min(num_likes, len(user_ids)))
        for user_id in liking_users:
            try:
                cursor.execute("""
                    INSERT INTO post_likes (user_id, post_id)
                    VALUES (%s, %s)
                    ON CONFLICT DO NOTHING
                """, (str(user_id), str(post_id)))
                like_count += 1
            except Exception:
                pass

    conn.commit()
    print(f"  ✅ Inserted {like_count} likes.")

    # ── 6. Follows ──
    follow_count = 0
    for user_id in user_ids:
        num_follows = random.randint(1, 5)
        targets = [u for u in user_ids if u != user_id]
        following = random.sample(targets, min(num_follows, len(targets)))
        for target in following:
            try:
                cursor.execute("""
                    INSERT INTO user_follows (follower_id, following_id)
                    VALUES (%s, %s)
                    ON CONFLICT DO NOTHING
                """, (str(user_id), str(target)))
                follow_count += 1
            except Exception:
                pass

    conn.commit()
    print(f"  ✅ Inserted {follow_count} follows.")

    # ── 7. Page views ──
    view_count = 0
    for post_id in random.sample(post_ids, min(10, len(post_ids))):
        for _ in range(random.randint(10, 50)):
            viewed_at = datetime.now() - timedelta(
                days=random.randint(0, 30),
                hours=random.randint(0, 23)
            )
            cursor.execute("""
                INSERT INTO page_views (post_id, viewer_ip, country, viewed_at)
                VALUES (%s, %s, %s, %s)
            """, (
                str(post_id),
                fake.ipv4(),
                random.choice(["PK", "US", "UK", "IN", "CA", "DE"]),
                viewed_at
            ))
            view_count += 1

    conn.commit()
    print(f"  ✅ Inserted {view_count} page view records.")
    print(f"\n  🎉 Blog platform database seeded successfully!")