# ============================================================
# src/reporter.py
# Terminal display for query results
# ============================================================

import json
from pathlib import Path
from datetime import datetime

try:
    from colorama import init, Fore, Style
    init(autoreset=True)
except ImportError:
    class Fore:
        CYAN = GREEN = YELLOW = RED = BLUE = MAGENTA = WHITE = ""
    class Style:
        RESET_ALL = BRIGHT = ""

DATA_DIR = Path(__file__).parent.parent / "data"


def header(title, subtitle=None):
    print(f"\n{Fore.CYAN}{'═' * 66}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}  {title}{Style.RESET_ALL}")
    if subtitle:
        print(f"{Fore.CYAN}  {subtitle}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'═' * 66}{Style.RESET_ALL}")


def section(title):
    print(f"\n{Fore.YELLOW}  ── {title} ──{Style.RESET_ALL}")


def display_overview(data):
    """Display database overview."""
    section("DATABASE OVERVIEW")
    ov = data["overview"]
    print(f"\n  {'Users:':<28} {ov['total_users']}")
    print(f"  {'Posts (total):':<28} {ov['total_posts']}")
    print(f"  {'Posts (published):':<28} {Fore.GREEN}{ov['published_posts']}{Style.RESET_ALL}")
    print(f"  {'Comments:':<28} {ov['total_comments']}")
    print(f"  {'Likes:':<28} {ov['total_likes']}")
    print(f"  {'Total views:':<28} {Fore.YELLOW}{int(ov['total_views']):,}{Style.RESET_ALL}")
    print(f"  {'Categories:':<28} {ov['categories']}")


def display_top_posts(data):
    """Display top posts by views."""
    section("TOP POSTS BY VIEWS")
    rows = data["top_posts"]

    if not rows:
        print(f"  {Fore.YELLOW}No published posts found.{Style.RESET_ALL}")
        return

    print(f"\n  {'Title':<38} {'Views':>6} {'Comments':>9} {'Likes':>6} {'Author'}")
    print(f"  {'─' * 66}")

    for row in rows:
        title = row["title"][:36] + ".." if len(row["title"]) > 38 else row["title"]
        print(
            f"  {title:<38} "
            f"{int(row['views'] or 0):>6,} "
            f"{int(row['comment_count'] or 0):>9} "
            f"{int(row['like_count'] or 0):>6} "
            f"{row['author_name'] or 'Unknown'}"
        )


def display_search_results(data):
    """Display full-text search results."""
    section("FULL-TEXT SEARCH RESULTS (python | postgresql | docker)")
    rows = data["search_results"]

    if not rows:
        print(f"  {Fore.YELLOW}No results found.{Style.RESET_ALL}")
        return

    for i, row in enumerate(rows, 1):
        print(f"\n  {Fore.GREEN}{i}. {row['title']}{Style.RESET_ALL}")
        print(f"     Rank: {float(row['rank']):.4f}")
        if row.get("snippet"):
            snippet = str(row["snippet"])[:120] + "..." if len(str(row["snippet"])) > 120 else str(row["snippet"])
            print(f"     {Fore.BLUE}{snippet}{Style.RESET_ALL}")


def display_tag_analytics(data):
    """Display tag analytics."""
    section("TAG ANALYTICS (from ARRAY unnesting)")
    rows = data["tag_analytics"]

    if not rows:
        print(f"  {Fore.YELLOW}No tag data found.{Style.RESET_ALL}")
        return

    max_count = max(row["post_count"] for row in rows) if rows else 1

    print(f"\n  {'Tag':<22} {'Posts':>6} {'Total Views':>12} {'Avg Views':>10}  Chart")
    print(f"  {'─' * 60}")

    for row in rows:
        bar_len = int(int(row["post_count"]) / max_count * 20)
        bar = "█" * bar_len
        print(
            f"  {row['tag']:<22} "
            f"{int(row['post_count']):>6} "
            f"{int(row['total_views'] or 0):>12,} "
            f"{float(row['avg_views'] or 0):>10.1f}  "
            f"{Fore.CYAN}{bar}{Style.RESET_ALL}"
        )


def display_leaderboard(data):
    """Display author leaderboard."""
    section("AUTHOR LEADERBOARD")
    rows = data["leaderboard"]

    if not rows:
        print(f"  {Fore.YELLOW}No author data found.{Style.RESET_ALL}")
        return

    medals = {0: "🥇", 1: "🥈", 2: "🥉"}
    print(f"\n  {'#':<4} {'Author':<22} {'Posts':>6} {'Views':>8} {'Likes':>6} {'Followers':>9}")
    print(f"  {'─' * 60}")

    for i, row in enumerate(rows):
        medal = medals.get(i, f"  {i+1}.")
        name = (row["display_name"] or row["username"])[:20]
        print(
            f"  {medal:<4} {name:<22} "
            f"{int(row['post_count'] or 0):>6} "
            f"{int(row['total_views'] or 0):>8,} "
            f"{int(row['total_likes_received'] or 0):>6} "
            f"{int(row['follower_count'] or 0):>9}"
        )


def display_window_functions(data):
    """Display window function results."""
    section("WINDOW FUNCTIONS — Rankings per Category")
    rows = data["category_rankings"]

    if not rows:
        print(f"  {Fore.YELLOW}No data found.{Style.RESET_ALL}")
        return

    print(f"\n  {'Category':<26} {'Rank':>5} {'Title':<30} {'Views':>7} {'% of Cat':>9}")
    print(f"  {'─' * 66}")

    for row in rows:
        rank = int(row["rank_in_category"])
        color = Fore.GREEN if rank == 1 else Fore.YELLOW if rank <= 3 else ""
        title = row["title"][:28] + ".." if len(row["title"]) > 30 else row["title"]

        print(
            f"  {row['category']:<26} "
            f"{color}{rank:>5}{Style.RESET_ALL} "
            f"{title:<30} "
            f"{int(row['views'] or 0):>7,} "
            f"{float(row['pct_of_category_views'] or 0):>8.1f}%"
        )


def display_all(results):
    """Display all query results."""
    display_overview(results)
    display_top_posts(results)
    display_search_results(results)
    display_tag_analytics(results)
    display_leaderboard(results)
    display_window_functions(results)


def save_report(results):
    """Save report to JSON."""
    DATA_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = DATA_DIR / f"blog_report_{timestamp}.json"

    # Convert non-serializable types
    def serialize(obj):
        if hasattr(obj, 'isoformat'):
            return obj.isoformat()
        return str(obj)

    with open(output, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, default=serialize, ensure_ascii=False)

    return output