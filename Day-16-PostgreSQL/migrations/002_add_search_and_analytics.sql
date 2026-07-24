-- ============================================================
-- Migration 002: Add triggers, functions, analytics
-- ============================================================

BEGIN;

-- ─── TRIGGER: Auto-update search vector ─────────────────────

CREATE OR REPLACE FUNCTION update_post_search_vector()
RETURNS TRIGGER AS $$
BEGIN
    NEW.search_vector = setweight(
        to_tsvector('english', COALESCE(NEW.title, '')),
        'A'    -- title has highest weight
    ) ||
    setweight(
        to_tsvector('english', COALESCE(NEW.excerpt, '')),
        'B'    -- excerpt has second highest weight
    ) ||
    setweight(
        to_tsvector('english', COALESCE(array_to_string(NEW.tags, ' '), '')),
        'B'    -- tags also have high weight
    ) ||
    setweight(
        to_tsvector('english', COALESCE(NEW.content, '')),
        'C'    -- content has lower weight
    );

    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER posts_search_vector_trigger
    BEFORE INSERT OR UPDATE OF title, excerpt, content, tags
    ON posts
    FOR EACH ROW
    EXECUTE FUNCTION update_post_search_vector();

-- ─── TRIGGER: Auto-update updated_at timestamps ─────────────

CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER comments_updated_at
    BEFORE UPDATE ON comments
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- ─── TRIGGER: Update category post count ────────────────────

CREATE OR REPLACE FUNCTION update_category_post_count()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' AND NEW.status = 'published' THEN
        UPDATE categories SET post_count = post_count + 1
        WHERE id = NEW.category_id;
    ELSIF TG_OP = 'DELETE' AND OLD.status = 'published' THEN
        UPDATE categories SET post_count = post_count - 1
        WHERE id = OLD.category_id;
    ELSIF TG_OP = 'UPDATE' THEN
        IF OLD.status != 'published' AND NEW.status = 'published' THEN
            UPDATE categories SET post_count = post_count + 1
            WHERE id = NEW.category_id;
        ELSIF OLD.status = 'published' AND NEW.status != 'published' THEN
            UPDATE categories SET post_count = post_count - 1
            WHERE id = OLD.category_id;
        END IF;
    END IF;
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER posts_category_count
    AFTER INSERT OR UPDATE OF status OR DELETE ON posts
    FOR EACH ROW EXECUTE FUNCTION update_category_post_count();

-- ─── FUNCTION: Calculate reading time ───────────────────────

CREATE OR REPLACE FUNCTION calculate_reading_time(p_content TEXT)
RETURNS INTEGER AS $$
DECLARE
    word_count INTEGER;
    words_per_minute CONSTANT INTEGER := 200;
BEGIN
    word_count := array_length(
        string_to_array(regexp_replace(p_content, '\s+', ' ', 'g'), ' '),
        1
    );
    RETURN GREATEST(1, CEIL(word_count::FLOAT / words_per_minute)::INTEGER);
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- ─── FUNCTION: Get user statistics ──────────────────────────

CREATE OR REPLACE FUNCTION get_user_stats(p_user_id UUID)
RETURNS TABLE (
    total_posts     BIGINT,
    published_posts BIGINT,
    total_comments  BIGINT,
    total_views     BIGINT,
    total_likes     BIGINT,
    followers       BIGINT,
    following       BIGINT,
    avg_views       NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        COUNT(DISTINCT p.id) AS total_posts,
        COUNT(DISTINCT p.id) FILTER (WHERE p.status = 'published') AS published_posts,
        COUNT(DISTINCT c.id) AS total_comments,
        COALESCE(SUM(p.views), 0) AS total_views,
        COUNT(DISTINCT pl.post_id) AS total_likes,
        COUNT(DISTINCT f1.follower_id) AS followers,
        COUNT(DISTINCT f2.following_id) AS following,
        ROUND(AVG(p.views), 2) AS avg_views
    FROM users u
    LEFT JOIN posts p ON u.id = p.author_id
    LEFT JOIN comments c ON u.id = c.author_id
    LEFT JOIN post_likes pl ON p.id = pl.post_id
    LEFT JOIN user_follows f1 ON u.id = f1.following_id
    LEFT JOIN user_follows f2 ON u.id = f2.follower_id
    WHERE u.id = p_user_id;
END;
$$ LANGUAGE plpgsql;

INSERT INTO schema_migrations (version, name) VALUES (2, 'add_search_and_analytics');

COMMIT;