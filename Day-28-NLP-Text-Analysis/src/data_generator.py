# ============================================================
# src/data_generator.py
# Generate labeled text data for NLP training
# ============================================================

import random
import pandas as pd
from faker import Faker

fake = Faker()
random.seed(42)

# ─── Training Templates by Category ─────────────────────────

TEMPLATES = {
    "bug": [
        "API endpoint {endpoint} returns {error} error after update",
        "{system} is completely broken, users cannot {action}",
        "Getting null pointer exception when trying to {action}",
        "{system} crashes after {duration} minutes of use",
        "HTTP {code} error on {endpoint}, started after {event}",
        "{system} throws unhandled exception on {action}",
        "Race condition causing data corruption in {system}",
        "Memory leak detected in {system} service",
        "Authentication fails for {percent} of users since {event}",
        "{system} returns wrong data when {condition}",
        "Critical: {system} is down in production environment",
        "Bug: {action} doesn't work when {condition}",
        "Error {code} when accessing {endpoint}",
        "{system} not responding to requests, all users affected",
        "Undefined behavior in {system} causing {symptom}",
    ],
    "feature_request": [
        "Please add ability to export data as {format}",
        "Feature request: bulk {action} for multiple items",
        "Would love to have dark mode in the {system} dashboard",
        "Request: implement {feature} in the {system}",
        "Enhancement: add {feature} support to {system}",
        "It would be great if users could {action} directly from {system}",
        "Add {feature} integration with {tool}",
        "Request to add keyboard shortcuts for common {action} actions",
        "Feature: allow customization of {component} appearance",
        "Please implement {feature} as it would greatly improve workflow",
        "Add support for {format} format in {system}",
        "Would like to see {feature} added to {system}",
        "Enhancement request: support {feature} in {system}",
        "Nice to have: {feature} for the {component}",
        "Request: ability to {action} via API",
    ],
    "performance": [
        "{system} is extremely slow, taking {duration} seconds to respond",
        "Page load time increased to {duration} seconds after update",
        "Database queries taking {duration} seconds, should be milliseconds",
        "{system} performance degraded significantly since {event}",
        "Memory usage growing continuously, now at {percent}%",
        "CPU usage spikes to {percent}% when {action}",
        "{system} times out when processing large datasets",
        "Response time for {endpoint} increased from {fast} to {slow}",
        "{action} is too slow for production workload",
        "Cache miss rate very high causing slow {system} responses",
        "{system} becomes unresponsive under heavy load",
        "High latency detected: {endpoint} taking {duration}ms",
        "{system} performance dropped {percent}% after last deployment",
        "OOM errors occurring in {system} under normal load",
        "Throughput decreased dramatically in {system}",
    ],
    "question": [
        "How do I configure {feature} in {system}?",
        "What is the correct way to {action} using the API?",
        "Is there documentation for {feature} integration?",
        "How can I {action} programmatically?",
        "What are the rate limits for the {endpoint} endpoint?",
        "Where can I find examples of {feature} implementation?",
        "Is it possible to {action} with current {system} version?",
        "What format should {data} be in for {action}?",
        "How should I handle {error} errors in {system}?",
        "What is the recommended way to {action}?",
        "Can I {action} using the existing {feature}?",
        "What permissions are needed to {action}?",
        "How long does {action} typically take?",
        "Is {feature} supported in the free tier?",
        "What happens when {condition} in {system}?",
    ],
    "maintenance": [
        "Upgrade {system} dependencies to latest versions",
        "Clean up deprecated {component} code",
        "Migrate {system} database schema to new format",
        "Update {system} SSL certificates before expiration",
        "Remove old {component} that is no longer used",
        "Refactor {component} for better code maintainability",
        "Update documentation for {feature} configuration",
        "Archive old {data} records from database",
        "Rotate API keys and update {system} configuration",
        "Perform scheduled {system} maintenance window",
        "Update {system} to latest stable version",
        "Clean up test data from production {system}",
        "Renew {feature} subscription before expiration",
        "Backup {system} data before migration",
        "Apply security patches to {system}",
    ]
}

# Placeholder values
SYSTEMS = ["API", "dashboard", "auth service", "database", "payment system",
           "notification service", "user portal", "cache layer", "CI/CD pipeline"]
