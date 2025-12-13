"""Code generation tool."""

from .base import Tool, ToolSchema
from .registry import register_tool
from ..prompts.templates import GENERATE_CODE
from ..utils.validation import (
    validate_string_input,
    call_llm,
    extract_and_validate_code,
    MIN_DESCRIPTION_LENGTH,
    MAX_DESCRIPTION_LENGTH,
)


@register_tool
class GenerateTool(Tool):
    """Generate code from natural language descriptions."""

    @property
    def name(self) -> str:
        return "generate_code"

    @property
    def description(self) -> str:
        return "Generate Python code from a natural language description."

    @property
    def schema(self) -> ToolSchema:
        return ToolSchema(
            properties={
                "description": {
                    "type": "string",
                    "description": "What the code should do"
                },
                "include_tests": {
                    "type": "boolean",
                    "description": "Whether to generate test cases",
                    "default": False
                }
            },
            required=["description"]
        )

    def execute(self, description: str, include_tests: bool = False) -> str:
        """Generate code based on description."""
        # Validate input using helper
        try:
            validate_string_input(
                description,
                "description",
                max_length=MAX_DESCRIPTION_LENGTH,
                min_length=MIN_DESCRIPTION_LENGTH
            )
        except ValueError as e:
            return f"Error: {str(e)}"

        # Build prompt
        prompt = GENERATE_CODE.format(
            description=description,
            with_tests="Include pytest test cases." if include_tests else ""
        )

        try:
            # Call LLM using helper
            response_content = call_llm(prompt)

            # Extract and validate code using helper
            code, is_valid = extract_and_validate_code(response_content)

            if code:
                if is_valid:
                    return f"Generated code:\n```python\n{code}\n```"
                else:
                    return f"Generated code has syntax errors:\n```python\n{code}\n```\nPlease review and fix."
            else:
                # No code block found, return raw response
                return f"Generated response:\n{response_content}"

        except Exception as e:
            return f"Error generating code: {str(e)}"
