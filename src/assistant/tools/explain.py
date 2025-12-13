"""Code explanation tool."""

from .base import Tool, ToolSchema
from .registry import register_tool
from ..prompts.templates import EXPLAIN_CODE
from ..utils.validation import validate_string_input, call_llm, MAX_CODE_LENGTH


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
        """Explain what the code does."""
        # Validate input using helper
        try:
            validate_string_input(code, "code", max_length=MAX_CODE_LENGTH)
        except ValueError as e:
            return f"Error: {str(e)}"

        # Build prompt
        prompt = EXPLAIN_CODE.format(code=code)

        try:
            # Call LLM using helper
            return call_llm(prompt)

        except Exception as e:
            return f"Error explaining code: {str(e)}"
