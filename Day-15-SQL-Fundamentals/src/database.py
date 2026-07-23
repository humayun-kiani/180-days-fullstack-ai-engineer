# ============================================================
# src/database.py
# Database setup and connection management
# ============================================================

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "students.db"


def get_connection():
    """
    Get a database connection with row factory set.

    Returns:
        sqlite3.Connection: Database connection.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row       # access columns by name
    conn.execute("PRAGMA foreign_keys = ON")   # enforce foreign keys
    conn.execute("PRAGMA journal_mode = WAL")  # better concurrent access
    return conn


def create_schema(conn):
    """
    Create all database tables and indexes.

    Args:
        conn: SQLite connection.
    """
    conn.executescript("""
        -- ─── DEPARTMENTS ───────────────────────────────────────────
        CREATE TABLE IF NOT EXISTS departments (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT NOT NULL UNIQUE,
            head_name   TEXT,
            building    TEXT,
            created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        -- ─── STUDENTS ────────────────────────────────────────────────
        CREATE TABLE IF NOT EXISTS students (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id      TEXT NOT NULL UNIQUE,    -- e.g. CS-2021-001
            first_name      TEXT NOT NULL,
            last_name       TEXT NOT NULL,
            email           TEXT NOT NULL UNIQUE,
            city            TEXT NOT NULL DEFAULT 'Rawalpindi',
            department_id   INTEGER NOT NULL,
            enrollment_year INTEGER NOT NULL,
            gpa             REAL DEFAULT 0.0,
            is_active       INTEGER DEFAULT 1,      -- 1=active, 0=inactive
            created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (department_id) REFERENCES departments(id)
                ON DELETE RESTRICT
        );

        -- ─── COURSES ─────────────────────────────────────────────────
        CREATE TABLE IF NOT EXISTS courses (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            course_code     TEXT NOT NULL UNIQUE,   -- e.g. CS101
            name            TEXT NOT NULL,
            credits         INTEGER NOT NULL DEFAULT 3 CHECK (credits BETWEEN 1 AND 6),
            department_id   INTEGER,
            semester        TEXT NOT NULL,          -- Spring, Fall, Summer
            year            INTEGER NOT NULL,
            max_students    INTEGER DEFAULT 50,

            FOREIGN KEY (department_id) REFERENCES departments(id)
        );

        -- ─── ENROLLMENTS ─────────────────────────────────────────────
        CREATE TABLE IF NOT EXISTS enrollments (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id      INTEGER NOT NULL,
            course_id       INTEGER NOT NULL,
            grade           REAL,                   -- 0.0 to 4.0 GPA scale
            grade_letter    TEXT,                   -- A, B, C, D, F
            marks           INTEGER,                -- raw marks out of 100
            status          TEXT DEFAULT 'enrolled', -- enrolled/completed/dropped
            enrolled_at     DATETIME DEFAULT CURRENT_TIMESTAMP,
            completed_at    DATETIME,

            FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
            FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE RESTRICT,
            UNIQUE (student_id, course_id)          -- can't enroll twice
        );

        -- ─── ATTENDANCE ──────────────────────────────────────────────
        CREATE TABLE IF NOT EXISTS attendance (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id      INTEGER NOT NULL,
            course_id       INTEGER NOT NULL,
            total_classes   INTEGER NOT NULL DEFAULT 40,
            attended        INTEGER NOT NULL DEFAULT 0,
            recorded_at     DATETIME DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (student_id) REFERENCES students(id),
            FOREIGN KEY (course_id) REFERENCES courses(id),
            UNIQUE (student_id, course_id)
        );

        -- ─── INDEXES ─────────────────────────────────────────────────
        -- These speed up frequent queries

        CREATE INDEX IF NOT EXISTS idx_students_dept
            ON students(department_id);

        CREATE INDEX IF NOT EXISTS idx_students_year
            ON students(enrollment_year);

        CREATE INDEX IF NOT EXISTS idx_students_gpa
            ON students(gpa);

        CREATE INDEX IF NOT EXISTS idx_enrollments_student
            ON enrollments(student_id);

        CREATE INDEX IF NOT EXISTS idx_enrollments_course
            ON enrollments(course_id);

        CREATE INDEX IF NOT EXISTS idx_enrollments_grade
            ON enrollments(grade);

        CREATE INDEX IF NOT EXISTS idx_courses_dept
            ON courses(department_id);
    """)
    conn.commit()
    print("  ✅ Database schema created with indexes.")