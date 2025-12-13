"""Anthropic Claude provider implementation."""

import anthropic
from typing import List, Optional
from .base import LLMProvider, Response, Message, ToolCall
from ..config import get_config


class AnthropicProvider(LLMProvider):
    """Claude via Anthropic API."""

    def __init__(self):
        config = get_config()

        # Validate API key exists
        if not config.anthropic_api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY not found in environment. "
                "Please set it in your .env file or environment variables."
            )

        self.client = anthropic.Anthropic(api_key=config.anthropic_api_key)
        self.model = config.llm.model
        self.max_tokens = config.llm.max_tokens

    @property
    def name(self) -> str:
        return "anthropic"

    def complete(
        self,
        messages: List[Message],
        system: Optional[str] = None,
        tools: Optional[List[dict]] = None,
    ) -> Response:
        """Send request to Claude."""

        # Validate inputs
        if not messages:
            raise ValueError("Messages list cannot be empty")

        # Validate message roles
        valid_roles = {"user", "assistant"}
        for msg in messages:
            if msg.role not in valid_roles:
                raise ValueError(f"Invalid message role: {msg.role}. Must be 'user' or 'assistant'")

        # Convert to Anthropic format
        api_messages = [{"role": m.role, "content": m.content} for m in messages]

        kwargs = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "messages": api_messages,
        }

        if system:
            kwargs["system"] = system
        if tools:
            kwargs["tools"] = tools

        try:
            response = self.client.messages.create(**kwargs)
        except anthropic.APIError as e:
            raise RuntimeError(f"Anthropic API error: {e}") from e

        # Parse response
        content = ""
        tool_calls = []

        for block in response.content:
            if hasattr(block, "text"):
                content = block.text
            elif block.type == "tool_use":
                tool_calls.append(ToolCall(
                    id=block.id,
                    name=block.name,
                    inputs=block.input
                ))

        return Response(
            content=content,
            tool_calls=tool_calls,
            stop_reason=response.stop_reason,
            usage={
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
            },
            raw=response
        )


# Provider factory
_providers = {
    "anthropic": AnthropicProvider,
}


def get_provider(name: str = None) -> LLMProvider:
    """Get an LLM provider by name."""
    config = get_config()
    provider_name = name or config.llm.provider

    if provider_name not in _providers:
        raise ValueError(f"Unknown provider: {provider_name}. Available: {list(_providers.keys())}")

    return _providers[provider_name]()


def register_provider(name: str, provider_class: type):
    """Register a new provider (for plugins)."""
    _providers[name] = provider_class
