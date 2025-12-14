"""Anthropic Claude provider implementation."""

import anthropic
import time
import httpx
from typing import List, Optional
from collections import deque
from .base import LLMProvider, Response, Message, ToolCall
from ..config import get_config


class RateLimiter:
    """
    Simple token bucket rate limiter with singleton pattern.

    Ensures rate limiting is enforced across all provider instances.
    """

    _instance: "RateLimiter" = None
    _lock = None  # Thread lock for singleton initialization

    def __init__(self, requests_per_minute: int):
        self.max_requests = requests_per_minute
        self.window_seconds = 60.0
        self.requests = deque()

    @classmethod
    def get_instance(cls, requests_per_minute: int) -> "RateLimiter":
        """
        Get singleton instance of RateLimiter.

        Args:
            requests_per_minute: Max requests per minute

        Returns:
            Shared RateLimiter instance
        """
        if cls._instance is None:
            cls._instance = cls(requests_per_minute)
        # Update max_requests if config changed
        elif cls._instance.max_requests != requests_per_minute:
            cls._instance.max_requests = requests_per_minute
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        """Reset singleton instance (useful for testing)."""
        cls._instance = None

    def wait_if_needed(self):
        """Block if rate limit would be exceeded."""
        now = time.time()

        # Remove requests outside the current window
        cutoff = now - self.window_seconds
        while self.requests and self.requests[0] < cutoff:
            self.requests.popleft()

        # If at limit, wait until oldest request expires
        if len(self.requests) >= self.max_requests:
            sleep_time = self.requests[0] - cutoff
            if sleep_time > 0:
                time.sleep(sleep_time)
                # Clean up after sleeping
                cutoff = time.time() - self.window_seconds
                while self.requests and self.requests[0] < cutoff:
                    self.requests.popleft()

        # Record this request
        self.requests.append(time.time())


class AnthropicProvider(LLMProvider):
    """Claude via Anthropic API with retry logic, timeout, and rate limiting."""

    def __init__(self):
        config = get_config()

        # Validate API key exists
        if not config.anthropic_api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY not found in environment. "
                "Please set it in your .env file or environment variables."
            )

        # Configure client with timeout
        timeout = httpx.Timeout(config.llm.timeout_seconds, connect=10.0)
        self.client = anthropic.Anthropic(
            api_key=config.anthropic_api_key,
            timeout=timeout
        )
        self.model = config.llm.model
        self.max_tokens = config.llm.max_tokens

        # Retry configuration
        self.max_retries = config.llm.max_retries
        self.retry_delay_base = config.llm.retry_delay_base

        # Rate limiting - use shared singleton instance across all providers
        self.rate_limiter = RateLimiter.get_instance(config.llm.rate_limit_requests_per_minute)

    @property
    def name(self) -> str:
        return "anthropic"

    def complete(
        self,
        messages: List[Message],
        system: Optional[str] = None,
        tools: Optional[List[dict]] = None,
    ) -> Response:
        """Send request to Claude with retry logic and rate limiting."""

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

        # Apply rate limiting
        self.rate_limiter.wait_if_needed()

        # Retry logic with exponential backoff
        last_exception = None
        for attempt in range(self.max_retries + 1):
            try:
                response = self.client.messages.create(**kwargs)
                break  # Success
            except anthropic.APIStatusError as e:
                last_exception = e
                # Retry on rate limits and server errors
                if e.status_code in {429, 500, 502, 503, 504}:
                    if attempt < self.max_retries:
                        # Exponential backoff: base * 2^attempt
                        delay = self.retry_delay_base * (2 ** attempt)
                        time.sleep(delay)
                        continue
                    # Retryable error but retries exhausted - will fall through to else block
                    continue
                # Non-retryable error
                raise RuntimeError(f"Anthropic API error: {e}") from e
            except (anthropic.APIConnectionError, httpx.TimeoutException) as e:
                last_exception = e
                # Retry on connection errors and timeouts
                if attempt < self.max_retries:
                    delay = self.retry_delay_base * (2 ** attempt)
                    time.sleep(delay)
                    continue
                # Retries exhausted - will fall through to else block
                continue
            except anthropic.APIError as e:
                # Other API errors are not retryable
                raise RuntimeError(f"Anthropic API error: {e}") from e
        else:
            # All retries exhausted
            raise RuntimeError(
                f"Anthropic API request failed after {self.max_retries + 1} attempts"
            ) from last_exception

        # Parse response
        content = ""
        tool_calls = []

        for block in response.content:
            if block.type == "tool_use":
                tool_calls.append(ToolCall(
                    id=block.id,
                    name=block.name,
                    inputs=block.input
                ))
            elif hasattr(block, "text"):
                content = block.text

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
