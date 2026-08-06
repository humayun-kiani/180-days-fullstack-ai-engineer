# ============================================================
# src/entity_extractor.py
# Extract structured information from unstructured text
# ============================================================

import re
from dataclasses import dataclass, field


@dataclass
class ExtractedEntities:
    """Structured entities extracted from task text."""
    error_codes: list[str] = field(default_factory=list)
    endpoints: list[str] = field(default_factory=list)
    references: list[str] = field(default_factory=list)
    versions: list[str] = field(default_factory=list)
    time_mentions: list[str] = field(default_factory=list)
    systems: list[str] = field(default_factory=list)
    emails: list[str] = field(default_factory=list)
    technologies: list[str] = field(default_factory=list)
    suggested_tags: list[str] = field(default_factory=list)
    action_items: list[str] = field(default_factory=list)


# ─── Known Systems and Technologies ──────────────────────────

KNOWN_SYSTEMS = [
    "api", "database", "db", "auth", "authentication", "authorization",
    "cache", "redis", "nginx", "docker", "kubernetes", "celery",
    "postgresql", "postgres", "mongodb", "elasticsearch", "kafka",
    "rabbitmq", "grafana", "prometheus", "jenkins", "github", "gitlab",
    "aws", "gcp", "azure", "s3", "ec2", "lambda", "cloudfront"
]

TECHNOLOGIES = [
    "python", "javascript", "react", "vue", "angular", "fastapi",
    "django", "flask", "nodejs", "typescript", "golang", "rust",
    "java", "kotlin", "swift", "graphql", "grpc", "websocket",
    "rest", "microservice", "serverless", "terraform", "ansible"
]

# Tag suggestions based on keywords
TAG_KEYWORDS = {
    "backend": ["api", "server", "endpoint", "service", "database", "sql"],
    "frontend": ["ui", "dashboard", "page", "button", "form", "css", "html"],
    "auth": ["login", "logout", "password", "token", "jwt", "oauth", "auth"],
    "database": ["sql", "query", "table", "migration", "schema", "db", "postgres"],
    "performance": ["slow", "fast", "latency", "timeout", "cache", "optimize"],
    "security": ["vulnerability", "breach", "injection", "xss", "auth", "permission"],
    "devops": ["deploy", "ci", "cd", "docker", "kubernetes", "pipeline", "build"],
    "testing": ["test", "unit", "integration", "coverage", "mock", "assertion"],
    "documentation": ["docs", "readme", "comment", "guide", "tutorial", "wiki"],
    "mobile": ["ios", "android", "mobile", "app", "phone", "tablet"],
    "bug": ["bug", "error", "crash", "exception", "null", "undefined", "broken"],
    "urgent": ["urgent", "critical", "asap", "emergency", "blocking", "p0"],
}


def extract_entities(text: str) -> ExtractedEntities:
    """
    Extract structured entities from task description text.

    Args:
        text: Input text to analyze.

    Returns:
        ExtractedEntities: Structured extraction results.
    """
    entities = ExtractedEntities()
    text_lower = text.lower()

    # ── HTTP Error Codes ──────────────────────────────────────
    entities.error_codes = list(set(re.findall(
        r'\b(?:HTTP\s+|Error\s+|Status\s+)?([4-5]\d{2})\b',
        text, re.IGNORECASE
    )))

    # ── API Endpoints ─────────────────────────────────────────
    entities.endpoints = list(set(re.findall(
        r'(?:GET|POST|PUT|PATCH|DELETE|HEAD)?\s*(/(?:api|v\d+)/\S+)|'
        r'(?:endpoint|route|path)[:\s]+(/\S+)',
        text, re.IGNORECASE
    )))
    # Flatten matches
    entities.endpoints = [
        e for match in entities.endpoints
        for e in (match if isinstance(match, tuple) else [match])
        if e
    ]

    # ── Issue/PR/Ticket References ────────────────────────────
    entities.references = list(set(re.findall(
        r'(?:issue|ticket|PR|bug|#)\s*#?(\d+)',
        text, re.IGNORECASE
    )))

    # ── Version Numbers ───────────────────────────────────────
    entities.versions = list(set(re.findall(
        r'\bv?(\d+\.\d+(?:\.\d+)?(?:-\w+)?)\b',
        text
    )))

    # ── Time/Urgency Mentions ─────────────────────────────────
    entities.time_mentions = list(set(re.findall(
        r'\b(today|tomorrow|asap|urgent|immediately|by\s+\w+day|'
        r'this\s+week|end\s+of\s+day|eod|end\s+of\s+week|eow|'
        r'before\s+(?:the\s+)?(?:meeting|demo|launch|release))\b',
        text, re.IGNORECASE
    )))

    # ── Known Systems ─────────────────────────────────────────
    entities.systems = list(set([
        sys for sys in KNOWN_SYSTEMS
        if re.search(r'\b' + sys + r'\b', text_lower)
    ]))

    # ── Email Addresses ───────────────────────────────────────
    entities.emails = list(set(re.findall(
        r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b',
        text
    )))

    # ── Technologies ──────────────────────────────────────────
    entities.technologies = list(set([
        tech for tech in TECHNOLOGIES
        if re.search(r'\b' + tech + r'\b', text_lower)
    ]))

    # ── Suggested Tags ────────────────────────────────────────
    suggested_tags = set()
    for tag, keywords in TAG_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            suggested_tags.add(tag)
    entities.suggested_tags = sorted(suggested_tags)

    # ── Action Items ──────────────────────────────────────────
    # Extract sentences that look like action items
    action_patterns = [
        r'(?:need\s+to|must|should|please|require)\s+([\w\s]+?)(?:\.|,|$)',
        r'(?:fix|implement|add|update|remove|create|deploy)\s+([\w\s]+?)(?:\.|,|$)',
    ]
    for pattern in action_patterns:
        matches = re.findall(pattern, text_lower)
        entities.action_items.extend([m.strip() for m in matches if len(m.strip()) > 3])
    entities.action_items = entities.action_items[:5]    # max 5

    return entities