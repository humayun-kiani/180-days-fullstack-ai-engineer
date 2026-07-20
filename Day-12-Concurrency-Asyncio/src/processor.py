# ============================================================
# src/processor.py
# Process, deduplicate, and rank fetched headlines
# ============================================================

import re
from collections import Counter, defaultdict


def deduplicate_headlines(all_results):
    """
    Remove duplicate headlines across sources.

    Uses title similarity to detect duplicates.

    Args:
        all_results (list): List of source result dicts.

    Returns:
        list: Deduplicated headline list.
    """
    seen_titles = set()
    unique_headlines = []

    for result in all_results:
        for headline in result.get("headlines", []):
            # Normalize title for comparison
            normalized = normalize_title(headline["title"])

            if normalized not in seen_titles:
                seen_titles.add(normalized)
                unique_headlines.append(headline)

    return unique_headlines


def normalize_title(title):
    """Normalize title for duplicate detection."""
    # Remove non-alphanumeric, lowercase, remove common words
    stopwords = {"a", "an", "the", "in", "on", "at", "to", "for",
                 "of", "and", "or", "but", "is", "are", "was",
                 "be", "has", "have", "had"}

    cleaned = re.sub(r"[^a-zA-Z0-9\s]", "", title.lower())
    words = [w for w in cleaned.split() if w not in stopwords and len(w) > 2]
    return " ".join(sorted(words[:8]))   # use first 8 significant words


def group_by_category(headlines):
    """
    Group headlines by category.

    Returns:
        dict: category → list of headlines
    """
    groups = defaultdict(list)
    for headline in headlines:
        groups[headline["category"]].append(headline)
    return dict(groups)


def compute_fetch_stats(results, sequential_time, async_time):
    """
    Compute performance statistics.

    Args:
        results (list): List of source results.
        sequential_time (float): Time for sequential fetch.
        async_time (float): Time for async fetch.

    Returns:
        dict: Statistics dictionary.
    """
    successful = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]

    all_headlines = []
    for r in results:
        all_headlines.extend(r.get("headlines", []))

    category_counts = Counter(h["category"] for h in all_headlines)
    source_counts = {
        r["source"]: len(r["headlines"]) for r in results
    }

    speedup = sequential_time / async_time if async_time > 0 else 1

    return {
        "total_sources": len(results),
        "successful_sources": len(successful),
        "failed_sources": len(failed),
        "total_headlines": len(all_headlines),
        "unique_categories": len(category_counts),
        "headlines_per_category": dict(category_counts.most_common()),
        "headlines_per_source": source_counts,
        "fetch_times": {r["source"]: round(r["fetch_time"], 3) for r in results},
        "slowest_source": max(results, key=lambda r: r["fetch_time"])["source"] if results else None,
        "fastest_source": min(successful, key=lambda r: r["fetch_time"])["source"] if successful else None,
        "sequential_time": round(sequential_time, 3),
        "async_time": round(async_time, 3),
        "speedup_factor": round(speedup, 2),
        "time_saved_seconds": round(sequential_time - async_time, 3),
        "time_saved_pct": round((1 - async_time / sequential_time) * 100, 1) if sequential_time > 0 else 0,
        "failed_sources_list": [
            {"source": r["source"], "error": r["error"]}
            for r in failed
        ]
    }


def prepare_export(headlines, stats):
    """Prepare data for JSON export."""
    from datetime import datetime
    return {
        "fetched_at": datetime.now().isoformat(),
        "statistics": stats,
        "headlines": headlines
    }