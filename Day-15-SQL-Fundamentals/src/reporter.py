# ============================================================
# src/reporter.py
# Display formatted query results in the terminal
# ============================================================

import json
from pathlib import Path
from datetime import datetime

try:
    from colorama import init, Fore, Style
    init(autoreset=True)
    HAS_COLOR = True
except ImportError:
    HAS_COLOR = False
    class Fore:
        CYAN = GREEN = YELLOW = RED = BLUE = MAGENTA = WHITE = ""
    class Style:
        RESET_ALL = BRIGHT = ""


DATA_DIR = Path(__file__).parent.parent / "data"


def print_header(title, subtitle=None):
    """Print a colored section header."""
    print(f"\n{Fore.CYAN}{'═' * 65}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}  {title}{Style.RESET_ALL}")
    if subtitle:
        print(f"{Fore.CYAN}  {subtitle}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'═' * 65}{Style.RESET_ALL}")


def print_section(title):
    """Print a subsection header."""
    print(f"\n{Fore.YELLOW}  ── {title} ──{Style.RESET_ALL}")


def bar_chart(value, max_value, width=25, char="█"):
    """Create a simple text bar chart."""
    if max_value == 0:
        return ""
    filled = int(value / max_value * width)
    return char * filled + "░" * (width - filled)


def display_overview(data):
    """Display database overview statistics."""
    print_section("DATABASE OVERVIEW")
    stats = data["overview"]
    print(f"\n  {'Total Students:':<30} {stats['total_students']}")
    print(f"  {'Active Students:':<30} {Fore.GREEN}{stats['active_students']}{Style.RESET_ALL}")
    print(f"  {'Total Courses:':<30} {stats['total_courses']}")
    print(f"  {'Total Enrollments:':<30} {stats['total_enrollments']}")
    print(f"  {'University Average GPA:':<30} {Fore.YELLOW}{stats['avg_gpa']:.2f} / 4.00{Style.RESET_ALL}")
    print(f"  {'Departments:':<30} {stats['departments']}")


def display_department_stats(data):
    """Display department comparison table."""
    print_section("DEPARTMENT STATISTICS")
    rows = data["department_stats"]

    print(f"\n  {'Department':<28} {'Students':>8} {'Avg GPA':>8} {'Max GPA':>8} {'Active':>7}")
    print(f"  {'─' * 63}")

    for row in rows:
        gpa_color = (Fore.GREEN if row["avg_gpa"] >= 3.0
                     else Fore.YELLOW if row["avg_gpa"] >= 2.5
                     else Fore.RED)
        print(
            f"  {row['department']:<28} "
            f"{row['student_count']:>8} "
            f"{gpa_color}{row['avg_gpa']:>8.2f}{Style.RESET_ALL} "
            f"{row['highest_gpa']:>8.2f} "
            f"{row['active_count']:>7}"
        )


def display_top_students(data):
    """Display top 10 students leaderboard."""
    print_section("TOP 10 STUDENTS BY GPA")
    rows = data["top_students"]

    medals = {0: "🥇", 1: "🥈", 2: "🥉"}
    print(f"\n  {'#':<4} {'Name':<22} {'GPA':>5} {'Dept':<20} {'City':<14} {'Courses'}")
    print(f"  {'─' * 70}")

    for i, row in enumerate(rows):
        medal = medals.get(i, f"  {i+1}.")
        print(
            f"  {medal:<4} "
            f"{row['full_name']:<22} "
            f"{Fore.GREEN}{row['gpa']:>5.2f}{Style.RESET_ALL} "
            f"{row['department']:<20} "
            f"{row['city']:<14} "
            f"{row['courses_taken']}"
        )


def display_gpa_distribution(data):
    """Display GPA distribution with bar chart."""
    print_section("GPA DISTRIBUTION")
    rows = data["gpa_distribution"]

    if not rows:
        return

    max_count = max(row["student_count"] for row in rows)

    print(f"\n  {'Band':<40} {'Count':>6}  {'%':>6}  Chart")
    print(f"  {'─' * 65}")

    for row in rows:
        bar = bar_chart(row["student_count"], max_count, width=20)
        band = row["gpa_band"]

        color = (Fore.GREEN if "Distinction" in band
                 else Fore.CYAN if "Merit" in band
                 else Fore.YELLOW if "Pass" in band
                 else Fore.RED)

        print(
            f"  {color}{band:<40}{Style.RESET_ALL} "
            f"{row['student_count']:>6}  "
            f"{row['percentage']:>5.1f}%  "
            f"{color}{bar}{Style.RESET_ALL}"
        )


