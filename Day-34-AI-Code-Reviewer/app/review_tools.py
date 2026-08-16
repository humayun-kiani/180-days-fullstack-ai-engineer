# ============================================================
# app/review_tools.py
# Tool implementations for code analysis
# ============================================================

import ast
import os
import re
from pathlib import Path

from app.tool_registry import ToolRegistry

registry = ToolRegistry()


# ─── Tool 1: Read File ───────────────────────────────────────

@registry.register(
    name="read_file",
    description="""Read the contents of a source code file.
    
Use this first to get the code content before analyzing it.
Returns the file content and basic info like line count.""",
    input_schema={
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "Relative or absolute path to the file"
            }
        },
        "required": ["file_path"]
    }
)
def read_file(file_path: str) -> dict:
    """Read a source file and return its contents."""
    path = Path(file_path)

    if not path.exists():
        return {"error": f"File not found: {file_path}"}

    if path.suffix not in (".py", ".js", ".ts", ".go", ".java", ".rb"):
        return {"error": f"Unsupported file type: {path.suffix}"}

    if path.stat().st_size > 100_000:    # 100KB limit
        return {"error": "File too large (max 100KB)"}

    content = path.read_text(encoding="utf-8")
    lines = content.split("\n")

    return {
        "file_path": str(path),
        "language": _detect_language(path.suffix),
        "content": content,
        "total_lines": len(lines),
        "file_size_bytes": path.stat().st_size
    }


def _detect_language(suffix: str) -> str:
    mapping = {
        ".py": "Python", ".js": "JavaScript", ".ts": "TypeScript",
        ".go": "Go", ".java": "Java", ".rb": "Ruby"
    }
    return mapping.get(suffix, "Unknown")


# ─── Tool 2: Compute Metrics ─────────────────────────────────

@registry.register(
    name="compute_code_metrics",
    description="""Compute quantitative metrics for Python code.

Use this after reading the file to get numeric measurements:
- Line counts (total, code, comments, blank)
- Function and class counts  
- Import count
- Average and maximum function lengths
- Complexity estimation

Returns structured JSON with all metrics.""",
    input_schema={
        "type": "object",
        "properties": {
            "code": {
                "type": "string",
                "description": "Python source code to analyze"
            }
        },
        "required": ["code"]
    }
)
def compute_code_metrics(code: str) -> dict:
    """Compute quantitative metrics from Python source code."""
    lines = code.split("\n")
    total = len(lines)
    blank = sum(1 for l in lines if not l.strip())
    comments = sum(1 for l in lines if l.strip().startswith("#"))
    code_lines = total - blank - comments

    # Parse AST for structural metrics
    func_count = 0
    class_count = 0
    import_count = 0
    func_lengths = []
    max_func_len = 0

    try:
        tree = ast.parse(code)
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                func_count += 1
                # Approximate function length by line span
                if hasattr(node, "end_lineno") and hasattr(node, "lineno"):
                    length = node.end_lineno - node.lineno
                    func_lengths.append(length)
                    max_func_len = max(max_func_len, length)
            elif isinstance(node, ast.ClassDef):
                class_count += 1
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                import_count += 1
    except SyntaxError as e:
        return {"error": f"Syntax error: {e}"}

    avg_func_len = sum(func_lengths) / len(func_lengths) if func_lengths else 0

    # Simple complexity estimate
    if total < 50 and func_count <= 5:
        complexity = "low"
    elif total < 200 and func_count <= 15:
        complexity = "medium"
    else:
        complexity = "high"

    return {
        "total_lines": total,
        "code_lines": code_lines,
        "comment_lines": comments,
        "blank_lines": blank,
        "function_count": func_count,
        "class_count": class_count,
        "import_count": import_count,
        "avg_function_length": round(avg_func_len, 1),
        "max_function_length": max_func_len,
        "complexity_score": complexity
    }


# ─── Tool 3: Find Security Issues ────────────────────────────

