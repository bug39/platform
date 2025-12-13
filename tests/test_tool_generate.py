"""Tests for GenerateTool."""

import pytest
from unittest.mock import patch, MagicMock
from src.assistant.tools.generate import GenerateTool
from src.assistant.utils.validation import MIN_DESCRIPTION_LENGTH, MAX_DESCRIPTION_LENGTH


class TestGenerateTool:
    """Test GenerateTool functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.tool = GenerateTool()

    def test_generate_simple_function(self):
        """Test generating a simple function."""
        with patch('src.assistant.tools.generate.call_llm') as mock_llm, \
             patch('src.assistant.tools.generate.extract_and_validate_code') as mock_extract:

            # Mock LLM response
            mock_llm.return_value = "```python\ndef add(a, b):\n    return a + b\n```"

            # Mock code extraction
            mock_extract.return_value = ("def add(a, b):\n    return a + b", True)

            result = self.tool.execute("Create a function that adds two numbers")

            assert "Generated code:" in result
            assert "def add(a, b):" in result
            mock_llm.assert_called_once()

    def test_generate_with_tests(self):
        """Test generating code with test cases."""
        with patch('src.assistant.tools.generate.call_llm') as mock_llm, \
             patch('src.assistant.tools.generate.extract_and_validate_code') as mock_extract:

            code_with_tests = """def multiply(a, b):
    return a * b

def test_multiply():
    assert multiply(2, 3) == 6"""

            mock_llm.return_value = f"```python\n{code_with_tests}\n```"
            mock_extract.return_value = (code_with_tests, True)

            result = self.tool.execute("Create a multiply function", include_tests=True)

            assert "Generated code:" in result
            assert "def multiply(a, b):" in result
            assert "def test_multiply():" in result

    def test_generate_empty_description(self):
        """Test that empty description is rejected."""
        result = self.tool.execute("")

        assert "Error:" in result
        assert "cannot be empty" in result.lower()

    def test_generate_description_too_short(self):
        """Test that description below minimum length is rejected."""
        short_desc = "a" * (MIN_DESCRIPTION_LENGTH - 1)
        result = self.tool.execute(short_desc)

        assert "Error:" in result
        assert "too short" in result.lower()

    def test_generate_syntax_validation(self):
        """Test that generated code with syntax errors is flagged."""
        with patch('src.assistant.tools.generate.call_llm') as mock_llm, \
             patch('src.assistant.tools.generate.extract_and_validate_code') as mock_extract:

            # Mock code with syntax error
            invalid_code = "def broken(\n    print('unclosed"
            mock_llm.return_value = f"```python\n{invalid_code}\n```"
            mock_extract.return_value = (invalid_code, False)  # is_valid = False

            result = self.tool.execute("Create a function")

            assert "syntax errors" in result.lower()

    def test_generate_llm_failure(self):
        """Test that LLM failures are handled gracefully."""
        with patch('src.assistant.tools.generate.call_llm') as mock_llm:

            # Mock LLM raising an exception
            mock_llm.side_effect = Exception("API rate limit exceeded")

            result = self.tool.execute("Create a function")

            assert "Error generating code:" in result
            assert "API rate limit" in result
