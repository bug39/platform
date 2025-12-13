"""Code execution tool with sandboxed runtime."""

import ast
import logging
from typing import Optional
from .base import Tool, ToolSchema
from .registry import register_tool

logger = logging.getLogger(__name__)


@register_tool
class ExecuteTool(Tool):
    """Execute code in a safe sandboxed Docker environment."""

    def __init__(self):
        """Initialize execution tool with Python runtime."""
        self._runtime = None  # Lazy initialization

    def _get_runtime(self):
        """Lazy initialization of runtime to avoid Docker dependency at import time."""
        if self._runtime is None:
            try:
                from ..runtimes.python import PythonRuntime
                self._runtime = PythonRuntime()
                logger.info("Python runtime initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Python runtime: {e}")
                raise RuntimeError(
                    f"Failed to initialize Python runtime: {e}\n"
                    "Make sure Docker is running and the docker package is installed."
                )
        return self._runtime

    @property
    def name(self) -> str:
        return "execute_code"

    @property
    def description(self) -> str:
        return "Run Python code in a safe sandboxed Docker environment and return the output."

    @property
    def schema(self) -> ToolSchema:
        return ToolSchema(
            properties={
                "code": {
                    "type": "string",
                    "description": "Python code to execute"
                },
                "timeout": {
                    "type": "integer",
                    "description": "Timeout in seconds (default: 30)",
                    "default": 30
                }
            },
            required=["code"]
        )

    def execute(self, code: str, timeout: int = 30) -> str:
        """
        Execute Python code in a sandboxed Docker container.

        Args:
            code: Python code to execute
            timeout: Execution timeout in seconds

        Returns:
            Formatted string with execution results
        """
        if not code or not code.strip():
            return "Error: No code provided to execute."

        # Validate syntax first (fast fail)
        try:
            ast.parse(code)
        except SyntaxError as e:
            return f"Syntax error: {e.msg} at line {e.lineno}"

        # Execute in sandboxed runtime
        try:
            runtime = self._get_runtime()
            result = runtime.run(code, timeout=timeout)

            # Format output
            if result.success:
                output = f"Execution successful (completed in {result.execution_time_ms}ms)\n\n"
                if result.stdout:
                    output += f"Output:\n{result.stdout}"
                else:
                    output += "No output produced."

                if result.memory_used_mb > 0:
                    output += f"\n\nMemory used: {result.memory_used_mb:.2f} MB"

                return output
            else:
                # Execution failed
                error_msg = "Execution failed"
                if result.timed_out:
                    error_msg += f" (timed out after {timeout}s)"
                error_msg += f" (exit code: {result.exit_code})\n\n"

                if result.error_message:
                    error_msg += f"Error: {result.error_message}\n\n"

                if result.stderr:
                    error_msg += f"Error output:\n{result.stderr}"
                elif result.stdout:
                    error_msg += f"Output:\n{result.stdout}"

                return error_msg

        except RuntimeError as e:
            return f"Runtime error: {str(e)}"
        except Exception as e:
            logger.exception("Unexpected error during code execution")
            return f"Unexpected error: {str(e)}"
