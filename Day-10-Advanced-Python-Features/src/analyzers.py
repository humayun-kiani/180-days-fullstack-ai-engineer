# ============================================================
# src/analyzers.py
# Statistical analysis using functools, map, filter, zip
# ============================================================

import functools
import itertools
from src.decorators import timer, validate_not_empty


@validate_not_empty
@timer
def compute_statistics(processed_posts):
    """
    Compute comprehensive statistics using functional programming.

    Args:
        processed_posts (list): List of enriched post dicts.

    Returns:
        dict: Statistical analysis results.
    """
    # Extract values using list comprehensions
    word_counts = [p["word_count"] for p in processed_posts]
    comment_counts = [p["comment_count"] for p in processed_posts]
    title_lengths = [p["title_length"] for p in processed_posts]

    # Use functools.reduce for custom aggregations
    total_words = functools.reduce(lambda acc, n: acc + n, word_counts, 0)
    total_comments = functools.reduce(lambda acc, n: acc + n, comment_counts, 0)

    # Use map to transform data
    engagement_scores = list(map(
        lambda p: p["word_count"] * 0.3 + p["comment_count"] * 0.7,
        processed_posts
    ))

    # Use filter to find high-engagement posts
    high_engagement = list(filter(
        lambda score: score >= 15,
        engagement_scores
    ))

    # Zip word counts with post titles for ranking
    post_word_pairs = sorted(
        zip(word_counts, [p["title"] for p in processed_posts]),
        reverse=True
    )

    # Average calculations
    avg_words = total_words / len(word_counts) if word_counts else 0
    avg_comments = total_comments / len(comment_counts) if comment_counts else 0
    avg_engagement = sum(engagement_scores) / len(engagement_scores) if engagement_scores else 0

    # Use comprehensions for distribution analysis
    word_count_buckets = {
        "short (< 20 words)": len([w for w in word_counts if w < 20]),
        "medium (20-40 words)": len([w for w in word_counts if 20 <= w < 40]),
        "long (40+ words)": len([w for w in word_counts if w >= 40])
    }

    # Unique authors using set comprehension
    unique_authors = {p["author_name"] for p in processed_posts}
    unique_cities = {p["author_city"] for p in processed_posts if p["author_city"]}
    unique_companies = {p["author_company"] for p in processed_posts if p["author_company"]}

    return {
        "total_posts": len(processed_posts),
        "total_words": total_words,
        "total_comments": total_comments,
        "avg_words_per_post": round(avg_words, 1),
        "avg_comments_per_post": round(avg_comments, 1),
        "avg_engagement_score": round(avg_engagement, 2),
        "high_engagement_posts": len(high_engagement),
        "max_word_count": max(word_counts),
        "min_word_count": min(word_counts),
        "longest_posts": [title for _, title in post_word_pairs[:3]],
        "word_count_distribution": word_count_buckets,
        "unique_authors": len(unique_authors),
        "unique_cities": sorted(unique_cities),
        "unique_companies": sorted(unique_companies)
    }


@validate_not_empty
def find_top_posts(processed_posts, n=5, sort_by="word_count"):
    """
    Find top N posts sorted by a given metric.

    Args:
        processed_posts (list): List of enriched posts.
        n (int): Number of top posts to return.
        sort_by (str): Field to sort by.

    Returns:
        list: Top N posts.
    """
    valid_fields = ["word_count", "comment_count", "title_length"]
    if sort_by not in valid_fields:
        sort_by = "word_count"

    return sorted(
        processed_posts,
        key=lambda p: p[sort_by],
        reverse=True
    )[:n]


def author_leaderboard(processed_posts):
    """
    Create an author leaderboard based on total words written.

    Returns:
        list: Authors sorted by total words (highest first).
    """
    # Build per-author stats using comprehensions + grouping
    author_stats = {}
    for post in processed_posts:
        author = post["author_name"]
        if author not in author_stats:
            author_stats[author] = {
                "name": author,
                "company": post["author_company"],
                "city": post["author_city"],
                "post_count": 0,
                "total_words": 0,
                "total_comments": 0
            }
        author_stats[author]["post_count"] += 1
        author_stats[author]["total_words"] += post["word_count"]
        author_stats[author]["total_comments"] += post["comment_count"]

    # Sort by total words
    leaderboard = sorted(
        author_stats.values(),
        key=lambda a: a["total_words"],
        reverse=True
    )

    # Add rank using enumerate
    return [
        {**author, "rank": rank}
        for rank, author in enumerate(leaderboard, start=1)
    ]


def compute_correlations(processed_posts):
    """
    Find correlations between post metrics.

    Returns simple correlation observations using zip and map.
    """
    word_counts = [p["word_count"] for p in processed_posts]
    comment_counts = [p["comment_count"] for p in processed_posts]

    # Pair them up to analyze relationship
    pairs = list(zip(word_counts, comment_counts))

    # Posts where high word count AND high comments (both above average)
    avg_words = sum(word_counts) / len(word_counts)
    avg_comments = sum(comment_counts) / len(comment_counts)

    high_both = [
        (w, c) for w, c in pairs
        if w > avg_words and c > avg_comments
    ]

    return {
        "avg_words": round(avg_words, 1),
        "avg_comments": round(avg_comments, 1),
        "posts_above_avg_both": len(high_both),
        "correlation_note": (
            "Posts with more words tend to get more comments"
            if len(high_both) > len(processed_posts) * 0.3
            else "No strong correlation between length and comments"
        )
    }