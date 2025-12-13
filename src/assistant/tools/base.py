"""Abstract tool interface and registry."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any, List


@dataclass
class ToolSchema:
    """JSON Schema for tool inputs."""
    type: str = "object"
    properties: Dict[str, Any] = None
    required: List[str] = None


class Tool(ABC):
    """
    Abstract base for all tools.

    Implement this to add new capabilities to the agent.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique tool identifier."""
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        """What this tool does (shown to LLM)."""
        ...

    @property
    @abstractmethod
    def schema(self) -> ToolSchema:
        """Input parameters schema."""
        ...

    @abstractmethod
    def execute(self, **kwargs) -> str:
        """
        Execute the tool with given inputs.

        Returns:
            String result to send back to LLM
        """
        ...

    def to_dict(self) -> dict:
        """Convert to Claude tool format."""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": {
                "type": self.schema.type,
                "properties": self.schema.properties or {},
                "required": self.schema.required or [],
            }
        }
