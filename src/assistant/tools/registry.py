"""Tool registration and discovery system."""

from typing import Dict, List, Optional, Type
from .base import Tool


class ToolRegistry:
    """
    Central registry for all available tools.

    Supports:
    - Manual registration
    - Decorator-based registration
    - Plugin discovery
    """

    _instance: Optional["ToolRegistry"] = None

    def __init__(self):
        self._tools: Dict[str, Tool] = {}

    @classmethod
    def get(cls) -> "ToolRegistry":
        """Get singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def register(self, tool: Tool) -> None:
        """Register a tool instance."""
        if not tool.name or not tool.name.strip():
            raise ValueError("Tool name cannot be empty")
        if not tool.name.replace('_', '').replace('-', '').isalnum():
            raise ValueError(f"Tool name '{tool.name}' contains invalid characters")
        if tool.name in self._tools:
            raise ValueError(f"Tool '{tool.name}' already registered")
        self._tools[tool.name] = tool

    def unregister(self, name: str) -> None:
        """Unregister a tool by name."""
        if name in self._tools:
            del self._tools[name]

    def get_tool(self, name: str) -> Optional[Tool]:
        """Get a tool by name."""
        return self._tools.get(name)

    def list_tools(self) -> List[Tool]:
        """Get all registered tools."""
        return list(self._tools.values())

    def to_dicts(self) -> List[dict]:
        """Get all tools in Claude format."""
        return [tool.to_dict() for tool in self._tools.values()]

    def execute(self, name: str, inputs: dict) -> str:
        """Execute a tool by name."""
        tool = self.get_tool(name)
        if not tool:
            return f"Error: Unknown tool '{name}'"

        try:
            return tool.execute(**inputs)
        except TypeError as e:
            return f"Error: Invalid inputs for {name}: {e}"
        except Exception as e:
            return f"Error executing {name}: {str(e)}"

    def clear(self) -> None:
        """Clear all registered tools (useful for testing)."""
        self._tools = {}


def register_tool(tool_class: Type[Tool]) -> Type[Tool]:
    """Decorator to auto-register a tool class."""
    registry = ToolRegistry.get()
    registry.register(tool_class())
    return tool_class
