"""Tests for ExplainTool."""

import pytest
from unittest.mock import patch
from src.assistant.tools.explain import ExplainTool
from src.assistant.utils.validation import MAX_CODE_LENGTH


class TestExplainTool:
    """Test ExplainTool functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.tool = ExplainTool()

    def test_explain_simple_code(self):
        """Test explaining simple code."""
        with patch('src.assistant.tools.explain.call_llm') as mock_llm:

            mock_llm.return_value = "This function adds two numbers together and returns the sum."

            code = "def add(a, b):\n    return a + b"
            result = self.tool.execute(code)

            assert "adds two numbers" in result
            mock_llm.assert_called_once()

    def test_explain_complex_code(self):
        """Test explaining more complex code."""
        with patch('src.assistant.tools.explain.call_llm') as mock_llm:

            mock_llm.return_value = "This function implements the Fibonacci sequence using recursion."

            code = """def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)"""

            result = self.tool.execute(code)

            assert "Fibonacci" in result
            assert "recursion" in result

    def test_explain_empty_code(self):
        """Test that empty code is rejected."""
        result = self.tool.execute("")

        assert "Error:" in result
        assert "cannot be empty" in result.lower()

    def test_explain_invalid_syntax(self):
        """Test that code with syntax errors can still be explained."""
        with patch('src.assistant.tools.explain.call_llm') as mock_llm:

            mock_llm.return_value = "This code has a syntax error - missing closing parenthesis."

            # Code with syntax error
            code = "def broken(\n    print('test')"
            result = self.tool.execute(code)

            # Should still attempt to explain (not validate syntax)
            assert "syntax error" in result or "parenthesis" in result

    def test_explain_llm_failure(self):
        """Test that LLM failures are handled gracefully."""
        with patch('src.assistant.tools.explain.call_llm') as mock_llm:

            # Mock LLM raising an exception
            mock_llm.side_effect = Exception("Connection timeout")

            code = "def test():\n    pass"
            result = self.tool.execute(code)

            assert "Error explaining code:" in result
            assert "Connection timeout" in result