ENDPOINTS = ["/api/users", "/api/tasks", "/api/auth/login", "/api/projects",
             "/api/reports", "/api/payments", "/api/webhooks"]
ERRORS = ["500", "404", "401", "403", "503", "422", "400"]
CODES = ["500", "404", "403", "400", "503", "408", "429"]
ACTIONS = ["login", "create tasks", "export data", "upload files", "view reports",
           "delete records", "update profile", "generate reports", "sync data"]
DURATIONS = ["30", "45", "60", "2-3", "10", "30+"]
PERCENTS = ["50", "80", "90", "30", "100", "70"]
EVENTS = ["yesterday's update", "v2.3 deployment", "database migration",
          "config change", "last release", "server upgrade"]
FEATURES = ["two-factor auth", "dark mode", "bulk import", "API rate limiting",
            "webhook support", "CSV export", "SSO integration", "audit logs"]
TOOLS = ["Slack", "GitHub", "Jira", "Salesforce", "Google Workspace", "Zapier"]
FORMATS = ["CSV", "Excel", "PDF", "JSON", "XML", "YAML"]
COMPONENTS = ["user model", "task service", "notification handler",
              "payment processor", "auth middleware", "cache manager"]
SYMPTOMS = ["data loss", "incorrect results", "auth bypass", "data corruption"]
CONDITIONS = ["user has special characters", "under heavy load", "cache is empty",
              "multiple users are logged in", "request includes filters"]
DATA = ["user records", "task history", "log files", "analytics data", "exports"]
FAST = ["50ms", "100ms", "200ms", "500ms"]
SLOW = ["5s", "10s", "30s", "60s"]


def fill_template(template: str) -> str:
    """Fill template placeholders with random values."""
    replacements = {
        "{system}": random.choice(SYSTEMS),
        "{endpoint}": random.choice(ENDPOINTS),
        "{error}": random.choice(ERRORS),
        "{code}": random.choice(CODES),
        "{action}": random.choice(ACTIONS),
        "{duration}": random.choice(DURATIONS),
        "{percent}": random.choice(PERCENTS),
        "{event}": random.choice(EVENTS),
        "{feature}": random.choice(FEATURES),
        "{tool}": random.choice(TOOLS),
        "{format}": random.choice(FORMATS),
        "{component}": random.choice(COMPONENTS),
        "{symptom}": random.choice(SYMPTOMS),
        "{condition}": random.choice(CONDITIONS),
        "{data}": random.choice(DATA),
        "{fast}": random.choice(FAST),
        "{slow}": random.choice(SLOW),
    }
    result = template
    for placeholder, value in replacements.items():
        result = result.replace(placeholder, value)
    return result


def add_noise(text: str, category: str) -> str:
    """Add realistic noise to make text more natural."""
    # Add urgency for bugs
    if category == "bug" and random.random() < 0.4:
        prefixes = ["URGENT: ", "Critical: ", "BLOCKER: ", "P0: ", ""]
        text = random.choice(prefixes) + text

    # Add frustration indicators for bugs and performance
    if category in ("bug", "performance") and random.random() < 0.3:
        suffixes = [
            " This is blocking our team.",
            " Customers are complaining.",
            " We need this fixed ASAP.",
            " This is affecting all users.",
            " Revenue impact is significant."
        ]
        text = text + random.choice(suffixes)

    # Add polite language to feature requests
    if category == "feature_request" and random.random() < 0.4:
        prefixes = ["Feature request: ", "Enhancement: ", "Suggestion: ", "Idea: ", ""]
        text = random.choice(prefixes) + text

    return text


def generate_training_data(
    n_per_category: int = 300
) -> pd.DataFrame:
    """
    Generate balanced training dataset for text classification.

    Args:
        n_per_category: Number of examples per category.

    Returns:
        pd.DataFrame: Dataset with 'text' and 'category' columns.
    """
    rows = []
    categories = list(TEMPLATES.keys())

    for category in categories:
        templates = TEMPLATES[category]
        for _ in range(n_per_category):
            template = random.choice(templates)
            text = fill_template(template)
            text = add_noise(text, category)
            rows.append({"text": text, "category": category})

    df = pd.DataFrame(rows)
    df = df.sample(frac=1, random_state=42).reset_index(drop=True)
    return df