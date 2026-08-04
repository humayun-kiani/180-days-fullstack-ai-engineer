# ============================================================
# src/data_generator.py
# Generate realistic synthetic task data for training
# ============================================================

import random
import pandas as pd
from datetime import datetime, timedelta
from faker import Faker

fake = Faker()
random.seed(42)

# ─── Templates that determine priority ───────────────────────

TITLE_TEMPLATES = {
    "urgent": [
        "URGENT: Fix {system} failure in production",
        "CRITICAL: {system} is down, customers affected",
        "Emergency: Deploy hotfix for {bug} immediately",
        "ASAP: Review and merge security patch #{num}",
        "Immediately fix {system} vulnerability",
        "P0: {system} outage — all hands",
        "Customer escalation: {issue} blocking {num} users",
        "Production incident: {system} returning 500 errors",
        "CRITICAL security breach in {system}",
        "Hotfix needed NOW: {bug} causing data loss",
    ],
    "high": [
        "Implement {feature} for {client} launch",
        "Review pull request #{num} — auth module",
        "Fix {bug} before Friday release",
        "Deploy {feature} to staging for QA review",
        "Resolve {system} performance degradation",
        "Complete {feature} implementation",
        "Code review for {teammate}'s PR #{num}",
        "Fix {num} failing tests in CI pipeline",
        "Optimize slow database query in {system}",
        "Implement {feature} — sprint deadline today",
    ],
    "medium": [
        "Add {feature} to {system}",
        "Update {system} documentation",
        "Refactor {component} for better readability",
        "Write unit tests for {component}",
        "Review and update {system} dependencies",
        "Implement {feature} — due next week",
        "Set up {tool} for the team",
        "Create dashboard for {metric}",
        "Migrate {system} to new {tool}",
        "Add error handling to {component}",
    ],
    "low": [
        "Update README with new {feature} docs",
        "Nice to have: Add {feature} to admin panel",
        "Research {technology} for future use",
        "Clean up unused {component} code",
        "Format {component} according to style guide",
        "Add comment documentation to {component}",
        "Explore {technology} integration possibilities",
        "Update team wiki with {feature} guide",
        "Minor UI improvement: adjust {component} styling",
        "Investigate {technology} alternatives",
    ]
}

SYSTEMS = ["API", "database", "auth service", "payment module",
           "user portal", "notification service", "cache layer"]
FEATURES = ["dark mode", "export feature", "bulk operations",
            "search functionality", "filter system", "rate limiting"]
COMPONENTS = ["user model", "task service", "notification handler",
              "auth middleware", "cache manager", "API gateway"]
BUGS = ["memory leak", "race condition", "SQL injection", "null pointer",
        "infinite loop", "deadlock", "off-by-one error"]
TOOLS = ["Docker", "GitHub Actions", "Redis", "PostgreSQL", "Nginx",
         "Celery", "Prometheus"]
TECHNOLOGIES = ["GraphQL", "gRPC", "WebSockets", "Kafka", "Elasticsearch"]
CLIENTS = ["Acme Corp", "GlobalTech", "StartupXYZ", "Enterprise Co"]
TEAMMATES = ["Ali", "Sara", "Omar", "Fatima", "Ahmed"]
METRICS = ["uptime", "response time", "error rate", "throughput"]


def fill_template(template: str) -> str:
    """Fill a template with random values."""
    return (template
            .replace("{system}", random.choice(SYSTEMS))
            .replace("{feature}", random.choice(FEATURES))
            .replace("{component}", random.choice(COMPONENTS))
            .replace("{bug}", random.choice(BUGS))
            .replace("{tool}", random.choice(TOOLS))
            .replace("{technology}", random.choice(TECHNOLOGIES))
            .replace("{client}", random.choice(CLIENTS))
            .replace("{teammate}", random.choice(TEAMMATES))
            .replace("{metric}", random.choice(METRICS))
            .replace("{issue}", random.choice(BUGS))
            .replace("{num}", str(random.randint(1, 100))))


def generate_task(priority: str, index: int) -> dict:
    """Generate a realistic task with the given priority."""
    now = datetime.utcnow()
    template = random.choice(TITLE_TEMPLATES[priority])
    title = fill_template(template)

    # Due date based on priority
    if priority == "urgent":
        # Overdue or due very soon
        days_offset = random.choice([
            -random.randint(1, 3),   # overdue (negative)
            random.uniform(0, 1)      # due today
        ])
    elif priority == "high":
        days_offset = random.uniform(-1, 3)   # might be slightly overdue or due soon
    elif priority == "medium":
        days_offset = random.uniform(2, 14)   # 2 weeks ahead
    else:  # low
        if random.random() < 0.4:
            days_offset = None         # 40% of low priority have no due date
        else:
            days_offset = random.uniform(7, 30)   # a month ahead

    due_date = None
    is_overdue = False
    days_until_due = 0

    if days_offset is not None:
        due_date = now + timedelta(days=days_offset)
        is_overdue = days_offset < 0
        days_until_due = days_offset

    # Generate realistic description based on priority
    if priority in ("urgent", "high"):
        description = fake.paragraph(nb_sentences=3) if random.random() > 0.2 else None
    else:
        description = fake.paragraph(nb_sentences=2) if random.random() > 0.5 else None

    # Tags
    tag_pools = {
        "urgent": ["production", "incident", "critical", "bug"],
        "high": ["feature", "review", "deploy", "backend"],
        "medium": ["refactor", "docs", "test", "improvement"],
        "low": ["nice-to-have", "research", "cleanup", "docs"]
    }
    num_tags = random.randint(0, 3)
    tags = random.sample(tag_pools[priority], min(num_tags, len(tag_pools[priority])))

    # Estimate hours based on priority
    estimates = {
        "urgent": random.uniform(0.5, 4),
        "high": random.uniform(2, 8),
        "medium": random.uniform(2, 12),
        "low": random.uniform(0.5, 4) if random.random() > 0.3 else None
    }

    # Created at — within last 30 days
    created_hours_ago = random.uniform(0, 24 * 30)
    created_at = now - timedelta(hours=created_hours_ago)

    return {
        "id": index,
        "title": title,
        "description": description,
        "priority": priority,
        "due_date": due_date.isoformat() if due_date else None,
        "tags": tags,
        "estimated_hours": estimates[priority],
        "has_due_date": due_date is not None,
        "is_overdue": is_overdue,
        "days_until_due": days_until_due if due_date else None,
        "created_at": created_at.isoformat(),
        "hour_of_day": created_at.hour,
        "day_of_week": created_at.weekday()
    }


def generate_dataset(
    n_samples: int = 1000,
    class_distribution: dict = None
) -> pd.DataFrame:
    """
    Generate a balanced dataset of tasks.

    Args:
        n_samples: Total number of tasks to generate.
        class_distribution: Fraction of each priority.

    Returns:
        pd.DataFrame: Generated task dataset.
    """
    if class_distribution is None:
        # Realistic distribution: more medium tasks than urgent
        class_distribution = {
            "urgent": 0.15,
            "high": 0.25,
            "medium": 0.40,
            "low": 0.20
        }

    tasks = []
    idx = 0

    for priority, fraction in class_distribution.items():
        n = int(n_samples * fraction)
        for _ in range(n):
            tasks.append(generate_task(priority, idx))
            idx += 1

    # Shuffle so priorities are mixed
    random.shuffle(tasks)
    return pd.DataFrame(tasks)