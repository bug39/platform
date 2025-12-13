"""Session and conversation management."""

import json
from datetime import datetime
from pathlib import Path
from typing import List, Any, Optional
from dataclasses import dataclass, field

from ..providers.base import Message


@dataclass
class Session:
    """
    Manages conversation state.

    Supports:
    - Message history
    - Serialization/deserialization
    - Context length management
    """

    id: str = field(default_factory=lambda: datetime.now().strftime("%Y%m%d_%H%M%S"))
    messages: List[Message] = field(default_factory=list)
    _raw_messages: List[dict] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    def add_message(self, message: Message) -> None:
        """Add a typed message."""
        self.messages.append(message)
        self._raw_messages.append({
            "role": message.role,
            "content": message.content
        })

    def add_raw(self, raw: dict) -> None:
        """Add a raw message dict (for tool calls)."""
        self._raw_messages.append(raw)
        # Also add to typed messages if simple
        if isinstance(raw.get("content"), str):
            self.messages.append(Message(
                role=raw["role"],
                content=raw["content"]
            ))

    def get_messages_for_api(self) -> List[dict]:
        """Get messages in API format."""
        return self._raw_messages.copy()

    def clear(self) -> None:
        """Clear all messages."""
        self.messages = []
        self._raw_messages = []

    def save(self, path: Path) -> None:
        """Save session to file."""
        # Validate path
        path = Path(path).resolve()
        if not path.suffix == ".json":
            raise ValueError("Session file must have .json extension")
        if not path.name.replace('.json', '').replace('_', '').replace('-', '').isalnum():
            raise ValueError("Session filename contains invalid characters")

        data = {
            "id": self.id,
            "messages": self._raw_messages,
            "metadata": self.metadata,
            "saved_at": datetime.now().isoformat()
        }
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(data, f, indent=2, default=str)

    @classmethod
    def load(cls, path: Path) -> "Session":
        """Load session from file."""
        path = Path(path).resolve()
        if not path.exists():
            raise FileNotFoundError(f"Session file not found: {path}")
        if not path.is_file():
            raise ValueError(f"Path is not a file: {path}")

        try:
            with open(path) as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in session file: {e}")

        # Validate structure
        if not isinstance(data, dict):
            raise ValueError("Session data must be a dictionary")
        if "id" not in data or "messages" not in data:
            raise ValueError("Session data missing required fields (id, messages)")
        if not isinstance(data["messages"], list):
            raise ValueError("Session messages must be a list")

        session = cls(id=data["id"])
        session._raw_messages = data["messages"]
        session.metadata = data.get("metadata", {})

        # Reconstruct typed messages with validation
        valid_roles = {"user", "assistant"}
        for raw in session._raw_messages:
            if isinstance(raw.get("content"), str):
                role = raw.get("role")
                if role in valid_roles:
                    session.messages.append(Message(
                        role=role,
                        content=raw["content"]
                    ))

        return session

    def token_estimate(self) -> int:
        """Rough estimate of tokens in conversation."""
        text = "".join(str(m) for m in self._raw_messages)
        return len(text) // 4  # ~4 chars per token

    def get_message_count(self) -> int:
        """Get total number of messages."""
        return len(self._raw_messages)
