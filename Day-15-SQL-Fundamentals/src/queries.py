# ============================================================
# src/queries.py
# All SQL analytical queries with explanations
# ============================================================


def run_all_queries(conn):
    """
    Run all analytical queries and return results.

    Args:
        conn: SQLite database connection.

    Returns:
        dict: All query results organized by category.
    """
    cursor = conn.cursor()
    results = {}

    # ─────────────────────────────────────────
    # QUERY 1: Overview Statistics
    # ─────────────────────────────────────────
    cursor.execute("""
        SELECT
            (SELECT COUNT(*) FROM students) AS total_students,
            (SELECT COUNT(*) FROM students WHERE is_active = 1) AS active_students,
            (SELECT COUNT(*) FROM courses) AS total_courses,
            (SELECT COUNT(*) FROM enrollments) AS total_enrollments,
            (SELECT ROUND(AVG(gpa), 2) FROM students WHERE gpa > 0) AS avg_gpa,
            (SELECT COUNT(DISTINCT department_id) FROM students) AS departments
    """)
    results["overview"] = dict(cursor.fetchone())

    # ─────────────────────────────────────────
    # QUERY 2: Department Statistics (JOIN + GROUP BY)
    # ─────────────────────────────────────────
    cursor.execute("""
        SELECT
            d.name AS department,
            COUNT(s.id) AS student_count,
            ROUND(AVG(s.gpa), 2) AS avg_gpa,
            MAX(s.gpa) AS highest_gpa,
            MIN(s.gpa) AS lowest_gpa,
            SUM(CASE WHEN s.is_active = 1 THEN 1 ELSE 0 END) AS active_count
        FROM departments d
        LEFT JOIN students s ON d.id = s.department_id
        GROUP BY d.id, d.name
        ORDER BY avg_gpa DESC
    """)
    results["department_stats"] = [dict(row) for row in cursor.fetchall()]

    # ─────────────────────────────────────────
    # QUERY 3: Top 10 Students (with department name via JOIN)
    # ─────────────────────────────────────────
    cursor.execute("""
        SELECT
            s.student_id,
            s.first_name || ' ' || s.last_name AS full_name,
            d.name AS department,
            s.gpa,
            s.enrollment_year,
            s.city,
            COUNT(e.id) AS courses_taken
        FROM students s
        JOIN departments d ON s.department_id = d.id
        LEFT JOIN enrollments e ON s.id = e.student_id
        WHERE s.is_active = 1
        GROUP BY s.id
        ORDER BY s.gpa DESC
        LIMIT 10
    """)
    results["top_students"] = [dict(row) for row in cursor.fetchall()]

    # ─────────────────────────────────────────
    # QUERY 4: GPA Distribution (CASE WHEN for bucketing)
    # ─────────────────────────────────────────
    cursor.execute("""
        SELECT
            CASE
                WHEN gpa >= 3.7 THEN 'A  (3.7 - 4.0) — Distinction'
                WHEN gpa >= 3.0 THEN 'B  (3.0 - 3.69) — Merit'
                WHEN gpa >= 2.0 THEN 'C  (2.0 - 2.99) — Pass'
                WHEN gpa >= 1.0 THEN 'D  (1.0 - 1.99) — Marginal'
                ELSE             'F  (0.0 - 0.99) — Fail'
            END AS gpa_band,
            COUNT(*) AS student_count,
            ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM students WHERE gpa > 0), 1) AS percentage
        FROM students
        WHERE gpa > 0
        GROUP BY gpa_band
        ORDER BY gpa DESC
    """)
    results["gpa_distribution"] = [dict(row) for row in cursor.fetchall()]

    # ─────────────────────────────────────────
    # QUERY 5: Course Enrollment Stats (with difficulty ranking)
    # ─────────────────────────────────────────
    cursor.execute("""
        SELECT
            c.course_code,
            c.name AS course_name,
            c.credits,
            d.name AS department,
            COUNT(e.id) AS enrolled_count,
            ROUND(AVG(e.marks), 1) AS avg_marks,
            ROUND(AVG(e.grade), 2) AS avg_gpa,
            MIN(e.marks) AS lowest_marks,
            MAX(e.marks) AS highest_marks,
            SUM(CASE WHEN e.marks < 50 THEN 1 ELSE 0 END) AS failed_count
        FROM courses c
        JOIN departments d ON c.department_id = d.id
        LEFT JOIN enrollments e ON c.id = e.course_id
        GROUP BY c.id
        ORDER BY avg_marks ASC
        LIMIT 10
    """)
    results["hardest_courses"] = [dict(row) for row in cursor.fetchall()]

    # ─────────────────────────────────────────
    # QUERY 6: City-wise Student Distribution
    # ─────────────────────────────────────────
    cursor.execute("""
        SELECT
            city,
            COUNT(*) AS student_count,
            ROUND(AVG(gpa), 2) AS avg_gpa,
            ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM students), 1) AS percentage
        FROM students
        GROUP BY city
        ORDER BY student_count DESC
    """)
    results["city_distribution"] = [dict(row) for row in cursor.fetchall()]

    # ─────────────────────────────────────────
    # QUERY 7: Enrollment Year Analysis
    # ─────────────────────────────────────────
    cursor.execute("""
        SELECT
            enrollment_year,
            COUNT(*) AS total_students,
            ROUND(AVG(gpa), 2) AS avg_gpa,
            SUM(CASE WHEN is_active = 1 THEN 1 ELSE 0 END) AS still_active
        FROM students
        GROUP BY enrollment_year
        ORDER BY enrollment_year DESC
    """)
    results["year_analysis"] = [dict(row) for row in cursor.fetchall()]

    # ─────────────────────────────────────────
    # QUERY 8: Students Above Average GPA (Subquery)
    # ─────────────────────────────────────────
    cursor.execute("""
        SELECT
            s.first_name || ' ' || s.last_name AS full_name,
            s.gpa,
            d.name AS department,
            ROUND(s.gpa - (SELECT AVG(gpa) FROM students WHERE gpa > 0), 2) AS above_avg_by
        FROM students s
        JOIN departments d ON s.department_id = d.id
        WHERE s.gpa > (SELECT AVG(gpa) FROM students WHERE gpa > 0)
        ORDER BY s.gpa DESC
        LIMIT 15
    """)
    results["above_average"] = [dict(row) for row in cursor.fetchall()]

    # ─────────────────────────────────────────
    # QUERY 9: Attendance Analysis
    # ─────────────────────────────────────────
    cursor.execute("""
        SELECT
            s.first_name || ' ' || s.last_name AS student_name,
            c.name AS course_name,
            a.total_classes,
            a.attended,
            ROUND(a.attended * 100.0 / a.total_classes, 1) AS attendance_pct,
            ROUND(AVG(e.marks), 1) AS marks_obtained,
            CASE
                WHEN a.attended * 100.0 / a.total_classes < 75 THEN 'AT RISK'
                WHEN a.attended * 100.0 / a.total_classes < 85 THEN 'Warning'
                ELSE 'Good'
            END AS attendance_status
        FROM attendance a
        JOIN students s ON a.student_id = s.id
        JOIN courses c ON a.course_id = c.id
        LEFT JOIN enrollments e ON e.student_id = s.id AND e.course_id = c.id
        GROUP BY a.id
        ORDER BY attendance_pct ASC
        LIMIT 12
    """)
    results["attendance_risk"] = [dict(row) for row in cursor.fetchall()]

    # ─────────────────────────────────────────
    # QUERY 10: Grade Distribution per Course
    # ─────────────────────────────────────────
    cursor.execute("""
        SELECT
            c.course_code,
            c.name AS course_name,
            SUM(CASE WHEN e.grade_letter LIKE 'A%' THEN 1 ELSE 0 END) AS A_grades,
            SUM(CASE WHEN e.grade_letter LIKE 'B%' THEN 1 ELSE 0 END) AS B_grades,
            SUM(CASE WHEN e.grade_letter LIKE 'C%' THEN 1 ELSE 0 END) AS C_grades,
            SUM(CASE WHEN e.grade_letter = 'D' THEN 1 ELSE 0 END) AS D_grades,
            SUM(CASE WHEN e.grade_letter = 'F' THEN 1 ELSE 0 END) AS F_grades,
            COUNT(e.id) AS total_enrolled
        FROM courses c
        JOIN enrollments e ON c.id = e.course_id
        GROUP BY c.id
        HAVING total_enrolled >= 5
        ORDER BY A_grades DESC
        LIMIT 8
    """)
    results["grade_distribution"] = [dict(row) for row in cursor.fetchall()]

    # ─────────────────────────────────────────
    # QUERY 11: Students with Perfect Attendance
    # ─────────────────────────────────────────
    cursor.execute("""
        SELECT
            s.first_name || ' ' || s.last_name AS student_name,
            s.gpa,
            COUNT(a.id) AS courses_with_perfect,
            d.name AS department
        FROM students s
        JOIN attendance a ON s.id = a.student_id
        JOIN departments d ON s.department_id = d.id
        WHERE a.attended = a.total_classes
        GROUP BY s.id
        HAVING courses_with_perfect >= 2
        ORDER BY s.gpa DESC
    """)
    results["perfect_attendance"] = [dict(row) for row in cursor.fetchall()]

    # ─────────────────────────────────────────
    # QUERY 12: Department GPA Ranking (Window-style using subquery)
    # ─────────────────────────────────────────
    cursor.execute("""
        SELECT
            d.name AS department,
            ROUND(AVG(s.gpa), 2) AS dept_avg_gpa,
            COUNT(s.id) AS students,
            (
                SELECT COUNT(DISTINCT d2.id)
                FROM departments d2
                JOIN students s2 ON d2.id = s2.department_id
                GROUP BY d2.id
                HAVING AVG(s2.gpa) > AVG(s.gpa)
            ) + 1 AS gpa_rank
        FROM departments d
        JOIN students s ON d.id = s.department_id
        WHERE s.gpa > 0
        GROUP BY d.id, d.name
        ORDER BY dept_avg_gpa DESC
    """)
    results["dept_ranking"] = [dict(row) for row in cursor.fetchall()]

    # ─────────────────────────────────────────
    # QUERY 13: Students Failing Multiple Courses
    # ─────────────────────────────────────────
    cursor.execute("""
        SELECT
            s.student_id,
            s.first_name || ' ' || s.last_name AS student_name,
            s.gpa,
            d.name AS department,
            COUNT(e.id) AS failed_courses,
            GROUP_CONCAT(c.course_code, ', ') AS failed_course_codes
        FROM students s
        JOIN departments d ON s.department_id = d.id
        JOIN enrollments e ON s.id = e.student_id
        JOIN courses c ON e.course_id = c.id
        WHERE e.marks < 50
        GROUP BY s.id
        HAVING failed_courses >= 2
        ORDER BY failed_courses DESC, s.gpa ASC
    """)
    results["at_risk_students"] = [dict(row) for row in cursor.fetchall()]

    # ─────────────────────────────────────────
    # QUERY 14: Credit Hours Summary per Student
    # ─────────────────────────────────────────
    cursor.execute("""
        SELECT
            s.first_name || ' ' || s.last_name AS student_name,
            s.gpa,
            COUNT(e.id) AS courses_enrolled,
            SUM(c.credits) AS total_credits,
            SUM(CASE WHEN e.status = 'completed' THEN c.credits ELSE 0 END) AS credits_completed
        FROM students s
        JOIN enrollments e ON s.id = e.student_id
        JOIN courses c ON e.course_id = c.id
        GROUP BY s.id
        ORDER BY total_credits DESC
        LIMIT 10
    """)
    results["credit_summary"] = [dict(row) for row in cursor.fetchall()]

    # ─────────────────────────────────────────
    # QUERY 15: Correlation — Attendance vs Performance
    # ─────────────────────────────────────────
    cursor.execute("""
        SELECT
            CASE
                WHEN a.attended * 100.0 / a.total_classes >= 90 THEN '90-100% (Excellent)'
                WHEN a.attended * 100.0 / a.total_classes >= 75 THEN '75-89%  (Good)'
                WHEN a.attended * 100.0 / a.total_classes >= 60 THEN '60-74%  (Average)'
                ELSE '< 60%   (Poor)'
            END AS attendance_range,
            COUNT(*) AS student_course_count,
            ROUND(AVG(e.marks), 1) AS avg_marks,
            ROUND(AVG(e.grade), 2) AS avg_gpa
        FROM attendance a
        JOIN enrollments e ON a.student_id = e.student_id
            AND a.course_id = e.course_id
        GROUP BY attendance_range
        ORDER BY avg_marks DESC
    """)
    results["attendance_correlation"] = [dict(row) for row in cursor.fetchall()]

    return results