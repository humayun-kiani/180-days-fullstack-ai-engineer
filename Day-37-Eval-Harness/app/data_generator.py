# ============================================================
# app/data_generator.py
# Generate training data in JSONL format for fine-tuning
# ============================================================

import json
import random
from pathlib import Path
from datetime import datetime

random.seed(42)
OUTPUT_DIR = Path(__file__).parent.parent / "reports"
OUTPUT_DIR.mkdir(exist_ok=True)


TEMPLATES = {
    "urgent": [
        "URGENT: {system} is completely down for all {scope}",
        "P0: Critical {issue} affecting {scope} in production",
        "Emergency: {system} experiencing {issue}, immediate action needed",
        "CRITICAL: {issue} detected, {scope} are unable to {action}",
        "Production incident: {system} returning {error} for {scope}",
    ],
    "high": [
        "Fix {issue} causing {symptom} for some users",
        "Bug: {action} fails when {condition}",
        "Resolve {issue} before {deadline}",
        "{symptom} in {system} after recent deployment",
        "Fix {error} in {system} affecting {scope}",
    ],
    "medium": [
        "Add {feature} to {system}",
        "Implement {feature} for better {benefit}",
        "Build {feature} integration",
        "Create {feature} for {scope}",
        "Develop {feature} to support {benefit}",
    ],
    "low": [
        "Update {doc} documentation",
        "Refactor {component} for cleaner code",
        "Research {technology} as alternative",
        "Clean up {component} after migration",
        "Explore {technology} integration possibilities",
    ]
}

FILLS = {
    "{system}": ["API", "authentication service", "payment module", "database", "notification service"],
    "{scope}": ["all users", "enterprise customers", "mobile users", "admin users"],
    "{issue}": ["memory leak", "race condition", "authentication failure", "SQL injection", "timeout"],
    "{action}": ["log in", "checkout", "export data", "submit forms", "view reports"],
    "{error}": ["500 errors", "null pointer exception", "connection refused", "timeout error"],
    "{symptom}": ["crashes", "hangs", "returns errors", "produces wrong output", "runs slowly"],
    "{deadline}": ["Friday release", "tomorrow's demo", "end of sprint", "client presentation"],
    "{condition}": ["user has special characters in name", "under high load", "cache is empty"],
    "{feature}": ["dark mode", "CSV export", "bulk import", "Slack integration", "analytics dashboard"],
    "{benefit}": ["productivity", "user experience", "team collaboration", "data visibility"],
    "{doc}": ["API", "deployment", "onboarding", "configuration", "architecture"],
    "{component}": ["user model", "auth middleware", "task service", "notification handler"],
    "{technology}": ["GraphQL", "gRPC", "WebSockets", "Kafka", "Elasticsearch"],
}


def fill_template(template: str) -> str:
    """Fill a template with random values."""
    result = template
    for placeholder, options in FILLS.items():
        if placeholder in result:
            result = result.replace(placeholder, random.choice(options))
    return result


def generate_training_data(
    n_per_class: int = 50,
    system_prompt: str = ""
) -> list[dict]:
    """
    Generate JSONL training examples for fine-tuning.

    Args:
        n_per_class: Number of examples per priority class
        system_prompt: Optional system prompt to include

    Returns:
        list[dict]: Training examples in messages format
    """
    examples = []

    for priority, templates in TEMPLATES.items():
        for i in range(n_per_class):
            template = templates[i % len(templates)]
            task_title = fill_template(template)

            messages = []
            if system_prompt:
                messages.append({
                    "role": "system",
                    "content": system_prompt
                })

            messages.extend([
                {
                    "role": "user",
                    "content": f"Classify the priority of this task:\n\n\"{task_title}\""
                },
                {
                    "role": "assistant",
                    "content": json.dumps({
                        "priority": priority,
                        "confidence": "high",
                        "reason": f"This is a {priority} priority task based on its characteristics"
                    })
                }
            ])

            examples.append({"messages": messages})

    random.shuffle(examples)
    return examples


def save_jsonl(examples: list[dict], filename: str) -> Path:
    """Save examples to a JSONL file."""
    path = OUTPUT_DIR / filename
    with open(path, "w") as f:
        for example in examples:
            f.write(json.dumps(example, ensure_ascii=False) + "\n")
    return path


def validate_jsonl(filepath: Path) -> dict:
    """Validate a JSONL training file."""
    issues = []
    examples = []

    with open(filepath) as f:
        for i, line in enumerate(f):
            line = line.strip()
            if not line:
                continue
            try:
                example = json.loads(line)
                examples.append(example)
            except json.JSONDecodeError as e:
                issues.append(f"Line {i+1}: Invalid JSON — {e}")

    # Check structure
    for i, ex in enumerate(examples):
        messages = ex.get("messages", [])
        if len(messages) < 2:
            issues.append(f"Example {i+1}: Fewer than 2 messages")
            continue
        roles = [m.get("role") for m in messages]
        if "user" not in roles:
            issues.append(f"Example {i+1}: Missing user message")
        if "assistant" not in roles:
            issues.append(f"Example {i+1}: Missing assistant message")

    from collections import Counter
    class_counts = Counter()
    for ex in examples:
        for msg in ex.get("messages", []):
            if msg.get("role") == "assistant":
                try:
                    data = json.loads(msg["content"])
                    class_counts[data.get("priority", "unknown")] += 1
                except Exception:
                    pass

    return {
        "total_examples": len(examples),
        "issues": issues,
        "class_distribution": dict(class_counts),
        "is_valid": len(issues) == 0
    }