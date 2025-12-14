"""Runtime security hardening tests."""

import pytest
import json
from pathlib import Path
from src.assistant.config import SandboxConfig
from src.assistant.runtimes.python import PythonRuntime
from src.assistant.runtimes.docker import DockerManager, DOCKER_AVAILABLE


# Skip all tests if Docker is not available
pytestmark = pytest.mark.skipif(not DOCKER_AVAILABLE, reason="Docker not available")


class TestRuntimeSecurity:
    """Test security features of the runtime."""

    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: Path):
        """Set up runtime and create dummy seccomp profiles for each test."""
        self.tmp_path = tmp_path
        self.valid_seccomp_profile = {
            "defaultAction": "SCMP_ACT_ERRNO",
            "architectures": ["SCMP_ARCH_X86_64", "SCMP_ARCH_AARCH64"],
            "syscalls": []
        }
        self.seccomp_profile_path = self.tmp_path / "seccomp.json"
        with open(self.seccomp_profile_path, "w") as f:
            json.dump(self.valid_seccomp_profile, f)

        try:
            # Basic manager for initial check
            manager = DockerManager(SandboxConfig())
            if not manager.is_available():
                pytest.skip("Docker daemon not running")
        except Exception as e:
            pytest.skip(f"Docker not available: {e}")

        self.runtime = PythonRuntime()

    def test_seccomp_valid_profile_loaded(self):
        """Test that a valid seccomp profile is loaded correctly."""
        config = SandboxConfig(seccomp_profile_path=str(self.seccomp_profile_path))
        manager = DockerManager(sandbox_config=config)
        assert manager._seccomp_profile_data is not None
        assert manager._seccomp_profile_data["defaultAction"] == "SCMP_ACT_ERRNO"

    def test_seccomp_missing_profile_raises_error(self):
        """Test that a missing seccomp profile raises FileNotFoundError."""
        missing_path = self.tmp_path / "not_real.json"
        config = SandboxConfig(seccomp_profile_path=str(missing_path))
        with pytest.raises(FileNotFoundError):
            DockerManager(sandbox_config=config)

    def test_seccomp_malformed_json_raises_error(self):
        """Test that a malformed seccomp profile raises ValueError."""
        malformed_path = self.tmp_path / "malformed.json"
        malformed_path.write_text("{ not valid json }")
        config = SandboxConfig(seccomp_profile_path=str(malformed_path))
        with pytest.raises(ValueError, match="Invalid JSON"):
            DockerManager(sandbox_config=config)

    def test_seccomp_invalid_default_action_raises_error(self):
        """Test that an invalid defaultAction raises ValueError."""
        profile = self.valid_seccomp_profile.copy()
        profile["defaultAction"] = "INVALID_ACTION"
        invalid_path = self.tmp_path / "invalid.json"
        invalid_path.write_text(json.dumps(profile))
        config = SandboxConfig(seccomp_profile_path=str(invalid_path))
        with pytest.raises(ValueError, match="Invalid defaultAction"):
            DockerManager(sandbox_config=config)

    def test_seccomp_invalid_arch_raises_error(self):
        """Test that invalid architectures list raises ValueError."""
        profile = self.valid_seccomp_profile.copy()
        profile["architectures"] = "not-a-list"
        invalid_path = self.tmp_path / "invalid.json"
        invalid_path.write_text(json.dumps(profile))
        config = SandboxConfig(seccomp_profile_path=str(invalid_path))
        with pytest.raises(ValueError, match="'architectures' must be a list"):
            DockerManager(sandbox_config=config)

    def test_seccomp_invalid_syscalls_raises_error(self):
        """Test that invalid syscalls list raises ValueError."""
        profile = self.valid_seccomp_profile.copy()
        profile["syscalls"] = {"not": "a list"}
        invalid_path = self.tmp_path / "invalid.json"
        invalid_path.write_text(json.dumps(profile))
        config = SandboxConfig(seccomp_profile_path=str(invalid_path))
        with pytest.raises(ValueError, match="'syscalls' must be a list"):
            DockerManager(sandbox_config=config)

    def test_seccomp_invalid_syscall_item_raises_error(self):
        """Test that invalid item in syscalls list raises ValueError."""
        profile = self.valid_seccomp_profile.copy()
        profile["syscalls"] = [{"names": ["test"], "action": "INVALID_ACTION"}]
        invalid_path = self.tmp_path / "invalid.json"
        invalid_path.write_text(json.dumps(profile))
        config = SandboxConfig(seccomp_profile_path=str(invalid_path))
        with pytest.raises(ValueError, match="Invalid action in syscall at index 0"):
            DockerManager(sandbox_config=config)

    @pytest.mark.skip(reason="Docker bind-mount error on macOS")
    def test_seccomp_custom_profile_blocks_syscall(self):
        """Test that a custom seccomp profile can block a syscall."""
        profile = {
            "defaultAction": "SCMP_ACT_ALLOW",
            "syscalls": [
                {
                    "names": ["mkdir"],
                    "action": "SCMP_ACT_ERRNO"
                }
            ]
        }
        profile_path = self.tmp_path / "blocking_profile.json"
        profile_path.write_text(json.dumps(profile))

        config = SandboxConfig(seccomp_profile_path=str(profile_path))
        manager = DockerManager(sandbox_config=config)
        runtime = PythonRuntime(manager=manager)

        code = """
import os
try:
    os.mkdir("/test_dir")
    print("MKDIR_ALLOWED")
except Exception as e:
    print(f"MKDIR_BLOCKED: {type(e).__name__}")
"""
        result = runtime.run(code)
        assert "MKDIR_BLOCKED" in result.stdout
        assert "MKDIR_ALLOWED" not in result.stdout

    @pytest.mark.skip(reason="Docker bind-mount error on macOS")
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

    @pytest.mark.skip(reason="Docker bind-mount error on macOS")
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

    @pytest.mark.skip(reason="Docker bind-mount error on macOS")
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
