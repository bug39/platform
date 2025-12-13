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
    # Try to find python code block
    pattern = r"```python\n(.*?)```"
    matches = re.findall(pattern, text, re.DOTALL)
    if matches:
        return matches[0].strip()

    # Try generic code block
    pattern = r"```\n(.*?)```"
    matches = re.findall(pattern, text, re.DOTALL)
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
