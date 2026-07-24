# ============================================================
# src/queries.py
# PostgreSQL analytical queries showcasing advanced features
# ============================================================


def run_all_queries(conn):
    """Run all analytical queries and return results."""
    cursor = conn.cursor()
    results = {}

    # ── Q1: Overview from multiple tables ──
    cursor.execute("""
        SELECT
            (SELECT COUNT(*) FROM users WHERE is_active) AS total_users,
            (SELECT COUNT(*) FROM posts) AS total_posts,
            (SELECT COUNT(*) FROM posts WHERE status = 'published') AS published_posts,
            (SELECT COUNT(*) FROM comments WHERE is_approved) AS total_comments,
            (SELECT COUNT(*) FROM post_likes) AS total_likes,
            (SELECT COALESCE(SUM(views), 0) FROM posts) AS total_views,
            (SELECT COUNT(*) FROM categories) AS categories
    """)
    results["overview"] = dict(cursor.fetchone())

    # ── Q2: Published posts using VIEW ──
    cursor.execute("""
        SELECT
            title,
            author_name,
            category_name,
            views,
            comment_count,
            like_count,
            reading_time,
            to_char(published_at, 'Mon DD, YYYY') AS published_date
        FROM published_posts_detail
        ORDER BY views DESC
        LIMIT 10
    """)
    results["top_posts"] = [dict(row) for row in cursor.fetchall()]

    # ── Q3: Author leaderboard using VIEW ──
    cursor.execute("""
        SELECT
            username,
            display_name,
            post_count,
            total_views,
            total_likes_received,
            follower_count,
            avg_views_per_post
        FROM author_leaderboard
        LIMIT 8
    """)
    results["leaderboard"] = [dict(row) for row in cursor.fetchall()]

    # ── Q4: Category analytics with post counts ──
    cursor.execute("""
        SELECT
            c.name AS category,
            c.color,
            c.post_count AS cached_count,
            COUNT(p.id) AS actual_count,
            COALESCE(SUM(p.views), 0) AS total_views,
            ROUND(AVG(p.views), 0) AS avg_views
        FROM categories c
        LEFT JOIN posts p ON c.id = p.category_id AND p.status = 'published'
        GROUP BY c.id, c.name, c.color, c.post_count
        ORDER BY total_views DESC
    """)
    results["category_stats"] = [dict(row) for row in cursor.fetchall()]

    # ── Q5: Full-text search ──
    cursor.execute("""
        SELECT
            title,
            ts_rank(search_vector, query) AS rank,
            ts_headline(
                'english', excerpt,
                query,
                'MaxWords=20, MinWords=10'
            ) AS snippet
        FROM posts,
            to_tsquery('english', 'python | postgresql | docker') query
        WHERE search_vector @@ query
            AND status = 'published'
        ORDER BY rank DESC
        LIMIT 5
    """)
    results["search_results"] = [dict(row) for row in cursor.fetchall()]

    # ── Q6: Tag analytics using unnest (ARRAY expansion) ──
    cursor.execute("""
        SELECT
            tag,
            post_count,
            total_views,
            avg_views
        FROM tag_analytics
        LIMIT 10
    """)
    results["tag_analytics"] = [dict(row) for row in cursor.fetchall()]

    # ── Q7: Window function — post rankings within categories ──
    cursor.execute("""
        SELECT
            c.name AS category,
            p.title,
            p.views,
            RANK() OVER (
                PARTITION BY p.category_id
                ORDER BY p.views DESC
            ) AS rank_in_category,
            ROUND(
                p.views * 100.0 / NULLIF(
                    SUM(p.views) OVER (PARTITION BY p.category_id),
                    0
                ),
                1
            ) AS pct_of_category_views
        FROM posts p
        JOIN categories c ON p.category_id = c.id
        WHERE p.status = 'published'
        ORDER BY c.name, rank_in_category
        LIMIT 20
    """)
    results["category_rankings"] = [dict(row) for row in cursor.fetchall()]

    # ── Q8: Running total of views over time ──
    cursor.execute("""
        SELECT
            to_char(published_at, 'YYYY-MM-DD') AS date,
            COUNT(*) AS posts_published,
            SUM(views) AS views_on_day,
            SUM(SUM(views)) OVER (
                ORDER BY DATE(published_at)
            ) AS cumulative_views
        FROM posts
        WHERE status = 'published'
            AND published_at IS NOT NULL
        GROUP BY DATE(published_at)
        ORDER BY DATE(published_at) DESC
        LIMIT 10
    """)
    results["views_over_time"] = [dict(row) for row in cursor.fetchall()]

    # ── Q9: User stats using custom FUNCTION ──
    cursor.execute("SELECT id FROM users LIMIT 3")
    sample_users = [row["id"] for row in cursor.fetchall()]
    user_stats = []
    for user_id in sample_users:
        cursor.execute("SELECT * FROM get_user_stats(%s)", (str(user_id),))
        row = cursor.fetchone()
        if row:
            user_stats.append(dict(row))
    results["user_stats"] = user_stats

    # ── Q10: JSONB query — user preferences ──
    cursor.execute("""
        SELECT
            username,
            preferences,
            social_links,
            jsonb_array_length(
                COALESCE(preferences->'notifications', '[]')
            ) AS notification_prefs
        FROM users
        WHERE preferences != '{}'
        LIMIT 5
    """)
    results["jsonb_demo"] = [dict(row) for row in cursor.fetchall()]

    # ── Q11: Comment threads (self-join for hierarchy) ──
    cursor.execute("""
        SELECT
            p.title AS post_title,
            u.username AS commenter,
            c.content AS comment,
            c.created_at,
            parent_comment.content AS reply_to,
            CASE WHEN c.parent_id IS NULL THEN 'Root'
                 ELSE 'Reply' END AS comment_type
        FROM comments c
        JOIN posts p ON c.post_id = p.id
        JOIN users u ON c.author_id = u.id
        LEFT JOIN comments parent_comment ON c.parent_id = parent_comment.id
        ORDER BY p.id, c.created_at
        LIMIT 15
    """)
    results["comment_threads"] = [dict(row) for row in cursor.fetchall()]

    # ── Q12: Daily analytics VIEW ──
    cursor.execute("""
        SELECT * FROM daily_analytics
        ORDER BY date DESC
        LIMIT 7
    """)
    results["daily_analytics"] = [dict(row) for row in cursor.fetchall()]

    # ── Q13: Posts with ARRAY operations ──
    cursor.execute("""
        SELECT
            title,
            tags,
            array_length(tags, 1) AS tag_count,
            array_to_string(tags, ' • ') AS tags_display
        FROM posts
        WHERE 'python' = ANY(tags)
            AND status = 'published'
        ORDER BY array_length(tags, 1) DESC
        LIMIT 8
    """)
    results["posts_with_python_tag"] = [dict(row) for row in cursor.fetchall()]

    # ── Q14: Most followed authors ──
    cursor.execute("""
        SELECT
            u.username,
            u.display_name,
            u.role,
            COUNT(f.follower_id) AS followers,
            COUNT(DISTINCT p.id) FILTER (WHERE p.status = 'published') AS published_posts
        FROM users u
        LEFT JOIN user_follows f ON u.id = f.following_id
        LEFT JOIN posts p ON u.id = p.author_id
        GROUP BY u.id, u.username, u.display_name, u.role
        ORDER BY followers DESC
        LIMIT 8
    """)
    results["top_authors"] = [dict(row) for row in cursor.fetchall()]

    return results