"""Event system for hooks and middleware."""

from dataclasses import dataclass
from typing import Callable, Dict, List, Any
from enum import Enum


class EventType(Enum):
    """Core events that can be hooked."""

    # LLM events
    BEFORE_LLM_CALL = "before_llm_call"
    AFTER_LLM_CALL = "after_llm_call"

    # Tool events
    BEFORE_TOOL_EXECUTE = "before_tool_execute"
    AFTER_TOOL_EXECUTE = "after_tool_execute"

    # Agent events
    AGENT_ITERATION_START = "agent_iteration_start"
    AGENT_ITERATION_END = "agent_iteration_end"
    AGENT_COMPLETE = "agent_complete"

    # Session events
    SESSION_START = "session_start"
    SESSION_END = "session_end"
    MESSAGE_ADDED = "message_added"


@dataclass
class Event:
    """Event payload."""
    type: EventType
    data: Dict[str, Any]


# Type for event handlers
EventHandler = Callable[[Event], None]


class EventBus:
    """
    Publish/subscribe event system.

    Use this to hook into the agent's behavior without modifying core code.

    Example:
        bus = EventBus.get()

        @bus.on(EventType.BEFORE_TOOL_EXECUTE)
        def log_tool_use(event):
            print(f"Using tool: {event.data['tool_name']}")
    """

    _instance: "EventBus" = None

    def __init__(self):
        self._handlers: Dict[EventType, List[EventHandler]] = {}

    @classmethod
    def get(cls) -> "EventBus":
        """Get singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def subscribe(self, event_type: EventType, handler: EventHandler) -> None:
        """Subscribe to an event type."""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)

    def unsubscribe(self, event_type: EventType, handler: EventHandler) -> None:
        """Unsubscribe from an event type."""
        if event_type in self._handlers and handler in self._handlers[event_type]:
            self._handlers[event_type].remove(handler)

    def on(self, event_type: EventType) -> Callable:
        """Decorator to subscribe to an event."""
        def decorator(handler: EventHandler) -> EventHandler:
            self.subscribe(event_type, handler)
            return handler
        return decorator

    def emit(self, event_type: EventType, data: Dict[str, Any] = None) -> None:
        """Emit an event to all subscribers."""
        event = Event(type=event_type, data=data or {})

        for handler in self._handlers.get(event_type, []):
            try:
                handler(event)
            except Exception as e:
                # Don't let handlers break the main flow
                print(f"Warning: Event handler error for {event_type.value}: {e}")

    def clear(self) -> None:
        """Clear all handlers (useful for testing)."""
        self._handlers = {}

    def get_handler_count(self, event_type: EventType) -> int:
        """Get number of handlers for an event type."""
        return len(self._handlers.get(event_type, []))
