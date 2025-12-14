"""
Example: Code Generation and Execution Pipeline

This demonstrates the core workflow:
1. Generate code from a description
2. Execute code in a sandboxed Docker container
3. Return and display results
"""

import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from assistant.tools.generate import GenerateTool
from assistant.tools.execute import ExecuteTool
from assistant.tools.explain import ExplainTool
from assistant.tools.fix import FixTool
from assistant.utils.code import extract_code


def example_1_basic_workflow():
    """Example 1: Basic code generation and execution"""
    print("=" * 70)
    print("EXAMPLE 1: Basic Code Generation and Execution")
    print("=" * 70)

    # Step 1: Generate code
    print("\n[1] Generating code from description...")
    generator = GenerateTool()

    description = "Write a function that calculates the factorial of a number using recursion"
    print(f"Description: {description}")

    generated_code = generator.execute(description=description)
    print(f"\n[Generated Code]:\n{generated_code}\n")

    # Extract code from markdown formatting
    code = extract_code(generated_code)
    if not code:
        code = generated_code  # Use as-is if no markdown blocks found

    # Step 2: Execute the generated code
    print("\n[2] Executing generated code in Docker sandbox...")
    executor = ExecuteTool()

    # Add a test case to the generated code
    test_code = code + "\n\n# Test the function\nprint(f'factorial(5) = {factorial(5)}')\nprint(f'factorial(10) = {factorial(10)}')"

    result = executor.execute(code=test_code, timeout=10)
    print(f"\n[Execution Result]:\n{result}\n")


def example_2_with_error_fixing():
    """Example 2: Generate code with intentional error, then fix it"""
    print("\n" + "=" * 70)
    print("EXAMPLE 2: Error Detection and Fixing")
    print("=" * 70)

    # Intentionally broken code
    broken_code = """
def calculate_average(numbers):
    total = sum(numbers)
    return total / len(numbers)

# This will cause a ZeroDivisionError
empty_list = []
print(f"Average: {calculate_average(empty_list)}")
"""

    print("\n[1] Executing code with potential error...")
    executor = ExecuteTool()
    result = executor.execute(code=broken_code, timeout=10)
    print(f"\n[Execution Result]:\n{result}\n")

    # If there was an error, fix it
    if "Error" in result or "Traceback" in result:
        print("\n[2] Error detected! Attempting to fix...")
        fixer = FixTool()

        fixed_code = fixer.execute(
            code=broken_code,
            error=result
        )
        print(f"\n[Fixed Code]:\n{fixed_code}\n")

        # Extract code from markdown
        code = extract_code(fixed_code)
        if not code:
            code = fixed_code

        print("\n[3] Executing fixed code...")
        result = executor.execute(code=code, timeout=10)
        print(f"\n[Execution Result]:\n{result}\n")


def example_3_explain_generated_code():
    """Example 3: Generate code and then explain it"""
    print("\n" + "=" * 70)
    print("EXAMPLE 3: Generate, Execute, and Explain")
    print("=" * 70)

    # Generate code
    print("\n[1] Generating code...")
    generator = GenerateTool()
    description = "Create a function to check if a string is a palindrome"

    generated_code = generator.execute(description=description)
    print(f"\n[Generated Code]:\n{generated_code}\n")

    # Extract code from markdown
    code = extract_code(generated_code)
    if not code:
        code = generated_code

    # Execute it
    print("\n[2] Executing with test cases...")
    executor = ExecuteTool()
    test_code = code + """
# Test cases
test_cases = ['racecar', 'hello', 'A man a plan a canal Panama', '12321', 'python']
for test in test_cases:
    result = is_palindrome(test.lower().replace(' ', ''))
    print(f"'{test}' -> {result}")
"""

    result = executor.execute(code=test_code, timeout=10)
    print(f"\n[Execution Result]:\n{result}\n")

    # Explain the code
    print("\n[3] Explaining the generated code...")
    explainer = ExplainTool()
    explanation = explainer.execute(code=code)
    print(f"\n[Explanation]:\n{explanation}\n")


