# ============================================================
# src/reporter.py
# Terminal display for product catalog
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


def bar(value, max_val, width=20, char="█"):
    filled = int(value / max_val * width) if max_val > 0 else 0
    return char * filled + "░" * (width - filled)


def display_overview(repo):
    """Display catalog overview."""
    section("CATALOG OVERVIEW")
    product_count = repo.count()
    review_count = repo.count_reviews()
    categories = repo.get_categories()

    print(f"\n  {'Total Products:':<28} {Fore.GREEN}{product_count}{Style.RESET_ALL}")
    print(f"  {'Total Reviews:':<28} {review_count}")
    print(f"  {'Categories:':<28} {len(categories)}")

    print(f"\n  {'Category':<26} {'Products':>8} {'Avg Price':>11} {'Brands':>7}")
    print(f"  {'─' * 56}")
    for cat in categories:
        print(
            f"  {cat['category']:<26} "
            f"{cat['count']:>8} "
            f"Rs.{int(cat.get('avg_price', 0)):>8,}  "
            f"{cat.get('brand_count', 0):>7}"
        )


def display_category_performance(data):
    """Display category performance analytics."""
    section("CATEGORY PERFORMANCE ANALYTICS")
    if not data:
        print("  No data.")
        return

    print(f"\n  {'Category':<22} {'Products':>8} {'Avg Price':>11} "
          f"{'Avg Rating':>10} {'Reviews':>8} {'Stock':>8}")
    print(f"  {'─' * 72}")

    for row in data:
        rating_color = (Fore.GREEN if row.get('avg_rating', 0) >= 4.0
                        else Fore.YELLOW if row.get('avg_rating', 0) >= 3.0
                        else Fore.RED)
        print(
            f"  {row['category']:<22} "
            f"{row['product_count']:>8} "
            f"Rs.{int(row['avg_price']):>8,}  "
            f"{rating_color}{row.get('avg_rating', 0):>10.2f}{Style.RESET_ALL} "
            f"{row.get('total_reviews', 0):>8} "
            f"{row.get('total_stock', 0):>8}"
        )


def display_brand_analysis(data):
    """Display brand market analysis."""
    section("BRAND MARKET ANALYSIS")
    if not data:
        print("  No data.")
        return

    print(f"\n  {'Brand':<20} {'Products':>8} {'Avg Price':>11} "
          f"{'Rating':>7} {'Views':>8} {'Conv%':>7}")
    print(f"  {'─' * 65}")

    for row in data[:10]:
        print(
            f"  {row['brand']:<20} "
            f"{row['product_count']:>8} "
            f"Rs.{int(row['avg_price']):>8,}  "
            f"{row.get('avg_rating', 0):>7.2f} "
            f"{int(row.get('total_views', 0)):>8,} "
            f"{row.get('conversion_rate', 0):>6.1f}%"
        )


def display_price_distribution(data):
    """Display price bucket distribution."""
    section("PRICE DISTRIBUTION")
    if not data:
        print("  No data.")
        return

    max_count = max(row["count"] for row in data)

    print(f"\n  {'Price Range':<30} {'Count':>6}  {'Avg Rating':>10}  Chart")
    print(f"  {'─' * 65}")

    for row in data:
        b = bar(row["count"], max_count, width=18)
        print(
            f"  {row['price_range']:<30} "
            f"{row['count']:>6}  "
            f"{row.get('avg_rating', 0):>10.2f}  "
            f"{Fore.CYAN}{b}{Style.RESET_ALL}"
        )


def display_rating_analysis(data):
    """Display rating analysis."""
    section("RATING ANALYSIS")
    if not data:
        print("  No data.")
        return

    if "overall_stats" in data and data["overall_stats"]:
        stats = data["overall_stats"][0]
        print(f"\n  Overall average rating: {Fore.GREEN}{stats.get('avg_rating', 0):.2f}/5.00{Style.RESET_ALL}")
        print(f"  Products with reviews:  {stats.get('total_products', 0)}")
        print(f"  Total reviews:          {stats.get('total_reviews', 0):,}")
        print(f"  Products rated 4.5+:    {stats.get('five_star_products', 0)}")

    if "top_rated" in data and data["top_rated"]:
        print(f"\n  {'Top Rated Products'}")
        print(f"  {'─' * 55}")
        for i, p in enumerate(data["top_rated"], 1):
            stars = "⭐" * int(p.get('rating', 0))
            print(f"  {i}. {p['name'][:35]:<35} {p.get('rating', 0):.1f} ({p.get('reviews', 0)} reviews)")


