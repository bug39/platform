"""Abstract storage interface."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class Storage(ABC):
    """
    Abstract base for storage backends.

    Implement this to add new storage options (PostgreSQL, Redis, etc.)
    """

    @abstractmethod
    def save(self, key: str, data: Dict[str, Any]) -> None:
        """
        Save data to storage.

        Args:
            key: Unique identifier for the data
            data: Data to store (must be JSON-serializable)
        """
        ...

    @abstractmethod
    def load(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Load data from storage.

        Args:
            key: Unique identifier for the data

        Returns:
            Stored data or None if not found
        """
        ...

    @abstractmethod
    def delete(self, key: str) -> bool:
        """
        Delete data from storage.

        Args:
            key: Unique identifier for the data

        Returns:
            True if deleted, False if not found
        """
        ...

    @abstractmethod
    def exists(self, key: str) -> bool:
        """
        Check if key exists in storage.

        Args:
            key: Unique identifier to check

        Returns:
            True if exists, False otherwise
        """
        ...

    @abstractmethod
    def list_keys(self, prefix: str = "") -> list:
        """
        List all keys in storage.

        Args:
            prefix: Optional prefix to filter keys

        Returns:
            List of keys
        """
        ...
