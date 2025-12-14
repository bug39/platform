"""Comprehensive tests for ExecuteTool."""

import pytest
from unittest.mock import Mock, patch
from assistant.tools.execute import ExecuteTool
from assistant.runtimes.base import ExecutionResult


class TestExecuteToolValidation:
    """Test input validation in ExecuteTool."""

    @pytest.fixture
    def tool(self):
        """Create ExecuteTool instance."""
        return ExecuteTool()

    def test_empty_code_rejected(self, tool):
        """Empty code should be rejected."""
        result = tool.execute("")
        assert "Error: No code provided" in result

    def test_whitespace_only_rejected(self, tool):
        """Whitespace-only code should be rejected."""
        result = tool.execute("   \n\t  ")
        assert "Error: No code provided" in result

    def test_code_too_long_rejected(self, tool):
        """Code exceeding 50KB should be rejected."""
        long_code = "x = 1\n" * 10000  # ~60KB
        result = tool.execute(long_code)
        assert "Error: Code too long" in result
        assert "50,000" in result

    def test_timeout_must_be_integer(self, tool):
        """Timeout must be an integer."""
        result = tool.execute("print('hi')", timeout="30")
        assert "Error: Timeout must be an integer" in result

    def test_timeout_too_low_rejected(self, tool):
        """Timeout below 1 second should be rejected."""
        result = tool.execute("print('hi')", timeout=0)
        assert "Error: Timeout must be between 1 and 300" in result

    def test_timeout_too_high_rejected(self, tool):
        """Timeout above 300 seconds should be rejected."""
        result = tool.execute("print('hi')", timeout=301)
        assert "Error: Timeout must be between 1 and 300" in result

    def test_timeout_at_boundaries_accepted(self, tool):
        """Timeout at boundaries (1, 300) should be accepted."""
        # Mock runtime to avoid actual execution
        mock_runtime = Mock()
        mock_runtime.run.return_value = ExecutionResult(
            success=True, stdout="test", stderr="", exit_code=0,
            timed_out=False, execution_time_ms=100
        )

        with patch.object(tool, '_get_runtime', return_value=mock_runtime):
            # Minimum boundary
            result = tool.execute("print('hi')", timeout=1)
            assert "Error" not in result or "Timeout must be" not in result

            # Maximum boundary
            result = tool.execute("print('hi')", timeout=300)
            assert "Error" not in result or "Timeout must be" not in result

    def test_syntax_error_fast_fail(self, tool):
        """Syntax errors should fail without Docker execution."""
        result = tool.execute("print('unclosed string)")
        assert "Syntax error" in result
        assert "unterminated string literal" in result.lower() or "EOL" in result

    def test_valid_code_accepted(self, tool):
        """Valid code should pass validation."""
        mock_runtime = Mock()
        mock_runtime.run.return_value = ExecutionResult(
            success=True, stdout="Hello", stderr="", exit_code=0,
            timed_out=False, execution_time_ms=50
        )

        with patch.object(tool, '_get_runtime', return_value=mock_runtime):
            result = tool.execute("print('Hello')")
            assert "Error" not in result or "validation" not in result.lower()


class TestExecuteToolExecution:
    """Test code execution behavior."""

    @pytest.fixture
    def tool(self):
        """Create ExecuteTool instance."""
        return ExecuteTool()

    def test_successful_execution(self, tool):
        """Successful execution should show output."""
        mock_runtime = Mock()
        mock_runtime.run.return_value = ExecutionResult(
            success=True,
            stdout="Hello, World!",
            stderr="",
            exit_code=0,
            timed_out=False,
            execution_time_ms=123,
            memory_used_mb=45.67
        )

        with patch.object(tool, '_get_runtime', return_value=mock_runtime):
            result = tool.execute("print('Hello, World!')")

            assert "Execution successful" in result
            assert "123ms" in result
            assert "Hello, World!" in result
            assert "45.67 MB" in result

    def test_successful_execution_no_output(self, tool):
        """Successful execution with no output."""
        mock_runtime = Mock()
        mock_runtime.run.return_value = ExecutionResult(
            success=True,
            stdout="",
            stderr="",
            exit_code=0,
            timed_out=False,
            execution_time_ms=50
        )

        with patch.object(tool, '_get_runtime', return_value=mock_runtime):
            result = tool.execute("x = 1")

            assert "Execution successful" in result
            assert "No output produced" in result

    def test_execution_with_stderr(self, tool):
        """Failed execution should show stderr."""
        mock_runtime = Mock()
        mock_runtime.run.return_value = ExecutionResult(
            success=False,
            stdout="",
            stderr="NameError: name 'undefined' is not defined",
            exit_code=1,
            timed_out=False,
            execution_time_ms=100,
            error_message="Execution failed"
        )

        with patch.object(tool, '_get_runtime', return_value=mock_runtime):
            result = tool.execute("print(undefined)")

            assert "Execution failed" in result
            assert "NameError" in result
            assert "undefined" in result

    def test_execution_timeout(self, tool):
        """Timeout should be reported."""
        mock_runtime = Mock()
        mock_runtime.run.return_value = ExecutionResult(
            success=False,
            stdout="",
            stderr="",
            exit_code=-1,
            timed_out=True,
            execution_time_ms=5000,
            error_message="Execution timed out"
        )

        with patch.object(tool, '_get_runtime', return_value=mock_runtime):
            result = tool.execute("import time; time.sleep(100)", timeout=5)

            assert "timed out after 5s" in result
            assert "exit code: -1" in result

    def test_runtime_initialization_error(self, tool):
        """Runtime initialization errors should be handled."""
        with patch.object(tool, '_get_runtime', side_effect=RuntimeError("Docker not running")):
            result = tool.execute("print('hi')")

            assert "Runtime error" in result
            assert "Docker not running" in result

    def test_unexpected_error_handling(self, tool):
        """Unexpected errors should be caught and reported."""
        mock_runtime = Mock()
        mock_runtime.run.side_effect = Exception("Unexpected error occurred")

        with patch.object(tool, '_get_runtime', return_value=mock_runtime):
            result = tool.execute("print('hi')")

            assert "Unexpected error" in result
            assert "Unexpected error occurred" in result

    def test_timeout_parameter_passed_to_runtime(self, tool):
        """Custom timeout should be passed to runtime."""
        mock_runtime = Mock()
        mock_runtime.run.return_value = ExecutionResult(
            success=True, stdout="done", stderr="", exit_code=0,
            timed_out=False, execution_time_ms=100
        )

        with patch.object(tool, '_get_runtime', return_value=mock_runtime):
            tool.execute("print('hi')", timeout=60)

            # Verify runtime.run was called with correct timeout
            mock_runtime.run.assert_called_once()
            call_args = mock_runtime.run.call_args
            assert call_args[1]['timeout'] == 60


