-- ============================================================
-- Migration 003: Add database views for common queries
-- ============================================================

BEGIN;

-- ─── VIEW: Published posts with author info ──────────────────

CREATE OR REPLACE VIEW published_posts_detail AS
    SELECT
        p.id,
        p.title,
        p.slug,
        p.excerpt,
        p.cover_image,
        p.views,
        p.reading_time,
        p.tags,
        p.published_at,
        p.created_at,
        u.id AS author_id,
        u.username AS author_username,
        u.display_name AS author_name,
        u.avatar_url AS author_avatar,
        c.id AS category_id,
        c.name AS category_name,
        c.color AS category_color,
        COUNT(DISTINCT cm.id) AS comment_count,
        COUNT(DISTINCT pl.user_id) AS like_count
    FROM posts p
    JOIN users u ON p.author_id = u.id
    LEFT JOIN categories c ON p.category_id = c.id
    LEFT JOIN comments cm ON p.id = cm.post_id AND cm.is_approved = TRUE
    LEFT JOIN post_likes pl ON p.id = pl.post_id
    WHERE p.status = 'published'
    GROUP BY p.id, u.id, c.id;

-- ─── VIEW: Author leaderboard ───────────────────────────────

CREATE OR REPLACE VIEW author_leaderboard AS
    SELECT
        u.id,
        u.username,
        u.display_name,
        u.avatar_url,
        COUNT(DISTINCT p.id) FILTER (WHERE p.status = 'published') AS post_count,
        COALESCE(SUM(p.views), 0) AS total_views,
        COUNT(DISTINCT cm.id) AS total_comments_received,
        COUNT(DISTINCT pl.post_id) AS total_likes_received,
        COUNT(DISTINCT f.follower_id) AS follower_count,
        ROUND(
            COALESCE(AVG(p.views) FILTER (WHERE p.status = 'published'), 0),
            2
        ) AS avg_views_per_post
    FROM users u
    LEFT JOIN posts p ON u.id = p.author_id
    LEFT JOIN comments cm ON p.id = cm.post_id
    LEFT JOIN post_likes pl ON p.id = pl.post_id
    LEFT JOIN user_follows f ON u.id = f.following_id
    WHERE u.is_active = TRUE
    GROUP BY u.id, u.username, u.display_name, u.avatar_url
    ORDER BY total_views DESC;

-- ─── VIEW: Tag analytics ────────────────────────────────────

CREATE OR REPLACE VIEW tag_analytics AS
    SELECT
        tag,
        COUNT(*) AS post_count,
        SUM(views) AS total_views,
        ROUND(AVG(views), 2) AS avg_views,
        MAX(published_at) AS last_used
    FROM posts,
        unnest(tags) AS tag
    WHERE status = 'published'
    GROUP BY tag
    ORDER BY post_count DESC;

-- ─── VIEW: Daily analytics ──────────────────────────────────

CREATE OR REPLACE VIEW daily_analytics AS
    SELECT
        DATE(viewed_at) AS date,
        COUNT(*) AS total_views,
        COUNT(DISTINCT post_id) AS unique_posts_viewed,
        COUNT(DISTINCT viewer_ip) AS unique_visitors
    FROM page_views
    WHERE viewed_at >= NOW() - INTERVAL '30 days'
    GROUP BY DATE(viewed_at)
    ORDER BY date DESC;

INSERT INTO schema_migrations (version, name) VALUES (3, 'add_views_and_functions');

COMMIT;