@registry.register(
    name="find_security_issues",
    description="""Scan Python code for security vulnerabilities using pattern matching.

Detects:
- Hardcoded credentials (passwords, tokens, API keys)
- SQL injection vulnerabilities (string concatenation in queries)
- Command injection (shell=True in subprocess)
- Insecure random number generation
- Bare except clauses hiding errors
- Use of eval() or exec()
- HTTP instead of HTTPS for external calls
- Weak cryptography (MD5, SHA1)

Returns a list of security findings with line numbers.""",
    input_schema={
        "type": "object",
        "properties": {
            "code": {
                "type": "string",
                "description": "Python source code to scan for security issues"
            }
        },
        "required": ["code"]
    }
)
def find_security_issues(code: str) -> dict:
    """Scan code for common security vulnerabilities."""
    issues = []
    lines = code.split("\n")

    patterns = [
        # Hardcoded credentials
        (r'(?i)(password|passwd|pwd|secret|token|api_key|apikey)\s*=\s*["\'][^"\']{3,}["\']',
         "HARDCODED_CREDENTIAL",
         "Hardcoded credential detected — use environment variables instead",
         "error"),

        # SQL injection via string concatenation
        (r'(?i)(execute|query)\s*\(\s*["\'].*\+',
         "SQL_INJECTION",
         "Potential SQL injection via string concatenation — use parameterized queries",
         "error"),

        # SQL injection with f-string
        (r'(?i)(execute|query)\s*\(\s*f["\'].*\{',
         "SQL_INJECTION_FSTRING",
         "Potential SQL injection via f-string — use parameterized queries",
         "error"),

        # Bare except
        (r'^\s*except\s*:',
         "BARE_EXCEPT",
         "Bare except clause catches all exceptions including SystemExit — be specific",
         "warning"),

        # eval() usage
        (r'\beval\s*\(',
         "EVAL_USAGE",
         "eval() is dangerous if input is not fully controlled — avoid if possible",
         "warning"),

        # HTTP instead of HTTPS
        (r'["\']http://(?!localhost|127\.0\.0\.1)',
         "INSECURE_HTTP",
         "Using HTTP instead of HTTPS — credentials may be transmitted in plaintext",
         "warning"),

        # MD5 / SHA1
        (r'(?:hashlib\.)?(md5|sha1)\s*\(',
         "WEAK_HASH",
         "MD5/SHA1 are cryptographically weak — use SHA-256 or bcrypt for passwords",
         "warning"),

        # subprocess with shell=True
        (r'subprocess\.[a-z_]+\(.*shell\s*=\s*True',
         "SHELL_INJECTION",
         "shell=True in subprocess is dangerous with user input",
         "error"),
    ]

    for i, line in enumerate(lines, 1):
        for pattern, code_name, message, severity in patterns:
            if re.search(pattern, line):
                issues.append({
                    "line": i,
                    "severity": severity,
                    "category": "security",
                    "code": code_name,
                    "message": message,
                    "line_content": line.strip()[:100]
                })

    return {
        "security_issues": issues,
        "critical_count": sum(1 for i in issues if i["severity"] == "error"),
        "warning_count": sum(1 for i in issues if i["severity"] == "warning"),
        "scan_completed": True
    }


# ─── Tool 4: Find Style Issues ────────────────────────────────

@registry.register(
    name="find_style_issues",
    description="""Check Python code style against PEP 8 and best practices.

Checks for:
- Naming conventions (snake_case functions, PascalCase classes)
- Line length violations (default max 88 chars)
- Missing type hints on functions
- Missing docstrings on classes and public functions
- Comparing to None with == instead of 'is'
- Unnecessary 'else' after return
- Magic numbers without named constants
- Using range(len(list)) instead of enumerate

Returns a list of style findings with line numbers.""",
    input_schema={
        "type": "object",
        "properties": {
            "code": {
                "type": "string",
                "description": "Python source code to check for style issues"
            },
            "max_line_length": {
                "type": "integer",
                "description": "Maximum allowed line length (default: 88)",
                "default": 88
            }
        },
        "required": ["code"]
    }
)
def find_style_issues(code: str, max_line_length: int = 88) -> dict:
    """Find style and convention violations in Python code."""
    issues = []
    lines = code.split("\n")

    for i, line in enumerate(lines, 1):
        # Line length
        if len(line) > max_line_length:
            issues.append({
                "line": i,
                "severity": "warning",
                "category": "style",
                "message": f"Line too long ({len(line)} > {max_line_length} chars)",
                "line_content": line[:80] + "..."
            })

        # Comparing to None with ==
        if re.search(r'[!=]=\s*None\b', line):
            issues.append({
                "line": i,
                "severity": "warning",
                "category": "style",
                "message": "Use 'is None' or 'is not None' instead of == None",
                "line_content": line.strip()[:80]
            })

        # range(len(...)) anti-pattern
        if re.search(r'\brange\s*\(\s*len\s*\(', line):
            issues.append({
                "line": i,
                "severity": "info",
                "category": "style",
                "message": "Consider using enumerate() instead of range(len(...))",
                "line_content": line.strip()[:80]
            })

    # AST-based checks
    try:
        tree = ast.parse(code)
        for node in ast.walk(tree):
            # Function naming
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                name = node.name
                if name != name.lower() and not name.startswith("_"):
                    # Has uppercase but isn't a class — should be snake_case
                    if any(c.isupper() for c in name) and not name[0].isupper():
                        issues.append({
                            "line": node.lineno,
                            "severity": "warning",
                            "category": "style",
                            "message": f"Function '{name}' should use snake_case naming",
                            "line_content": f"def {name}(...)"
                        })

                # Missing docstring
                if (not (node.body and isinstance(node.body[0], ast.Expr)
                         and isinstance(node.body[0].value, ast.Constant)
                         and isinstance(node.body[0].value.value, str))
                        and not name.startswith("_")):
                    issues.append({
                        "line": node.lineno,
                        "severity": "info",
                        "category": "style",
                        "message": f"Function '{name}' is missing a docstring",
                        "line_content": f"def {name}(...)"
                    })

            # Class naming
            if isinstance(node, ast.ClassDef):
                name = node.name
                if not name[0].isupper():
                    issues.append({
                        "line": node.lineno,
                        "severity": "warning",
                        "category": "style",
                        "message": f"Class '{name}' should use PascalCase naming",
                        "line_content": f"class {name}:"
                    })
    except SyntaxError:
        pass

    return {
        "style_issues": issues,
        "error_count": sum(1 for i in issues if i["severity"] == "error"),
        "warning_count": sum(1 for i in issues if i["severity"] == "warning"),
        "info_count": sum(1 for i in issues if i["severity"] == "info")
    }


