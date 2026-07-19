# ============================================================
# src/display.py
# Terminal display functions with color output
# ============================================================

try:
    from colorama import init, Fore, Style, Back
    init(autoreset=True)
    HAS_COLOR = True
except ImportError:
    HAS_COLOR = False
    class Fore:
        RED = GREEN = YELLOW = CYAN = BLUE = MAGENTA = WHITE = ""
    class Style:
        RESET_ALL = BRIGHT = DIM = ""
    class Back:
        RED = GREEN = YELLOW = ""


# Level colors
LEVEL_COLORS = {
    "DEBUG": Fore.BLUE,
    "INFO": Fore.GREEN,
    "WARNING": Fore.YELLOW,
    "ERROR": Fore.RED,
    "CRITICAL": Fore.RED + Style.BRIGHT
}


def colorize_level(level):
    """Return colored level string."""
    color = LEVEL_COLORS.get(level, "")
    return f"{color}{level:<8}{Style.RESET_ALL}"


def print_header(title, subtitle=None):
    """Print a formatted header."""
    print(f"\n{Fore.CYAN}{'═' * 62}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}  {title}{Style.RESET_ALL}")
    if subtitle:
        print(f"{Fore.CYAN}  {subtitle}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'═' * 62}{Style.RESET_ALL}")


def print_subheader(title):
    """Print a section subheader."""
    print(f"\n{Fore.YELLOW}  ── {title} ──{Style.RESET_ALL}")


def display_entries_table(entries, limit=None):
    """
    Display log entries as a formatted table.

    Args:
        entries (list): Parsed log entries.
        limit (int): Maximum entries to show.
    """
    if not entries:
        print(f"\n  {Fore.YELLOW}No entries to display.{Style.RESET_ALL}")
        return

    show = entries[:limit] if limit else entries

    print(f"\n  {Fore.CYAN}{'Time':<10} {'Level':<10} {'Source':<18} Message{Style.RESET_ALL}")
    print(f"  {'─' * 62}")

    for entry in show:
        time_str = entry["time"]
        level_str = colorize_level(entry["level"])
        source = entry["source"][:16]
        message = entry["message"][:45]
        if len(entry["message"]) > 45:
            message += ".."

        print(f"  {time_str}  {level_str}  {source:<18} {message}")

    if limit and len(entries) > limit:
        remaining = len(entries) - limit
        print(f"\n  {Fore.YELLOW}... and {remaining} more entries{Style.RESET_ALL}")

    print(f"\n  Total: {len(entries)} entries")


def display_stats(stats):
    """Display statistical analysis."""
    if not stats:
        print(f"\n  {Fore.YELLOW}No statistics available.{Style.RESET_ALL}")
        return

    print_subheader("OVERVIEW")
    print(f"  Total log entries:    {stats['total_entries']:,}")
    print(f"  Date range:           {stats['date_range']['start']}")
    print(f"                        {stats['date_range']['end']}")
    print(f"  Error rate:           {stats['error_rate_pct']}%")
    print(f"  Unique IPs:           {stats['unique_ips']}")
    print(f"  Unique users:         {stats['unique_users']}")

    if stats.get("avg_duration_ms"):
        print(f"  Avg response time:    {stats['avg_duration_ms']}ms")
        print(f"  Max response time:    {stats['max_duration_ms']}ms")

    print_subheader("LEVEL DISTRIBUTION")
    total = stats["total_entries"]
    level_order = ["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"]
    for level in level_order:
        count = stats["level_distribution"].get(level, 0)
        if count == 0:
            continue
        pct = count / total * 100
        bar_len = int(pct / 2)    # max 50 chars
        bar = "█" * bar_len
        color = LEVEL_COLORS.get(level, "")
        print(f"  {color}{level:<10}{Style.RESET_ALL} "
              f"{count:>5}  {pct:>5.1f}%  {color}{bar}{Style.RESET_ALL}")

    print_subheader("TOP SOURCE FILES")
    for source, count in stats["top_sources"].items():
        print(f"  {source:<20} {count:>5} entries")

    if stats["top_ips"]:
        print_subheader("TOP IP ADDRESSES")
        for ip, count in stats["top_ips"].items():
            print(f"  {ip:<18} {count:>5} occurrences")

    if stats["top_users"]:
        print_subheader("TOP USERS")
        for user, count in stats["top_users"].items():
            print(f"  {user:<20} {count:>5} log entries")

    if stats.get("status_code_counts"):
        print_subheader("HTTP STATUS CODES")
        for code, count in sorted(stats["status_code_counts"].items()):
            color = (Fore.GREEN if str(code).startswith("2")
                     else Fore.YELLOW if str(code).startswith("4")
                     else Fore.RED)
            print(f"  {color}{code}{Style.RESET_ALL}  {count:>5} occurrences")

    if stats.get("hourly_distribution"):
        print_subheader("HOURLY ACTIVITY")
        max_count = max(stats["hourly_distribution"].values(), default=1)
        for hour, count in sorted(stats["hourly_distribution"].items()):
            bar_len = int(count / max_count * 30)
            bar = "█" * bar_len
            print(f"  {hour}  {bar} {count}")


def display_search_results(results, pattern, context=0):
    """Display search results with optional context."""
    if not results:
        print(f"\n  {Fore.YELLOW}No matches found for pattern: '{pattern}'{Style.RESET_ALL}")
        return

    print(f"\n  Found {Fore.GREEN}{len(results)}{Style.RESET_ALL} "
          f"match(es) for pattern: {Fore.CYAN}'{pattern}'{Style.RESET_ALL}")
    print(f"  {'─' * 62}")

    for i, result in enumerate(results, 1):
        match = result["match"]
        print(f"\n  {Fore.CYAN}Match {i} — Line {match['file_line']}{Style.RESET_ALL}")

        # Show context before
        if result["before"] and context > 0:
            for entry in result["before"]:
                print(f"    {Fore.BLUE}{entry['time']}  {entry['level']:<9} "
                      f"{entry['message'][:50]}{Style.RESET_ALL}")

        # Show the actual match (highlighted)
        print(f"  {Fore.GREEN}▶ {match['time']}  "
              f"{colorize_level(match['level'])}  "
              f"{match['message'][:55]}{Style.RESET_ALL}")

        # Show context after
        if result["after"] and context > 0:
            for entry in result["after"]:
                print(f"    {Fore.BLUE}{entry['time']}  {entry['level']:<9} "
                      f"{entry['message'][:50]}{Style.RESET_ALL}")


def display_summary_line(label, value, color=None):
    """Display a single summary line."""
    color = color or ""
    print(f"  {label:<30} {color}{value}{Style.RESET_ALL}")