# ============================================================
# app/reviewer.py
# AI code reviewer using raw Anthropic tool calling
# ============================================================

import json
import os
import time
from typing import Optional

import anthropic

from app.tool_registry import ToolRegistry
from app.schemas import CodeReview, CodeMetrics, CodeIssue


class MockAnthropicForReview:
    """Mock Claude responses for code review without API key."""

    def messages_create(self, **kwargs):
        """Generate realistic code review tool calls."""
        messages = kwargs.get("messages", [])
        last_content = ""
        for m in reversed(messages):
            if isinstance(m.get("content"), str):
                last_content = m["content"]
                break

        # Simulate tool use sequence
        import uuid

        class MockBlock:
            def __init__(self, type_, **data):
                self.type = type_
                for k, v in data.items():
                    setattr(self, k, v)

        class MockUsage:
            input_tokens = 500
            output_tokens = 200

        class MockResponse:
            def __init__(self, stop_reason, content):
                self.stop_reason = stop_reason
                self.content = content
                self.usage = MockUsage()

        if not hasattr(self, "_call_count"):
            self._call_count = 0

        self._call_count += 1

        # First call: read file
        if self._call_count == 1:
            return MockResponse("tool_use", [
                MockBlock("tool_use",
                    id=f"toolu_{uuid.uuid4().hex[:8]}",
                    name="read_file",
                    input={"file_path": "sample_code/bad_code.py"})
            ])
        # Second: compute metrics
        elif self._call_count == 2:
            code = kwargs.get("messages", [])[-1].get("content", [{}])[0].get("content", "x = 1\n" * 50)
            return MockResponse("tool_use", [
                MockBlock("tool_use",
                    id=f"toolu_{uuid.uuid4().hex[:8]}",
                    name="compute_code_metrics",
                    input={"code": code[:200]})
            ])
        # Third: security
        elif self._call_count == 3:
            return MockResponse("tool_use", [
                MockBlock("tool_use",
                    id=f"toolu_{uuid.uuid4().hex[:8]}",
                    name="find_security_issues",
                    input={"code": "# sample code"})
            ])
        # Fourth: final answer
        else:
            self._call_count = 0  # reset for next review
            return MockResponse("end_turn", [
                MockBlock("text", text=json.dumps({
                    "overall_score": 4,
                    "grade": "D",
                    "summary": "This code has significant issues requiring immediate attention.",
                    "top_improvements": [
                        "Remove hardcoded credentials and use environment variables",
                        "Fix SQL injection vulnerability with parameterized queries",
                        "Replace bare except with specific exception types",
                        "Add type hints and docstrings to all functions",
                        "Refactor nested loop for better performance"
                    ],
                    "positive_aspects": [
                        "Code is functional and produces results",
                        "Constants are defined at module level"
                    ]
                }))
            ])


