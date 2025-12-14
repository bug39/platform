"""Runtime error handling tests."""

import pytest
from src.assistant.config import SandboxConfig
from src.assistant.runtimes.python import PythonRuntime
from src.assistant.runtimes.docker import DockerManager, DOCKER_AVAILABLE


# Skip all tests if Docker is not available
pytestmark = pytest.mark.skipif(not DOCKER_AVAILABLE, reason="Docker not available")


class TestRuntimeErrorHandling:
    """Test runtime error handling."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up runtime for each test."""
        try:
            manager = DockerManager(SandboxConfig())
            if not manager.is_available():
                pytest.skip("Docker daemon not running")
        except Exception:
            pytest.skip("Docker not available")

        self.runtime = PythonRuntime()

    def test_syntax_error_handling(self):
        """Test that syntax errors are captured."""
        code = "def broken(\n    print('missing paren')"

        result = self.runtime.run(code)

        assert result.success is False
        assert result.exit_code != 0
        assert "SyntaxError" in result.stderr or "invalid syntax" in result.stderr

    def test_runtime_error_handling(self):
        """Test that runtime errors are captured."""
        code = """
def divide_by_zero():
    return 1 / 0

divide_by_zero()
"""
        result = self.runtime.run(code)

        assert result.success is False
        assert result.exit_code != 0
        assert "ZeroDivisionError" in result.stderr or "division by zero" in result.stderr

    def test_timeout_error(self):
        """Test that execution timeout is handled."""
        code = """
import time
while True:
    time.sleep(1)
"""
        result = self.runtime.run(code, timeout=2)

        # Should either timeout or be killed
        assert result.timed_out is True or not result.success
        assert result.execution_time_ms >= 2000  # Should run for at least 2 seconds

    def test_memory_limit_error(self):
        """Test that memory limit is enforced."""
        code = """
# Try to allocate way more memory than allowed (256MB limit)
try:
    huge_list = [0] * (1024 * 1024 * 1024)  # Try to allocate 8GB
    print('MEMORY_ALLOCATED')
except MemoryError:
    print('MEMORY_LIMITED')
"""
        result = self.runtime.run(code)

        # Should either hit memory limit or complete
        # (Docker may kill the process before Python raises MemoryError)
        assert "MEMORY_LIMITED" in result.stdout or not result.success or result.exit_code != 0

    def test_invalid_docker_image(self):
        """Test that invalid Docker image is handled."""
        from src.assistant.runtimes.docker import DockerRuntime
        from src.assistant.runtimes.base import RuntimeConfig

        # Create runtime with non-existent image
        config = RuntimeConfig(
            language="test",
            image="nonexistent-image-12345",
            command=["python", "-c"],
            file_extension=".py"
        )

        runtime = DockerRuntime(config)

        # Try to run code - should fail gracefully
        code = "print('test')"
        result = runtime.run(code)

        # Should fail (image not found)
        assert result.success is False
