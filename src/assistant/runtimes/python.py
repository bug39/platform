"""Python runtime implementation."""

from .base import RuntimeConfig, ExecutionResult
from .docker import DockerRuntime


# Python runtime configuration
PYTHON_CONFIG = RuntimeConfig(
    language="python",
    image="assistant-python:latest",
    command=["python", "-c"],
    file_extension=".py",
    timeout_seconds=30,
    memory_limit="256m",
    cpu_quota=50000,  # 50% of one CPU
    packages=["pytest", "numpy", "pandas", "requests"],
)


class PythonRuntime(DockerRuntime):
    """
    Python code execution runtime.

    Features:
    - Python 3.12 in Docker container
    - pytest support for test execution
    - Common packages: numpy, pandas, requests
    - Security hardening with non-root user
    """

    def __init__(self):
        """Initialize Python runtime with default config."""
        super().__init__(PYTHON_CONFIG)

    def run_tests(self, code: str, test_code: str) -> ExecutionResult:
        """
        Run Python code with pytest.

        Args:
            code: Main Python code to test
            test_code: pytest test code

        Returns:
            ExecutionResult with test execution details

        Example:
            >>> code = "def add(a, b): return a + b"
            >>> test = "def test_add(): assert add(1, 2) == 3"
            >>> result = runtime.run_tests(code, test)
        """
        # SECURITY FIX: Use json to safely pass code without string interpolation
        # This prevents code injection via triple-quote escaping
        import json

        # Combine code and tests
        combined_code = f"{code}\n\n{test_code}"

        # Create a wrapper that reads code from stdin (passed as JSON)
        # This avoids any string escaping issues
        wrapper = '''
import sys
import tempfile
import os
import json

# Read code from environment (safer than string interpolation)
code_data = json.loads(sys.stdin.read())
test_code = code_data["code"]

# Create temporary test file
with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
    test_file = f.name
    f.write(test_code)

try:
    # Run pytest
    import pytest
    exit_code = pytest.main([test_file, '-v', '--tb=short'])
    sys.exit(exit_code)
finally:
    # Cleanup
    if os.path.exists(test_file):
        os.remove(test_file)
'''

        # Instead of embedding in string, pass via stdin-like mechanism
        # Docker run_container passes code_input as command argument
        # We need to modify the wrapper to accept code via a different method
        # For now, use base64 encoding to safely embed without triple-quote issues
        import base64

        encoded_code = base64.b64encode(combined_code.encode('utf-8')).decode('ascii')

        safe_wrapper = f'''
import sys
import tempfile
import os
import base64

# Decode code from base64 (prevents injection via quote escaping)
encoded = "{encoded_code}"
test_code = base64.b64decode(encoded).decode('utf-8')

# Create temporary test file
with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
    test_file = f.name
    f.write(test_code)

try:
    # Run pytest
    import pytest
    exit_code = pytest.main([test_file, '-v', '--tb=short'])
    sys.exit(exit_code)
finally:
    # Cleanup
    if os.path.exists(test_file):
        os.remove(test_file)
'''
        return self.run(safe_wrapper)
