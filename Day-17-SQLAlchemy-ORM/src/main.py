# ============================================================
# src/main.py
# Blog ORM — Main Entry Point
# Day 17 — SQLAlchemy ORM
# ============================================================

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database import (
    get_session, test_connection,
    create_all_tables, drop_all_tables
)
from src.seed import seed_all
from src.queries import run_demo_queries
from src.reporter import (
    header, section,
    display_all, save_report,
    display_top_authors, display_popular_posts,
    display_category_stats, display_post_stats,
    display_tag_stats, display_eager_loading_demo,
    Fore, Style
)
from src.models import User, Post, Comment


def check_needs_seeding(session) -> bool:
    return session.query(User).count() == 0


def main():
    header(
        "BLOG ORM — SQLAlchemy",
        "Day 17 — Models, Relationships, Sessions, Repository Pattern"
    )

    # Test connection
    print("\n  Testing database connection...")
    if not test_connection():
        print("\n  Make sure PostgreSQL is running and .env is configured.")
        sys.exit(1)

    session = get_session()

    # Create schema
    print("\n  Creating tables from ORM models...")
    create_all_tables()

    # Seed if empty
    if check_needs_seeding(session):
        print("\n  No data found. Seeding...")
        seed_all(session)
        session.commit()
    else:
        count = session.query(User).count()
        print(f"\n  Found existing data ({count} users).")

    while True:
        print(f"\n{'─' * 65}")
        print("  MENU")
        print(f"{'─' * 65}")
        print("  1.  Full report (all queries)")
        print("  2.  Top authors")
        print("  3.  Popular posts")
        print("  4.  Category statistics")
        print("  5.  Post statistics")
        print("  6.  Tag statistics")
        print("  7.  Eager loading demo")
        print("  8.  Create a post (ORM write demo)")
        print("  9.  Search posts")
        print("  10. Save report to JSON")
        print("  11. Re-seed database")
        print("  12. Exit")
        print(f"{'─' * 65}")

        choice = input("  Choose (1-12): ").strip()

        if choice == "1":
            results = run_demo_queries(session)
            header("FULL ORM REPORT")
            display_all(results)

        elif choice == "2":
            results = run_demo_queries(session)
            display_top_authors(results)

        elif choice == "3":
            results = run_demo_queries(session)
            display_popular_posts(results)

        elif choice == "4":
            results = run_demo_queries(session)
            display_category_stats(results)

        elif choice == "5":
            results = run_demo_queries(session)
            display_post_stats(results)

        elif choice == "6":
            results = run_demo_queries(session)
            display_tag_stats(results)

        elif choice == "7":
            results = run_demo_queries(session)
            display_eager_loading_demo(results)

        elif choice == "8":
            section("CREATE POST (ORM Write Demo)")
            from src.repositories.post_repo import PostRepository
            from src.repositories.user_repo import UserRepository

            user_repo = UserRepository(session)
            post_repo = PostRepository(session)

            authors = user_repo.get_all_active(limit=5)
            if not authors:
                print("  No authors found.")
            else:
                print("  Available authors:")
                for i, u in enumerate(authors[:5], 1):
                    print(f"    {i}. {u.username} ({u.role})")

                title = input("  Post title: ").strip()
                content = input("  Content (brief): ").strip()

                if title and content:
                    post = post_repo.create(
                        author_id=authors[0].id,
                        title=title,
                        content=content,
                        status="published",
                        tag_names=["tutorial", "python"]
                    )
                    session.commit()
                    print(f"\n  ✅ Created: '{post.title}'")
                    print(f"     Slug: {post.slug}")
                    print(f"     Reading time: {post.reading_time} min")

        elif choice == "9":
            keyword = input("  Search keyword: ").strip()
            if keyword:
                from src.repositories.post_repo import PostRepository
                post_repo = PostRepository(session)
                results = post_repo.search(keyword)
                section(f"SEARCH RESULTS for '{keyword}'")
                if results:
                    for p in results:
                        print(f"  • {p.title} — {p.views} views")
                else:
                    print(f"  No posts found matching '{keyword}'.")

        elif choice == "10":
            results = run_demo_queries(session)
            saved = save_report(results)
            print(f"\n  {Fore.GREEN}✅ Saved to: {saved.name}{Style.RESET_ALL}")

        elif choice == "11":
            confirm = input("\n  Drop all tables and re-seed? (yes/no): ")
            if confirm.lower() == "yes":
                session.close()
                drop_all_tables()
                create_all_tables()
                session = get_session()
                seed_all(session)
                session.commit()

        elif choice == "12":
            session.close()
            print(f"\n  See you on Day 18! 💪\n")
            break
        else:
            print(f"  {Fore.RED}❌ Invalid option.{Style.RESET_ALL}")


if __name__ == "__main__":
    main()