def example_4_multi_step_pipeline():
    """Example 4: Complex pipeline with multiple operations"""
    print("\n" + "=" * 70)
    print("EXAMPLE 4: Multi-Step Pipeline")
    print("=" * 70)

    # Step 1: Generate a data processing function
    print("\n[1] Generating data processing code...")
    generator = GenerateTool()

    description = """
    Write a function that:
    1. Takes a list of numbers
    2. Filters out negative numbers
    3. Squares each remaining number
    4. Returns the sum of the squared numbers
    """

    generated_code = generator.execute(description=description)
    print(f"\n[Generated Code]:\n{generated_code}\n")

    # Extract code from markdown
    code = extract_code(generated_code)
    if not code:
        code = generated_code

    # Step 2: Execute with test data
    print("\n[2] Executing with test data...")
    executor = ExecuteTool()

    # Detect the function name from the generated code
    import re
    func_match = re.search(r'def (\w+)\(', code)
    func_name = func_match.group(1) if func_match else "process_numbers"

    test_code = code + f"""
# Test with sample data
test_data = [1, -2, 3, -4, 5, 6, -7, 8, 9, -10]
result = {func_name}(test_data)
print(f"Input: {{test_data}}")
print(f"Result: {{result}}")

# Additional test cases
print(f"\\nAll negative: {{{func_name}([-1, -2, -3])}}")
print(f"All positive: {{{func_name}([1, 2, 3])}}")
print(f"Empty list: {{{func_name}([])}}")
"""

    result = executor.execute(code=test_code, timeout=10)
    print(f"\n[Execution Result]:\n{result}\n")


def example_5_security_demonstration():
    """Example 5: Demonstrate security features"""
    print("\n" + "=" * 70)
    print("EXAMPLE 5: Security Features Demonstration")
    print("=" * 70)

    executor = ExecuteTool()

    # Test 1: Network isolation (should fail)
    print("\n[Test 1] Network isolation - attempting network access...")
    network_code = """
import socket
try:
    sock = socket.create_connection(('google.com', 80), timeout=2)
    print("SECURITY ISSUE: Network access succeeded!")
except Exception as e:
    print(f"✓ Network blocked as expected: {type(e).__name__}")
"""
    result = executor.execute(code=network_code, timeout=10)
    print(f"Result:\n{result}\n")

    # Test 2: Resource limits
    print("\n[Test 2] Resource limits - testing memory constraints...")
    memory_code = """
import sys
try:
    # Try to allocate a huge list (will hit memory limit)
    huge_list = [0] * (1024**3)  # 1GB of integers
    print("SECURITY ISSUE: Memory limit not enforced!")
except MemoryError:
    print("✓ Memory limit enforced as expected")
except Exception as e:
    print(f"✓ Resource limit active: {type(e).__name__}")
"""
    result = executor.execute(code=memory_code, timeout=10)
    print(f"Result:\n{result}\n")

    # Test 3: Filesystem restrictions
    print("\n[Test 3] Filesystem - testing read-only restrictions...")
    filesystem_code = """
import os
import tempfile

# Can write to /tmp (allowed)
try:
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("test")
        temp_path = f.name
    print(f"✓ Can write to /tmp: {temp_path}")
    os.unlink(temp_path)
except Exception as e:
    print(f"Failed to write to /tmp: {e}")

# Cannot write to root filesystem (blocked)
try:
    with open('/malicious.txt', 'w') as f:
        f.write("malware")
    print("SECURITY ISSUE: Root filesystem is writable!")
except Exception as e:
    print(f"✓ Root filesystem read-only: {type(e).__name__}")
"""
    result = executor.execute(code=filesystem_code, timeout=10)
    print(f"Result:\n{result}\n")


def main():
    """Run all examples"""
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 68 + "║")
    print("║" + "   CODING ASSISTANT - Code Generation & Execution Demo".center(68) + "║")
    print("║" + " " * 68 + "║")
    print("╚" + "=" * 68 + "╝")

    try:
        # Run examples
        example_1_basic_workflow()
        example_2_with_error_fixing()
        example_3_explain_generated_code()
        example_4_multi_step_pipeline()
        example_5_security_demonstration()

        print("\n" + "=" * 70)
        print("✓ All examples completed successfully!")
        print("=" * 70 + "\n")

    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
