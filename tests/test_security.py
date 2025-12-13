"""Security and validation tests."""

import pytest
import tempfile
from pathlib import Path

from assistant.config import LLMConfig, SandboxConfig, Config
from assistant.tools.registry import ToolRegistry, register_tool
from assistant.tools.base import Tool, ToolSchema
from assistant.core.session import Session
from assistant.core.agent import Agent
from assistant.providers.base import Message


def test_llm_config_validation():
    """Test LLM config validation."""
    # Valid config
    config = LLMConfig()
    assert config.provider == "anthropic"

    # Invalid provider
    with pytest.raises(ValueError, match="provider must be one of"):
        LLMConfig(provider="invalid")

    # Invalid max_tokens
    with pytest.raises(ValueError, match="max_tokens must be between"):
        LLMConfig(max_tokens=0)
    with pytest.raises(ValueError, match="max_tokens must be between"):
        LLMConfig(max_tokens=300000)

    # Invalid temperature
    with pytest.raises(ValueError, match="temperature must be between"):
        LLMConfig(temperature=-0.1)
    with pytest.raises(ValueError, match="temperature must be between"):
        LLMConfig(temperature=1.5)


def test_sandbox_config_validation():
    """Test sandbox config validation."""
    # Valid config
    config = SandboxConfig()
    assert config.memory_limit == "256m"

    # Invalid timeout
    with pytest.raises(ValueError, match="timeout_seconds must be between"):
        SandboxConfig(timeout_seconds=0)
    with pytest.raises(ValueError, match="timeout_seconds must be between"):
        SandboxConfig(timeout_seconds=400)

    # Invalid cpu_quota
    with pytest.raises(ValueError, match="cpu_quota must be between"):
        SandboxConfig(cpu_quota=500)

    # Invalid memory_limit format
    with pytest.raises(ValueError, match="memory_limit must be in format"):
        SandboxConfig(memory_limit="invalid")
    with pytest.raises(ValueError, match="memory_limit must be in format"):
        SandboxConfig(memory_limit="256")
    with pytest.raises(ValueError, match="memory_limit must be in format"):
        SandboxConfig(memory_limit="256mb")

    # Valid memory_limit formats
    SandboxConfig(memory_limit="256m")
    SandboxConfig(memory_limit="1g")
    SandboxConfig(memory_limit="512k")


def test_tool_name_validation():
    """Test tool name validation."""
    registry = ToolRegistry()
    registry.clear()

    class ValidTool(Tool):
        @property
        def name(self) -> str:
            return "valid_tool"

        @property
        def description(self) -> str:
            return "A valid tool"

        @property
        def schema(self) -> ToolSchema:
            return ToolSchema()

        def execute(self, **kwargs) -> str:
            return "ok"

    class EmptyNameTool(Tool):
        @property
        def name(self) -> str:
            return ""

        @property
        def description(self) -> str:
            return "Empty name"

        @property
        def schema(self) -> ToolSchema:
            return ToolSchema()

        def execute(self, **kwargs) -> str:
            return "ok"

    class InvalidNameTool(Tool):
        @property
        def name(self) -> str:
            return "invalid tool!"

        @property
        def description(self) -> str:
            return "Invalid name"

        @property
        def schema(self) -> ToolSchema:
            return ToolSchema()

        def execute(self, **kwargs) -> str:
            return "ok"

    # Valid tool should register
    registry.register(ValidTool())

    # Empty name should fail
    with pytest.raises(ValueError, match="Tool name cannot be empty"):
        registry.register(EmptyNameTool())

    # Invalid characters should fail
    with pytest.raises(ValueError, match="contains invalid characters"):
        registry.register(InvalidNameTool())


def test_session_save_validation():
    """Test session save path validation."""
    session = Session()
    session.add_message(Message(role="user", content="test"))

    with tempfile.TemporaryDirectory() as tmpdir:
        # Valid save
        valid_path = Path(tmpdir) / "test_session.json"
        session.save(valid_path)
        assert valid_path.exists()

        # Invalid extension
        with pytest.raises(ValueError, match="must have .json extension"):
            session.save(Path(tmpdir) / "test.txt")

        # Invalid characters in filename
        with pytest.raises(ValueError, match="contains invalid characters"):
            session.save(Path(tmpdir) / "test@session.json")


def test_session_load_validation():
    """Test session load validation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Non-existent file
        with pytest.raises(FileNotFoundError):
            Session.load(tmppath / "nonexistent.json")

        # Invalid JSON
        bad_json = tmppath / "bad.json"
        bad_json.write_text("{invalid json")
        with pytest.raises(ValueError, match="Invalid JSON"):
            Session.load(bad_json)

        # Missing required fields
        missing_fields = tmppath / "missing.json"
        missing_fields.write_text('{"foo": "bar"}')
        with pytest.raises(ValueError, match="missing required fields"):
            Session.load(missing_fields)

        # Invalid messages type
        bad_messages = tmppath / "bad_messages.json"
        bad_messages.write_text('{"id": "test", "messages": "not a list"}')
        with pytest.raises(ValueError, match="messages must be a list"):
            Session.load(bad_messages)


def test_agent_input_validation():
    """Test agent input validation."""
    agent = Agent()

    # Empty input
    with pytest.raises(ValueError, match="cannot be empty"):
        agent.run("")

    with pytest.raises(ValueError, match="cannot be empty"):
        agent.run("   ")

    # Too long input
    with pytest.raises(ValueError, match="too long"):
        agent.run("x" * 100001)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
