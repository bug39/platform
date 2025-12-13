"""Tests for FixTool."""

import pytest
from unittest.mock import patch
from src.assistant.tools.fix import FixTool
from src.assistant.utils.validation import MAX_CODE_LENGTH


class TestFixTool:
    """Test FixTool functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.tool = FixTool()

    def test_fix_syntax_error(self):
        """Test fixing code with syntax error."""
        with patch('src.assistant.tools.fix.call_llm') as mock_llm, \
             patch('src.assistant.tools.fix.extract_and_validate_code') as mock_extract:

            broken_code = "def add(a, b\n    return a + b"
            error_msg = "SyntaxError: invalid syntax"
            fixed_code = "def add(a, b):\n    return a + b"

            mock_llm.return_value = f"Fixed the missing colon:\n```python\n{fixed_code}\n```"
            mock_extract.return_value = (fixed_code, True)

            result = self.tool.execute(broken_code, error_msg)

            assert "Fixed code:" in result
            assert "def add(a, b):" in result
            mock_llm.assert_called_once()

    def test_fix_runtime_error(self):
        """Test fixing code with runtime error."""
        with patch('src.assistant.tools.fix.call_llm') as mock_llm, \
             patch('src.assistant.tools.fix.extract_and_validate_code') as mock_extract:

            broken_code = "def divide(a, b):\n    return a / b"
            error_msg = "ZeroDivisionError: division by zero"
            fixed_code = "def divide(a, b):\n    if b == 0:\n        return None\n    return a / b"

            mock_llm.return_value = f"Added zero check:\n```python\n{fixed_code}\n```"
            mock_extract.return_value = (fixed_code, True)

            result = self.tool.execute(broken_code, error_msg)

            assert "Fixed code:" in result
            assert "if b == 0:" in result

    def test_fix_empty_code(self):
        """Test that empty code is rejected."""
        result = self.tool.execute("", "Some error")

        assert "Error:" in result
        assert "cannot be empty" in result.lower()

    def test_fix_empty_error(self):
        """Test that empty error message is rejected."""
        result = self.tool.execute("def test(): pass", "")

        assert "Error:" in result
        assert "cannot be empty" in result.lower()

    def test_fix_code_too_long(self):
        """Test that excessively long code is rejected."""
        huge_code = "x = 1\n" * 30000  # Exceeds MAX_CODE_LENGTH
        result = self.tool.execute(huge_code, "Some error")

        assert "Error:" in result
        assert "too long" in result.lower()

    def test_fix_syntax_validation(self):
        """Test that fixed code with syntax errors is flagged."""
        with patch('src.assistant.tools.fix.call_llm') as mock_llm, \
             patch('src.assistant.tools.fix.extract_and_validate_code') as mock_extract:

            broken_code = "def test():\n    print('test'"
            error_msg = "SyntaxError: EOL while scanning string literal"
            still_broken = "def test():\n    print('test"  # Still missing quote

            mock_llm.return_value = f"```python\n{still_broken}\n```"
            mock_extract.return_value = (still_broken, False)  # is_valid = False

            result = self.tool.execute(broken_code, error_msg)

            assert "syntax errors" in result.lower()

    def test_fix_llm_failure(self):
        """Test that LLM failures are handled gracefully."""
        with patch('src.assistant.tools.fix.call_llm') as mock_llm:

            # Mock LLM raising an exception
            mock_llm.side_effect = Exception("Model unavailable")

            code = "def test(): pass"
            error = "Some error"
            result = self.tool.execute(code, error)

            assert "Error fixing code:" in result
            assert "Model unavailable" in result
