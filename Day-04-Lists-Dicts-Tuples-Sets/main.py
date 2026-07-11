# ============================================================
# STUDENT GRADE CALCULATOR
# Day 04 - 180 Days Full Stack AI Engineer Roadmap
# ============================================================


def calculate_average(grades):
    """Calculate the average of a list of grades."""
    if not grades:
        return 0
    return sum(grades) / len(grades)


def get_letter_grade(average):
    """Return letter grade and GPA points based on average score."""
    if average >= 90:
        return "A", 4.0
    elif average >= 80:
        return "B", 3.0
    elif average >= 70:
        return "C", 2.0
    elif average >= 60:
        return "D", 1.0
    else:
        return "F", 0.0


def get_performance_comment(average):
    """Return a performance comment based on average."""
    if average >= 90:
        return "Outstanding performance!"
    elif average >= 80:
        return "Great work, keep it up!"
    elif average >= 70:
        return "Good effort, room to improve."
    elif average >= 60:
        return "Needs more dedication."
    else:
        return "Urgent: needs immediate support."


def build_student_report(student):
    """Build a complete report for one student."""
    name = student["name"]
    grades = student["grades"]
    subjects = student["subjects"]

    average = calculate_average(grades)
    letter, gpa = get_letter_grade(average)
    comment = get_performance_comment(average)
    highest = max(grades)
    lowest = min(grades)

    # Find which subject has highest and lowest grade
    # zip() pairs subjects with grades together
    subject_grade_pairs = list(zip(subjects, grades))
    best_subject = max(subject_grade_pairs, key=lambda x: x[1])
    weak_subject = min(subject_grade_pairs, key=lambda x: x[1])

    return {
        "name": name,
        "grades": grades,
        "subjects": subjects,
        "average": average,
        "letter": letter,
        "gpa": gpa,
        "comment": comment,
        "highest": highest,
        "lowest": lowest,
        "best_subject": best_subject,
        "weak_subject": weak_subject
    }