def display_hardest_courses(data):
    """Display hardest courses by average marks."""
    print_section("HARDEST COURSES (by average marks)")
    rows = data["hardest_courses"]

    print(f"\n  {'Code':<10} {'Course Name':<28} {'Credits':>7} {'Enrolled':>8} {'Avg Marks':>10} {'Failed':>7}")
    print(f"  {'─' * 70}")

    for row in rows:
        color = Fore.RED if row["avg_marks"] < 60 else Fore.YELLOW if row["avg_marks"] < 75 else Fore.GREEN
        print(
            f"  {row['course_code']:<10} "
            f"{row['course_name']:<28} "
            f"{row['credits']:>7} "
            f"{row['enrolled_count']:>8} "
            f"{color}{row['avg_marks']:>10.1f}{Style.RESET_ALL} "
            f"{row['failed_count']:>7}"
        )


def display_attendance_correlation(data):
    """Display correlation between attendance and performance."""
    print_section("ATTENDANCE vs PERFORMANCE CORRELATION")
    rows = data["attendance_correlation"]

    print(f"\n  {'Attendance Range':<26} {'Records':>8} {'Avg Marks':>10} {'Avg GPA':>8}")
    print(f"  {'─' * 55}")

    for row in rows:
        pct = row["attendance_range"]
        color = (Fore.GREEN if "Excellent" in pct
                 else Fore.CYAN if "Good" in pct
                 else Fore.YELLOW if "Average" in pct
                 else Fore.RED)
        print(
            f"  {color}{pct:<26}{Style.RESET_ALL} "
            f"{row['student_course_count']:>8} "
            f"{row['avg_marks']:>10.1f} "
            f"{row['avg_gpa']:>8.2f}"
        )

    print(f"\n  {Fore.CYAN}💡 Higher attendance strongly correlates with better marks!{Style.RESET_ALL}")


def display_at_risk(data):
    """Display students at risk."""
    print_section("AT-RISK STUDENTS (failing 2+ courses)")
    rows = data["at_risk_students"]

    if not rows:
        print(f"\n  {Fore.GREEN}✅ No students failing 2 or more courses!{Style.RESET_ALL}")
        return

    print(f"\n  {'Student':<22} {'GPA':>5} {'Failed':>7} {'Courses'}")
    print(f"  {'─' * 60}")

    for row in rows:
        print(
            f"  {Fore.RED}{row['student_name']:<22}{Style.RESET_ALL} "
            f"{row['gpa']:>5.2f} "
            f"{row['failed_courses']:>7}   "
            f"{row['failed_course_codes']}"
        )


def display_city_distribution(data):
    """Display city-wise distribution."""
    print_section("CITY-WISE STUDENT DISTRIBUTION")
    rows = data["city_distribution"]

    if not rows:
        return

    max_count = max(row["student_count"] for row in rows)
    print(f"\n  {'City':<16} {'Students':>8}  {'%':>6}  {'Avg GPA':>8}  Chart")
    print(f"  {'─' * 60}")

    for row in rows:
        bar = bar_chart(row["student_count"], max_count, width=15)
        print(
            f"  {row['city']:<16} "
            f"{row['student_count']:>8}  "
            f"{row['percentage']:>5.1f}%  "
            f"{row['avg_gpa']:>8.2f}  "
            f"{Fore.BLUE}{bar}{Style.RESET_ALL}"
        )


def save_report(results):
    """Save all query results to a JSON report file."""
    DATA_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = DATA_DIR / f"student_report_{timestamp}.json"

    report = {
        "generated_at": datetime.now().isoformat(),
        "title": "Student Analytics Report",
        "day": "Day 15 — 180-Day Full Stack AI Engineer Roadmap",
        "data": results
    }

    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    return report_file


def display_all(results):
    """Display all query results."""
    display_overview(results)
    display_department_stats(results)
    display_top_students(results)
    display_gpa_distribution(results)
    display_hardest_courses(results)
    display_attendance_correlation(results)
    display_at_risk(results)
    display_city_distribution(results)