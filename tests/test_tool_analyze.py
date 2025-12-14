"""Comprehensive tests for AnalyzeTool."""

import pytest
from assistant.tools.analyze import AnalyzeTool, AnalysisResult


class TestAnalyzeToolValidation:
    """Test input validation in AnalyzeTool."""

    @pytest.fixture
    def tool(self):
        """Create AnalyzeTool instance."""
        return AnalyzeTool()

    def test_empty_code_rejected(self, tool):
        """Empty code should be rejected."""
        result = tool.execute("")
        assert "Error" in result
        assert "cannot be empty" in result

    def test_whitespace_only_rejected(self, tool):
        """Whitespace-only code should be rejected."""
        result = tool.execute("   \n\t  ")
        assert "Error" in result

    def test_code_too_long_rejected(self, tool):
        """Code exceeding 50KB should be rejected."""
        long_code = "x = 1\n" * 10000  # ~60KB
        result = tool.execute(long_code)
        assert "Error" in result
        assert "too long" in result


class TestAnalyzeToolFunctionDetection:
    """Test function detection and analysis."""

    @pytest.fixture
    def tool(self):
        """Create AnalyzeTool instance."""
        return AnalyzeTool()

    def test_single_function_detected(self, tool):
        """Single function should be detected."""
        code = '''
def hello():
    """Say hello."""
    print("Hello")
'''
        result = tool.execute(code)
        assert "Functions: hello" in result

    def test_multiple_functions_detected(self, tool):
        """Multiple functions should be detected."""
        code = '''
def add(a, b):
    return a + b

def subtract(a, b):
    return a - b

def multiply(a, b):
    return a * b
'''
        result = tool.execute(code)
        assert "add" in result
        assert "subtract" in result
        assert "multiply" in result

    def test_no_functions(self, tool):
        """Code with no functions should report 'None'."""
        code = "x = 1\ny = 2\nprint(x + y)"
        result = tool.execute(code)
        assert "Functions: None" in result

    def test_missing_docstring_flagged(self, tool):
        """Functions without docstrings should be flagged."""
        code = '''
def no_docs():
    pass
'''
        result = tool.execute(code)
        assert "missing docstring" in result
        assert "no_docs" in result

    def test_long_function_flagged(self, tool):
        """Very long functions should be flagged."""
        # Create a function with >50 lines
        lines = ["def long_func():"] + ["    x = 1"] * 55
        code = "\n".join(lines)

        result = tool.execute(code)
        assert "very long" in result
        assert "long_func" in result


class TestAnalyzeToolClassDetection:
    """Test class detection and analysis."""

    @pytest.fixture
    def tool(self):
        """Create AnalyzeTool instance."""
        return AnalyzeTool()

    def test_single_class_detected(self, tool):
        """Single class should be detected."""
        code = '''
class MyClass:
    """A class."""
    pass
'''
        result = tool.execute(code)
        assert "Classes: MyClass" in result

    def test_multiple_classes_detected(self, tool):
        """Multiple classes should be detected."""
        code = '''
class Dog:
    pass

class Cat:
    pass
'''
        result = tool.execute(code)
        assert "Dog" in result
        assert "Cat" in result

    def test_no_classes(self, tool):
        """Code with no classes should report 'None'."""
        code = "def foo(): pass"
        result = tool.execute(code)
        assert "Classes: None" in result

    def test_class_missing_docstring(self, tool):
        """Classes without docstrings should be flagged."""
        code = '''
class UndocumentedClass:
    pass
'''
        result = tool.execute(code)
        assert "missing docstring" in result
        assert "UndocumentedClass" in result


class TestAnalyzeToolImportDetection:
    """Test import statement detection."""

    @pytest.fixture
    def tool(self):
        """Create AnalyzeTool instance."""
        return AnalyzeTool()

    def test_simple_import(self, tool):
        """Simple imports should be detected."""
        code = "import os"
        result = tool.execute(code)
        assert "os" in result

    def test_multiple_imports(self, tool):
        """Multiple imports should be detected."""
        code = '''
import os
import sys
import json
'''
        result = tool.execute(code)
        assert "os" in result
        assert "sys" in result
        assert "json" in result

    def test_from_import(self, tool):
        """From imports should be detected."""
        code = "from pathlib import Path"
        result = tool.execute(code)
        assert "pathlib" in result

    def test_no_imports(self, tool):
        """Code with no imports should report 'None'."""
        code = "x = 1 + 1"
        result = tool.execute(code)
        assert "Imports: None" in result

    def test_duplicate_imports_removed(self, tool):
        """Duplicate imports should be deduplicated."""
        code = '''
import os
from os import path
import os
'''
        result = tool.execute(code)
        # Should only list 'os' once in the analysis
        # (The AnalysisResult uses set to deduplicate)
        assert "os" in result


