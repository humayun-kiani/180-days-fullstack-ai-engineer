# ============================================================
# src/reporter.py
# Terminal display
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
    print(f"\n{Fore.CYAN}{'═' * 65}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}  {title}{Style.RESET_ALL}")
    if subtitle:
        print(f"{Fore.CYAN}  {subtitle}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'═' * 65}{Style.RESET_ALL}")


def section(title):
    print(f"\n{Fore.YELLOW}  ── {title} ──{Style.RESET_ALL}")


def display_overview(results):
    section("DATABASE OVERVIEW")
    ov = results["overview"]
    for key, value in ov.items():
        print(f"  {key.title():<20} {Fore.GREEN}{value}{Style.RESET_ALL}")


def display_top_authors(results):
    section("TOP AUTHORS BY VIEWS")
    rows = results["top_authors"]
    if not rows:
        print("  No data.")
        return
    print(f"\n  {'Username':<20} {'Posts':>6} {'Total Views':>12} {'Avg Views':>10}")
    print(f"  {'─' * 52}")
    medals = ["🥇", "🥈", "🥉"]
    for i, r in enumerate(rows):
        medal = medals[i] if i < 3 else f"  {i+1}."
        name = (r['display_name'] or r['username'])[:18]
        print(
            f"  {medal} {name:<18} "
            f"{r['post_count']:>6} "
            f"{r['total_views']:>12,} "
            f"{r['avg_views']:>10.1f}"
        )


def display_popular_posts(results):
    section("POPULAR POSTS")
    rows = results["popular_posts"]
    if not rows:
        print("  No published posts found.")
        return
    print(f"\n  {'Title':<38} {'Views':>6} {'Likes':>6} {'Author'}")
    print(f"  {'─' * 60}")
    for r in rows:
        title = r["title"][:36] + ".." if len(r["title"]) > 38 else r["title"]
        print(
            f"  {title:<38} "
            f"{r['views']:>6,} "
            f"{r['likes']:>6} "
            f"{r['author']}"
        )


def display_category_stats(results):
    section("CATEGORY STATISTICS")
    rows = results["category_stats"]
    print(f"\n  {'Category':<28} {'Posts':>6} {'Views':>10} {'Avg':>8}")
    print(f"  {'─' * 56}")
    for r in rows:
        print(
            f"  {r['category']:<28} "
            f"{r['post_count']:>6} "
            f"{r['total_views']:>10,} "
            f"{r['avg_views']:>8.1f}"
        )


def display_post_stats(results):
    section("POST STATISTICS")
    s = results["post_stats"]
    print(f"\n  {'Total posts:':<25} {s['total']}")
    print(f"  {'Published:':<25} {Fore.GREEN}{s['published']}{Style.RESET_ALL}")
    print(f"  {'Drafts:':<25} {Fore.YELLOW}{s['drafts']}{Style.RESET_ALL}")
    print(f"  {'Total views:':<25} {s['total_views']:,}")
    print(f"  {'Average views:':<25} {s['avg_views']:.1f}")
    print(f"  {'Max views:':<25} {s['max_views']:,}")


def display_tag_stats(results):
    section("TAG STATISTICS")
    rows = results["tag_stats"]
    max_posts = max(r["posts"] for r in rows) if rows else 1
    print(f"\n  {'Tag':<20} {'Posts':>6} {'Views':>10}  Chart")
    print(f"  {'─' * 48}")
    for r in rows:
        bar_len = int(r["posts"] / max_posts * 20)
        bar = "█" * bar_len
        print(
            f"  {r['tag']:<20} "
            f"{r['posts']:>6} "
            f"{r['views']:>10,}  "
            f"{Fore.CYAN}{bar}{Style.RESET_ALL}"
        )


def display_eager_loading_demo(results):
    section("EAGER LOADING — N+1 PREVENTION")
    demo = results["eager_loading_demo"]
    print(f"\n  {Fore.RED}Problem:  {demo['naive_approach']}{Style.RESET_ALL}")
    print(f"  {Fore.GREEN}Solution: {demo['note']}{Style.RESET_ALL}")
    print(f"\n  SQLAlchemy solves this with:")
    print(f"    joinedload()   → single LEFT JOIN query")
    print(f"    selectinload() → 2 queries using IN clause")


def display_all(results):
    display_overview(results)
    display_top_authors(results)
    display_popular_posts(results)
    display_category_stats(results)
    display_post_stats(results)
    display_tag_stats(results)
    display_eager_loading_demo(results)


def save_report(results):
    DATA_DIR.mkdir(exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = DATA_DIR / f"orm_report_{ts}.json"
    with open(out, "w") as f:
        json.dump(results, f, indent=2, default=str)
    return out