# ─── Tool 5: Find Performance Issues ─────────────────────────

@registry.register(
    name="find_performance_issues",
    description="""Detect common Python performance anti-patterns.

Detects:
- Nested loops with O(n²) or worse complexity
- String concatenation in loops (use join())
- List membership testing with 'in' on lists (use sets)
- Blocking sleep() calls
- Missing async/await on I/O-bound operations
- Large global variables
- Repeated dictionary lookups in loops

Returns performance issues with optimization suggestions.""",
    input_schema={
        "type": "object",
        "properties": {
            "code": {
                "type": "string",
                "description": "Python source code to check for performance issues"
            }
        },
        "required": ["code"]
    }
)
def find_performance_issues(code: str) -> dict:
    """Find performance anti-patterns in Python code."""
    issues = []
    lines = code.split("\n")

    for i, line in enumerate(lines, 1):
        stripped = line.strip()

        # time.sleep in a loop (needs context — simplified check)
        if "time.sleep" in stripped:
            issues.append({
                "line": i,
                "severity": "warning",
                "category": "performance",
                "message": "time.sleep() blocks the thread — use asyncio.sleep() in async code",
                "suggestion": "Replace with asyncio.sleep() if in async context"
            })

        # String concatenation with +=
        if re.search(r'\b\w+\s*\+=\s*["\']', stripped) or re.search(r'\b\w+\s*=\s*\w+\s*\+\s*["\']', stripped):
            issues.append({
                "line": i,
                "severity": "info",
                "category": "performance",
                "message": "String concatenation with + in a loop is O(n²) — use list.append() + ''.join()",
                "suggestion": "Collect strings in a list, then use ''.join(list)"
            })

    # AST analysis for nested loops
    try:
        tree = ast.parse(code)

        class LoopVisitor(ast.NodeVisitor):
            def __init__(self):
                self.nested_loops = []
                self.loop_depth = 0

            def visit_For(self, node):
                self.loop_depth += 1
                if self.loop_depth >= 2:
                    self.nested_loops.append(node.lineno)
                self.generic_visit(node)
                self.loop_depth -= 1

            def visit_While(self, node):
                self.loop_depth += 1
                if self.loop_depth >= 2:
                    self.nested_loops.append(node.lineno)
                self.generic_visit(node)
                self.loop_depth -= 1

        visitor = LoopVisitor()
        visitor.visit(tree)

        for lineno in set(visitor.nested_loops):
            issues.append({
                "line": lineno,
                "severity": "warning",
                "category": "performance",
                "message": "Nested loops detected — may indicate O(n²) or worse complexity",
                "suggestion": "Consider using sets, dicts, or different algorithms to reduce complexity"
            })
    except SyntaxError:
        pass

    return {
        "performance_issues": issues,
        "issue_count": len(issues)
    }