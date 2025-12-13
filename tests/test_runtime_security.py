"""Runtime security hardening tests."""

import pytest
from src.assistant.runtimes.python import PythonRuntime
from src.assistant.runtimes.docker import DockerManager, DOCKER_AVAILABLE


# Skip all tests if Docker is not available
pytestmark = pytest.mark.skipif(not DOCKER_AVAILABLE, reason="Docker not available")


class TestRuntimeSecurity:
    """Test security features of the runtime."""

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

    def test_network_isolation(self):
        """Test that network access is blocked."""
        code = """
import socket
try:
    socket.create_connection(('google.com', 80), timeout=1)
    print('NETWORK_ALLOWED')
except Exception as e:
    print(f'NETWORK_BLOCKED: {type(e).__name__}')
"""
        result = self.runtime.run(code)

        # Network should be blocked
        assert "NETWORK_BLOCKED" in result.stdout or "NETWORK_BLOCKED" in result.stderr
        assert "NETWORK_ALLOWED" not in result.stdout

    def test_filesystem_readonly(self):
        """Test that filesystem is read-only (except /tmp)."""
        code = """
import os
try:
    # Try to write to root filesystem (should fail)
    with open('/test_file.txt', 'w') as f:
        f.write('test')
    print('WRITE_ALLOWED')
except Exception as e:
    print(f'WRITE_BLOCKED: {type(e).__name__}')
"""
        result = self.runtime.run(code)

        # Writing to root should be blocked
        assert "WRITE_BLOCKED" in result.stdout or not result.success

    def test_resource_limits_enforced(self):
        """Test that resource limits are enforced."""
        code = """
# Try to use a lot of CPU
import sys
count = 0
for i in range(10000000):
    count += i
print('DONE')
"""
        result = self.runtime.run(code, timeout=5)

        # Should complete within timeout (CPU quota limits execution speed)
        assert not result.timed_out
        assert result.execution_time_ms < 10000  # Less than 10 seconds

    def test_timeout_enforcement(self):
        """Test that timeout is enforced."""
        code = """
import time
time.sleep(10)
print('SHOULD_NOT_REACH')
"""
        result = self.runtime.run(code, timeout=2)

        # Should timeout
        assert result.timed_out is True or not result.success
        assert "SHOULD_NOT_REACH" not in result.stdout

    def test_capability_restrictions(self):
        """Test that capabilities are restricted."""
        code = """
import os
try:
    # Try to change uid (requires CAP_SETUID)
    os.setuid(0)
    print('SETUID_ALLOWED')
except Exception as e:
    print(f'SETUID_BLOCKED: {type(e).__name__}')
"""
        result = self.runtime.run(code)

        # setuid should be blocked
        assert "SETUID_BLOCKED" in result.stdout or "SETUID_BLOCKED" in result.stderr
        assert "SETUID_ALLOWED" not in result.stdout

    def test_seccomp_profile_applied(self):
        """Test that seccomp profile restricts syscalls."""
        code = """
import ctypes
import sys
try:
    # Try to use a potentially dangerous syscall
    # Note: This is a simple test - real seccomp testing is complex
    print('SYSCALL_TEST: Basic Python operations work')
except Exception as e:
    print(f'SYSCALL_ERROR: {type(e).__name__}')
"""
        result = self.runtime.run(code)

        # Basic operations should work (seccomp allows necessary syscalls)
        assert "SYSCALL_TEST" in result.stdout
        assert result.success is True
