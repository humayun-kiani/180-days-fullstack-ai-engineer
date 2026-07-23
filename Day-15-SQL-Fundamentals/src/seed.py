# ============================================================
# src/seed.py
# Seed the database with realistic fake data
# ============================================================

import random
from datetime import datetime, timedelta
from faker import Faker

fake = Faker()
random.seed(42)   # reproducible results


# Sample data
DEPARTMENTS = [
    ("Computer Science", "Dr. Khalid Ahmed", "Block A"),
    ("Electrical Engineering", "Dr. Fatima Shah", "Block B"),
    ("Business Administration", "Prof. Omar Malik", "Block C"),
    ("Mathematics", "Dr. Sara Ali", "Block D"),
    ("Physics", "Dr. Ahmed Khan", "Block E"),
]

COURSES_BY_DEPT = {
    "Computer Science": [
        ("CS101", "Introduction to Programming", 3),
        ("CS201", "Data Structures", 3),
        ("CS301", "Database Systems", 3),
        ("CS401", "Artificial Intelligence", 4),
        ("CS501", "Machine Learning", 4),
        ("CS601", "Web Development", 3),
        ("CS701", "Software Engineering", 3),
    ],
    "Electrical Engineering": [
        ("EE101", "Circuit Analysis", 3),
        ("EE201", "Digital Electronics", 3),
        ("EE301", "Signals and Systems", 4),
        ("EE401", "Microcontrollers", 3),
    ],
    "Business Administration": [
        ("BA101", "Principles of Management", 3),
        ("BA201", "Financial Accounting", 3),
        ("BA301", "Marketing Management", 3),
        ("BA401", "Business Analytics", 3),
    ],
    "Mathematics": [
        ("MATH101", "Calculus I", 4),
        ("MATH201", "Linear Algebra", 3),
        ("MATH301", "Statistics", 3),
        ("MATH401", "Discrete Mathematics", 3),
    ],
    "Physics": [
        ("PHY101", "Mechanics", 3),
        ("PHY201", "Thermodynamics", 3),
        ("PHY301", "Quantum Physics", 4),
    ],
}

CITIES = [
    "Rawalpindi", "Lahore", "Karachi", "Islamabad",
    "Faisalabad", "Multan", "Peshawar", "Quetta"
]

SEMESTERS = ["Fall", "Spring", "Summer"]


def gpa_to_letter(gpa):
    """Convert GPA to letter grade."""
    if gpa >= 3.7:
        return "A"
    elif gpa >= 3.3:
        return "A-"
    elif gpa >= 3.0:
        return "B+"
    elif gpa >= 2.7:
        return "B"
    elif gpa >= 2.3:
        return "B-"
    elif gpa >= 2.0:
        return "C+"
    elif gpa >= 1.7:
        return "C"
    elif gpa >= 1.0:
        return "D"
    else:
        return "F"


def marks_to_gpa(marks):
    """Convert marks (0-100) to GPA (0-4.0)."""
    if marks >= 90:
        return round(random.uniform(3.7, 4.0), 2)
    elif marks >= 80:
        return round(random.uniform(3.0, 3.69), 2)
    elif marks >= 70:
        return round(random.uniform(2.0, 2.99), 2)
    elif marks >= 60:
        return round(random.uniform(1.0, 1.99), 2)
    else:
        return round(random.uniform(0.0, 0.99), 2)