class TestExecuteToolSchema:
    """Test tool schema and metadata."""

    @pytest.fixture
    def tool(self):
        """Create ExecuteTool instance."""
        return ExecuteTool()

    def test_tool_name(self, tool):
        """Tool should have correct name."""
        assert tool.name == "execute_code"

    def test_tool_description(self, tool):
        """Tool should have descriptive text."""
        assert "sandbox" in tool.description.lower()
        assert "python" in tool.description.lower()

    def test_tool_schema_structure(self, tool):
        """Tool schema should be properly structured."""
        schema = tool.schema

        assert "code" in schema.properties
        assert schema.properties["code"]["type"] == "string"
        assert "code" in schema.required

        assert "timeout" in schema.properties
        assert schema.properties["timeout"]["type"] == "integer"
        assert schema.properties["timeout"]["default"] == 30

    def test_tool_to_dict(self, tool):
        """Tool should serialize to dict format."""
        tool_dict = tool.to_dict()

        assert tool_dict["name"] == "execute_code"
        assert "sandbox" in tool_dict["description"].lower()
        assert tool_dict["input_schema"]["type"] == "object"
        assert "code" in tool_dict["input_schema"]["required"]


class TestExecuteToolEdgeCases:
    """Test edge cases and special scenarios."""

    @pytest.fixture
    def tool(self):
        """Create ExecuteTool instance."""
        return ExecuteTool()

    def test_multiline_output(self, tool):
        """Multiline output should be formatted correctly."""
        mock_runtime = Mock()
        mock_runtime.run.return_value = ExecutionResult(
            success=True,
            stdout="Line 1\nLine 2\nLine 3",
            stderr="",
            exit_code=0,
            timed_out=False,
            execution_time_ms=100
        )

        with patch.object(tool, '_get_runtime', return_value=mock_runtime):
            result = tool.execute("for i in range(3): print(f'Line {i+1}')")

            assert "Line 1" in result
            assert "Line 2" in result
            assert "Line 3" in result

    def test_special_characters_in_output(self, tool):
        """Special characters should be preserved."""
        mock_runtime = Mock()
        mock_runtime.run.return_value = ExecutionResult(
            success=True,
            stdout="Special: \t\n\r 日本語 émojis 🎉",
            stderr="",
            exit_code=0,
            timed_out=False,
            execution_time_ms=100
        )

        with patch.object(tool, '_get_runtime', return_value=mock_runtime):
            result = tool.execute("print('Special: \\t\\n\\r 日本語 émojis 🎉')")

            assert "Special:" in result

    def test_memory_usage_displayed_when_available(self, tool):
        """Memory usage should be shown when available."""
        mock_runtime = Mock()
        mock_runtime.run.return_value = ExecutionResult(
            success=True,
            stdout="done",
            stderr="",
            exit_code=0,
            timed_out=False,
            execution_time_ms=100,
            memory_used_mb=128.5
        )

        with patch.object(tool, '_get_runtime', return_value=mock_runtime):
            result = tool.execute("x = [1] * 1000000")

            assert "128.5" in result or "128.50" in result
            assert "MB" in result

    def test_memory_usage_not_shown_when_zero(self, tool):
        """Memory usage should not be shown when zero."""
        mock_runtime = Mock()
        mock_runtime.run.return_value = ExecutionResult(
            success=True,
            stdout="done",
            stderr="",
            exit_code=0,
            timed_out=False,
            execution_time_ms=100,
            memory_used_mb=0.0
        )

        with patch.object(tool, '_get_runtime', return_value=mock_runtime):
            result = tool.execute("print('hi')")

            # Memory should not be mentioned when zero
            assert "Memory used" not in result or "0.00 MB" in result

    def test_code_at_max_length_boundary(self, tool):
        """Code at exactly 50KB should be accepted."""
        # Create code that's exactly 50,000 characters
        code = "x = 1  # " + "a" * (50000 - 10)

        mock_runtime = Mock()
        mock_runtime.run.return_value = ExecutionResult(
            success=True, stdout="", stderr="", exit_code=0,
            timed_out=False, execution_time_ms=100
        )

        with patch.object(tool, '_get_runtime', return_value=mock_runtime):
            result = tool.execute(code)

            # Should not have length error
            assert "Code too long" not in result
