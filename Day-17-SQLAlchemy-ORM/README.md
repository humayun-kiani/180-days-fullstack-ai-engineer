# Day 17 — SQLAlchemy ORM: Models, Relationships, Sessions & Migrations

> **Phase 1 — Foundations** | Week 3 | Day 17 of 180

---

## 📌 What I Learned Today

- SQLAlchemy architecture: Core vs ORM layers
- DeclarativeBase — the foundation for all models
- Mapped[] type hints — modern SQLAlchemy 2.0 style
- mapped_column() — defining columns with types and constraints
- Column types: String, Integer, Text, Boolean, DateTime, Numeric
- Relationships: one-to-many with back_populates
- Many-to-many with secondary association table
- Self-referential relationships (user follows, comment replies)
- Mixins — reusable column groups (TimestampMixin, SoftDeleteMixin)
- @validates decorator — custom validation on model attributes
- Sessions — create, add, flush, commit, rollback, close
- The session_scope() context manager for safe transactions
- Query API: get, filter, filter_by, first, one, all, count
- Filtering: ==, !=, ilike, in*, between, is*, is_not
- Ordering, limiting, offsetting for pagination
- Joins through relationships: join(Post.author)
- Aggregate functions: func.count, func.sum, func.avg
- N+1 problem — what it is and why it destroys performance
- joinedload — fixes N+1 with LEFT JOIN (single query)
- selectinload — fixes N+1 with IN query (2 queries, better for collections)
- expire_on_commit=False — keep objects accessible after commit
- Repository pattern — separating data access from business logic
- Alembic setup and autogenerate migrations
- SoftDeleteMixin — mark as deleted without removing from DB

## 🔨 Project Built

**Blog ORM Layer** — Full SQLAlchemy implementation:

- 6 models: User, Category, Tag, Post, Comment, PostLike
- TimestampMixin and SoftDeleteMixin for all models
- @validates decorators for email lowercase normalization
- One-to-many: User→Posts, Post→Comments, Comment→Replies
- Many-to-many: Post↔Tag via post_tags association table
- Self-referential M2M: User follows Users via user_follows
- UserRepository with 10 methods for all user operations
- PostRepository with 15 methods including pagination, search, tags
- Proper eager loading with joinedload and selectinload throughout
- 8 analytical queries using func aggregates and GROUP BY
- Alembic migration initialized and configured
- Full menu-driven interface with live ORM write demo

## 🚀 How to Run

```bash
cd Day-17-SQLAlchemy-ORM
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Setup PostgreSQL first
psql -U postgres
CREATE DATABASE blog_orm;
CREATE USER blog_user WITH PASSWORD 'secure_password_here';
GRANT ALL PRIVILEGES ON DATABASE blog_orm TO blog_user;
\c blog_orm
GRANT ALL ON SCHEMA public TO blog_user;
\q

cp .env.example .env   # edit with your password
python src/main.py
```

## 🧠 Key Concepts

| Concept        | Code                                                    |
| -------------- | ------------------------------------------------------- |
| Define model   | `class Post(Base): __tablename__ = "posts"`             |
| Column         | `id: Mapped[int] = mapped_column(primary_key=True)`     |
| Relationship   | `posts = relationship("Post", back_populates="author")` |
| ForeignKey     | `mapped_column(ForeignKey("users.id"))`                 |
| M2M            | `secondary=post_tags_table`                             |
| Session create | `with Session(engine) as session:`                      |
| Add object     | `session.add(obj); session.commit()`                    |
| Query          | `session.query(User).filter(...).first()`               |
| Fix N+1        | `.options(joinedload(Post.author))`                     |
| Migration      | `alembic revision --autogenerate -m "name"`             |

## 🔗 Back to Main Roadmap

[← Back to 180-Day Roadmap](../README.md)