def seed_database(conn):
    """
    Populate the database with realistic fake data.

    Args:
        conn: SQLite connection.
    """
    cursor = conn.cursor()

    print("\n  Seeding database...")

    # ── 1. Insert Departments ──
    dept_ids = {}
    for name, head, building in DEPARTMENTS:
        cursor.execute(
            "INSERT INTO departments (name, head_name, building) VALUES (?, ?, ?)",
            (name, head, building)
        )
        dept_ids[name] = cursor.lastrowid
    print(f"  ✅ Inserted {len(DEPARTMENTS)} departments.")

    # ── 2. Insert Courses ──
    course_ids = {}
    for dept_name, courses in COURSES_BY_DEPT.items():
        dept_id = dept_ids[dept_name]
        for code, name, credits in courses:
            year = random.choice([2023, 2024, 2025])
            semester = random.choice(SEMESTERS)
            cursor.execute("""
                INSERT INTO courses (course_code, name, credits, department_id, semester, year)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (code, name, credits, dept_id, semester, year))
            course_ids[code] = cursor.lastrowid
    total_courses = sum(len(c) for c in COURSES_BY_DEPT.values())
    print(f"  ✅ Inserted {total_courses} courses.")

    # ── 3. Insert Students ──
    student_ids = []
    dept_names = list(dept_ids.keys())

    for i in range(1, 51):    # 50 students
        dept_name = random.choice(dept_names)
        dept_id = dept_ids[dept_name]
        year = random.choice([2020, 2021, 2022, 2023, 2024])

        # Generate student ID: CS-2021-001
        dept_code = dept_name.split()[0][:2].upper()
        student_code = f"{dept_code}-{year}-{i:03d}"

        first_name = fake.first_name()
        last_name = fake.last_name()
        email = f"{first_name.lower()}.{last_name.lower()}{i}@university.edu.pk"
        city = random.choice(CITIES)
        is_active = 1 if random.random() > 0.1 else 0   # 90% active

        cursor.execute("""
            INSERT INTO students
            (student_id, first_name, last_name, email, city, department_id, enrollment_year, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (student_code, first_name, last_name, email, city, dept_id, year, is_active))

        student_ids.append({
            "db_id": cursor.lastrowid,
            "dept": dept_name
        })

    print(f"  ✅ Inserted 50 students.")

    # ── 4. Insert Enrollments ──
    enrollment_count = 0
    attendance_count = 0

    dept_courses = {}
    for dept_name, courses in COURSES_BY_DEPT.items():
        dept_courses[dept_name] = [c[0] for c in courses]

    for student in student_ids:
        # Each student enrolled in 3-6 courses from their department
        dept_course_codes = dept_courses.get(student["dept"], [])
        if not dept_course_codes:
            continue

        num_courses = min(random.randint(3, 6), len(dept_course_codes))
        selected_courses = random.sample(dept_course_codes, num_courses)

        student_gpas = []

        for code in selected_courses:
            course_id = course_ids[code]
            marks = random.randint(45, 100)

            # Bias some students to be high performers
            if random.random() < 0.2:    # 20% chance of very high marks
                marks = random.randint(85, 100)
            elif random.random() < 0.1:  # 10% chance of failing
                marks = random.randint(30, 54)

            gpa = marks_to_gpa(marks)
            letter = gpa_to_letter(gpa)
            student_gpas.append(gpa)

            # Determine status
            if marks < 50:
                status = "completed"
            else:
                status = random.choice(["completed", "completed", "enrolled"])

            completed_at = None
            if status == "completed":
                completed_at = datetime.now().strftime("%Y-%m-%d")

            cursor.execute("""
                INSERT INTO enrollments
                (student_id, course_id, grade, grade_letter, marks, status, completed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (student["db_id"], course_id, gpa, letter, marks, status, completed_at))
            enrollment_count += 1

            # Attendance record
            total_classes = 40
            if marks >= 70:
                attended = random.randint(32, 40)  # good attendees
            else:
                attended = random.randint(20, 35)  # poor attendees

            cursor.execute("""
                INSERT OR IGNORE INTO attendance
                (student_id, course_id, total_classes, attended)
                VALUES (?, ?, ?, ?)
            """, (student["db_id"], course_id, total_classes, attended))
            attendance_count += 1

        # Calculate and update overall GPA
        if student_gpas:
            overall_gpa = round(sum(student_gpas) / len(student_gpas), 2)
            cursor.execute(
                "UPDATE students SET gpa = ? WHERE id = ?",
                (overall_gpa, student["db_id"])
            )

    conn.commit()
    print(f"  ✅ Inserted {enrollment_count} enrollment records.")
    print(f"  ✅ Inserted {attendance_count} attendance records.")
    print(f"\n  🎉 Database seeded successfully!")