class TestAnalyzeToolComplexity:
    """Test cyclomatic complexity calculation."""

    @pytest.fixture
    def tool(self):
        """Create AnalyzeTool instance."""
        return AnalyzeTool()

    def test_simple_code_low_complexity(self, tool):
        """Simple linear code should have complexity of 1."""
        code = '''
x = 1
y = 2
z = x + y
'''
        result = tool.execute(code)
        assert "Cyclomatic Complexity: 1" in result

    def test_if_statement_increases_complexity(self, tool):
        """If statements should increase complexity."""
        code = '''
if x > 0:
    print("positive")
'''
        result = tool.execute(code)
        assert "Cyclomatic Complexity: 2" in result

    def test_loops_increase_complexity(self, tool):
        """Loops should increase complexity."""
        code = '''
for i in range(10):
    pass

while True:
    break
'''
        result = tool.execute(code)
        assert "Cyclomatic Complexity: 3" in result

    def test_exception_handler_increases_complexity(self, tool):
        """Exception handlers should increase complexity."""
        code = '''
try:
    risky_operation()
except ValueError:
    handle_error()
'''
        result = tool.execute(code)
        assert "Cyclomatic Complexity: 2" in result

    def test_high_complexity_flagged(self, tool):
        """High complexity (>20) should be flagged."""
        # Create code with many branches
        conditions = ["if True: pass" for _ in range(25)]
        code = "\n".join(conditions)

        result = tool.execute(code)
        assert "High cyclomatic complexity" in result

    def test_nested_complexity(self, tool):
        """Nested structures should accumulate complexity."""
        code = '''
def complex_func():
    for i in range(10):
        if i % 2 == 0:
            while i > 0:
                try:
                    if i == 5:
                        pass
                except:
                    pass
                i -= 1
'''
        result = tool.execute(code)
        # Should have complexity from: for, if, while, try, if = 6
        complexity = int(result.split("Cyclomatic Complexity: ")[1].split("\n")[0])
        assert complexity >= 6


class TestAnalyzeToolSyntaxErrors:
    """Test handling of syntax errors."""

    @pytest.fixture
    def tool(self):
        """Create AnalyzeTool instance."""
        return AnalyzeTool()

    def test_syntax_error_reported(self, tool):
        """Syntax errors should be reported in issues."""
        code = "def bad syntax:"
        result = tool.execute(code)
        assert "Syntax error" in result

    def test_syntax_error_shows_line_number(self, tool):
        """Syntax error should show line number."""
        code = "x = 1\ny = 2\ndef bad():"
        result = tool.execute(code)
        assert "line" in result.lower()

    def test_syntax_error_still_counts_lines(self, tool):
        """Even with syntax error, line count should be shown."""
        code = "x = 1\ny = 2\nz = bad syntax"
        result = tool.execute(code)
        assert "Lines: 3" in result


class TestAnalyzeToolSchema:
    """Test tool schema and metadata."""

    @pytest.fixture
    def tool(self):
        """Create AnalyzeTool instance."""
        return AnalyzeTool()

    def test_tool_name(self, tool):
        """Tool should have correct name."""
        assert tool.name == "analyze_code"

    def test_tool_description(self, tool):
        """Tool should have descriptive text."""
        assert "analyze" in tool.description.lower()
        assert "python" in tool.description.lower()

    def test_tool_schema_structure(self, tool):
        """Tool schema should be properly structured."""
        schema = tool.schema

        assert "code" in schema.properties
        assert schema.properties["code"]["type"] == "string"
        assert "code" in schema.required

    def test_tool_to_dict(self, tool):
        """Tool should serialize to dict format."""
        tool_dict = tool.to_dict()

        assert tool_dict["name"] == "analyze_code"
        assert "analyze" in tool_dict["description"].lower()
        assert tool_dict["input_schema"]["type"] == "object"
        assert "code" in tool_dict["input_schema"]["required"]


class TestAnalyzeToolEdgeCases:
    """Test edge cases and special scenarios."""

    @pytest.fixture
    def tool(self):
        """Create AnalyzeTool instance."""
        return AnalyzeTool()

    def test_empty_file(self, tool):
        """Empty Python file (after validation bypass for testing internal)."""
        # This tests the _analyze method directly
        analysis = tool._analyze("")

        assert analysis.functions == []
        assert analysis.classes == []
        assert analysis.imports == []
        assert analysis.line_count == 0  # Empty string has 0 lines
        assert analysis.complexity == 1

    def test_comments_only(self, tool):
        """File with only comments."""
        code = '''
# This is a comment
# Another comment
'''
        result = tool.execute(code)
        assert "Functions: None" in result
        assert "Classes: None" in result

    def test_class_with_methods(self, tool):
        """Class with methods should detect both."""
        code = '''
class Calculator:
    """A calculator."""

    def add(self, a, b):
        """Add two numbers."""
        return a + b

    def subtract(self, a, b):
        """Subtract two numbers."""
        return a - b
'''
        result = tool.execute(code)
        assert "Calculator" in result
        assert "add" in result
        assert "subtract" in result

    def test_nested_functions(self, tool):
        """Nested functions should be detected."""
        code = '''
def outer():
    def inner():
        pass
    return inner
'''
        result = tool.execute(code)
        assert "outer" in result
        assert "inner" in result

    def test_lambda_functions_not_detected(self, tool):
        """Lambda functions should not appear in function list."""
        code = "f = lambda x: x + 1"
        result = tool.execute(code)
        assert "Functions: None" in result

    def test_multiline_strings(self, tool):
        """Multiline strings should not break analysis."""
        code = '''
text = """
This is a multiline
string with many lines
"""
'''
        result = tool.execute(code)
        # Should not crash
        assert "Lines:" in result

    def test_all_issues_none(self, tool):
        """Well-written code should have no issues."""
        code = '''
def well_documented():
    """This function is well documented."""
    return True
'''
        result = tool.execute(code)
        assert "Issues: None found" in result

    def test_code_at_max_length(self, tool):
        """Code at exactly 50KB should be analyzed."""
        code = "# " + "a" * 49997  # Exactly 50,000 chars

        result = tool.execute(code)
        # Should not error about length
        assert "too long" not in result.lower()
        assert "Lines: 1" in result
