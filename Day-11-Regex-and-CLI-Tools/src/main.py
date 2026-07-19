# ============================================================
# src/main.py
# Log File Analyzer CLI Tool — Entry Point
# Day 11 - 180 Days Full Stack AI Engineer Roadmap
# ============================================================

import sys
import argparse
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.log_parser import (
    parse_log_file,
    filter_entries,
    search_with_context,
    compute_stats,
    export_to_json,
    export_to_csv
)
from src.log_generator import generate_log_file
from src.display import (
    print_header,
    print_subheader,
    display_entries_table,
    display_stats,
    display_search_results,
    display_summary_line,
    Fore, Style
)


# ─────────────────────────────────────────
# COMMAND HANDLERS
# ─────────────────────────────────────────

def handle_generate(args):
    """Handle the 'generate' subcommand."""
    print_header(
        "LOG FILE GENERATOR",
        f"Generating {args.lines} log lines → {args.output}"
    )

    try:
        filepath = generate_log_file(
            filepath=args.output,
            num_lines=args.lines
        )

        file_size = filepath.stat().st_size
        print(f"\n  ✅ Generated: {filepath}")
        print(f"  Lines:       {args.lines:,}")
        print(f"  File size:   {file_size:,} bytes")
        print(f"\n  Now try:")
        print(f"  {Fore.CYAN}python src/main.py analyze {filepath}{Style.RESET_ALL}")
        print(f"  {Fore.CYAN}python src/main.py stats {filepath}{Style.RESET_ALL}")
        print(f"  {Fore.CYAN}python src/main.py search \"ERROR\" {filepath}{Style.RESET_ALL}")

    except Exception as e:
        print(f"\n  ❌ Generation failed: {e}")
        sys.exit(1)


def handle_analyze(args):
    """Handle the 'analyze' subcommand."""
    print_header(
        "LOG ANALYZER",
        f"File: {args.file}"
    )

    # Parse the file
    print(f"\n  Parsing {args.file}...")
    try:
        entries, unparseable = parse_log_file(args.file)
    except FileNotFoundError:
        print(f"\n  ❌ File not found: {args.file}")
        print(f"     Generate a sample: python src/main.py generate logs/server.log")
        sys.exit(1)
    except Exception as e:
        print(f"\n  ❌ Error reading file: {e}")
        sys.exit(1)

    print(f"  Parsed {len(entries):,} entries "
          f"({len(unparseable)} unparseable lines)")

    # Apply filters
    filtered = filter_entries(
        entries,
        level=args.level,
        since=args.since,
        until=args.until,
        source=args.source,
        pattern=args.pattern
    )

    # Show filter summary
    if any([args.level, args.since, args.until, args.source, args.pattern]):
        print_subheader("FILTERS APPLIED")
        if args.level:
            display_summary_line("Level filter:", args.level)
        if args.since:
            display_summary_line("Since:", args.since)
        if args.until:
            display_summary_line("Until:", args.until)
        if args.source:
            display_summary_line("Source filter:", args.source)
        if args.pattern:
            display_summary_line("Message pattern:", args.pattern)
        print(f"\n  Matching entries: {len(filtered):,} of {len(entries):,}")

    # Output based on format
    if args.output == "json":
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = Path("data") / f"analysis_{timestamp}.json"
        saved = export_to_json(filtered[:args.limit], output_file)
        print(f"\n  ✅ Exported {len(filtered[:args.limit]):,} entries to: {saved}")

    elif args.output == "csv":
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = Path("data") / f"analysis_{timestamp}.csv"
        saved = export_to_csv(filtered[:args.limit], output_file)
        print(f"\n  ✅ Exported {len(filtered[:args.limit]):,} entries to: {saved}")

    else:
        # Default: table
        print_subheader("LOG ENTRIES")
        display_entries_table(filtered, limit=args.limit)


def handle_search(args):
    """Handle the 'search' subcommand."""
    print_header(
        "LOG SEARCH",
        f"Pattern: '{args.pattern}' | File: {args.file}"
    )

    try:
        entries, _ = parse_log_file(args.file)
    except FileNotFoundError:
        print(f"\n  ❌ File not found: {args.file}")
        sys.exit(1)

    # Apply level filter if specified
    if args.level:
        entries = filter_entries(entries, level=args.level)

    try:
        results = search_with_context(entries, args.pattern, args.context)
    except ValueError as e:
        print(f"\n  ❌ {e}")
        sys.exit(1)

    display_search_results(results, args.pattern, args.context)

    # Export if requested
    if args.output != "table" and results:
        matches = [r["match"] for r in results]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if args.output == "json":
            output_file = Path("data") / f"search_{timestamp}.json"
            saved = export_to_json(matches, output_file)
            print(f"\n  ✅ Results saved to: {saved}")
        elif args.output == "csv":
            output_file = Path("data") / f"search_{timestamp}.csv"
            saved = export_to_csv(matches, output_file)
            print(f"\n  ✅ Results saved to: {saved}")


