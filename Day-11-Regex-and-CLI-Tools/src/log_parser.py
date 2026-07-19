# ============================================================
# src/log_parser.py
# Parses log files using regular expressions
# ============================================================

import re
import json
import csv
from pathlib import Path
from datetime import datetime
from collections import defaultdict, Counter


# ─────────────────────────────────────────
# COMPILED REGEX PATTERNS
# ─────────────────────────────────────────

# Main log line pattern with named groups
LOG_LINE_PATTERN = re.compile(r"""
    \[
    (?P<date>\d{4}-\d{2}-\d{2})      # date: YYYY-MM-DD
    \s
    (?P<time>\d{2}:\d{2}:\d{2})      # time: HH:MM:SS
    \]
    \s
    (?P<level>DEBUG|INFO|WARNING|ERROR|CRITICAL)  # log level
    \s
    \[
    (?P<source>[^\]:]+)               # source file
    :
    (?P<line_num>\d+)                 # line number
    \]
    \s
    (?P<message>.+)                   # log message
""", re.VERBOSE)

# Patterns for extracting specific data from messages
IP_PATTERN = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
EMAIL_PATTERN = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
URL_PATTERN = re.compile(r"https?://[^\s,\]]+")
DURATION_PATTERN = re.compile(r"(\d+(?:\.\d+)?)\s*ms\b")
STATUS_CODE_PATTERN = re.compile(r"\bstatus\s+(\d{3})\b", re.IGNORECASE)
USER_PATTERN = re.compile(r"\buser[:\s]+([a-zA-Z0-9._-]+)\b", re.IGNORECASE)
PORT_PATTERN = re.compile(r"\bport\s+(\d+)\b", re.IGNORECASE)
MEMORY_PATTERN = re.compile(r"(\d+(?:\.\d+)?)\s*(?:MB|GB|KB)\b", re.IGNORECASE)


# ─────────────────────────────────────────
# PARSING FUNCTIONS
# ─────────────────────────────────────────

def parse_log_line(line):
    """
    Parse a single log line into a structured dictionary.

    Args:
        line (str): A raw log line.

    Returns:
        dict or None: Parsed log entry, or None if line does not match.
    """
    line = line.strip()
    if not line:
        return None

    match = LOG_LINE_PATTERN.match(line)
    if not match:
        return None

    data = match.groupdict()

    # Combine date and time into datetime object
    try:
        data["datetime"] = datetime.strptime(
            f"{data['date']} {data['time']}",
            "%Y-%m-%d %H:%M:%S"
        )
        data["timestamp"] = data["datetime"].isoformat()
    except ValueError:
        data["datetime"] = None
        data["timestamp"] = None

    # Extract embedded data from message using regex
    message = data["message"]
    data["extracted"] = {
        "ips": IP_PATTERN.findall(message),
        "emails": EMAIL_PATTERN.findall(message),
        "urls": URL_PATTERN.findall(message),
        "durations_ms": [float(d) for d in DURATION_PATTERN.findall(message)],
        "status_codes": [int(s) for s in STATUS_CODE_PATTERN.findall(message)],
        "users": USER_PATTERN.findall(message),
        "ports": [int(p) for p in PORT_PATTERN.findall(message)],
    }

    return data


def parse_log_file(filepath):
    """
    Parse an entire log file into a list of entries.

    Args:
        filepath (str or Path): Path to the log file.

    Returns:
        tuple: (list of parsed entries, list of unparseable lines)
    """
    filepath = Path(filepath)

    if not filepath.exists():
        raise FileNotFoundError(f"Log file not found: {filepath}")

    if not filepath.is_file():
        raise ValueError(f"Path is not a file: {filepath}")

    entries = []
    unparseable = []

    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        for line_num, line in enumerate(f, start=1):
            parsed = parse_log_line(line)
            if parsed:
                parsed["raw_line"] = line.strip()
                parsed["file_line"] = line_num
                entries.append(parsed)
            elif line.strip():
                unparseable.append({
                    "line_num": line_num,
                    "content": line.strip()
                })

    return entries, unparseable


def filter_entries(entries, level=None, since=None, until=None,
                   source=None, pattern=None):
    """
    Filter log entries by various criteria.

    Args:
        entries (list): Parsed log entries.
        level (str): Filter by exact log level.
        since (str): Show entries after this date string (YYYY-MM-DD).
        until (str): Show entries before this date string (YYYY-MM-DD).
        source (str): Filter by source filename.
        pattern (str): Regex pattern to match in message.

    Returns:
        list: Filtered entries.
    """
    filtered = entries

    # Filter by level
    if level:
        level = level.upper()
        filtered = [e for e in filtered if e["level"] == level]

    # Filter by date range
    if since:
        try:
            since_dt = datetime.strptime(since, "%Y-%m-%d")
            filtered = [
                e for e in filtered
                if e["datetime"] and e["datetime"] >= since_dt
            ]
        except ValueError:
            pass

    if until:
        try:
            until_dt = datetime.strptime(until, "%Y-%m-%d")
            filtered = [
                e for e in filtered
                if e["datetime"] and e["datetime"] <= until_dt
            ]
        except ValueError:
            pass

    # Filter by source file
    if source:
        source_pattern = re.compile(source, re.IGNORECASE)
        filtered = [
            e for e in filtered
            if source_pattern.search(e["source"])
        ]

    # Filter by message pattern
    if pattern:
        try:
            msg_pattern = re.compile(pattern, re.IGNORECASE)
            filtered = [
                e for e in filtered
                if msg_pattern.search(e["message"])
            ]
        except re.error as e:
            raise ValueError(f"Invalid regex pattern '{pattern}': {e}")

    return filtered