def display_tag_cloud(data):
    """Display tag frequency as a visual cloud."""
    section("TAG CLOUD (from $unwind aggregation)")
    if not data:
        print("  No data.")
        return

    max_count = max(row["count"] for row in data)

    print(f"\n  {'Tag':<20} {'Count':>6} {'Avg Price':>11} {'Categories':>10}  Chart")
    print(f"  {'─' * 64}")

    for row in data[:15]:
        b = bar(row["count"], max_count, width=15)
        print(
            f"  {row['tag']:<20} "
            f"{row['count']:>6} "
            f"Rs.{int(row.get('avg_price', 0)):>8,}  "
            f"{row.get('category_count', 0):>10}  "
            f"{Fore.CYAN}{b}{Style.RESET_ALL}"
        )


def display_inventory_health(data):
    """Display inventory health report."""
    section("INVENTORY HEALTH")
    if not data or not data.get("stock_levels"):
        print("  No inventory data.")
        return

    print(f"\n  Stock Level Status:")
    print(f"  {'─' * 40}")
    for level in data.get("stock_levels", []):
        color = (Fore.RED if level["_id"] == "Out of Stock"
                 else Fore.YELLOW if level["_id"] == "Low Stock"
                 else Fore.GREEN)
        print(f"  {color}{level['_id']:<20}{Style.RESET_ALL} {level['count']:>4} products")

    if data.get("category_stock"):
        print(f"\n  Category Stock Levels:")
        print(f"  {'Category':<22} {'Total':>8} {'Available':>10} {'Utilization':>12}")
        print(f"  {'─' * 55}")
        for row in data["category_stock"]:
            util = row.get("utilization_pct", 0)
            color = Fore.GREEN if util < 50 else Fore.YELLOW if util < 80 else Fore.RED
            print(
                f"  {row['category']:<22} "
                f"{row['total_units']:>8} "
                f"{row['available']:>10} "
                f"{color}{util:>11.1f}%{Style.RESET_ALL}"
            )


def display_top_products(products):
    """Display product list."""
    section("TOP PRODUCTS BY RATING")
    if not products:
        print("  No products found.")
        return

    print(f"\n  {'Name':<35} {'Brand':<12} {'Price':>10} {'Rating':>8} {'Reviews':>8}")
    print(f"  {'─' * 75}")

    for p in products:
        rating = p.get("rating", {})
        avg = rating.get("average", 0) if isinstance(rating, dict) else 0
        count = rating.get("count", 0) if isinstance(rating, dict) else 0
        name = p["name"][:33] + ".." if len(p["name"]) > 35 else p["name"]
        color = Fore.GREEN if avg >= 4.5 else Fore.YELLOW if avg >= 4.0 else ""
        print(
            f"  {name:<35} "
            f"{p.get('brand', 'N/A'):<12} "
            f"Rs.{int(p.get('price', 0)):>7,} "
            f"{color}{avg:>8.2f}{Style.RESET_ALL} "
            f"{count:>8}"
        )


def display_search_results(results, query):
    """Display text search results."""
    section(f"SEARCH RESULTS for '{query}'")
    if not results:
        print(f"  No products found matching '{query}'.")
        return

    print(f"\n  Found {len(results)} result(s):\n")
    for i, p in enumerate(results, 1):
        rating = p.get("rating", {})
        avg = rating.get("average", 0) if isinstance(rating, dict) else 0
        print(
            f"  {i}. {Fore.GREEN}{p['name']}{Style.RESET_ALL}"
            f" — {p.get('brand', 'N/A')}"
        )
        print(
            f"     Category: {p['category']} | "
            f"Price: Rs.{int(p.get('price', 0)):,} | "
            f"Rating: {avg:.1f}"
        )


def save_report(analytics_data):
    """Save analytics report to JSON."""
    DATA_DIR.mkdir(exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = DATA_DIR / f"catalog_report_{ts}.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(analytics_data, f, indent=2, default=str)
    return out