# ============================================================
# src/main.py
# Data Pipeline — Main Entry Point
# Day 10 - 180 Days Full Stack AI Engineer Roadmap
# ============================================================

import sys
import json
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.pipeline import (
    fetch_posts,
    fetch_users,
    fetch_comments,
    build_pipeline,
    group_by_author,
    get_top_posts_per_author
)
from src.analyzers import (
    compute_statistics,
    find_top_posts,
    author_leaderboard,
    compute_correlations
)
from src.decorators import timer

try:
    from colorama import init, Fore, Style
    init(autoreset=True)
    HAS_COLOR = True
except ImportError:
    HAS_COLOR = False
    class Fore:
        CYAN = GREEN = YELLOW = RED = BLUE = ""
    class Style:
        RESET_ALL = BRIGHT = ""


DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)


def print_section(title):
    print(f"\n{Fore.CYAN}{'═' * 60}")
    print(f"{Fore.CYAN}  {title}")
    print(f"{Fore.CYAN}{'═' * 60}{Style.RESET_ALL}")


def print_subsection(title):
    print(f"\n{Fore.YELLOW}  ── {title} ──{Style.RESET_ALL}")


def display_statistics(stats):
    """Display statistical analysis results."""
    print_section("STATISTICAL ANALYSIS")

    print(f"\n  {'Posts processed:':<30} {stats['total_posts']}")
    print(f"  {'Total words:':<30} {stats['total_words']:,}")
    print(f"  {'Total comments:':<30} {stats['total_comments']:,}")
    print(f"  {'Avg words per post:':<30} {stats['avg_words_per_post']}")
    print(f"  {'Avg comments per post:':<30} {stats['avg_comments_per_post']}")
    print(f"  {'Avg engagement score:':<30} {stats['avg_engagement_score']}")
    print(f"  {'High engagement posts:':<30} {stats['high_engagement_posts']}")
    print(f"  {'Unique authors:':<30} {stats['unique_authors']}")

    print_subsection("Word Count Distribution")
    for category, count in stats["word_count_distribution"].items():
        bar = "█" * count
        print(f"  {category:<25} {count:>3}  {bar}")

    print_subsection("3 Longest Posts")
    for i, title in enumerate(stats["longest_posts"], 1):
        print(f"  {i}. {title}")

    print_subsection("Author Locations")
    cities = stats["unique_cities"][:5]
    print(f"  Cities: {', '.join(cities)}")


def display_top_posts(top_posts, metric="word_count"):
    """Display top posts table."""
    print_section(f"TOP POSTS BY {metric.upper().replace('_', ' ')}")

    headers = f"  {'#':<3} {'Title':<35} {'Words':>5} {'Comments':>8} {'Author'}"
    print(f"\n{Fore.YELLOW}{headers}{Style.RESET_ALL}")
    print(f"  {'─' * 65}")

    for i, post in enumerate(top_posts, 1):
        title = post["title"][:33] + ".." if len(post["title"]) > 35 else post["title"]
        print(
            f"  {i:<3} "
            f"{title:<35} "
            f"{post['word_count']:>5} "
            f"{post['comment_count']:>8} "
            f"{post['author_name']}"
        )


def display_leaderboard(leaderboard):
    """Display author leaderboard."""
    print_section("AUTHOR LEADERBOARD")

    headers = f"  {'Rank':<5} {'Author':<25} {'Posts':>5} {'Words':>7} {'Comments':>9} {'Company'}"
    print(f"\n{Fore.YELLOW}{headers}{Style.RESET_ALL}")
    print(f"  {'─' * 72}")

    medals = {1: "🥇", 2: "🥈", 3: "🥉"}

    for author in leaderboard[:10]:
        rank = author["rank"]
        medal = medals.get(rank, "  ")
        name = author["name"][:23]
        company = author["company"][:20] if author["company"] else "—"

        print(
            f"  {medal}{rank:<3} "
            f"{name:<25} "
            f"{author['post_count']:>5} "
            f"{author['total_words']:>7} "
            f"{author['total_comments']:>9} "
            f"{company}"
        )


