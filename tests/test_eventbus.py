"""Tests for EventBus module."""

import pytest
from src.assistant.core.events import EventBus, EventType, Event


class TestEventBusBasics:
    """Test basic EventBus functionality."""

    def setup_method(self):
        """Reset EventBus before each test."""
        EventBus.reset()

    def teardown_method(self):
        """Clean up after each test."""
        EventBus.reset()

    def test_singleton_pattern(self):
        """Test that EventBus is a singleton."""
        bus1 = EventBus.get()
        bus2 = EventBus.get()
        assert bus1 is bus2

    def test_reset_creates_new_instance(self):
        """Test that reset clears the singleton."""
        bus1 = EventBus.get()
        EventBus.reset()
        bus2 = EventBus.get()

        # After reset, we get a fresh instance
        assert bus1 is not bus2

    def test_subscribe_handler(self):
        """Test subscribing to an event."""
        bus = EventBus.get()
        calls = []

        def handler(event):
            calls.append(event)

        bus.subscribe(EventType.AGENT_COMPLETE, handler)
        bus.emit(EventType.AGENT_COMPLETE, {"test": "data"})

        assert len(calls) == 1
        assert calls[0].type == EventType.AGENT_COMPLETE
        assert calls[0].data["test"] == "data"

    def test_multiple_subscribers(self):
        """Test that multiple subscribers all receive events."""
        bus = EventBus.get()
        calls1 = []
        calls2 = []

        def handler1(event):
            calls1.append(event)

        def handler2(event):
            calls2.append(event)

        bus.subscribe(EventType.AGENT_COMPLETE, handler1)
        bus.subscribe(EventType.AGENT_COMPLETE, handler2)
        bus.emit(EventType.AGENT_COMPLETE)

        assert len(calls1) == 1
        assert len(calls2) == 1

    def test_unsubscribe_handler(self):
        """Test unsubscribing from an event."""
        bus = EventBus.get()
        calls = []

        def handler(event):
            calls.append(event)

        bus.subscribe(EventType.AGENT_COMPLETE, handler)
        bus.emit(EventType.AGENT_COMPLETE)
        assert len(calls) == 1

        bus.unsubscribe(EventType.AGENT_COMPLETE, handler)
        bus.emit(EventType.AGENT_COMPLETE)
        assert len(calls) == 1  # No new calls after unsubscribe

    def test_decorator_subscription(self):
        """Test subscribing using @bus.on decorator."""
        bus = EventBus.get()
        calls = []

        @bus.on(EventType.BEFORE_TOOL_EXECUTE)
        def handler(event):
            calls.append(event)

        bus.emit(EventType.BEFORE_TOOL_EXECUTE, {"tool": "test"})

        assert len(calls) == 1
        assert calls[0].data["tool"] == "test"

    def test_emit_with_no_subscribers(self):
        """Test that emit works with no subscribers."""
        bus = EventBus.get()
        # Should not raise
        bus.emit(EventType.AGENT_COMPLETE)

    def test_emit_with_none_data(self):
        """Test emit with None data (should convert to empty dict)."""
        bus = EventBus.get()
        received = []

        def handler(event):
            received.append(event)

        bus.subscribe(EventType.AGENT_COMPLETE, handler)
        bus.emit(EventType.AGENT_COMPLETE, None)

        assert len(received) == 1
        assert received[0].data == {}

    def test_handler_error_doesnt_break_chain(self):
        """Test that handler errors don't prevent other handlers from running."""
        bus = EventBus.get()
        calls = []

        def bad_handler(event):
            raise RuntimeError("Handler error")

        def good_handler(event):
            calls.append(event)

        bus.subscribe(EventType.AGENT_COMPLETE, bad_handler)
        bus.subscribe(EventType.AGENT_COMPLETE, good_handler)

        # Should not raise, good_handler should still be called
        bus.emit(EventType.AGENT_COMPLETE)

        assert len(calls) == 1

    def test_clear_handlers(self):
        """Test clearing all handlers."""
        bus = EventBus.get()
        calls = []

        def handler(event):
            calls.append(event)

        bus.subscribe(EventType.AGENT_COMPLETE, handler)
        bus.emit(EventType.AGENT_COMPLETE)
        assert len(calls) == 1

        bus.clear()
        bus.emit(EventType.AGENT_COMPLETE)
        assert len(calls) == 1  # No new calls after clear

    def test_get_handler_count(self):
        """Test getting handler count."""
        bus = EventBus.get()

        assert bus.get_handler_count(EventType.AGENT_COMPLETE) == 0

        def handler1(event):
            pass

        def handler2(event):
            pass

        bus.subscribe(EventType.AGENT_COMPLETE, handler1)
        assert bus.get_handler_count(EventType.AGENT_COMPLETE) == 1

        bus.subscribe(EventType.AGENT_COMPLETE, handler2)
        assert bus.get_handler_count(EventType.AGENT_COMPLETE) == 2

        bus.unsubscribe(EventType.AGENT_COMPLETE, handler1)
        assert bus.get_handler_count(EventType.AGENT_COMPLETE) == 1


