"""Code analysis tool."""

import ast
from dataclasses import dataclass
from typing import List

from .base import Tool, ToolSchema
from .registry import register_tool
from ..utils.validation import validate_string_input, MAX_CODE_LENGTH


@dataclass
class AnalysisResult:
    functions: List[str]
    classes: List[str]
    imports: List[str]
    line_count: int
    complexity: int
    issues: List[str]


@register_tool
class AnalyzeTool(Tool):
    """Analyze code structure and quality."""

    @property
    def name(self) -> str:
        return "analyze_code"

    @property
    def description(self) -> str:
        return "Analyze Python code structure, find functions, classes, and potential issues."

    @property
    def schema(self) -> ToolSchema:
        return ToolSchema(
            properties={
                "code": {
                    "type": "string",
                    "description": "Python code to analyze"
                }
            },
            required=["code"]
        )

    def execute(self, code: str) -> str:
        """Analyze code and return structured results."""
        # Validate input using helper
        try:
            validate_string_input(code, "code", max_length=MAX_CODE_LENGTH)
        except ValueError as e:
            return f"Error: {str(e)}"

        result = self._analyze(code)

        return f"""Code Analysis:
- Functions: {', '.join(result.functions) or 'None'}
- Classes: {', '.join(result.classes) or 'None'}
- Imports: {', '.join(result.imports) or 'None'}
- Lines: {result.line_count}
- Cyclomatic Complexity: {result.complexity}
- Issues: {'; '.join(result.issues) or 'None found'}"""

    def _analyze(self, code: str) -> AnalysisResult:
        """Perform static analysis."""
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return AnalysisResult(
                functions=[], classes=[], imports=[],
                line_count=len(code.splitlines()),
                complexity=0,
                issues=[f"Syntax error at line {e.lineno}: {e.msg}"]
            )

        functions = []
        classes = []
        imports = []
        issues = []
        complexity = 1

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                functions.append(node.name)
                if not ast.get_docstring(node):
                    issues.append(f"Function '{node.name}' missing docstring")
                # Check for long functions
                if hasattr(node, 'end_lineno') and hasattr(node, 'lineno'):
                    func_lines = node.end_lineno - node.lineno
                    if func_lines > 50:
                        issues.append(f"Function '{node.name}' is very long ({func_lines} lines)")

            elif isinstance(node, ast.ClassDef):
                classes.append(node.name)
                if not ast.get_docstring(node):
                    issues.append(f"Class '{node.name}' missing docstring")

            elif isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)

            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)

            elif isinstance(node, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1

            # Check for potential issues
            # FIX: Use ast.Constant instead of deprecated ast.Str (Python 3.8+)
            elif isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant):
                if isinstance(node.value.value, str):
                    # Standalone strings might be commented-out code
                    pass

        # Check for complexity issues
        if complexity > 20:
            issues.append(f"High cyclomatic complexity ({complexity})")

        return AnalysisResult(
            functions=functions,
            classes=classes,
            imports=list(set(imports)),  # Remove duplicates
            line_count=len(code.splitlines()),
            complexity=complexity,
            issues=issues
        )
