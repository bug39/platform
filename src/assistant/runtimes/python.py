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
        # Create a pytest wrapper that writes code to a temporary module
        # and runs pytest on it
        wrapper = f'''
import sys
import tempfile
import os

# Create temporary test file
with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
    test_file = f.name
    f.write("""{code}

{test_code}""")

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
        return self.run(wrapper)
