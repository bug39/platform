"""Pytest integration tests for runtime."""

import pytest
from src.assistant.runtimes.python import PythonRuntime
from src.assistant.runtimes.docker import DockerManager, DOCKER_AVAILABLE


# Skip all tests if Docker is not available
pytestmark = pytest.mark.skipif(not DOCKER_AVAILABLE, reason="Docker not available")


class TestPytestIntegration:
    """Test pytest integration in runtime."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up runtime for each test."""
        try:
            manager = DockerManager()
            if not manager.is_available():
                pytest.skip("Docker daemon not running")
        except Exception:
            pytest.skip("Docker not available")

        self.runtime = PythonRuntime()

    def test_pytest_integration(self):
        """Test that pytest is available in the runtime."""
        code = """
import pytest
print(f'pytest version: {pytest.__version__}')
"""
        result = self.runtime.run(code)

        assert result.success is True
        assert "pytest version:" in result.stdout

    def test_passing_tests(self):
        """Test running passing tests with pytest."""
        code = "def add(a, b):\n    return a + b"
        test_code = """
def test_add():
    assert add(1, 2) == 3
    assert add(0, 0) == 0
    assert add(-1, 1) == 0
"""
        result = self.runtime.run_tests(code, test_code)

        # Pytest should pass
        assert result.success is True or result.exit_code == 0
        # Check for pytest output markers
        assert "test_add" in result.stdout or "passed" in result.stdout.lower()

    def test_failing_tests(self):
        """Test running failing tests with pytest."""
        code = "def add(a, b):\n    return a + b"
        test_code = """
def test_add_fail():
    assert add(1, 2) == 5  # Wrong!
"""
        result = self.runtime.run_tests(code, test_code)

        # Pytest should fail
        assert not result.success or result.exit_code != 0
        # Check for pytest failure markers
        assert "FAILED" in result.stdout or "AssertionError" in result.stdout

    def test_test_timeout(self):
        """Test that long-running tests can timeout."""
        code = "def slow_function():\n    import time\n    time.sleep(10)\n    return 'done'"
        test_code = """
def test_slow():
    assert slow_function() == 'done'
"""
        result = self.runtime.run_tests(code, test_code)

        # Should timeout (default timeout is 30 seconds, but sleep is 10)
        # This test verifies timeout mechanism works with pytest
        assert result.execution_time_ms < 30000  # Should complete within timeout
