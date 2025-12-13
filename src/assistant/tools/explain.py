"""Code explanation tool."""

from .base import Tool, ToolSchema
from .registry import register_tool
from ..providers import get_provider
from ..providers.base import Message
from ..prompts.templates import EXPLAIN_CODE


@register_tool
class ExplainTool(Tool):
    """Explain what code does."""

    @property
    def name(self) -> str:
        return "explain_code"

    @property
    def description(self) -> str:
        return "Explain what Python code does in plain English."

    @property
    def schema(self) -> ToolSchema:
        return ToolSchema(
            properties={
                "code": {
                    "type": "string",
                    "description": "Python code to explain"
                }
            },
            required=["code"]
        )

    def execute(self, code: str) -> str:
        """Explain code using LLM."""
        if not code or not code.strip():
            return "Error: No code provided to explain."

        # Validate input length
        if len(code) > 10000:
            return "Error: Code too long to explain (max 10,000 characters)."

        prompt = EXPLAIN_CODE.format(code=code)

        try:
            provider = get_provider()
            response = provider.complete([Message(role="user", content=prompt)])
            return response.content

        except Exception as e:
            return f"Error explaining code: {str(e)}"
