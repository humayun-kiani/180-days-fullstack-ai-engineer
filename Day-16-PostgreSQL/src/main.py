# ============================================================
# src/main.py
# Blog Platform Database — Main Entry Point
# Day 16 — PostgreSQL
# ============================================================

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database import get_connection, run_migrations, test_connection
from src.seed import seed_database
from src.queries import run_all_queries
from src.reporter import (
    header, section,
    display_all, save_report,
    Fore, Style
)


def check_connection():
    """Test and display connection info."""
    info = test_connection()
    if not info["success"]:
        print(f"\n  {Fore.RED}❌ Cannot connect to PostgreSQL!{Style.RESET_ALL}")
        print(f"\n  Error: {info.get('error', 'Unknown error')}")
        print(f"\n  Please ensure:")
        print(f"  1. PostgreSQL is running")
        print(f"  2. Database 'blog_platform' exists")
        print(f"  3. User 'blog_user' has access")
        print(f"  4. .env file has correct credentials")
        print(f"\n  Run this in psql as postgres user:")
        print(f"  {Fore.CYAN}CREATE DATABASE blog_platform;{Style.RESET_ALL}")
        print(f"  {Fore.CYAN}CREATE USER blog_user WITH PASSWORD 'secure_password_here';{Style.RESET_ALL}")
        print(f"  {Fore.CYAN}GRANT ALL PRIVILEGES ON DATABASE blog_platform TO blog_user;{Style.RESET_ALL}")
        return None

    print(f"\n  {Fore.GREEN}✅ Connected to PostgreSQL{Style.RESET_ALL}")
    print(f"  Server:   {info['version']}")
    print(f"  Database: {info['database']}")
    print(f"  User:     {info['user']}")
    return True


def check_needs_seeding(conn):
    """Check if database needs seeding."""
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT COUNT(*) AS count FROM users")
        count = cursor.fetchone()["count"]
        return count == 0
    except Exception:
        return True


def main():
    """Main entry point."""
    header(
        "BLOG PLATFORM DATABASE",
        "Day 16 — PostgreSQL: Advanced Features, Views, Triggers, Full-Text Search"
    )

    # Check connection
    if not check_connection():
        sys.exit(1)

    conn = get_connection()

    # Run migrations
    print("\n  Running migrations...")
    run_migrations(conn)

    # Seed if empty
    if check_needs_seeding(conn):
        print("\n  No data found. Seeding database...")
        seed_database(conn)

    while True:
        print(f"\n{'─' * 66}")
        print("  MENU")
        print(f"{'─' * 66}")
        print("  1.  Full analytics report")
        print("  2.  Top posts by views")
        print("  3.  Full-text search demo")
        print("  4.  Tag analytics (ARRAY unnest)")
        print("  5.  Author leaderboard")
        print("  6.  Window functions demo")
        print("  7.  Save report to JSON")
        print("  8.  Re-seed database")
        print("  9.  Interactive psql query")
        print("  10. Exit")
        print(f"{'─' * 66}")

        choice = input("  Choose option (1-10): ").strip()

        if choice == "1":
            header("FULL ANALYTICS REPORT")
            results = run_all_queries(conn)
            display_all(results)

        elif choice == "2":
            results = run_all_queries(conn)
            from src.reporter import display_top_posts
            display_top_posts(results)

        elif choice == "3":
            results = run_all_queries(conn)
            from src.reporter import display_search_results
            display_search_results(results)

        elif choice == "4":
            results = run_all_queries(conn)
            from src.reporter import display_tag_analytics
            display_tag_analytics(results)

        elif choice == "5":
            results = run_all_queries(conn)
            from src.reporter import display_leaderboard
            display_leaderboard(results)

        elif choice == "6":
            results = run_all_queries(conn)
            from src.reporter import display_window_functions
            display_window_functions(results)

        elif choice == "7":
            results = run_all_queries(conn)
            saved = save_report(results)
            print(f"\n  {Fore.GREEN}✅ Report saved to: {saved.name}{Style.RESET_ALL}")

        elif choice == "8":
            confirm = input("\n  This will clear all data. Confirm? (yes/no): ")
            if confirm.lower() == "yes":
                cursor = conn.cursor()
                cursor.execute("""
                    TRUNCATE page_views, user_follows, post_likes,
                               comments, posts, users, categories
                    RESTART IDENTITY CASCADE
                """)
                conn.commit()
                seed_database(conn)

        elif choice == "9":
            section("INTERACTIVE QUERY")
            print("  Type SQL (multi-line OK, end with ;)")
            print("  Type 'exit' to return\n")

            query_buffer = []
            while True:
                prompt = "  SQL> " if not query_buffer else "  ...> "
                line = input(prompt).strip()

                if line.lower() == "exit":
                    query_buffer = []
                    break

                query_buffer.append(line)
                full_query = " ".join(query_buffer)

                if full_query.rstrip().endswith(";"):
                    query = full_query.rstrip(";")
                    try:
                        cursor = conn.cursor()
                        cursor.execute(query)

                        if cursor.description:
                            rows = cursor.fetchall()
                            if rows:
                                headers = [d[0] for d in cursor.description]
                                widths = [max(len(str(h)), max(len(str(r[h])) for r in rows)) for h in headers]

                                header_line = "  " + " | ".join(
                                    f"{h:<{w}}" for h, w in zip(headers, widths)
                                )
                                print(f"\n{Fore.CYAN}{header_line}{Style.RESET_ALL}")
                                print(f"  {'─' * len(header_line)}")

                                for row in rows[:25]:
                                    print("  " + " | ".join(
                                        f"{str(row[h]):<{w}}" for h, w in zip(headers, widths)
                                    ))

                                if len(rows) > 25:
                                    print(f"  ... {len(rows) - 25} more rows")
                                print(f"\n  {len(rows)} row(s) returned")
                            else:
                                print("  No results.")
                        else:
                            conn.commit()
                            print(f"  {Fore.GREEN}✅ {cursor.rowcount} row(s) affected.{Style.RESET_ALL}")
                    except Exception as e:
                        conn.rollback()
                        print(f"  {Fore.RED}❌ Error: {e}{Style.RESET_ALL}")

                    query_buffer = []

        elif choice == "10":
            conn.close()
            print(f"\n  See you on Day 17! 💪\n")
            break

        else:
            print(f"  {Fore.RED}❌ Invalid option.{Style.RESET_ALL}")


if __name__ == "__main__":
    main()