def handle_stats(args):
    """Handle the 'stats' subcommand."""
    print_header(
        "LOG STATISTICS",
        f"File: {args.file}"
    )

    try:
        entries, unparseable = parse_log_file(args.file)
    except FileNotFoundError:
        print(f"\n  ❌ File not found: {args.file}")
        sys.exit(1)

    print(f"\n  Parsed {len(entries):,} entries")

    stats = compute_stats(entries)
    display_stats(stats)

    # Export stats if requested
    if args.output == "json":
        import json
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = Path("data") / f"stats_{timestamp}.json"
        output_file.parent.mkdir(exist_ok=True)
        with open(output_file, "w") as f:
            json.dump(stats, f, indent=2)
        print(f"\n  ✅ Statistics saved to: {output_file}")


# ─────────────────────────────────────────
# ARGUMENT PARSER SETUP
# ─────────────────────────────────────────

def build_parser():
    """Build and return the argument parser."""

    # Main parser
    parser = argparse.ArgumentParser(
        prog="loganalyzer",
        description=(
            "Log File Analyzer — A powerful CLI tool for analyzing "
            "server log files using regex pattern matching."
        ),
        epilog=(
            "Examples:\n"
            "  python src/main.py generate logs/server.log --lines 500\n"
            "  python src/main.py analyze logs/server.log --level ERROR\n"
            "  python src/main.py search 'database.*failed' logs/server.log\n"
            "  python src/main.py stats logs/server.log --output json"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        "--version", "-V",
        action="version",
        version="loganalyzer 1.0.0 — Day 11 of 180-Day Roadmap"
    )

    # Subcommands
    subparsers = parser.add_subparsers(
        dest="command",
        metavar="COMMAND",
        help="Available commands (use COMMAND --help for details)"
    )

    # ── generate subcommand ──
    gen_parser = subparsers.add_parser(
        "generate",
        help="Generate a sample log file for testing",
        description="Generate a realistic server log file with mixed log levels."
    )
    gen_parser.add_argument(
        "output",
        help="Output file path (e.g. logs/server.log)"
    )
    gen_parser.add_argument(
        "--lines", "-n",
        type=int,
        default=200,
        metavar="N",
        help="Number of log lines to generate (default: 200)"
    )

    # ── analyze subcommand ──
    analyze_parser = subparsers.add_parser(
        "analyze",
        help="Analyze a log file and display entries",
        description="Parse and display log entries with optional filtering."
    )
    analyze_parser.add_argument(
        "file",
        help="Path to the log file to analyze"
    )
    analyze_parser.add_argument(
        "--level", "-l",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        metavar="LEVEL",
        help="Filter by log level (DEBUG/INFO/WARNING/ERROR/CRITICAL)"
    )
    analyze_parser.add_argument(
        "--since", "-s",
        metavar="YYYY-MM-DD",
        help="Show entries on or after this date"
    )
    analyze_parser.add_argument(
        "--until", "-u",
        metavar="YYYY-MM-DD",
        help="Show entries on or before this date"
    )
    analyze_parser.add_argument(
        "--source",
        metavar="FILE",
        help="Filter by source filename (supports regex)"
    )
    analyze_parser.add_argument(
        "--pattern", "-p",
        metavar="REGEX",
        help="Filter messages matching this regex pattern"
    )
    analyze_parser.add_argument(
        "--limit",
        type=int,
        default=50,
        metavar="N",
        help="Maximum entries to display (default: 50)"
    )
    analyze_parser.add_argument(
        "--output", "-o",
        choices=["table", "json", "csv"],
        default="table",
        help="Output format: table, json, or csv (default: table)"
    )

    # ── search subcommand ──
    search_parser = subparsers.add_parser(
        "search",
        help="Search log entries using a regex pattern",
        description="Search for log entries matching a regex pattern."
    )
    search_parser.add_argument(
        "pattern",
        help="Regex pattern to search for in log messages"
    )
    search_parser.add_argument(
        "file",
        help="Path to the log file to search"
    )
    search_parser.add_argument(
        "--context", "-c",
        type=int,
        default=0,
        metavar="N",
        help="Show N entries of context around each match (default: 0)"
    )
    search_parser.add_argument(
        "--level", "-l",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Filter by log level before searching"
    )
    search_parser.add_argument(
        "--output", "-o",
        choices=["table", "json", "csv"],
        default="table",
        help="Output format for results (default: table)"
    )

    # ── stats subcommand ──
    stats_parser = subparsers.add_parser(
        "stats",
        help="Show statistical summary of a log file",
        description="Compute and display statistics about a log file."
    )
    stats_parser.add_argument(
        "file",
        help="Path to the log file"
    )
    stats_parser.add_argument(
        "--output", "-o",
        choices=["table", "json"],
        default="table",
        help="Output format (default: table)"
    )

    return parser


# ─────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────

def main():
    """Main entry point for the CLI tool."""

    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        print_header(
            "LOG FILE ANALYZER",
            "Day 11 — 180 Days Full Stack AI Engineer Roadmap"
        )
        print(f"\n  A professional CLI tool for analyzing server log files.")
        print(f"  Built with Python argparse + regular expressions.\n")
        parser.print_help()
        sys.exit(0)

    # Route to the appropriate handler
    handlers = {
        "generate": handle_generate,
        "analyze": handle_analyze,
        "search": handle_search,
        "stats": handle_stats
    }

    handler = handlers.get(args.command)
    if handler:
        handler(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()