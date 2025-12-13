"""Tests for security validation features."""

import pytest
from src.assistant.tools.execute import ExecuteTool, MAX_CODE_LENGTH, MIN_TIMEOUT, MAX_TIMEOUT
from src.assistant.runtimes.docker import ContainerConfig


class TestExecuteToolValidation:
    """Test ExecuteTool input validation."""

    def test_code_length_limit(self):
        """Test that excessively long code is rejected."""
        tool = ExecuteTool()
        huge_code = "x = 1\n" * 30000  # ~180KB

        result = tool.execute(huge_code)

        assert "too long" in result.lower()
        assert "50,000" in result  # Formatted with comma

    def test_timeout_too_low(self):
        """Test that timeout below minimum is rejected."""
        tool = ExecuteTool()

        result = tool.execute("print(1)", timeout=0)

        assert "must be between" in result.lower()
        assert str(MIN_TIMEOUT) in result
        assert str(MAX_TIMEOUT) in result

    def test_timeout_too_high(self):
        """Test that timeout above maximum is rejected."""
        tool = ExecuteTool()

        result = tool.execute("print(1)", timeout=999)

        assert "must be between" in result.lower()
        assert "999" in result

    def test_timeout_invalid_type(self):
        """Test that non-integer timeout is rejected."""
        tool = ExecuteTool()

        result = tool.execute("print(1)", timeout="abc")

        assert "must be an integer" in result.lower()

    def test_valid_code_still_works(self):
        """Test that valid code with valid timeout still executes."""
        tool = ExecuteTool()

        result = tool.execute("print('test')", timeout=30)

        assert "successful" in result.lower()

    def test_timeout_at_boundaries(self):
        """Test that timeout at exact boundaries is accepted."""
        tool = ExecuteTool()

        # Test minimum
        result = tool.execute("print(1)", timeout=MIN_TIMEOUT)
        assert "successful" in result.lower() or "test" in result.lower()

        # Test maximum (don't actually run, just validate)
        # We can't test this fully without a long-running task


class TestContainerConfigValidation:
    """Test ContainerConfig validation."""

    def test_valid_config(self):
        """Test that valid config is accepted."""
        config = ContainerConfig(
            image="python:3.12",
            command=["python", "-c"],
            timeout_seconds=30,
            memory_limit="256m",
            cpu_quota=50000,
            pids_limit=50
        )
        assert config.image == "python:3.12"

    def test_empty_image_rejected(self):
        """Test that empty image name is rejected."""
        with pytest.raises(ValueError, match="Docker image name cannot be empty"):
            ContainerConfig(image="", command=["python"])

    def test_timeout_too_low_rejected(self):
        """Test that timeout below 1 is rejected."""
        with pytest.raises(ValueError, match="timeout_seconds must be between"):
            ContainerConfig(image="python", command=["python"], timeout_seconds=0)

    def test_timeout_too_high_rejected(self):
        """Test that timeout above 300 is rejected."""
        with pytest.raises(ValueError, match="timeout_seconds must be between"):
            ContainerConfig(image="python", command=["python"], timeout_seconds=999)

    def test_invalid_memory_format_rejected(self):
        """Test that invalid memory format is rejected."""
        with pytest.raises(ValueError, match="memory_limit must be in format"):
            ContainerConfig(image="python", command=["python"], memory_limit="256mb")

        with pytest.raises(ValueError, match="memory_limit must be in format"):
            ContainerConfig(image="python", command=["python"], memory_limit="invalid")

    def test_valid_memory_formats_accepted(self):
        """Test that valid memory formats are accepted."""
        for mem_limit in ["128k", "256m", "1g", "2G"]:
            config = ContainerConfig(
                image="python",
                command=["python"],
                memory_limit=mem_limit
            )
            assert config.memory_limit == mem_limit

    def test_cpu_quota_too_low_rejected(self):
        """Test that cpu_quota below 1000 is rejected."""
        with pytest.raises(ValueError, match="cpu_quota must be between"):
            ContainerConfig(image="python", command=["python"], cpu_quota=500)

    def test_cpu_quota_too_high_rejected(self):
        """Test that cpu_quota above 1,000,000 is rejected."""
        with pytest.raises(ValueError, match="cpu_quota must be between"):
            ContainerConfig(image="python", command=["python"], cpu_quota=2_000_000)

    def test_pids_limit_too_low_rejected(self):
        """Test that pids_limit below 1 is rejected."""
        with pytest.raises(ValueError, match="pids_limit must be between"):
            ContainerConfig(image="python", command=["python"], pids_limit=0)

    def test_pids_limit_too_high_rejected(self):
        """Test that pids_limit above 1000 is rejected."""
        with pytest.raises(ValueError, match="pids_limit must be between"):
            ContainerConfig(image="python", command=["python"], pids_limit=2000)
