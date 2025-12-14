"""Validation utilities for input validation and sanitization."""

import re
from pathlib import Path
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


def validate_docker_image_name(image_name: str) -> None:
    """
    Validate Docker image name contains only safe characters.

    Args:
        image_name: Docker image name to validate

    Raises:
        ValueError: If image name contains unsafe characters

    Example:
        >>> validate_docker_image_name("python:3.12")  # OK
        >>> validate_docker_image_name("user/repo:tag")  # OK
        >>> validate_docker_image_name("../../../etc/passwd")  # Raises ValueError
    """
    if not image_name or not image_name.strip():
        raise ValueError("Docker image name cannot be empty")

    # Allow alphanumeric, :, /, -, _, and .
    # This matches Docker's official image name format
    if not re.match(r'^[a-zA-Z0-9:/_.-]+$', image_name):
        raise ValueError(
            f"Invalid Docker image name: '{image_name}'. "
            "Only alphanumeric characters and :/_.- are allowed"
        )

    # Additional check: prevent path traversal attempts
    if ".." in image_name:
        raise ValueError(
            f"Invalid Docker image name: '{image_name}'. "
            "Path traversal sequences (..) are not allowed"
        )


def validate_dockerfile_path(dockerfile_path: str, build_context: str = ".") -> Path:
    """
    Validate and sanitize Dockerfile path to prevent path traversal.

    Args:
        dockerfile_path: Path to Dockerfile (relative to build_context)
        build_context: Build context directory

    Returns:
        Sanitized Path object

    Raises:
        ValueError: If path contains path traversal or is unsafe

    Example:
        >>> validate_dockerfile_path("Dockerfile.python", "docker")
        >>> validate_dockerfile_path("../../../etc/passwd", "docker")  # Raises
    """
    if not dockerfile_path or not dockerfile_path.strip():
        raise ValueError("Dockerfile path cannot be empty")

    # Check for path traversal attempts (basic check)
    if ".." in dockerfile_path:
        raise ValueError(
            f"Invalid Dockerfile path: '{dockerfile_path}'. "
            "Path traversal sequences (..) are not allowed"
        )

    # Check for absolute paths (should be relative to build context)
    if Path(dockerfile_path).is_absolute():
        raise ValueError(
            f"Invalid Dockerfile path: '{dockerfile_path}'. "
            "Path must be relative to build context"
        )

    # Resolve the full path and ensure it's within build context
    try:
        context_path = Path(build_context).resolve(strict=False)
        full_path = (context_path / dockerfile_path).resolve(strict=False)

        # SECURITY: Use is_relative_to() instead of string comparison to prevent bypasses
        # This properly handles symlinks, .. sequences, and other edge cases
        try:
            # Python 3.9+ has is_relative_to()
            if not full_path.is_relative_to(context_path):
                raise ValueError(
                    f"Invalid Dockerfile path: '{dockerfile_path}'. "
                    "Path must be within build context"
                )
        except AttributeError:
            # Fallback for Python < 3.9: use os.path.commonpath
            # This is more secure than string comparison
            import os
            try:
                common = Path(os.path.commonpath([str(context_path), str(full_path)]))
                if common != context_path:
                    raise ValueError(
                        f"Invalid Dockerfile path: '{dockerfile_path}'. "
                        "Path must be within build context"
                    )
            except ValueError:
                # commonpath raises ValueError if paths are on different drives
                raise ValueError(
                    f"Invalid Dockerfile path: '{dockerfile_path}'. "
                    "Path must be within build context"
                )

        return full_path

    except ValueError:
        # Re-raise ValueError (from our validation)
        raise
    except Exception as e:
        raise ValueError(f"Invalid Dockerfile path: {e}")


def validate_build_context(build_context: str) -> Path:
    """
    Validate build context is a valid directory.

    Args:
        build_context: Path to build context directory

    Returns:
        Validated Path object

    Raises:
        ValueError: If path is invalid or doesn't exist

    Example:
        >>> validate_build_context("docker")
        >>> validate_build_context("/nonexistent")  # Raises
    """
    if not build_context or not build_context.strip():
        raise ValueError("Build context cannot be empty")

    try:
        context_path = Path(build_context).resolve()

        # Check if path exists
        if not context_path.exists():
            raise ValueError(
                f"Build context does not exist: '{build_context}'"
            )

        # Check if it's a directory
        if not context_path.is_dir():
            raise ValueError(
                f"Build context must be a directory: '{build_context}'"
            )

        return context_path

    except Exception as e:
        if isinstance(e, ValueError):
            raise
        raise ValueError(f"Invalid build context: {e}")
