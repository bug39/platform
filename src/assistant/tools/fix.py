"""Code fixing tool."""

import re
from .base import Tool, ToolSchema
from .registry import register_tool
from ..prompts.templates import FIX_ERROR
from ..utils.validation import (
    validate_string_input,
    call_llm,
    extract_and_validate_code,
    MAX_CODE_LENGTH,
)


@register_tool
class FixTool(Tool):
    """Fix broken code."""

    @property
    def name(self) -> str:
        return "fix_code"

    @property
    def description(self) -> str:
        return "Fix Python code that has errors."

    @property
    def schema(self) -> ToolSchema:
        return ToolSchema(
            properties={
                "code": {
                    "type": "string",
                    "description": "The broken Python code"
                },
                "error": {
                    "type": "string",
                    "description": "The error message received"
                }
            },
            required=["code", "error"]
        )

    def execute(self, code: str, error: str) -> str:
        """Fix code based on error message."""
        # Validate inputs using helpers
        try:
            validate_string_input(code, "code", max_length=MAX_CODE_LENGTH)
            validate_string_input(error, "error", max_length=10_000)
        except ValueError as e:
            return f"Error: {str(e)}"

        # Build prompt
        prompt = FIX_ERROR.format(code=code, error=error)

        try:
            # Call LLM using helper
            response_content = call_llm(prompt)

            # Extract and validate fixed code using helper
            fixed_code, is_valid = extract_and_validate_code(response_content)

            if fixed_code:
                if is_valid:
                    return f"Fixed code:\n```python\n{fixed_code}\n```\n\nExplanation:\n{self._extract_explanation(response_content)}"
                else:
                    return f"Generated fix has syntax errors:\n{response_content}"
            else:
                return f"Fix suggestion:\n{response_content}"

        except Exception as e:
            return f"Error fixing code: {str(e)}"

    def _extract_explanation(self, text: str) -> str:
        """Extract explanation (text after code block)."""
        # Remove code blocks
        text = re.sub(r"```python.*?```", "", text, flags=re.DOTALL)
        text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
        return text.strip()
