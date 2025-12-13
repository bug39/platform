"""Phase 1 integration test."""

from assistant.tools.base import Tool, ToolSchema
from assistant.tools.registry import ToolRegistry, register_tool
from assistant.core.events import EventBus, EventType
from assistant.core.session import Session
from assistant.core.agent import Agent, AgentConfig
from assistant.providers.base import Message


# Test tool
@register_tool
class GreetTool(Tool):
    """Simple test tool that greets someone."""

    @property
    def name(self) -> str:
        return "greet"

    @property
    def description(self) -> str:
        return "Greet someone by name"

    @property
    def schema(self) -> ToolSchema:
        return ToolSchema(
            properties={
                "name": {
                    "type": "string",
                    "description": "Name of person to greet"
                }
            },
            required=["name"]
        )

    def execute(self, name: str) -> str:
        return f"Hello, {name}! Nice to meet you."


def test_tool_registry():
    """Test tool registration and execution."""
    print("Testing Tool Registry...")

    registry = ToolRegistry.get()

    # Verify tool is registered
    assert registry.get_tool("greet") is not None, "Tool not registered"

    # Test execution
    result = registry.execute("greet", {"name": "Alice"})
    assert "Alice" in result, f"Unexpected result: {result}"

    # Test to_dicts
    tool_dicts = registry.to_dicts()
    assert len(tool_dicts) >= 1, "No tools in dicts"

    print("✓ Tool Registry working")


def test_event_bus():
    """Test event system."""
    print("\nTesting Event Bus...")

    bus = EventBus.get()
    bus.clear()  # Clear previous handlers

    # Track events
    events_received = []

    @bus.on(EventType.BEFORE_TOOL_EXECUTE)
    def track_event(event):
        events_received.append(event.data.get("tool"))

    # Emit event
    bus.emit(EventType.BEFORE_TOOL_EXECUTE, {"tool": "test_tool"})

    assert len(events_received) == 1, f"Expected 1 event, got {len(events_received)}"
    assert events_received[0] == "test_tool", f"Wrong event data: {events_received[0]}"

    print("✓ Event Bus working")


def test_session():
    """Test session management."""
    print("\nTesting Session...")

    session = Session()

    # Add messages
    session.add_message(Message(role="user", content="Hello"))
    session.add_message(Message(role="assistant", content="Hi there!"))

    assert len(session.messages) == 2, f"Expected 2 messages, got {len(session.messages)}"
    assert session.token_estimate() > 0, "Token estimate should be > 0"

    # Test save/load
    import tempfile
    from pathlib import Path

    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "test_session.json"
        session.save(path)

        loaded = Session.load(path)
        assert len(loaded.messages) == 2, "Loaded session has wrong message count"
        assert loaded.id == session.id, "Session ID mismatch"

    print("✓ Session working")


def test_agent_basic():
    """Test basic agent functionality (no LLM call)."""
    print("\nTesting Agent (basic)...")

    config = AgentConfig(max_iterations=5)
    agent = Agent(config)

    # Verify components initialized
    assert agent.provider is not None, "Provider not initialized"
    assert agent.tools is not None, "Tools not initialized"
    assert agent.events is not None, "Events not initialized"
    assert agent.session is not None, "Session not initialized"

    print("✓ Agent initialized correctly")


def main():
    """Run all Phase 1 tests."""
    print("=" * 60)
    print("Phase 1 Integration Tests")
    print("=" * 60)

    try:
        test_tool_registry()
        test_event_bus()
        test_session()
        test_agent_basic()

        print("\n" + "=" * 60)
        print("✓ All Phase 1 tests passed!")
        print("=" * 60)
        return 0

    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        return 1
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