class TestEventBusMemoryLeak:
    """Test memory leak fix (Platform-jga)."""

    def setup_method(self):
        """Reset EventBus before each test."""
        EventBus.reset()

    def teardown_method(self):
        """Clean up after each test."""
        EventBus.reset()

    def test_reset_prevents_handler_accumulation(self):
        """Test that reset() prevents handlers from accumulating."""
        # Simulate creating multiple agent instances
        for i in range(5):
            bus = EventBus.get()

            def handler(event):
                pass

            bus.subscribe(EventType.AGENT_COMPLETE, handler)

        # Without reset, we'd have 5 handlers
        bus = EventBus.get()
        assert bus.get_handler_count(EventType.AGENT_COMPLETE) == 5

        # After reset, handlers should be cleared
        EventBus.reset()
        bus = EventBus.get()
        assert bus.get_handler_count(EventType.AGENT_COMPLETE) == 0

    def test_reset_clears_all_event_types(self):
        """Test that reset clears handlers for all event types."""
        bus = EventBus.get()

        def handler(event):
            pass

        # Subscribe to multiple event types
        bus.subscribe(EventType.AGENT_COMPLETE, handler)
        bus.subscribe(EventType.BEFORE_TOOL_EXECUTE, handler)
        bus.subscribe(EventType.SESSION_START, handler)

        assert bus.get_handler_count(EventType.AGENT_COMPLETE) > 0
        assert bus.get_handler_count(EventType.BEFORE_TOOL_EXECUTE) > 0
        assert bus.get_handler_count(EventType.SESSION_START) > 0

        EventBus.reset()
        bus = EventBus.get()

        assert bus.get_handler_count(EventType.AGENT_COMPLETE) == 0
        assert bus.get_handler_count(EventType.BEFORE_TOOL_EXECUTE) == 0
        assert bus.get_handler_count(EventType.SESSION_START) == 0


class TestEventTypes:
    """Test all event types."""

    def setup_method(self):
        """Reset EventBus before each test."""
        EventBus.reset()

    def teardown_method(self):
        """Clean up after each test."""
        EventBus.reset()

    def test_llm_events(self):
        """Test LLM-related events."""
        bus = EventBus.get()
        calls = []

        @bus.on(EventType.BEFORE_LLM_CALL)
        def handler(event):
            calls.append(("before", event))

        @bus.on(EventType.AFTER_LLM_CALL)
        def handler2(event):
            calls.append(("after", event))

        bus.emit(EventType.BEFORE_LLM_CALL, {"model": "claude"})
        bus.emit(EventType.AFTER_LLM_CALL, {"tokens": 100})

        assert len(calls) == 2
        assert calls[0][0] == "before"
        assert calls[1][0] == "after"

    def test_tool_events(self):
        """Test tool-related events."""
        bus = EventBus.get()
        calls = []

        @bus.on(EventType.BEFORE_TOOL_EXECUTE)
        def handler(event):
            calls.append(event)

        bus.emit(EventType.BEFORE_TOOL_EXECUTE, {"tool": "execute"})
        assert len(calls) == 1

    def test_agent_events(self):
        """Test agent-related events."""
        bus = EventBus.get()
        calls = []

        @bus.on(EventType.AGENT_ITERATION_START)
        def handler(event):
            calls.append(event)

        bus.emit(EventType.AGENT_ITERATION_START)
        assert len(calls) == 1

    def test_session_events(self):
        """Test session-related events."""
        bus = EventBus.get()
        calls = []

        @bus.on(EventType.SESSION_START)
        def handler(event):
            calls.append(event)

        bus.emit(EventType.SESSION_START, {"session_id": "123"})
        assert len(calls) == 1
        assert calls[0].data["session_id"] == "123"
