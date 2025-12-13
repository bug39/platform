"""Code generation tool."""

from .base import Tool, ToolSchema
from .registry import register_tool
from ..providers import get_provider
from ..providers.base import Message
from ..prompts.templates import GENERATE_CODE
from ..utils.code import extract_code, validate_syntax


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
        # Validate input
        if not description or len(description.strip()) < 10:
            return "Error: Description too short. Please provide more details."

        prompt = GENERATE_CODE.format(
            description=description,
            with_tests="Include pytest test cases." if include_tests else ""
        )

        try:
            provider = get_provider()
            response = provider.complete([Message(role="user", content=prompt)])

            # Extract and validate code
            code = extract_code(response.content)

            if code:
                if validate_syntax(code):
                    return f"Generated code:\n```python\n{code}\n```"
                else:
                    return f"Generated code has syntax errors:\n```python\n{code}\n```\nPlease review and fix."
            else:
                # No code block found, return raw response
                return f"Generated response:\n{response.content}"

        except Exception as e:
            return f"Error generating code: {str(e)}"
