# ============================================================
# src/pipeline.py
# Data fetching and transformation pipeline
# ============================================================

import requests
import itertools
from requests.exceptions import RequestException
from src.decorators import timer, retry, log_calls


# ─────────────────────────────────────────
# DATA FETCHING
# ─────────────────────────────────────────

@log_calls
@retry(max_attempts=3, delay=1.0, exceptions=(RequestException,))
@timer
def fetch_posts(limit=20):
    """
    Fetch posts from JSONPlaceholder API.

    Args:
        limit (int): Maximum number of posts to fetch.

    Returns:
        list: List of post dictionaries.
    """
    response = requests.get(
        "https://jsonplaceholder.typicode.com/posts",
        params={"_limit": limit},
        timeout=(5, 15)
    )
    response.raise_for_status()
    return response.json()


@log_calls
@retry(max_attempts=3, delay=1.0, exceptions=(RequestException,))
@timer
def fetch_users():
    """
    Fetch users from JSONPlaceholder API.

    Returns:
        list: List of user dictionaries.
    """
    response = requests.get(
        "https://jsonplaceholder.typicode.com/users",
        timeout=(5, 15)
    )
    response.raise_for_status()
    return response.json()


@log_calls
@retry(max_attempts=3, delay=1.0, exceptions=(RequestException,))
@timer
def fetch_comments(post_id=None, limit=50):
    """
    Fetch comments, optionally for a specific post.

    Args:
        post_id (int): Filter to specific post. None fetches all.
        limit (int): Maximum comments to fetch.

    Returns:
        list: List of comment dictionaries.
    """
    params = {"_limit": limit}
    if post_id:
        params["postId"] = post_id

    response = requests.get(
        "https://jsonplaceholder.typicode.com/comments",
        params=params,
        timeout=(5, 15)
    )
    response.raise_for_status()
    return response.json()


# ─────────────────────────────────────────
# TRANSFORMATION PIPELINE — Using Generators
# ─────────────────────────────────────────

def clean_posts(posts):
    """
    Generator: Clean and normalize post data.
    Yields one cleaned post at a time.
    """
    for post in posts:
        yield {
            "id": post["id"],
            "user_id": post["userId"],
            "title": post["title"].strip().title(),
            "body": post["body"].replace("\n", " ").strip(),
            "word_count": len(post["body"].split()),
            "title_length": len(post["title"])
        }


def filter_long_posts(posts, min_words=20):
    """
    Generator: Filter to posts with at least min_words words.
    """
    for post in posts:
        if post["word_count"] >= min_words:
            yield post


def enrich_posts_with_users(posts, users_dict):
    """
    Generator: Enrich posts with user information.

    Args:
        posts: Iterator of post dicts.
        users_dict (dict): user_id → user data mapping.
    """
    for post in posts:
        user = users_dict.get(post["user_id"], {})
        yield {
            **post,    # spread all existing post fields
            "author_name": user.get("name", "Unknown"),
            "author_email": user.get("email", ""),
            "author_company": user.get(
                "company", {}
            ).get("name", ""),
            "author_city": user.get(
                "address", {}
            ).get("city", "")
        }


def add_comment_counts(posts, comments_by_post):
    """
    Generator: Add comment count to each post.

    Args:
        posts: Iterator of post dicts.
        comments_by_post (dict): post_id → list of comments.
    """
    for post in posts:
        yield {
            **post,
            "comment_count": len(comments_by_post.get(post["id"], []))
        }


def build_pipeline(posts, users, comments):
    """
    Build the complete data transformation pipeline.

    Args:
        posts (list): Raw posts from API.
        users (list): Raw users from API.
        comments (list): Raw comments from API.

    Returns:
        list: Fully processed and enriched posts.
    """
    # Build lookup structures using comprehensions
    users_dict = {user["id"]: user for user in users}

    # Group comments by post_id using defaultdict pattern
    comments_by_post = {}
    for comment in comments:
        post_id = comment["postId"]
        comments_by_post.setdefault(post_id, []).append(comment)

    # Build the pipeline — each step is a generator
    # Nothing executes until we convert to list at the end
    pipeline = clean_posts(posts)
    pipeline = filter_long_posts(pipeline, min_words=15)
    pipeline = enrich_posts_with_users(pipeline, users_dict)
    pipeline = add_comment_counts(pipeline, comments_by_post)

    # Execute the pipeline by converting to list
    return list(pipeline)


# ─────────────────────────────────────────
# ITERTOOLS OPERATIONS
# ─────────────────────────────────────────

def group_by_author(processed_posts):
    """
    Group posts by author using itertools.groupby.

    Returns:
        dict: author_name → list of posts.
    """
    sorted_posts = sorted(
        processed_posts,
        key=lambda p: p["author_name"]
    )

    grouped = {}
    for author, posts in itertools.groupby(
        sorted_posts,
        key=lambda p: p["author_name"]
    ):
        grouped[author] = list(posts)

    return grouped


def get_top_posts_per_author(grouped_posts, top_n=2):
    """
    Get top N posts per author by word count.

    Uses itertools.islice for efficient slicing.
    """
    result = {}
    for author, posts in grouped_posts.items():
        sorted_posts = sorted(
            posts,
            key=lambda p: p["word_count"],
            reverse=True
        )
        result[author] = list(itertools.islice(sorted_posts, top_n))
    return result


def interleave_posts_from_authors(*author_post_lists):
    """
    Interleave posts from multiple authors using itertools.chain.

    Creates a balanced feed mixing posts from different authors.
    """
    return list(itertools.chain.from_iterable(
        zip(*author_post_lists)
    ))