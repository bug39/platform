"""Tests for validation helper utilities."""

import pytest
from src.assistant.utils.validation import (
    validate_non_empty,
    validate_length,
    validate_string_input,
    extract_and_validate_code,
    sanitize_error_message,
    MAX_STRING_LENGTH,
    MIN_DESCRIPTION_LENGTH,
)


class TestValidateNonEmpty:
    """Test validate_non_empty helper."""

    def test_valid_string(self):
        """Test that valid non-empty string passes."""
        validate_non_empty("hello", "test_field")  # Should not raise

    def test_empty_string_raises(self):
        """Test that empty string raises ValueError."""
        with pytest.raises(ValueError, match="test_field cannot be empty"):
            validate_non_empty("", "test_field")

    def test_whitespace_only_raises(self):
        """Test that whitespace-only string raises ValueError."""
        with pytest.raises(ValueError, match="test_field cannot be empty"):
            validate_non_empty("   ", "test_field")

    def test_none_raises(self):
        """Test that None raises ValueError."""
        with pytest.raises(ValueError, match="test_field cannot be empty"):
            validate_non_empty(None, "test_field")


class TestValidateLength:
    """Test validate_length helper."""

    def test_within_bounds(self):
        """Test that string within bounds passes."""
        validate_length("hello", max_length=10, field_name="test")

    def test_at_max_length(self):
        """Test that string at exact max length passes."""
        validate_length("hello", max_length=5, field_name="test")

    def test_exceeds_max_raises(self):
        """Test that string exceeding max raises ValueError."""
        with pytest.raises(ValueError, match="too long"):
            validate_length("hello world", max_length=5, field_name="test")

    def test_min_length_pass(self):
        """Test that string meeting min length passes."""
        validate_length("hello", max_length=10, field_name="test", min_length=3)

    def test_min_length_fail(self):
        """Test that string below min length raises ValueError."""
        with pytest.raises(ValueError, match="too short"):
            validate_length("hi", max_length=10, field_name="test", min_length=5)

    def test_formatted_numbers_in_message(self):
        """Test that error message includes formatted numbers."""
        with pytest.raises(ValueError) as exc_info:
            validate_length("x" * 100, max_length=50, field_name="test")

        assert "50" in str(exc_info.value)
        assert "100" in str(exc_info.value)


class TestValidateStringInput:
    """Test validate_string_input comprehensive helper."""

    def test_valid_input(self):
        """Test that valid input passes all checks."""
        validate_string_input("hello world", "test", max_length=100)

    def test_empty_not_allowed_by_default(self):
        """Test that empty strings are rejected by default."""
        with pytest.raises(ValueError, match="cannot be empty"):
            validate_string_input("", "test")

    def test_empty_allowed_when_specified(self):
        """Test that empty strings can be allowed."""
        validate_string_input("", "test", allow_empty=True, max_length=100)

    def test_length_validation(self):
        """Test that length validation is enforced."""
        with pytest.raises(ValueError, match="too long"):
            validate_string_input("x" * 1000, "test", max_length=100)

    def test_min_length_validation(self):
        """Test that min length validation works."""
        with pytest.raises(ValueError, match="too short"):
            validate_string_input("hi", "test", min_length=MIN_DESCRIPTION_LENGTH)

    def test_uses_default_max_length(self):
        """Test that default MAX_STRING_LENGTH is used."""
        # Should pass - under default limit
        validate_string_input("x" * 1000, "test")

        # Should fail - over default limit
        with pytest.raises(ValueError):
            validate_string_input("x" * (MAX_STRING_LENGTH + 1), "test")


class TestExtractAndValidateCode:
    """Test extract_and_validate_code helper."""

    def test_valid_code_block(self):
        """Test extraction of valid Python code."""
        text = "```python\nprint('hello')\n```"
        code, is_valid = extract_and_validate_code(text)

        assert code == "print('hello')"
        assert is_valid is True

    def test_invalid_syntax(self):
        """Test extraction of code with syntax errors."""
        text = "```python\nprint('unclosed\n```"
        code, is_valid = extract_and_validate_code(text)

        assert code is not None
        assert is_valid is False

    def test_no_code_block(self):
        """Test when no code block is found."""
        text = "Just some regular text"
        code, is_valid = extract_and_validate_code(text)

        assert code is None
        assert is_valid is False

    def test_multiple_code_blocks(self):
        """Test extraction when multiple blocks exist."""
        text = "```python\nx = 1\n```\nSome text\n```python\ny = 2\n```"
        code, is_valid = extract_and_validate_code(text)

        # Should extract first block
        assert code is not None
        assert "x = 1" in code


class TestSanitizeErrorMessage:
    """Test sanitize_error_message helper."""

    def test_file_not_found_error(self):
        """Test sanitization of FileNotFoundError."""
        error = FileNotFoundError("/secret/path/file.txt")
        message = sanitize_error_message(error, show_details=False)

        assert message == "The requested file was not found."
        assert "/secret/path" not in message

    def test_value_error(self):
        """Test sanitization of ValueError."""
        error = ValueError("invalid password")
        message = sanitize_error_message(error, show_details=False)

        assert message == "Invalid input provided."
        assert "password" not in message

    def test_show_details_mode(self):
        """Test that details are shown when requested."""
        error = ValueError("test error message")
        message = sanitize_error_message(error, show_details=True)

        assert "ValueError" in message
        assert "test error message" in message

    def test_unknown_error_type(self):
        """Test sanitization of unknown error types."""
        class CustomError(Exception):
            pass

        error = CustomError("custom message")
        message = sanitize_error_message(error, show_details=False)

        assert message == "An error occurred."
        assert "custom message" not in message

    def test_timeout_error(self):
        """Test sanitization of TimeoutError."""
        error = TimeoutError("Connection timed out after 30s")
        message = sanitize_error_message(error, show_details=False)

        assert message == "The operation timed out."
