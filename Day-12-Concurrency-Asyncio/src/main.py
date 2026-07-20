# ============================================================
# src/main.py
# Async News Headline Fetcher — Main Entry Point
# Day 12 - 180 Days Full Stack AI Engineer Roadmap
# ============================================================

import asyncio
import json
import os
import sys
import time
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from src.fetcher import (
    FREE_SOURCES,
    fetch_all_async,
    fetch_all_sequential
)
from src.processor import (
    deduplicate_headlines,
    group_by_category,
    compute_fetch_stats,
    prepare_export
)
from src.cache import get_cached, set_cached, clear_cache
from src.display import (
    print_header,
    print_section,
    display_fetch_progress,
    display_performance,
    display_statistics,
    display_headlines,
    display_error_summary,
    Fore, Style
)


DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)

MAX_CONCURRENT = int(os.environ.get("MAX_CONCURRENT_REQUESTS", "10"))
TIMEOUT = int(os.environ.get("REQUEST_TIMEOUT_SECONDS", "10"))
CACHE_MINUTES = int(os.environ.get("CACHE_MINUTES", "15"))


async def run_full_fetch(use_cache=True, run_benchmark=True):
    """
    Execute the complete fetch pipeline.

    Args:
        use_cache (bool): Use cached results if available.
        run_benchmark (bool): Compare sequential vs async timing.

    Returns:
        tuple: (all_headlines, stats, export_data)
    """
    sources = FREE_SOURCES

    # ── Step 1: Check cache ──
    if use_cache:
        cached = get_cached("all_sources", CACHE_MINUTES)
        if cached:
            print(f"\n  {Fore.YELLOW}ℹ️  Using cached data "
                  f"(cached within {CACHE_MINUTES} minutes).{Style.RESET_ALL}")
            print(f"  To fetch fresh data, choose 'Clear cache & refresh'.\n")

            all_results = cached["results"]
            sequential_time = cached.get("sequential_time", 5.0)
            async_time = cached.get("async_time", 1.0)

            all_headlines = deduplicate_headlines(all_results)
            headlines_by_category = group_by_category(all_headlines)
            stats = compute_fetch_stats(
                all_results, sequential_time, async_time
            )
            return all_headlines, headlines_by_category, stats

    # ── Step 2: Sequential fetch (for benchmarking) ──
    if run_benchmark:
        print(f"\n  {Fore.BLUE}Step 1: Sequential fetch (baseline)...{Style.RESET_ALL}")
        sequential_results, sequential_time = fetch_all_sequential(
            sources, timeout=TIMEOUT
        )
        print(f"  Sequential completed in {Fore.RED}{sequential_time:.3f}s{Style.RESET_ALL}")
    else:
        sequential_time = len(sources) * 0.5   # estimated

    # ── Step 3: Async fetch ──
    print(f"\n  {Fore.BLUE}Step 2: Async concurrent fetch...{Style.RESET_ALL}")
    print(f"  Fetching {len(sources)} sources with max "
          f"{MAX_CONCURRENT} concurrent requests")

    async_results, async_time = await fetch_all_async(
        sources,
        max_concurrent=MAX_CONCURRENT,
        timeout=TIMEOUT
    )
    print(f"  Async completed in {Fore.GREEN}{async_time:.3f}s{Style.RESET_ALL}")

    # ── Step 4: Process results ──
    display_fetch_progress(async_results)

    all_headlines = deduplicate_headlines(async_results)
    headlines_by_category = group_by_category(all_headlines)
    stats = compute_fetch_stats(async_results, sequential_time, async_time)

    # ── Step 5: Cache results ──
    set_cached("all_sources", {
        "results": async_results,
        "sequential_time": sequential_time,
        "async_time": async_time
    })

    return all_headlines, headlines_by_category, stats


def save_results(all_headlines, stats):
    """Save results to JSON file."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = DATA_DIR / f"headlines_{timestamp}.json"

    export_data = prepare_export(all_headlines, stats)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(export_data, f, indent=2, ensure_ascii=False)

    return output_file


async def main():
    """Main entry point."""
    print_header(
        "ASYNC NEWS HEADLINE FETCHER",
        "Day 12 — Concurrency: Threading, Multiprocessing & Asyncio"
    )

    print(f"\n  This app demonstrates Python concurrency:")
    print(f"  • Sequential fetching (one request at a time)")
    print(f"  • Async concurrent fetching (all at once with asyncio)")
    print(f"  • Real speedup measurement and comparison")
    print(f"\n  Sources: {len(FREE_SOURCES)} APIs  |  "
          f"Max concurrent: {MAX_CONCURRENT}  |  "
          f"Cache: {CACHE_MINUTES}min")

    while True:
        print(f"\n{'─' * 64}")
        print("  MENU")
        print(f"{'─' * 64}")
        print("  1. Fetch headlines (with benchmark comparison)")
        print("  2. Fetch headlines (async only, faster)")
        print("  3. Clear cache and refresh")
        print("  4. Exit")
        print(f"{'─' * 64}")

        choice = input("  Choose option (1-4): ").strip()

        if choice == "1":
            print_header("FETCHING HEADLINES", "Running benchmark comparison...")
            all_headlines, by_category, stats = await run_full_fetch(
                use_cache=True,
                run_benchmark=True
            )

            display_performance(stats)
            display_statistics(stats)
            display_headlines(by_category, limit_per_category=4)
            display_error_summary(stats)

            # Save results
            saved_file = save_results(all_headlines, stats)
            print(f"\n  💾 Results saved to: {saved_file.name}")

        elif choice == "2":
            print_header("FETCHING HEADLINES", "Async only (no benchmark)...")
            all_headlines, by_category, stats = await run_full_fetch(
                use_cache=True,
                run_benchmark=False
            )

            display_statistics(stats)
            display_headlines(by_category, limit_per_category=4)
            display_error_summary(stats)

            saved_file = save_results(all_headlines, stats)
            print(f"\n  💾 Results saved to: {saved_file.name}")

        elif choice == "3":
            clear_cache()
            print(f"\n  {Fore.GREEN}✅ Cache cleared.{Style.RESET_ALL}")
            print("  Next fetch will get fresh data from all sources.")

        elif choice == "4":
            print(f"\n  See you on Day 13! 💪\n")
            break

        else:
            print(f"\n  {Fore.RED}❌ Invalid option. Choose 1-4.{Style.RESET_ALL}")


if __name__ == "__main__":
    asyncio.run(main())