def display_correlations(correlations):
    """Display correlation analysis."""
    print_section("CORRELATION ANALYSIS")
    print(f"\n  Average words per post:   {correlations['avg_words']}")
    print(f"  Average comments per post: {correlations['avg_comments']}")
    print(f"  Posts above average in both: {correlations['posts_above_avg_both']}")
    print(f"\n  💡 {correlations['correlation_note']}")


def save_results(processed_posts, stats, leaderboard):
    """Save pipeline results to JSON files."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Save processed posts
    posts_file = DATA_DIR / f"processed_posts_{timestamp}.json"
    with open(posts_file, "w") as f:
        json.dump(processed_posts, f, indent=2)
    print(f"\n  💾 Posts saved to: {posts_file.name}")

    # Save statistics
    stats_file = DATA_DIR / f"statistics_{timestamp}.json"
    with open(stats_file, "w") as f:
        json.dump(stats, f, indent=2)
    print(f"  💾 Statistics saved to: {stats_file.name}")

    # Save leaderboard
    board_file = DATA_DIR / f"leaderboard_{timestamp}.json"
    with open(board_file, "w") as f:
        json.dump(leaderboard, f, indent=2)
    print(f"  💾 Leaderboard saved to: {board_file.name}")


@timer
def run_pipeline():
    """Execute the complete data pipeline."""
    print_section("DATA PIPELINE — FETCHING")

    # Step 1 — Fetch data from APIs
    print(f"\n{Fore.BLUE}  Fetching data from JSONPlaceholder API...{Style.RESET_ALL}")
    posts = fetch_posts(limit=20)
    users = fetch_users()
    comments = fetch_comments(limit=100)

    print(f"\n  Raw data loaded:")
    print(f"    Posts:    {len(posts)}")
    print(f"    Users:    {len(users)}")
    print(f"    Comments: {len(comments)}")

    # Step 2 — Run transformation pipeline
    print_section("PIPELINE — TRANSFORMING")
    print(f"\n{Fore.BLUE}  Running transformation pipeline...{Style.RESET_ALL}")
    print("  Steps: clean → filter → enrich with users → add comment counts")

    processed = build_pipeline(posts, users, comments)
    print(f"\n  ✅ Pipeline complete: {len(processed)} posts processed")

    # Step 3 — Analyze
    print_section("PIPELINE — ANALYZING")
    stats = compute_statistics(processed)
    top_by_words = find_top_posts(processed, n=5, sort_by="word_count")
    top_by_comments = find_top_posts(processed, n=5, sort_by="comment_count")
    leaderboard = author_leaderboard(processed)
    correlations = compute_correlations(processed)

    return processed, stats, top_by_words, top_by_comments, leaderboard, correlations


def main():
    """Main entry point."""
    print(f"\n{Fore.CYAN}{'═' * 60}")
    print(f"{Fore.CYAN}  DATA PIPELINE SCRIPT")
    print(f"{Fore.CYAN}  180 Days Full Stack AI — Day 10")
    print(f"{Fore.CYAN}  Advanced Python: Comprehensions, Generators, Decorators")
    print(f"{Fore.CYAN}{'═' * 60}{Style.RESET_ALL}")

    while True:
        print(f"\n{Fore.YELLOW}  MENU{Style.RESET_ALL}")
        print("  ─" * 30)
        print("  1. Run full pipeline")
        print("  2. Exit")
        print("  ─" * 30)

        choice = input("  Choose option (1-2): ").strip()

        if choice == "1":
            try:
                (processed, stats, top_words,
                 top_comments, leaderboard, correlations) = run_pipeline()

                # Display all results
                display_statistics(stats)
                display_top_posts(top_words, "word_count")
                display_top_posts(top_comments, "comment_count")
                display_leaderboard(leaderboard)
                display_correlations(correlations)

                # Save to files
                save_results(processed, stats, leaderboard)

                print(f"\n{Fore.GREEN}  ✅ Pipeline completed successfully!{Style.RESET_ALL}")

            except Exception as e:
                print(f"\n  ❌ Pipeline failed: {e}")
                import traceback
                traceback.print_exc()

        elif choice == "2":
            print("\n  See you on Day 11! 💪\n")
            break
        else:
            print("  ❌ Invalid option.")


if __name__ == "__main__":
    main()