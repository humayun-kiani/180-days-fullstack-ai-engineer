-- ============================================================
-- Migration 001: Initial Blog Platform Schema
-- ============================================================

BEGIN;

-- Track migrations
CREATE TABLE IF NOT EXISTS schema_migrations (
    version     INTEGER PRIMARY KEY,
    name        TEXT NOT NULL,
    applied_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";       -- trigram similarity search

-- ─── CUSTOM TYPES ───────────────────────────────────────────

CREATE TYPE post_status AS ENUM ('draft', 'published', 'archived', 'scheduled');
CREATE TYPE user_role AS ENUM ('reader', 'author', 'editor', 'admin');
CREATE TYPE notification_type AS ENUM ('comment', 'like', 'follow', 'mention');

-- ─── USERS ──────────────────────────────────────────────────

CREATE TABLE users (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username        VARCHAR(50) UNIQUE NOT NULL,
    email           VARCHAR(255) UNIQUE NOT NULL,
    password_hash   TEXT NOT NULL,
    display_name    VARCHAR(100),
    bio             TEXT,
    avatar_url      TEXT,
    role            user_role DEFAULT 'reader',
    is_active       BOOLEAN DEFAULT TRUE,
    email_verified  BOOLEAN DEFAULT FALSE,
    last_login_at   TIMESTAMPTZ,
    preferences     JSONB DEFAULT '{}',   -- flexible user settings
    social_links    JSONB DEFAULT '{}',   -- {"twitter": "...", "github": "..."}
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT valid_username CHECK (
        username ~ '^[a-zA-Z0-9_]{3,50}$'   -- regex constraint
    ),
    CONSTRAINT valid_email CHECK (
        email ~ '^[^@\s]+@[^@\s]+\.[^@\s]+$'
    )
);

-- ─── CATEGORIES ─────────────────────────────────────────────

CREATE TABLE categories (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(100) UNIQUE NOT NULL,
    slug            VARCHAR(120) UNIQUE NOT NULL,
    description     TEXT,
    color           VARCHAR(7) DEFAULT '#3B82F6',   -- hex color
    icon            VARCHAR(50),
    parent_id       INTEGER REFERENCES categories(id),   -- nested categories
    post_count      INTEGER DEFAULT 0,                   -- denormalized counter
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ─── POSTS ──────────────────────────────────────────────────

CREATE TABLE posts (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    author_id       UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    category_id     INTEGER REFERENCES categories(id) ON DELETE SET NULL,
    title           VARCHAR(300) NOT NULL,
    slug            VARCHAR(350) UNIQUE NOT NULL,
    excerpt         TEXT,
    content         TEXT NOT NULL,
    cover_image     TEXT,
    status          post_status DEFAULT 'draft',
    tags            TEXT[] DEFAULT '{}',          -- array of tag strings
    metadata        JSONB DEFAULT '{}',            -- flexible extra data
    views           INTEGER DEFAULT 0,
    reading_time    INTEGER,                       -- minutes to read
    search_vector   TSVECTOR,                     -- full-text search
    published_at    TIMESTAMPTZ,
    scheduled_for   TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT valid_slug CHECK (slug ~ '^[a-z0-9-]+$'),
    CONSTRAINT reading_time_positive CHECK (reading_time IS NULL OR reading_time > 0)
);

-- ─── COMMENTS ───────────────────────────────────────────────

CREATE TABLE comments (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    post_id         UUID NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
    author_id       UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    parent_id       UUID REFERENCES comments(id) ON DELETE CASCADE,  -- nested comments
    content         TEXT NOT NULL,
    is_approved     BOOLEAN DEFAULT TRUE,
    like_count      INTEGER DEFAULT 0,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT min_comment_length CHECK (LENGTH(content) >= 1),
    CONSTRAINT max_comment_length CHECK (LENGTH(content) <= 10000)
);

-- ─── LIKES ──────────────────────────────────────────────────

CREATE TABLE post_likes (
    user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    post_id     UUID NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
    created_at  TIMESTAMPTZ DEFAULT NOW(),

    PRIMARY KEY (user_id, post_id)    -- composite PK prevents duplicate likes
);

-- ─── FOLLOWERS ──────────────────────────────────────────────

CREATE TABLE user_follows (
    follower_id  UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    following_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at   TIMESTAMPTZ DEFAULT NOW(),

    PRIMARY KEY (follower_id, following_id),
    CONSTRAINT no_self_follow CHECK (follower_id != following_id)
);

-- ─── PAGE VIEWS (Analytics) ─────────────────────────────────

CREATE TABLE page_views (
    id          BIGSERIAL PRIMARY KEY,
    post_id     UUID REFERENCES posts(id) ON DELETE CASCADE,
    viewer_ip   INET,
    user_agent  TEXT,
    referer     TEXT,
    country     VARCHAR(2),
    viewed_at   TIMESTAMPTZ DEFAULT NOW()
);

-- ─── INDEXES ────────────────────────────────────────────────

-- Users
CREATE INDEX idx_users_email ON users(LOWER(email));
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_role ON users(role) WHERE is_active = TRUE;

-- Posts
CREATE INDEX idx_posts_author ON posts(author_id);
CREATE INDEX idx_posts_category ON posts(category_id);
CREATE INDEX idx_posts_status ON posts(status);
CREATE INDEX idx_posts_published ON posts(published_at DESC) WHERE status = 'published';
CREATE INDEX idx_posts_tags ON posts USING GIN(tags);
CREATE INDEX idx_posts_search ON posts USING GIN(search_vector);
CREATE INDEX idx_posts_slug ON posts(slug);
CREATE INDEX idx_posts_metadata ON posts USING GIN(metadata);

-- Comments
CREATE INDEX idx_comments_post ON comments(post_id);
CREATE INDEX idx_comments_author ON comments(author_id);
CREATE INDEX idx_comments_parent ON comments(parent_id);

-- Analytics
CREATE INDEX idx_page_views_post ON page_views(post_id);
CREATE INDEX idx_page_views_time ON page_views(viewed_at DESC);

-- Record migration
INSERT INTO schema_migrations (version, name) VALUES (1, 'initial_schema');

COMMIT;