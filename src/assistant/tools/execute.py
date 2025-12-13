"""Code execution tool with sandboxed runtime."""

import ast
import logging
from .base import Tool, ToolSchema
from .registry import register_tool

logger = logging.getLogger(__name__)

# Security constants
MAX_CODE_LENGTH = 50_000  # 50KB maximum code size
MIN_TIMEOUT = 1  # Minimum timeout in seconds
MAX_TIMEOUT = 300  # Maximum timeout in seconds (5 minutes)


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
            code: Python code to execute (max 50KB)
            timeout: Execution timeout in seconds (1-300)

        Returns:
            Formatted string with execution results
        """
        # Validate code is not empty
        if not code or not code.strip():
            return "Error: No code provided to execute."

        # Validate code length (prevent DoS)
        if len(code) > MAX_CODE_LENGTH:
            logger.warning(f"Code length {len(code)} exceeds maximum {MAX_CODE_LENGTH}")
            return f"Error: Code too long. Maximum allowed: {MAX_CODE_LENGTH:,} characters ({len(code):,} provided)."

        # Validate timeout bounds (prevent resource exhaustion)
        if not isinstance(timeout, int):
            return f"Error: Timeout must be an integer, got {type(timeout).__name__}."

        if timeout < MIN_TIMEOUT or timeout > MAX_TIMEOUT:
            logger.warning(f"Invalid timeout {timeout}, must be between {MIN_TIMEOUT}-{MAX_TIMEOUT}")
            return f"Error: Timeout must be between {MIN_TIMEOUT} and {MAX_TIMEOUT} seconds (got {timeout})."

        # Validate syntax (fast fail)
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
