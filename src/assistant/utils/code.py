"""Code extraction and validation utilities."""

import re
import ast


def extract_code(text: str) -> str:
    """
    Extract code from markdown code blocks.

    Tries to find:
    1. Python-tagged code blocks (```python)
    2. Generic code blocks (```)

    Returns:
        Extracted code or empty string if no code blocks found
    """
    # SECURITY: Use non-backtracking patterns to prevent ReDoS attacks
    # Match code blocks by using negated character class instead of .* with DOTALL

    # Try to find python code block
    # Pattern matches: ```python\n followed by any chars except ``` sequence, then ```
    pattern = r"```python\n((?:(?!```)[\s\S])*?)```"
    matches = re.findall(pattern, text)
    if matches:
        return matches[0].strip()

    # Try generic code block
    pattern = r"```\n((?:(?!```)[\s\S])*?)```"
    matches = re.findall(pattern, text)
    if matches:
        return matches[0].strip()

    return ""


def validate_syntax(code: str) -> bool:
    """
    Check if code has valid Python syntax.

    Args:
        code: Python code string to validate

    Returns:
        True if syntax is valid, False otherwise
    """
    try:
        ast.parse(code)
        return True
    except SyntaxError:
        return False