class AICodeReviewer:
    """
    AI Code Reviewer using raw Anthropic tool calling.

    Uses a multi-step agentic loop:
    1. Claude reads the file
    2. Claude runs metrics analysis
    3. Claude scans for security issues
    4. Claude checks style issues
    5. Claude checks performance issues
    6. Claude synthesizes everything into a review
    """

    MAX_ITERATIONS = 10

    def __init__(self, registry: ToolRegistry):
        self.registry = registry

        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        if api_key and api_key != "your-api-key-here":
            self.client = anthropic.Anthropic(api_key=api_key)
            self.mock = False
        else:
            self.client = MockAnthropicForReview()
            self.mock = True

    def review(
        self,
        file_path: str,
        focus_areas: list[str] | None = None
    ) -> CodeReview:
        """
        Run a complete AI code review.

        Uses the agent loop to let Claude decide which tools to call
        and in what order to build a comprehensive review.

        Args:
            file_path: Path to the file to review.
            focus_areas: Specific areas to focus on.

        Returns:
            CodeReview: Structured review result.
        """
        start = time.perf_counter()
        self.registry.clear_log()

        focus = focus_areas or ["security", "style", "performance", "bugs"]
        focus_str = ", ".join(focus)

        system_prompt = f"""You are an expert Python code reviewer.

Your job: Thoroughly review the specified Python file and produce a comprehensive code review.

Process (use tools in this order):
1. read_file — Get the actual code content
2. compute_code_metrics — Get quantitative metrics
3. find_security_issues — Check for vulnerabilities  
4. find_style_issues — Check PEP 8 and conventions
5. find_performance_issues — Check for anti-patterns
6. Once you have all data, respond with a JSON review (no tool call)

Focus areas for this review: {focus_str}

Final response must be ONLY valid JSON with this structure:
{{
  "overall_score": <integer 0-10>,
  "grade": "<A|B|C|D|F>",
  "summary": "<2-3 sentence overall assessment>",
  "top_improvements": ["<specific improvement 1>", "<specific improvement 2>", ...],
  "positive_aspects": ["<positive aspect 1>", ...]
}}"""

        user_message = f"Please review this file: {file_path}"
        messages = [{"role": "user", "content": user_message}]
        tools = self.registry.get_all_schemas()

        # Collected data from tool calls
        collected_metrics = {}
        collected_issues = []
        all_tool_results = {}

        # Agentic loop
        for iteration in range(self.MAX_ITERATIONS):
            try:
                if self.mock:
                    response = self.client.messages_create(
                        model="claude-sonnet-4-6",
                        max_tokens=2048,
                        system=system_prompt,
                        tools=tools,
                        messages=messages
                    )
                else:
                    response = self.client.messages.create(
                        model="claude-sonnet-4-6",
                        max_tokens=2048,
                        system=system_prompt,
                        tools=tools,
                        messages=messages
                    )
            except Exception as e:
                break

            # Add Claude's response to history
            messages.append({
                "role": "assistant",
                "content": response.content
            })

            if response.stop_reason == "end_turn":
                # Claude has finished — extract JSON review
                for block in response.content:
                    text = getattr(block, "text", "")
                    if text and text.strip().startswith("{"):
                        try:
                            review_data = json.loads(text.strip())
                            all_tool_results["final_review"] = review_data
                        except json.JSONDecodeError:
                            all_tool_results["final_review"] = {
                                "overall_score": 5,
                                "grade": "C",
                                "summary": "Review completed.",
                                "top_improvements": ["Review the code manually"],
                                "positive_aspects": ["Code runs"]
                            }
                break

            if response.stop_reason == "tool_use":
                # Claude wants to call tools
                tool_results = []

                for block in response.content:
                    if getattr(block, "type", "") == "tool_use":
                        tool_name = block.name
                        tool_input = block.input
                        print(f"  🔧 Tool call: {tool_name}({list(tool_input.keys())})")

                        result_str = self.registry.execute(tool_name, tool_input)
                        all_tool_results[tool_name] = result_str

                        # Parse results for later use
                        try:
                            result_data = json.loads(result_str)
                            if tool_name == "compute_code_metrics":
                                collected_metrics = result_data
                            elif tool_name in ("find_security_issues", "find_style_issues", "find_performance_issues"):
                                for key in result_data:
                                    if isinstance(result_data[key], list):
                                        collected_issues.extend(result_data[key])
                        except (json.JSONDecodeError, TypeError):
                            pass

                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": result_str
                        })

                messages.append({"role": "user", "content": tool_results})

        # Build structured review from collected data
        return self._build_review(
            file_path=file_path,
            collected_metrics=collected_metrics,
            collected_issues=collected_issues,
            final_review=all_tool_results.get("final_review", {}),
            elapsed_ms=(time.perf_counter() - start) * 1000
        )

    def review_inline(self, code: str, filename: str = "code.py") -> CodeReview:
        """Review code provided as a string (not a file path)."""
        import tempfile
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".py",
            prefix="review_",
            delete=False
        ) as f:
            f.write(code)
            temp_path = f.name

        try:
            return self.review(temp_path)
        finally:
            os.unlink(temp_path)

    def _build_review(
        self,
        file_path: str,
        collected_metrics: dict,
        collected_issues: list,
        final_review: dict,
        elapsed_ms: float
    ) -> CodeReview:
        """Construct the CodeReview dataclass from collected data."""

        # Build metrics
        metrics = CodeMetrics(
            total_lines=collected_metrics.get("total_lines", 0),
            code_lines=collected_metrics.get("code_lines", 0),
            comment_lines=collected_metrics.get("comment_lines", 0),
            blank_lines=collected_metrics.get("blank_lines", 0),
            function_count=collected_metrics.get("function_count", 0),
            class_count=collected_metrics.get("class_count", 0),
            import_count=collected_metrics.get("import_count", 0),
            avg_function_length=collected_metrics.get("avg_function_length", 0),
            max_function_length=collected_metrics.get("max_function_length", 0),
            complexity_score=collected_metrics.get("complexity_score", "unknown")
        )

        # Build issues list
        issues = []
        for issue in collected_issues[:30]:    # cap at 30 issues
            try:
                issues.append(CodeIssue(
                    line=issue.get("line"),
                    severity=issue.get("severity", "info"),
                    category=issue.get("category", "general"),
                    message=issue.get("message", "Issue detected"),
                    suggestion=issue.get("suggestion", issue.get("message", "Review this code"))
                ))
            except Exception:
                pass

        score = final_review.get("overall_score", 5)
        grade = final_review.get("grade", "C")
        if not grade:
            grade = "A" if score >= 9 else "B" if score >= 7 else "C" if score >= 5 else "D" if score >= 3 else "F"

        return CodeReview(
            file_path=file_path,
            language="Python",
            overall_score=score,
            grade=grade,
            summary=final_review.get("summary", "Code review completed."),
            metrics=metrics,
            issues=issues,
            top_improvements=final_review.get("top_improvements", []),
            positive_aspects=final_review.get("positive_aspects", []),
            review_time_ms=round(elapsed_ms, 1)
        )