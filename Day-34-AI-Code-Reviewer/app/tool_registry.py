# ============================================================
# app/tool_registry.py
# Custom tool registry for the code reviewer
# ============================================================

import json
import traceback
from typing import Callable, Any
from pydantic import BaseModel


class Tool:
    """A registered tool with schema and implementation."""

    def __init__(
        self,
        name: str,
        description: str,
        input_schema: dict,
        func: Callable
    ):
        self.name = name
        self.description = description
        self.input_schema = input_schema
        self.func = func

    def to_schema(self) -> dict:
        """Convert to Anthropic tool definition format."""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema
        }

    def execute(self, **kwargs) -> str:
        """
        Execute tool and return string result.

        Always returns a string — errors included in JSON format.
        """
        try:
            result = self.func(**kwargs)
            if isinstance(result, (dict, list)):
                return json.dumps(result, indent=2, default=str)
            return str(result)
        except Exception as e:
            return json.dumps({
                "error": str(e),
                "tool": self.name,
                "traceback": traceback.format_exc()[-500:]  # last 500 chars
            })


class ToolRegistry:
    """
    Central registry for all AI-callable tools.

    Manages tool registration, schema generation,
    and execution with error handling.
    """

    def __init__(self):
        self._tools: dict[str, Tool] = {}
        self._call_log: list[dict] = []

    def register(
        self,
        name: str,
        description: str,
        input_schema: dict
    ) -> Callable:
        """
        Decorator to register a function as a tool.

        Usage:
            @registry.register(
                name="my_tool",
                description="Does something useful",
                input_schema={...}
            )
            def my_tool(param: str) -> dict:
                return {"result": param}
        """
        def decorator(func: Callable) -> Callable:
            self._tools[name] = Tool(
                name=name,
                description=description,
                input_schema=input_schema,
                func=func
            )
            return func
        return decorator

    def execute(self, tool_name: str, tool_input: dict) -> str:
        """Execute a tool by name with given inputs."""
        if tool_name not in self._tools:
            return json.dumps({
                "error": f"Tool '{tool_name}' not found",
                "available_tools": list(self._tools.keys())
            })

        # Log the call
        self._call_log.append({
            "tool": tool_name,
            "input": tool_input
        })

        tool = self._tools[tool_name]
        result = tool.execute(**tool_input)
        return result

    def get_all_schemas(self) -> list[dict]:
        """Get schemas for all tools (pass to Claude API)."""
        return [t.to_schema() for t in self._tools.values()]

    def get_call_log(self) -> list[dict]:
        """Get log of all tool calls made."""
        return self._call_log.copy()

    def clear_log(self) -> None:
        self._call_log.clear()

    @property
    def tool_names(self) -> list[str]:
        return list(self._tools.keys())