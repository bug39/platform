"""Tests for Session module."""

import pytest
import json
import tempfile
from pathlib import Path
from src.assistant.core.session import Session
from src.assistant.providers.base import Message


class TestSessionBasics:
    """Test basic session functionality."""

    def test_create_session(self):
        """Test creating a new session."""
        session = Session()
        assert session.id is not None
        assert len(session.messages) == 0
        assert len(session._raw_messages) == 0

    def test_create_session_with_id(self):
        """Test creating session with custom ID."""
        session = Session(id="test123")
        assert session.id == "test123"

    def test_add_simple_message(self):
        """Test adding a simple message."""
        session = Session()
        msg = Message(role="user", content="Hello")
        session.add_message(msg)

        assert len(session.messages) == 1
        assert len(session._raw_messages) == 1
        assert session.messages[0].role == "user"
        assert session.messages[0].content == "Hello"

    def test_add_multiple_messages(self):
        """Test adding multiple messages."""
        session = Session()
        session.add_message(Message(role="user", content="Hello"))
        session.add_message(Message(role="assistant", content="Hi there"))
        session.add_message(Message(role="user", content="How are you?"))

        assert len(session.messages) == 3
        assert session.messages[1].role == "assistant"

    def test_add_raw_message(self):
        """Test adding raw message dict."""
        session = Session()
        session.add_raw({"role": "user", "content": "Test"})

        assert len(session._raw_messages) == 1
        assert len(session.messages) == 1

    def test_add_complex_raw_message(self):
        """Test adding raw message with complex content."""
        session = Session()
        session.add_raw({
            "role": "assistant",
            "content": [
                {"type": "text", "text": "I'll use a tool"},
                {"type": "tool_use", "id": "123", "name": "execute"}
            ]
        })

        assert len(session._raw_messages) == 1
        # Complex content shouldn't add to typed messages automatically
        assert len(session.messages) == 0

    def test_get_messages_for_api(self):
        """Test getting messages in API format."""
        session = Session()
        session.add_message(Message(role="user", content="Test"))

        api_messages = session.get_messages_for_api()
        assert isinstance(api_messages, list)
        assert len(api_messages) == 1
        assert api_messages[0]["role"] == "user"
        assert api_messages[0]["content"] == "Test"

    def test_clear(self):
        """Test clearing session."""
        session = Session()
        session.add_message(Message(role="user", content="Test"))
        assert len(session.messages) > 0

        session.clear()
        assert len(session.messages) == 0
        assert len(session._raw_messages) == 0

    def test_message_count(self):
        """Test getting message count."""
        session = Session()
        assert session.get_message_count() == 0

        session.add_message(Message(role="user", content="1"))
        session.add_message(Message(role="user", content="2"))
        assert session.get_message_count() == 2

    def test_token_estimate(self):
        """Test token estimation."""
        session = Session()
        session.add_message(Message(role="user", content="Hello"))

        tokens = session.token_estimate()
        assert tokens > 0
        assert isinstance(tokens, int)


class TestSessionSerialization:
    """Test session save/load functionality."""

    def test_save_session(self):
        """Test saving session to file."""
        session = Session(id="test123")
        session.add_message(Message(role="user", content="Hello"))

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "session.json"
            session.save(path)

            assert path.exists()
            assert path.is_file()

    def test_save_creates_directory(self):
        """Test that save creates parent directories."""
        session = Session()

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "subdir" / "session.json"
            session.save(path)

            assert path.exists()

    def test_save_rejects_non_json_extension(self):
        """Test that save rejects non-.json files."""
        session = Session()

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "session.txt"

            with pytest.raises(ValueError, match="must have .json extension"):
                session.save(path)

    def test_save_rejects_invalid_filename(self):
        """Test that save rejects filenames with invalid characters."""
        session = Session()

        with tempfile.TemporaryDirectory() as tmpdir:
            # Test with special characters in filename
            path = Path(tmpdir) / "session@#$.json"

            with pytest.raises(ValueError, match="invalid characters"):
                session.save(path)

    def test_load_session(self):
        """Test loading session from file."""
        session = Session(id="test123")
        session.add_message(Message(role="user", content="Hello"))
        session.add_message(Message(role="assistant", content="Hi"))

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "session.json"
            session.save(path)

            loaded = Session.load(path)
            assert loaded.id == "test123"
            assert len(loaded.messages) == 2
            assert loaded.messages[0].content == "Hello"

    def test_load_preserves_complex_content(self):
        """Test that load preserves complex message content (tool results)."""
        session = Session(id="test456")

        # Add message with complex content
        session.add_raw({
            "role": "assistant",
            "content": [
                {"type": "text", "text": "Using tool"},
                {"type": "tool_use", "id": "tool_1", "name": "execute"}
            ]
        })

        session.add_raw({
            "role": "tool",
            "content": [{"type": "tool_result", "tool_use_id": "tool_1"}]
        })

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "session.json"
            session.save(path)

            loaded = Session.load(path)
            assert len(loaded._raw_messages) == 2

            # BUG FIX VERIFICATION: Complex content should now be preserved
            assert len(loaded.messages) == 2
            assert isinstance(loaded.messages[0].content, list)
            assert isinstance(loaded.messages[1].content, list)

    def test_load_nonexistent_file(self):
        """Test loading from nonexistent file."""
        with pytest.raises(FileNotFoundError):
            Session.load(Path("/nonexistent/file.json"))

    def test_load_invalid_json(self):
        """Test loading file with invalid JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "bad.json"
            path.write_text("not valid json {{{")

            with pytest.raises(ValueError, match="Invalid JSON"):
                Session.load(path)

    def test_load_missing_required_fields(self):
        """Test loading session missing required fields."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "bad.json"

            # Missing 'id' field
            path.write_text(json.dumps({"messages": []}))

            with pytest.raises(ValueError, match="missing required fields"):
                Session.load(path)

    def test_load_invalid_messages_type(self):
        """Test loading session with invalid messages type."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "bad.json"

            # messages should be list, not string
            path.write_text(json.dumps({"id": "123", "messages": "not a list"}))

            with pytest.raises(ValueError, match="messages must be a list"):
                Session.load(path)

    def test_roundtrip_serialization(self):
        """Test that save/load preserves all data."""
        session = Session(id="roundtrip")
        session.add_message(Message(role="user", content="Test 1"))
        session.add_message(Message(role="assistant", content="Test 2"))
        session.metadata = {"key": "value"}

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "session.json"
            session.save(path)
            loaded = Session.load(path)

            assert loaded.id == session.id
            assert len(loaded.messages) == len(session.messages)
            assert loaded.metadata == session.metadata
