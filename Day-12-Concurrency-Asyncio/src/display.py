# ============================================================
# src/display.py
# Terminal display functions
# ============================================================

try:
    from colorama import init, Fore, Style, Back
    init(autoreset=True)
    HAS_COLOR = True
except ImportError:
    HAS_COLOR = False
    class Fore:
        CYAN = GREEN = YELLOW = RED = BLUE = MAGENTA = WHITE = ""
    class Style:
        RESET_ALL = BRIGHT = DIM = ""


CATEGORY_COLORS = {
    "Technology": Fore.CYAN,
    "Science": Fore.BLUE,
    "World": Fore.GREEN,
    "Business": Fore.YELLOW,
    "Sports": Fore.MAGENTA,
    "Updates": Fore.WHITE,
    "Discussion": Fore.BLUE,
}


def print_header(title, subtitle=None):
    """Print a formatted header."""
    print(f"\n{Fore.CYAN}{'═' * 64}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}  {title}{Style.RESET_ALL}")
    if subtitle:
        print(f"{Fore.CYAN}  {subtitle}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'═' * 64}{Style.RESET_ALL}")


def print_section(title):
    """Print a section separator."""
    print(f"\n{Fore.YELLOW}  ── {title} ──{Style.RESET_ALL}")


def display_fetch_progress(results):
    """Show per-source fetch results."""
    print_section("FETCH RESULTS")
    print(f"\n  {'Source':<22} {'Status':<10} {'Headlines':>9} {'Time':>8}")
    print(f"  {'─' * 54}")

    for result in results:
        status = (f"{Fore.GREEN}✅ OK{Style.RESET_ALL}"
                  if result["success"]
                  else f"{Fore.RED}❌ Failed{Style.RESET_ALL}")
        count = len(result.get("headlines", []))
        time_str = f"{result['fetch_time']:.3f}s"

        print(f"  {result['source']:<22} {status:<18} {count:>9} {time_str:>8}")

        if not result["success"] and result.get("error"):
            print(f"    {Fore.RED}Error: {result['error']}{Style.RESET_ALL}")


def display_performance(stats):
    """Display performance comparison."""
    print_section("PERFORMANCE COMPARISON")

    seq = stats["sequential_time"]
    async_t = stats["async_time"]
    speedup = stats["speedup_factor"]
    saved = stats["time_saved_seconds"]
    pct = stats["time_saved_pct"]

    print(f"\n  Sequential fetch:  {Fore.RED}{seq:.3f}s{Style.RESET_ALL}")
    print(f"  Async fetch:       {Fore.GREEN}{async_t:.3f}s{Style.RESET_ALL}")
    print(f"  Speedup:           {Fore.YELLOW}{speedup}x faster{Style.RESET_ALL}")
    print(f"  Time saved:        {saved:.3f}s ({pct}%)")

    # Visual bar comparison
    max_bar = 40
    seq_bar = max_bar
    async_bar = max(1, int(async_t / seq * max_bar)) if seq > 0 else 1

    print(f"\n  Sequential: {Fore.RED}{'█' * seq_bar}{Style.RESET_ALL} {seq:.3f}s")
    print(f"  Async:      {Fore.GREEN}{'█' * async_bar}{Style.RESET_ALL} {async_t:.3f}s")

    if speedup >= 4:
        print(f"\n  {Fore.GREEN}🚀 Excellent! Async is {speedup}x faster than sequential.{Style.RESET_ALL}")
    elif speedup >= 2:
        print(f"\n  {Fore.YELLOW}⚡ Good! Async is {speedup}x faster than sequential.{Style.RESET_ALL}")
    else:
        print(f"\n  {Fore.BLUE}ℹ️  Speedup was {speedup}x (network conditions may vary).{Style.RESET_ALL}")


def display_statistics(stats):
    """Display headline statistics."""
    print_section("STATISTICS")

    print(f"\n  Total sources:      {stats['total_sources']}")
    print(f"  Successful:         {Fore.GREEN}{stats['successful_sources']}{Style.RESET_ALL}")
    if stats["failed_sources"] > 0:
        print(f"  Failed:             {Fore.RED}{stats['failed_sources']}{Style.RESET_ALL}")
    print(f"  Total headlines:    {stats['total_headlines']}")
    print(f"  Categories:         {stats['unique_categories']}")

    print_section("HEADLINES BY CATEGORY")
    for category, count in stats["headlines_per_category"].items():
        color = CATEGORY_COLORS.get(category, "")
        bar = "█" * count
        print(f"  {color}{category:<14}{Style.RESET_ALL} {count:>3}  {color}{bar}{Style.RESET_ALL}")

    print_section("FETCH TIME PER SOURCE")
    sorted_times = sorted(
        stats["fetch_times"].items(),
        key=lambda x: x[1]
    )
    for source, t in sorted_times:
        bar_len = max(1, int(t / max(stats["fetch_times"].values()) * 20))
        bar = "█" * bar_len
        color = Fore.GREEN if t < 0.5 else Fore.YELLOW if t < 1.0 else Fore.RED
        print(f"  {source:<22} {color}{t:.3f}s  {bar}{Style.RESET_ALL}")

    if stats.get("fastest_source"):
        print(f"\n  ⚡ Fastest: {Fore.GREEN}{stats['fastest_source']}{Style.RESET_ALL}")
    if stats.get("slowest_source"):
        print(f"  🐢 Slowest: {Fore.RED}{stats['slowest_source']}{Style.RESET_ALL}")


def display_headlines(headlines_by_category, limit_per_category=5):
    """Display headlines organized by category."""
    print_section("TOP HEADLINES BY CATEGORY")

    for category, headlines in headlines_by_category.items():
        color = CATEGORY_COLORS.get(category, "")
        print(f"\n  {color}◆ {category.upper()}{Style.RESET_ALL} "
              f"({len(headlines)} headlines)")
        print(f"  {'─' * 60}")

        for i, headline in enumerate(headlines[:limit_per_category], 1):
            title = headline["title"]
            if len(title) > 55:
                title = title[:52] + "..."
            source = headline["source"]
            print(f"  {i}. {title}")
            print(f"     {Fore.BLUE}{source}{Style.RESET_ALL}")

    total = sum(len(h) for h in headlines_by_category.values())
    if total > sum(min(limit_per_category, len(h)) for h in headlines_by_category.values()):
        hidden = total - sum(min(limit_per_category, len(h)) for h in headlines_by_category.values())
        print(f"\n  {Fore.YELLOW}... and {hidden} more headlines{Style.RESET_ALL}")


def display_error_summary(stats):
    """Display any errors that occurred."""
    if not stats.get("failed_sources_list"):
        return

    print_section("ERRORS")
    for failed in stats["failed_sources_list"]:
        print(f"  {Fore.RED}❌ {failed['source']}: {failed['error']}{Style.RESET_ALL}")