def display_student_report(report):
    """Display a formatted report for one student."""
    print(f"\n  Student: {report['name']}")
    print(f"  " + "-" * 44)

    # Subject-wise grades
    for subject, grade in zip(report["subjects"], report["grades"]):
        bar = "█" * (grade // 10)  # visual bar
        grade_letter, _ = get_letter_grade(grade)
        print(f"  {subject:<15} {grade:>3}/100  {bar:<10} {grade_letter}")

    print(f"  " + "-" * 44)
    print(f"  Average Score:  {report['average']:.2f}/100")
    print(f"  Letter Grade:   {report['letter']}")
    print(f"  GPA Points:     {report['gpa']:.1f}")
    print(f"  Highest Score:  {report['highest']} ({report['best_subject'][0]})")
    print(f"  Lowest Score:   {report['lowest']} ({report['weak_subject'][0]})")
    print(f"  Comment:        {report['comment']}")


def display_class_summary(reports):
    """Display overall class statistics."""
    all_averages = [r["average"] for r in reports]
    all_names = [r["name"] for r in reports]
    all_grades = [r["letter"] for r in reports]

    class_average = calculate_average(all_averages)
    top_student = reports[all_averages.index(max(all_averages))]
    lowest_student = reports[all_averages.index(min(all_averages))]

    # Use a set to find unique grade letters in class
    unique_grades = set(all_grades)

    # Find failing students
    failing = [r["name"] for r in reports if r["letter"] == "F"]

    # Grade distribution using dictionary
    grade_distribution = {}
    for letter in all_grades:
        grade_distribution[letter] = grade_distribution.get(letter, 0) + 1

    print("\n" + "=" * 50)
    print("           CLASS SUMMARY REPORT")
    print("=" * 50)
    print(f"  Total Students:    {len(reports)}")
    print(f"  Class Average:     {class_average:.2f}/100")
    print(f"  Top Student:       {top_student['name']} ({top_student['average']:.1f})")
    print(f"  Needs Most Help:   {lowest_student['name']} ({lowest_student['average']:.1f})")
    print(f"  Grade Levels:      {', '.join(sorted(unique_grades))}")

    print(f"\n  Grade Distribution:")
    for grade in sorted(grade_distribution.keys()):
        count = grade_distribution[grade]
        bar = "▓" * count
        print(f"    {grade}: {bar} ({count} student(s))")

    if failing:
        print(f"\n   Failing Students: {', '.join(failing)}")
    else:
        print(f"\n   No failing students!")

    print("=" * 50)


def add_student_interactive(classroom):
    """Add a new student interactively."""
    print("\n--- Add New Student ---")

    name = input("Student name: ").strip().title()
    if not name:
        print("Name cannot be empty.")
        return

    subjects = ["Math", "Science", "English", "History", "Computer"]
    grades = []

    print(f"Enter grades for {name} (0-100):")
    for subject in subjects:
        while True:
            try:
                grade = int(input(f"  {subject}: "))
                if 0 <= grade <= 100:
                    grades.append(grade)
                    break
                else:
                    print("  Grade must be between 0 and 100.")
            except ValueError:
                print("  Please enter a valid number.")

    classroom.append({
        "name": name,
        "grades": grades,
        "subjects": subjects
    })
    print(f" {name} added successfully!")


def main():
    """Main function to run the grade calculator."""

    # Pre-loaded classroom data
    # Each student is a dictionary with name, grades, and subjects
    classroom = [
        {
            "name": "Humayun Kiani",
            "grades": [92, 88, 95, 79, 98],
            "subjects": ["Math", "Science", "English", "History", "Computer"]
        },
        {
            "name": "Ali Hassan",
            "grades": [78, 85, 72, 90, 88],
            "subjects": ["Math", "Science", "English", "History", "Computer"]
        },
        {
            "name": "Sara Ahmed",
            "grades": [95, 98, 92, 96, 99],
            "subjects": ["Math", "Science", "English", "History", "Computer"]
        },
        {
            "name": "Omar Farooq",
            "grades": [55, 62, 48, 70, 58],
            "subjects": ["Math", "Science", "English", "History", "Computer"]
        },
        {
            "name": "Fatima Malik",
            "grades": [82, 79, 88, 85, 91],
            "subjects": ["Math", "Science", "English", "History", "Computer"]
        }
    ]

    while True:
        # Main menu
        print("\n" + "=" * 50)
        print("      STUDENT GRADE CALCULATOR")
        print("=" * 50)
        print("  1. View all student reports")
        print("  2. View specific student report")
        print("  3. View class summary")
        print("  4. Add new student")
        print("  5. Find students by grade")
        print("  6. Exit")
        print("=" * 50)

        choice = input("  Choose an option (1-5): ").strip()

        if choice == "1":
            # Build and display all reports
            print("\n" + "=" * 50)
            print("         ALL STUDENT REPORTS")
            print("=" * 50)
            reports = [build_student_report(s) for s in classroom]
            for report in reports:
                display_student_report(report)

        elif choice == "2":
            # Show names and let user pick
            print("\nAvailable students:")
            for i, student in enumerate(classroom, start=1):
                print(f"  {i}. {student['name']}")

            try:
                pick = int(input("Enter student number: ")) - 1
                if 0 <= pick < len(classroom):
                    report = build_student_report(classroom[pick])
                    print("\n" + "=" * 50)
                    display_student_report(report)
                else:
                    print("Invalid selection.")
            except ValueError:
                print("Please enter a valid number.")

        elif choice == "3":
            # Build all reports then show summary
            reports = [build_student_report(s) for s in classroom]
            display_class_summary(reports)

        elif choice == "4":
            add_student_interactive(classroom)

        elif choice == "5":
            # Filter students by grade letter
            grade_filter = input("Enter grade letter (A/B/C/D/F): ").strip().upper()
            reports = [build_student_report(s) for s in classroom]
            filtered = [r for r in reports if r["letter"] == grade_filter]

            if filtered:
                print(f"\nStudents with grade {grade_filter}:")
                for r in filtered:
                    print(f"  - {r['name']} ({r['average']:.1f})")
            else:
                print(f"No students with grade {grade_filter}.")

        else:
            print("  Invalid option. Please choose 1-5.")


if __name__ == "__main__":
    main()