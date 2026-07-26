# ============================================================
# src/main.py
# E-Commerce Product Catalog — Main Entry Point
# Day 18 — MongoDB: Documents, CRUD, Aggregation Pipeline
# ============================================================

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database import get_database, test_connection, setup_indexes, close_connection
from src.repository import ProductRepository
from src.analytics import CatalogAnalytics
from src.seed import seed_catalog
from src.reporter import (
    header, section,
    display_overview, display_category_performance,
    display_brand_analysis, display_price_distribution,
    display_rating_analysis, display_tag_cloud,
    display_inventory_health, display_top_products,
    display_search_results, save_report,
    Fore, Style
)


def check_needs_seeding(repo: ProductRepository) -> bool:
    return repo.count() == 0


def main():
    header(
        "E-COMMERCE PRODUCT CATALOG",
        "Day 18 — MongoDB: Documents, Collections, CRUD & Aggregation Pipeline"
    )

    # Test connection
    print("\n  Connecting to MongoDB...")
    info = test_connection()

    if not info["success"]:
        print(f"\n  {Fore.RED}❌ Cannot connect to MongoDB!{Style.RESET_ALL}")
        print(f"  Error: {info.get('error', 'Unknown')}")
        print(f"\n  Options:")
        print(f"  1. Install MongoDB locally: brew install mongodb-community")
        print(f"  2. Use MongoDB Atlas (free): cloud.mongodb.com")
        print(f"  3. Use Docker: docker run -d -p 27017:27017 mongo:7")
        print(f"\n  Update MONGODB_URI in .env file.")
        sys.exit(1)

    print(f"  {Fore.GREEN}✅ Connected! MongoDB v{info['version']}{Style.RESET_ALL}")
    print(f"  Database: {info['database']}")

    # Setup
    db = get_database()
    setup_indexes(db)
    repo = ProductRepository(db)
    analytics = CatalogAnalytics(db)

    # Seed if empty
    if check_needs_seeding(repo):
        print("\n  No products found. Seeding catalog...")
        counts = seed_catalog(db)
        print(f"\n  Loaded: {counts['products']} products, "
              f"{counts['reviews']} reviews, "
              f"{counts['categories']} categories")
    else:
        count = repo.count()
        print(f"\n  Found {count} existing products.")

    while True:
        print(f"\n{'─' * 66}")
        print("  MENU")
        print(f"{'─' * 66}")
        print("  1.  Catalog overview")
        print("  2.  Category performance analytics")
        print("  3.  Brand market analysis")
        print("  4.  Price distribution ($bucket)")
        print("  5.  Rating analysis ($facet)")
        print("  6.  Tag cloud ($unwind)")
        print("  7.  Inventory health")
        print("  8.  Top rated products")
        print("  9.  Text search demo")
        print("  10. Full analytics report")
        print("  11. Save report to JSON")
        print("  12. Re-seed catalog")
        print("  13. MongoDB query playground")
        print("  14. Exit")
        print(f"{'─' * 66}")

        choice = input("  Choose (1-14): ").strip()

        if choice == "1":
            header("CATALOG OVERVIEW")
            display_overview(repo)

        elif choice == "2":
            header("CATEGORY PERFORMANCE")
            data = analytics.category_performance()
            display_category_performance(data)

        elif choice == "3":
            header("BRAND ANALYSIS")
            data = analytics.brand_analysis()
            display_brand_analysis(data)

        elif choice == "4":
            header("PRICE DISTRIBUTION")
            data = analytics.price_distribution()
            display_price_distribution(data)

        elif choice == "5":
            header("RATING ANALYSIS")
            data = analytics.rating_analysis()
            display_rating_analysis(data)

        elif choice == "6":
            header("TAG CLOUD")
            data = analytics.tag_cloud(top_n=15)
            display_tag_cloud(data)

        elif choice == "7":
            header("INVENTORY HEALTH")
            data = analytics.inventory_health()
            display_inventory_health(data)

        elif choice == "8":
            header("TOP RATED PRODUCTS")
            products = repo.get_top_rated(limit=10)
            display_top_products(products)

        elif choice == "9":
            query = input("\n  Enter search term (e.g. 'laptop', 'python', 'samsung'): ").strip()
            if query:
                header(f"SEARCH: '{query}'")
                results = analytics.search_analytics(query)
                display_search_results(results, query)

        elif choice == "10":
            header("FULL ANALYTICS REPORT")
            display_overview(repo)
            display_category_performance(analytics.category_performance())
            display_brand_analysis(analytics.brand_analysis())
            display_price_distribution(analytics.price_distribution())
            display_tag_cloud(analytics.tag_cloud())
            display_inventory_health(analytics.inventory_health())

        elif choice == "11":
            data = {
                "overview": {
                    "products": repo.count(),
                    "reviews": repo.count_reviews(),
                    "categories": repo.get_categories()
                },
                "category_performance": analytics.category_performance(),
                "brand_analysis": analytics.brand_analysis(),
                "price_distribution": analytics.price_distribution(),
                "rating_analysis": analytics.rating_analysis(),
                "tag_cloud": analytics.tag_cloud(),
                "inventory_health": analytics.inventory_health()
            }
            saved = save_report(data)
            print(f"\n  {Fore.GREEN}✅ Report saved: {saved.name}{Style.RESET_ALL}")

        elif choice == "12":
            confirm = input("\n  Drop all products and re-seed? (yes/no): ")
            if confirm.lower() == "yes":
                db["products"].drop()
                db["reviews"].drop()
                setup_indexes(db)
                counts = seed_catalog(db)
                print(f"  {Fore.GREEN}✅ Re-seeded with {counts['products']} products{Style.RESET_ALL}")

        elif choice == "13":
            section("MONGODB QUERY PLAYGROUND")
            print("  Examples:")
            print("    db.products.find({ 'category': 'Laptops' })")
            print("    db.products.find({ 'price': { '$lt': 5000 } })")
            print("    db.products.countDocuments({ 'is_active': True })")
            print("  Type 'exit' to return\n")

            # Simple Python expression evaluator for MongoDB queries
            while True:
                cmd = input("  >>> ").strip()
                if cmd.lower() == "exit":
                    break
                if not cmd:
                    continue

                try:
                    # Replace common MongoDB shell syntax with Python
                    cmd_py = (
                        cmd
                        .replace("db.products.", "repo.products.")
                        .replace("db.reviews.", "repo.reviews.")
                        .replace("true", "True")
                        .replace("false", "False")
                        .replace("null", "None")
                    )
                    result = eval(cmd_py)
                    if hasattr(result, '__iter__') and not isinstance(result, dict):
                        results = list(result)
                        print(f"  {len(results)} result(s):")
                        for r in results[:5]:
                            print(f"  {r}")
                        if len(results) > 5:
                            print(f"  ... and {len(results) - 5} more")
                    else:
                        print(f"  Result: {result}")
                except Exception as e:
                    print(f"  {Fore.RED}Error: {e}{Style.RESET_ALL}")

        elif choice == "14":
            close_connection()
            print(f"\n  See you on Day 19! 💪\n")
            break

        else:
            print(f"  {Fore.RED}❌ Invalid option.{Style.RESET_ALL}")


if __name__ == "__main__":
    main()