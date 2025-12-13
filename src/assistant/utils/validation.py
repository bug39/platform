"""Validation utilities for input validation and sanitization."""

from typing import Optional, Tuple
from ..providers import get_provider
from ..providers.base import Message


# Validation constants
MAX_STRING_LENGTH = 50_000  # 50KB for general string inputs
MAX_CODE_LENGTH = 50_000  # 50KB for code inputs
MAX_DESCRIPTION_LENGTH = 10_000  # 10KB for descriptions
MIN_DESCRIPTION_LENGTH = 10  # Minimum description length


def validate_non_empty(value: str, field_name: str) -> None:
    """
    Validate that a string value is not empty or whitespace-only.

    Args:
        value: The string value to validate
        field_name: Name of the field (for error messages)

    Raises:
        ValueError: If value is None, empty, or only whitespace
    """
    if not value or not value.strip():
        raise ValueError(f"{field_name} cannot be empty")


def validate_length(
    value: str,
    max_length: int,
    field_name: str,
    min_length: Optional[int] = None
) -> None:
    """
    Validate that a string length is within bounds.

    Args:
        value: The string value to validate
        max_length: Maximum allowed length
        field_name: Name of the field (for error messages)
        min_length: Optional minimum length

    Raises:
        ValueError: If value length is outside bounds
    """
    actual_length = len(value)

    if min_length is not None and actual_length < min_length:
        raise ValueError(
            f"{field_name} too short. Minimum: {min_length} characters "
            f"(got {actual_length})"
        )

    if actual_length > max_length:
        raise ValueError(
            f"{field_name} too long. Maximum: {max_length:,} characters "
            f"(got {actual_length:,})"
        )


def validate_string_input(
    value: str,
    field_name: str,
    max_length: int = MAX_STRING_LENGTH,
    min_length: Optional[int] = None,
    allow_empty: bool = False
) -> None:
    """
    Comprehensive string validation combining non-empty and length checks.

    Args:
        value: The string value to validate
        field_name: Name of the field (for error messages)
        max_length: Maximum allowed length
        min_length: Optional minimum length
        allow_empty: If True, allows empty strings

    Raises:
        ValueError: If validation fails
    """
    if not allow_empty:
        validate_non_empty(value, field_name)

    validate_length(value, max_length, field_name, min_length)


def call_llm(prompt: str, system_prompt: Optional[str] = None) -> str:
    """
    Helper to call LLM with a prompt and return the response.

    Args:
        prompt: The prompt to send to the LLM
        system_prompt: Optional system prompt

    Returns:
        The LLM's response content

    Raises:
        Exception: If LLM call fails
    """
    provider = get_provider()

    messages = []
    if system_prompt:
        messages.append(Message(role="system", content=system_prompt))
    messages.append(Message(role="user", content=prompt))

    response = provider.complete(messages)
    return response.content


def extract_and_validate_code(response_text: str) -> Tuple[Optional[str], bool]:
    """
    Extract code from LLM response and validate its syntax.

    Args:
        response_text: The LLM response text (may contain markdown code blocks)

    Returns:
        Tuple of (extracted_code, is_valid)
        - extracted_code: The extracted code or None if no code found
        - is_valid: True if code has valid syntax, False otherwise

    Example:
        >>> text = '```python\nprint("hello")\n```'
        >>> code, valid = extract_and_validate_code(text)
        >>> code
        'print("hello")'
        >>> valid
        True
    """
    from .code import extract_code, validate_syntax

    code = extract_code(response_text)
    if not code:
        return None, False

    is_valid = validate_syntax(code)
    return code, is_valid


def sanitize_error_message(error: Exception, show_details: bool = False) -> str:
    """
    Sanitize error messages to prevent information leakage.

    Args:
        error: The exception to sanitize
        show_details: If True, includes more details (for debugging)

    Returns:
        Sanitized error message safe to show to users
    """
    error_type = type(error).__name__

    # Map specific errors to user-friendly messages
    error_map = {
        "FileNotFoundError": "The requested file was not found.",
        "PermissionError": "Permission denied.",
        "TimeoutError": "The operation timed out.",
        "ConnectionError": "Failed to connect to the service.",
        "ValueError": "Invalid input provided.",
        "TypeError": "Invalid data type provided.",
    }

    base_message = error_map.get(error_type, "An error occurred.")

    if show_details:
        # In development, show more details
        return f"{base_message} ({error_type}: {str(error)})"
    else:
        # In production, just show the sanitized message
        return base_message
