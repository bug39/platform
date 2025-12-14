"""Tests for AnthropicProvider retry logic, timeout, and rate limiting."""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
import anthropic
import httpx

from assistant.providers.anthropic import AnthropicProvider, RateLimiter
from assistant.providers.base import Message, Response


class TestRateLimiter:
    """Test the RateLimiter class."""

    def setup_method(self):
        """Reset singleton before each test."""
        RateLimiter.reset()

    def test_allows_requests_under_limit(self):
        """Requests under the limit should not block."""
        limiter = RateLimiter.get_instance(requests_per_minute=10)

        start = time.time()
        for _ in range(5):
            limiter.wait_if_needed()
        elapsed = time.time() - start

        # Should complete quickly (no blocking)
        assert elapsed < 0.5

    def test_blocks_when_limit_exceeded(self):
        """Requests exceeding the limit should block."""
        RateLimiter.reset()  # Fresh instance for this test
        limiter = RateLimiter.get_instance(requests_per_minute=5)

        # Make 5 requests (at limit)
        for _ in range(5):
            limiter.wait_if_needed()

        # 6th request should block
        start = time.time()
        limiter.wait_if_needed()
        elapsed = time.time() - start

        # Should have blocked for some time
        assert elapsed > 0.1

    def test_window_slides_correctly(self):
        """Old requests should be removed from the window."""
        RateLimiter.reset()  # Fresh instance for this test
        limiter = RateLimiter.get_instance(requests_per_minute=2)
        limiter.window_seconds = 1.0  # Shorter window for testing

        # Make 2 requests
        limiter.wait_if_needed()
        limiter.wait_if_needed()

        # Wait for window to slide
        time.sleep(1.1)

        # Should allow new requests without blocking
        start = time.time()
        limiter.wait_if_needed()
        elapsed = time.time() - start

        assert elapsed < 0.5