def search_with_context(entries, pattern, context_lines=0):
    """
    Search entries and return matches with surrounding context.

    Args:
        entries (list): All parsed log entries.
        pattern (str): Regex pattern to search for.
        context_lines (int): Number of entries before/after to include.

    Returns:
        list: List of match groups with context.
    """
    try:
        compiled = re.compile(pattern, re.IGNORECASE)
    except re.error as e:
        raise ValueError(f"Invalid regex pattern: {e}")

    results = []
    for i, entry in enumerate(entries):
        if compiled.search(entry["message"]) or compiled.search(entry.get("raw_line", "")):
            # Get context
            start = max(0, i - context_lines)
            end = min(len(entries), i + context_lines + 1)

            results.append({
                "match_index": i,
                "match": entry,
                "before": entries[start:i],
                "after": entries[i + 1:end]
            })

    return results


# ─────────────────────────────────────────
# ANALYSIS FUNCTIONS
# ─────────────────────────────────────────

def compute_stats(entries):
    """
    Compute comprehensive statistics from log entries.

    Args:
        entries (list): Parsed log entries.

    Returns:
        dict: Statistical analysis.
    """
    if not entries:
        return {}

    # Level distribution
    level_counts = Counter(e["level"] for e in entries)

    # Source file distribution
    source_counts = Counter(e["source"] for e in entries)

    # Hourly distribution
    hourly = defaultdict(int)
    for entry in entries:
        if entry["datetime"]:
            hour = entry["datetime"].strftime("%H:00")
            hourly[hour] += 1

    # Extract all IPs across all entries
    all_ips = []
    all_users = []
    all_durations = []
    all_status_codes = []

    for entry in entries:
        extracted = entry.get("extracted", {})
        all_ips.extend(extracted.get("ips", []))
        all_users.extend(extracted.get("users", []))
        all_durations.extend(extracted.get("durations_ms", []))
        all_status_codes.extend(extracted.get("status_codes", []))

    # Date range
    timestamps = [e["datetime"] for e in entries if e["datetime"]]
    date_range = {
        "start": min(timestamps).strftime("%Y-%m-%d %H:%M:%S") if timestamps else "N/A",
        "end": max(timestamps).strftime("%Y-%m-%d %H:%M:%S") if timestamps else "N/A"
    }

    # Error rate
    error_count = level_counts.get("ERROR", 0) + level_counts.get("CRITICAL", 0)
    error_rate = (error_count / len(entries) * 100) if entries else 0

    return {
        "total_entries": len(entries),
        "date_range": date_range,
        "level_distribution": dict(level_counts.most_common()),
        "error_rate_pct": round(error_rate, 2),
        "top_sources": dict(source_counts.most_common(5)),
        "hourly_distribution": dict(sorted(hourly.items())),
        "unique_ips": len(set(all_ips)),
        "top_ips": dict(Counter(all_ips).most_common(5)),
        "unique_users": len(set(all_users)),
        "top_users": dict(Counter(all_users).most_common(5)),
        "avg_duration_ms": round(sum(all_durations) / len(all_durations), 2) if all_durations else 0,
        "max_duration_ms": max(all_durations) if all_durations else 0,
        "status_code_counts": dict(Counter(all_status_codes).most_common()),
    }


# ─────────────────────────────────────────
# OUTPUT FUNCTIONS
# ─────────────────────────────────────────

def export_to_json(entries, output_file):
    """Export entries to a JSON file."""
    # Convert datetime objects to strings for JSON serialization
    serializable = []
    for entry in entries:
        e = {k: v for k, v in entry.items() if k != "datetime"}
        serializable.append(e)

    output_file = Path(output_file)
    output_file.parent.mkdir(exist_ok=True)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(serializable, f, indent=2)

    return output_file


def export_to_csv(entries, output_file):
    """Export entries to a CSV file."""
    if not entries:
        return None

    output_file = Path(output_file)
    output_file.parent.mkdir(exist_ok=True)

    fieldnames = ["timestamp", "level", "source", "line_num", "message"]

    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for entry in entries:
            writer.writerow({
                "timestamp": entry.get("timestamp", ""),
                "level": entry.get("level", ""),
                "source": entry.get("source", ""),
                "line_num": entry.get("line_num", ""),
                "message": entry.get("message", "")
            })

    return output_file