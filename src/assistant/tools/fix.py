"""Code fixing tool."""

import re
import ast
from .base import Tool, ToolSchema
from .registry import register_tool
from ..providers import get_provider
from ..providers.base import Message
from ..prompts.templates import FIX_ERROR


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
        if not code or not code.strip():
            return "Error: No code provided to fix."
        if not error or not error.strip():
            return "Error: No error message provided."

        prompt = FIX_ERROR.format(code=code, error=error)

        try:
            provider = get_provider()
            response = provider.complete([Message(role="user", content=prompt)])

            # Extract fixed code
            fixed_code = self._extract_code(response.content)

            if fixed_code:
                # Validate the fixed code
                if self._validate_syntax(fixed_code):
                    return f"Fixed code:\n```python\n{fixed_code}\n```\n\nExplanation:\n{self._extract_explanation(response.content)}"
                else:
                    return f"Generated fix has syntax errors:\n{response.content}"
            else:
                return f"Fix suggestion:\n{response.content}"

        except Exception as e:
            return f"Error fixing code: {str(e)}"

    def _extract_code(self, text: str) -> str:
        """Extract code from markdown code blocks."""
        pattern = r"```python\n(.*?)```"
        matches = re.findall(pattern, text, re.DOTALL)
        if matches:
            return matches[0].strip()

        pattern = r"```\n(.*?)```"
        matches = re.findall(pattern, text, re.DOTALL)
        if matches:
            return matches[0].strip()

        return ""

    def _extract_explanation(self, text: str) -> str:
        """Extract explanation (text after code block)."""
        # Remove code blocks
        text = re.sub(r"```python.*?```", "", text, flags=re.DOTALL)
        text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
        return text.strip()

    def _validate_syntax(self, code: str) -> bool:
        """Check if code has valid Python syntax."""
        try:
            ast.parse(code)
            return True
        except SyntaxError:
            return False
