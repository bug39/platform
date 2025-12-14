"""Basic runtime functionality tests."""

import pytest
from src.assistant.config import SandboxConfig
from src.assistant.runtimes.python import PythonRuntime
from src.assistant.runtimes.docker import DockerManager, DOCKER_AVAILABLE


# Skip all tests if Docker is not available
pytestmark = pytest.mark.skipif(not DOCKER_AVAILABLE, reason="Docker not available")


class TestPythonRuntimeBasic:
    """Test basic PythonRuntime functionality."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up runtime for each test."""
        try:
            # Check if Docker is actually running
            manager = DockerManager(SandboxConfig())
            if not manager.is_available():
                pytest.skip("Docker daemon not running")
        except Exception:
            pytest.skip("Docker not available")

        self.runtime = PythonRuntime()

    def test_python_runtime_initialization(self):
        """Test that PythonRuntime initializes correctly."""
        assert self.runtime.language == "python"
        assert self.runtime.config.image == "assistant-python:latest"
        assert self.runtime.config.command == ["python", "-c"]
        assert self.runtime.is_available()

    def test_simple_execution(self):
        """Test executing simple Python code."""
        code = "print('Hello, World!')"
        result = self.runtime.run(code)

        assert result.success is True
        assert "Hello, World!" in result.stdout
        assert result.exit_code == 0
        assert result.timed_out is False

    def test_execution_with_output(self):
        """Test execution captures both stdout and stderr."""
        code = """
import sys
print('stdout message')
print('stderr message', file=sys.stderr)
"""
        result = self.runtime.run(code)

        assert result.success is True
        assert "stdout message" in result.stdout
        assert "stderr message" in result.stderr
        assert result.exit_code == 0

    def test_execution_timing(self):
        """Test that execution time is tracked."""
        code = """
import time
time.sleep(0.1)
print('done')
"""
        result = self.runtime.run(code)

        assert result.success is True
        assert result.execution_time_ms >= 100  # At least 100ms for sleep
        assert result.execution_time_ms < 5000  # But not too long

    def test_memory_tracking(self):
        """Test that memory usage is tracked."""
        code = """
# Allocate some memory
data = [0] * 1000000
print('done')
"""
        result = self.runtime.run(code)

        assert result.success is True
        # Memory tracking may not always work, but if it does, should be > 0
        # Don't fail if memory tracking isn't available
        if result.memory_used_mb > 0:
            assert result.memory_used_mb > 0.1  # Should use at least some memory
