# ============================================================
# src/log_generator.py
# Generates realistic sample log files for testing
# ============================================================

import random
import string
from datetime import datetime, timedelta
from pathlib import Path


# Log level weights (more INFO than ERROR in real logs)
LOG_LEVELS = {
    "DEBUG": 15,
    "INFO": 50,
    "WARNING": 20,
    "ERROR": 12,
    "CRITICAL": 3
}

# Sample source files
SOURCE_FILES = [
    "app.py", "database.py", "auth.py", "api.py",
    "cache.py", "worker.py", "scheduler.py", "models.py",
    "middleware.py", "utils.py", "config.py", "views.py"
]

# Sample messages per level
MESSAGES = {
    "DEBUG": [
        "Variable value: x={val}",
        "Cache hit for key: {key}",
        "SQL query: SELECT * FROM {table} WHERE id={id}",
        "Function {func}() called with args: {args}",
        "Processing item {id} of {total}",
        "Memory usage: {mem}MB",
        "Request received from {ip}",
    ],
    "INFO": [
        "Server started on port {port}",
        "User {user} logged in successfully",
        "Database connection established to {host}:{port}",
        "Processing {count} records",
        "Task {task} completed in {duration}ms",
        "File {file} uploaded successfully ({size}KB)",
        "Cache cleared. {count} entries removed",
        "Scheduled job {job} started",
        "API request to {endpoint} returned 200",
        "User {user} updated profile",
    ],
    "WARNING": [
        "High memory usage: {mem}% of available RAM",
        "Slow query detected: {duration}ms for {query}",
        "Rate limit approaching for IP {ip}: {count}/100 requests",
        "Deprecated function {func}() called in {file}",
        "Disk usage at {pct}% on {drive}",
        "Connection pool running low: {count}/{max} available",
        "Failed login attempt for user {user} from {ip}",
        "Response time above threshold: {duration}ms",
    ],
    "ERROR": [
        "Database connection failed: {error}",
        "Failed to process request from {ip}: {error}",
        "FileNotFoundError: {file} does not exist",
        "Authentication failed for user {user}: invalid token",
        "API call to {endpoint} failed with status {status}",
        "Task {task} failed after {attempts} attempts: {error}",
        "Uncaught exception in {func}(): {error}",
        "Permission denied: {user} cannot access {resource}",
    ],
    "CRITICAL": [
        "Database is unreachable after {attempts} retries",
        "Out of memory! Available: {mem}MB",
        "Disk full on {drive}: {space}MB remaining",
        "Security breach detected: {details}",
        "Server overloaded: {cpu}% CPU usage",
        "Critical service {service} is down",
    ]
}

# Sample values for template placeholders
SAMPLE_VALUES = {
    "val": lambda: random.randint(0, 9999),
    "key": lambda: f"user:{random.randint(1, 1000)}:session",
    "table": lambda: random.choice(["users", "posts", "sessions", "logs", "products"]),
    "id": lambda: random.randint(1, 10000),
    "total": lambda: random.randint(100, 10000),
    "func": lambda: random.choice(["process_request", "validate_user", "compute_hash", "sync_data"]),
    "args": lambda: f"(user_id={random.randint(1, 100)}, debug=True)",
    "mem": lambda: random.randint(50, 95),
    "ip": lambda: f"{random.randint(10, 200)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 254)}",
    "port": lambda: random.choice([8000, 8080, 5432, 6379, 3306, 80, 443]),
    "user": lambda: random.choice(["humayun", "ali", "sara", "ahmed", "fatima", "omar"]),
    "host": lambda: random.choice(["localhost", "db.production.com", "redis.internal", "10.0.0.5"]),
    "count": lambda: random.randint(1, 500),
    "task": lambda: random.choice(["send_email", "process_payment", "sync_inventory", "generate_report"]),
    "duration": lambda: random.randint(10, 30000),
    "file": lambda: random.choice(["upload.csv", "report.pdf", "data.json", "image.png"]),
    "size": lambda: random.randint(1, 5000),
    "job": lambda: random.choice(["daily_backup", "weekly_report", "cache_cleanup", "db_optimize"]),
    "endpoint": lambda: random.choice(["/api/users", "/api/posts", "/api/auth/login", "/api/products"]),
    "query": lambda: random.choice(["SELECT *", "UPDATE users", "INSERT INTO logs", "DELETE FROM sessions"]),
    "pct": lambda: random.randint(70, 99),
    "drive": lambda: random.choice(["/", "/var", "/data", "C:", "D:"]),
    "max": lambda: 100,
    "resource": lambda: random.choice(["admin_panel", "user_data", "system_config", "logs"]),
    "error": lambda: random.choice([
        "timeout after 30s", "connection refused",
        "invalid credentials", "disk I/O error",
        "null pointer exception", "permission denied"
    ]),
    "status": lambda: random.choice([400, 401, 403, 404, 429, 500, 502, 503]),
    "attempts": lambda: random.randint(2, 5),
    "details": lambda: random.choice([
        "multiple failed logins from 198.51.100.x",
        "unusual API access pattern detected",
        "SQL injection attempt blocked"
    ]),
    "cpu": lambda: random.randint(90, 100),
    "service": lambda: random.choice(["database", "cache", "message_queue", "auth_service"]),
    "space": lambda: random.randint(10, 500),
    "args_str": lambda: "()",
}


def fill_template(template):
    """Fill a message template with random values."""
    result = template
    for key, fn in SAMPLE_VALUES.items():
        placeholder = "{" + key + "}"
        if placeholder in result:
            result = result.replace(placeholder, str(fn()))
    return result


def generate_log_line(timestamp):
    """Generate a single realistic log line."""
    # Pick level based on weights
    level = random.choices(
        list(LOG_LEVELS.keys()),
        weights=list(LOG_LEVELS.values())
    )[0]

    source_file = random.choice(SOURCE_FILES)
    line_number = random.randint(10, 500)

    # Get a message template for this level
    template = random.choice(MESSAGES[level])
    message = fill_template(template)

    # Format: [YYYY-MM-DD HH:MM:SS] LEVEL [file.py:line] message
    return (
        f"[{timestamp.strftime('%Y-%m-%d %H:%M:%S')}] "
        f"{level} "
        f"[{source_file}:{line_number}] "
        f"{message}"
    )


def generate_log_file(filepath, num_lines=200, start_date=None):
    """
    Generate a realistic log file.

    Args:
        filepath (str or Path): Where to save the log file.
        num_lines (int): Number of log lines to generate.
        start_date (datetime): Starting timestamp. Defaults to 24 hours ago.

    Returns:
        Path: Path to the generated file.
    """
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)

    if start_date is None:
        start_date = datetime.now() - timedelta(hours=24)

    # Generate timestamps spread over the time range
    total_seconds = 24 * 3600
    timestamps = sorted([
        start_date + timedelta(seconds=random.randint(0, total_seconds))
        for _ in range(num_lines)
    ])

    with open(filepath, "w", encoding="utf-8") as f:
        for timestamp in timestamps:
            line = generate_log_line(timestamp)
            f.write(line + "\n")

    return filepath