class TestAnthropicProvider:
    """Test AnthropicProvider retry logic and error handling."""

    def setup_method(self):
        """Reset RateLimiter singleton before each test."""
        RateLimiter.reset()

    @pytest.fixture
    def mock_config(self):
        """Mock configuration."""
        with patch('assistant.providers.anthropic.get_config') as mock:
            config = Mock()
            config.anthropic_api_key = "test-api-key"
            config.llm.model = "claude-sonnet-4-20250514"
            config.llm.max_tokens = 4096
            config.llm.timeout_seconds = 60
            config.llm.max_retries = 3
            config.llm.retry_delay_base = 0.01  # Fast retries for testing
            config.llm.rate_limit_requests_per_minute = 100
            mock.return_value = config
            yield config

    @pytest.fixture
    def provider(self, mock_config):
        """Create a provider with mocked config."""
        return AnthropicProvider()

    def test_successful_request(self, provider):
        """Test successful API request."""
        mock_response = Mock()
        mock_response.content = [Mock(text="Hello", type="text")]
        mock_response.stop_reason = "end_turn"
        mock_response.usage = Mock(input_tokens=10, output_tokens=5)

        with patch.object(provider.client.messages, 'create', return_value=mock_response):
            result = provider.complete([Message(role="user", content="Hi")])

        assert result.content == "Hello"
        assert result.stop_reason == "end_turn"
        assert result.usage["input_tokens"] == 10
        assert result.usage["output_tokens"] == 5

    def test_timeout_configuration(self, mock_config):
        """Test that timeout is properly configured."""
        provider = AnthropicProvider()

        # Verify timeout is configured (non-None)
        # The internal httpx client should have a timeout configured
        assert provider.client._client.timeout is not None
        # Verify it's an httpx.Timeout object
        assert isinstance(provider.client._client.timeout, httpx.Timeout)

    def test_retry_on_rate_limit(self, provider):
        """Test retry logic for 429 rate limit errors."""
        mock_response = Mock()
        mock_response.content = [Mock(text="Success", type="text")]
        mock_response.stop_reason = "end_turn"
        mock_response.usage = Mock(input_tokens=10, output_tokens=5)

        # First call fails with 429, second succeeds
        rate_limit_error = anthropic.APIStatusError(
            message="Rate limit exceeded",
            response=Mock(status_code=429),
            body=None
        )

        with patch.object(
            provider.client.messages,
            'create',
            side_effect=[rate_limit_error, mock_response]
        ) as mock_create:
            start = time.time()
            result = provider.complete([Message(role="user", content="Hi")])
            elapsed = time.time() - start

        # Should have retried and succeeded
        assert result.content == "Success"
        assert mock_create.call_count == 2
        # Should have waited (exponential backoff)
        assert elapsed >= 0.01

    def test_retry_on_server_error(self, provider):
        """Test retry logic for 500 server errors."""
        mock_response = Mock()
        mock_response.content = [Mock(text="Success", type="text")]
        mock_response.stop_reason = "end_turn"
        mock_response.usage = Mock(input_tokens=10, output_tokens=5)

        server_error = anthropic.APIStatusError(
            message="Internal server error",
            response=Mock(status_code=500),
            body=None
        )

        with patch.object(
            provider.client.messages,
            'create',
            side_effect=[server_error, mock_response]
        ):
            result = provider.complete([Message(role="user", content="Hi")])

        assert result.content == "Success"

    def test_retry_exhaustion(self, provider):
        """Test that retries are exhausted and error is raised."""
        rate_limit_error = anthropic.APIStatusError(
            message="Rate limit exceeded",
            response=Mock(status_code=429),
            body=None
        )

        with patch.object(
            provider.client.messages,
            'create',
            side_effect=rate_limit_error
        ) as mock_create:
            with pytest.raises(RuntimeError, match="failed after 4 attempts"):
                provider.complete([Message(role="user", content="Hi")])

        # Should have tried initial + 3 retries = 4 total
        assert mock_create.call_count == 4

    def test_exponential_backoff(self, provider):
        """Test that retry delays follow exponential backoff."""
        rate_limit_error = anthropic.APIStatusError(
            message="Rate limit exceeded",
            response=Mock(status_code=429),
            body=None
        )

        with patch.object(
            provider.client.messages,
            'create',
            side_effect=rate_limit_error
        ):
            with patch('time.sleep') as mock_sleep:
                with pytest.raises(RuntimeError):
                    provider.complete([Message(role="user", content="Hi")])

        # Should have exponential backoff: 0.01, 0.02, 0.04
        assert mock_sleep.call_count == 3
        calls = [call[0][0] for call in mock_sleep.call_args_list]
        assert calls[0] == pytest.approx(0.01)
        assert calls[1] == pytest.approx(0.02)
        assert calls[2] == pytest.approx(0.04)

    def test_non_retryable_error(self, provider):
        """Test that non-retryable errors fail immediately."""
        auth_error = anthropic.APIStatusError(
            message="Invalid API key",
            response=Mock(status_code=401),
            body=None
        )

        with patch.object(
            provider.client.messages,
            'create',
            side_effect=auth_error
        ) as mock_create:
            with pytest.raises(RuntimeError, match="Anthropic API error"):
                provider.complete([Message(role="user", content="Hi")])

        # Should only try once (no retries)
        assert mock_create.call_count == 1

    def test_retry_on_connection_error(self, provider):
        """Test retry logic for connection errors."""
        mock_response = Mock()
        mock_response.content = [Mock(text="Success", type="text")]
        mock_response.stop_reason = "end_turn"
        mock_response.usage = Mock(input_tokens=10, output_tokens=5)

        # Create a proper APIConnectionError with required request parameter
        mock_request = Mock()
        connection_error = anthropic.APIConnectionError(
            message="Connection failed",
            request=mock_request
        )

        with patch.object(
            provider.client.messages,
            'create',
            side_effect=[connection_error, mock_response]
        ):
            result = provider.complete([Message(role="user", content="Hi")])

        assert result.content == "Success"

    def test_retry_on_timeout(self, provider):
        """Test retry logic for timeout errors."""
        mock_response = Mock()
        mock_response.content = [Mock(text="Success", type="text")]
        mock_response.stop_reason = "end_turn"
        mock_response.usage = Mock(input_tokens=10, output_tokens=5)

        timeout_error = httpx.TimeoutException("Request timeout")

        with patch.object(
            provider.client.messages,
            'create',
            side_effect=[timeout_error, mock_response]
        ):
            result = provider.complete([Message(role="user", content="Hi")])

        assert result.content == "Success"

    def test_tool_calls_parsing(self, provider):
        """Test parsing of tool calls from response."""
        mock_response = Mock()
        tool_block = Mock()
        tool_block.type = "tool_use"
        tool_block.id = "tool_1"
        tool_block.name = "get_weather"
        tool_block.input = {"location": "SF"}
        mock_response.content = [tool_block]
        mock_response.stop_reason = "tool_use"
        mock_response.usage = Mock(input_tokens=10, output_tokens=5)

        with patch.object(provider.client.messages, 'create', return_value=mock_response):
            result = provider.complete([Message(role="user", content="Weather?")])

        assert len(result.tool_calls) == 1
        assert result.tool_calls[0].id == "tool_1"
        assert result.tool_calls[0].name == "get_weather"
        assert result.tool_calls[0].inputs == {"location": "SF"}

    def test_input_validation_empty_messages(self, provider):
        """Test that empty messages list raises error."""
        with pytest.raises(ValueError, match="Messages list cannot be empty"):
            provider.complete([])

    def test_input_validation_invalid_role(self, provider):
        """Test that invalid message roles raise error."""
        with pytest.raises(ValueError, match="Invalid message role"):
            provider.complete([Message(role="system", content="Hi")])

    def test_rate_limiting_applied(self, provider):
        """Test that rate limiting is applied before API calls."""
        mock_response = Mock()
        mock_response.content = [Mock(text="Hello", type="text")]
        mock_response.stop_reason = "end_turn"
        mock_response.usage = Mock(input_tokens=10, output_tokens=5)

        with patch.object(provider.client.messages, 'create', return_value=mock_response):
            with patch.object(provider.rate_limiter, 'wait_if_needed') as mock_wait:
                provider.complete([Message(role="user", content="Hi")])

        # Rate limiter should have been called
        mock_wait.assert_called_once()
