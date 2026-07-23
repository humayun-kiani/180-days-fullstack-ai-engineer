# ============================================================
# src/main.py
# Student Analytics Database — Main Entry Point
# Day 15 - 180 Days Full Stack AI Engineer Roadmap
# ============================================================

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database import get_connection, create_schema
from src.seed import seed_database
from src.queries import run_all_queries
from src.reporter import (
    print_header, print_section,
    display_all, save_report,
    Fore, Style
)


def initialize_database():
    """Set up database and seed with data if empty."""
    conn = get_connection()
    create_schema(conn)

    # Check if data already exists
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM students")
    count = cursor.fetchone()[0]

    if count == 0:
        print("  No data found. Seeding database...")
        seed_database(conn)
    else:
        print(f"  Found {count} existing students.")

    return conn


def main():
    """Main entry point."""
    print_header(
        "STUDENT ANALYTICS DATABASE",
        "Day 15 — SQL Fundamentals: Queries, JOINs, Indexes"
    )

    print(f"\n  Tech Stack: SQLite | Python sqlite3 | faker")
    print(f"  Schema: students ↔ departments ↔ courses ↔ enrollments ↔ attendance")

    # Initialize
    print("\n  Setting up database...")
    conn = initialize_database()

    while True:
        print(f"\n{'─' * 65}")
        print("  MENU")
        print(f"{'─' * 65}")
        print("  1.  View all analytics (all 15 queries)")
        print("  2.  Department statistics")
        print("  3.  Top 10 students leaderboard")
        print("  4.  GPA distribution")
        print("  5.  Hardest courses analysis")
        print("  6.  Attendance vs performance")
        print("  7.  At-risk students")
        print("  8.  City distribution")
        print("  9.  Save full report to JSON")
        print("  10. Re-seed database (fresh data)")
        print("  11. Interactive SQL query")
        print("  12. Exit")
        print(f"{'─' * 65}")

        choice = input("  Choose option (1-12): ").strip()

        if choice == "1":
            print_header("FULL ANALYTICS REPORT")
            results = run_all_queries(conn)
            display_all(results)

        elif choice == "2":
            results = run_all_queries(conn)
            from src.reporter import display_department_stats
            display_department_stats(results)

        elif choice == "3":
            results = run_all_queries(conn)
            from src.reporter import display_top_students
            display_top_students(results)

        elif choice == "4":
            results = run_all_queries(conn)
            from src.reporter import display_gpa_distribution
            display_gpa_distribution(results)

        elif choice == "5":
            results = run_all_queries(conn)
            from src.reporter import display_hardest_courses
            display_hardest_courses(results)

        elif choice == "6":
            results = run_all_queries(conn)
            from src.reporter import display_attendance_correlation
            display_attendance_correlation(results)

        elif choice == "7":
            results = run_all_queries(conn)
            from src.reporter import display_at_risk
            display_at_risk(results)

        elif choice == "8":
            results = run_all_queries(conn)
            from src.reporter import display_city_distribution
            display_city_distribution(results)

        elif choice == "9":
            results = run_all_queries(conn)
            saved = save_report(results)
            print(f"\n  {Fore.GREEN}✅ Report saved to: {saved.name}{Style.RESET_ALL}")

        elif choice == "10":
            confirm = input("\n  This will delete all existing data. Confirm? (yes/no): ")
            if confirm.lower() == "yes":
                conn.executescript("""
                    DELETE FROM attendance;
                    DELETE FROM enrollments;
                    DELETE FROM students;
                    DELETE FROM courses;
                    DELETE FROM departments;
                """)
                conn.commit()
                seed_database(conn)
                print(f"  {Fore.GREEN}✅ Database re-seeded with fresh data.{Style.RESET_ALL}")

        elif choice == "11":
            print_section("INTERACTIVE SQL QUERY")
            print("  Type your SQL query (end with semicolon ;)")
            print("  Type 'exit' to return to menu\n")

            while True:
                query = input("  SQL> ").strip()
                if query.lower() == "exit":
                    break
                if not query:
                    continue

                try:
                    cursor = conn.cursor()
                    cursor.execute(query)

                    if query.upper().startswith("SELECT"):
                        rows = cursor.fetchall()
                        if rows:
                            # Print column headers
                            headers = [d[0] for d in cursor.description]
                            print(f"\n  {' | '.join(f'{h:<15}' for h in headers)}")
                            print(f"  {'─' * (len(headers) * 16)}")
                            for row in rows[:20]:    # limit to 20 rows
                                print(f"  {' | '.join(f'{str(v):<15}' for v in row)}")
                            if len(rows) > 20:
                                print(f"  ... and {len(rows) - 20} more rows")
                            print(f"\n  {len(rows)} row(s) returned")
                        else:
                            print("  No results.")
                    else:
                        conn.commit()
                        print(f"  {Fore.GREEN}✅ Query executed. {cursor.rowcount} row(s) affected.{Style.RESET_ALL}")
                except Exception as e:
                    print(f"  {Fore.RED}❌ SQL Error: {e}{Style.RESET_ALL}")

        elif choice == "12":
            conn.close()
            print(f"\n  See you on Day 16! 💪\n")
            break

        else:
            print(f"  {Fore.RED}❌ Invalid option.{Style.RESET_ALL}")


if __name__ == "__main__":
    main()