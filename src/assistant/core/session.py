"""Session and conversation management."""

import json
from datetime import datetime
from pathlib import Path
from typing import List, Any, Optional
from dataclasses import dataclass, field

from ..providers.base import Message
from ..config import get_config


@dataclass
class Session:
    """
    Manages conversation state with configurable message limits.

    Supports:
    - Message history with automatic pruning
    - Serialization/deserialization
    - Context length management
    """

    id: str = field(default_factory=lambda: datetime.now().strftime("%Y%m%d_%H%M%S"))
    messages: List[Message] = field(default_factory=list)
    _raw_messages: List[dict] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    max_messages: Optional[int] = None  # Override config default if set
    prune_strategy: Optional[str] = None  # Override config default if set

    def _prune_if_needed(self) -> None:
        """Prune messages if limit is exceeded."""
        config = get_config()
        max_msgs = self.max_messages if self.max_messages is not None else config.session.max_messages

        if len(self._raw_messages) <= max_msgs:
            return  # No pruning needed

        strategy = self.prune_strategy if self.prune_strategy is not None else config.session.prune_strategy

        if strategy == "keep_last":
            # Keep only the most recent messages
            to_remove = len(self._raw_messages) - max_msgs
            self._raw_messages = self._raw_messages[to_remove:]
            self.messages = self.messages[to_remove:]

        elif strategy == "keep_first_and_last":
            # Keep first few and last few messages
            # This preserves conversation context (beginning + recent)
            to_remove = len(self._raw_messages) - max_msgs
            if to_remove > 0:
                # Keep first 20% and last 80%
                keep_first = max(2, max_msgs // 5)
                keep_last = max_msgs - keep_first

                self._raw_messages = (
                    self._raw_messages[:keep_first] +
                    self._raw_messages[-keep_last:]
                )
                self.messages = (
                    self.messages[:keep_first] +
                    self.messages[-keep_last:]
                )

        elif strategy == "fifo":
            # First-in-first-out: same as keep_last
            to_remove = len(self._raw_messages) - max_msgs
            self._raw_messages = self._raw_messages[to_remove:]
            self.messages = self.messages[to_remove:]

    def add_message(self, message: Message) -> None:
        """Add a typed message and prune if limit exceeded."""
        self.messages.append(message)
        self._raw_messages.append({
            "role": message.role,
            "content": message.content
        })
        self._prune_if_needed()

    def add_raw(self, raw: dict) -> None:
        """Add a raw message dict (for tool calls) and prune if needed."""
        self._raw_messages.append(raw)
        # Also add to typed messages if simple
        if isinstance(raw.get("content"), str):
            self.messages.append(Message(
                role=raw["role"],
                content=raw["content"]
            ))
        self._prune_if_needed()

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
        # BUG FIX: Handle both string and complex content (tool results)
        valid_roles = {"user", "assistant", "tool"}
        for raw in session._raw_messages:
            role = raw.get("role")
            content = raw.get("content")

            if role in valid_roles and content is not None:
                # Handle string content (simple messages)
                if isinstance(content, str):
                    session.messages.append(Message(
                        role=role,
                        content=content
                    ))
                # Handle complex content (tool calls/results with content blocks)
                elif isinstance(content, (list, dict)):
                    # Keep complex content as-is for tool messages
                    session.messages.append(Message(
                        role=role,
                        content=content
                    ))

        return session

    def token_estimate(self) -> int:
        """Rough estimate of tokens in conversation."""
        text = "".join(str(m) for m in self._raw_messages)
        return len(text) // 4  # ~4 chars per token

    def get_message_count(self) -> int:
        """Get total number of messages."""
        return len(self._raw_messages)
