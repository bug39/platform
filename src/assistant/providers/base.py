"""Abstract LLM provider interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Any, Union


@dataclass
class Message:
    role: str  # "user" | "assistant" | "tool"
    content: Union[str, list, dict]  # String for simple messages, list/dict for tool results


@dataclass
class ToolCall:
    id: str
    name: str
    inputs: dict


@dataclass
class Response:
    """Unified response format from any LLM provider."""
    content: str
    tool_calls: List[ToolCall]
    stop_reason: str  # "end_turn" | "tool_use"
    usage: dict  # token counts
    raw: Any  # original response for debugging


class LLMProvider(ABC):
    """
    Abstract base for LLM providers.

    Implement this to add new providers (OpenAI, Gemini, local models, etc.)
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider identifier."""
        ...

    @abstractmethod
    def complete(
        self,
        messages: List[Message],
        system: Optional[str] = None,
        tools: Optional[List[dict]] = None,
    ) -> Response:
        """
        Send messages to the LLM and get a response.

        Args:
            messages: Conversation history
            system: System prompt
            tools: Tool definitions (for function calling)

        Returns:
            Unified Response object
        """
        ...

    def supports_tools(self) -> bool:
        """Whether this provider supports tool/function calling."""
        return True

    def supports_streaming(self) -> bool:
        """Whether this provider supports streaming responses."""
        return False
