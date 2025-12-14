#!/usr/bin/env python3
"""
Interactive code generation and execution tool.

This script asks the user for a code prompt, generates Python code using AI,
and executes it in a sandboxed Docker environment.
"""

import sys
import os

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from assistant.tools.generate import GenerateTool
from assistant.tools.execute import ExecuteTool
from assistant.config import get_config


def print_header():
    """Print a nice header."""
    print("=" * 70)
    print("  Code Generation & Execution Tool")
    print("=" * 70)
    print()
    print("This tool will:")
    print("  1. Ask you for a description of what code you want")
    print("  2. Generate Python code using AI (Claude)")
    print("  3. Execute the code in a safe Docker sandbox")
    print("  4. Show you the results")
    print()
    print("=" * 70)
    print()


def get_user_input() -> tuple[str, bool]:
    """
    Get code description from user.

    Returns:
        Tuple of (description, include_tests)
    """
    print("What code would you like to generate?")
    print("(Describe what you want the code to do)")
    print()

    # Get description
    description = input(">>> ").strip()

    if not description:
        print("Error: Description cannot be empty.")
        sys.exit(1)

    # Ask about tests
    print()
    tests_input = input("Include test cases? (y/n) [n]: ").strip().lower()
    include_tests = tests_input in ['y', 'yes']

    return description, include_tests


def extract_code_from_response(response: str) -> str:
    """
    Extract code from the generation response.

    Args:
        response: Tool response containing code blocks

    Returns:
        Extracted Python code
    """
    # Look for code between ```python and ```
    if "```python" in response:
        start = response.find("```python") + len("```python")
        end = response.find("```", start)
        if end != -1:
            return response[start:end].strip()

    # Fallback: look for any code block
    if "```" in response:
        parts = response.split("```")
        if len(parts) >= 3:
            # Get the first code block
            return parts[1].strip()

    return ""


def main():
    """Main entry point."""
    try:
        # Check for API key
        config = get_config()
        if not config.anthropic_api_key:
            print("Error: ANTHROPIC_API_KEY environment variable not set.")
            print()
            print("Please set your API key:")
            print("  export ANTHROPIC_API_KEY='your-api-key-here'")
            print()
            print("Or create a .env file with:")
            print("  ANTHROPIC_API_KEY=your-api-key-here")
            sys.exit(1)

        print_header()

        # Get user input
        description, include_tests = get_user_input()

        print()
        print("=" * 70)
        print("  Step 1: Generating code...")
        print("=" * 70)
        print()

        # Generate code
        generator = GenerateTool()
        gen_result = generator.execute(
            description=description,
            include_tests=include_tests
        )

        print(gen_result)
        print()

        # Check if generation was successful
        if gen_result.startswith("Error:"):
            print("Code generation failed. Exiting.")
            sys.exit(1)

        # Extract code
        code = extract_code_from_response(gen_result)

        if not code:
            print("Warning: Could not extract code from response.")
            print("Please review the output above.")
            sys.exit(1)

        # Ask if user wants to execute
        print("=" * 70)
        print("  Step 2: Execute the generated code?")
        print("=" * 70)
        print()
        execute_input = input("Execute this code? (y/n) [y]: ").strip().lower()

        if execute_input in ['n', 'no']:
            print("Execution skipped. Goodbye!")
            sys.exit(0)

        print()
        print("=" * 70)
        print("  Step 3: Executing code in Docker sandbox...")
        print("=" * 70)
        print()

        # Execute code
        executor = ExecuteTool()
        exec_result = executor.execute(code=code, timeout=30)

        print(exec_result)
        print()

        print("=" * 70)
        print("  Done!")
        print("=" * 70)

    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
