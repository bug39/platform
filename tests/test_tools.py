"""Tests for built-in tools."""

import pytest
from assistant.tools.registry import ToolRegistry
from assistant.tools.analyze import AnalyzeTool
from assistant.tools.execute import ExecuteTool


def test_analyze_tool_basic():
    """Test basic code analysis."""
    tool = AnalyzeTool()

    code = """
def hello(name):
    '''Greet someone.'''
    return f"Hello, {name}!"

class Person:
    '''A person class.'''
    def __init__(self, name):
        self.name = name
"""

    result = tool.execute(code=code)

    assert "hello" in result
    assert "Person" in result
    assert "Lines:" in result
    assert "Complexity:" in result


def test_analyze_tool_syntax_error():
    """Test analysis with syntax error."""
    tool = AnalyzeTool()

    code = "def broken("

    result = tool.execute(code=code)

    assert "Syntax error" in result


def test_analyze_tool_missing_docstrings():
    """Test detection of missing docstrings."""
    tool = AnalyzeTool()

    code = """
def no_docstring():
    pass

class NoDocstring:
    pass
"""

    result = tool.execute(code=code)

    assert "missing docstring" in result.lower()


def test_analyze_tool_empty_input():
    """Test analysis with empty input."""
    tool = AnalyzeTool()

    result = tool.execute(code="")

    assert "Error" in result


def test_execute_tool_stub():
    """Test execute tool with actual execution."""
    tool = ExecuteTool()

    code = "print('hello')"

    result = tool.execute(code=code)

    # Should now execute successfully and return output
    assert "successful" in result.lower()
    assert "hello" in result


def test_execute_tool_syntax_error():
    """Test execute tool with syntax error."""
    tool = ExecuteTool()

    code = "print('broken"

    result = tool.execute(code=code)

    assert "Syntax error" in result or "error" in result.lower()


def test_execute_tool_empty_input():
    """Test execute tool with empty input."""
    tool = ExecuteTool()

    result = tool.execute(code="")

    assert "Error" in result


def test_all_tools_registered():
    """Test that all tools are auto-registered."""
    registry = ToolRegistry.get()

    # Check that our Phase 2 tools are registered
    expected_tools = {
        "generate_code",
        "analyze_code",
        "explain_code",
        "fix_code",
        "execute_code",
    }

    registered_names = {tool.name for tool in registry.list_tools()}

    for tool_name in expected_tools:
        assert tool_name in registered_names, f"Tool '{tool_name}' not registered"


def test_tool_schemas():
    """Test that all tools have valid schemas."""
    registry = ToolRegistry.get()

    for tool in registry.list_tools():
        # Check schema has required fields
        schema = tool.schema
        assert hasattr(schema, 'type')
        assert hasattr(schema, 'properties')

        # Check to_dict produces valid format
        tool_dict = tool.to_dict()
        assert "name" in tool_dict
        assert "description" in tool_dict
        assert "input_schema" in tool_dict


def test_tool_execution_error_handling():
    """Test that tools handle errors gracefully."""
    registry = ToolRegistry.get()

    # Try to execute non-existent tool
    result = registry.execute("nonexistent", {})
    assert "Error" in result
    assert "Unknown tool" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
