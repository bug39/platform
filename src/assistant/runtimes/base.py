"""Abstract runtime interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Dict


@dataclass
class ExecutionResult:
    """Result from code execution."""
    success: bool
    stdout: str
    stderr: str
    exit_code: int
    timed_out: bool
    execution_time_ms: int
    memory_used_mb: float = 0.0
    error_message: Optional[str] = None


@dataclass
class RuntimeConfig:
    """Configuration for a runtime."""
    language: str
    image: str
    command: list
    file_extension: str
    timeout_seconds: int = 30
    memory_limit: str = "256m"
    cpu_quota: int = 50000
    packages: list = None  # Pre-installed packages


class Runtime(ABC):
    """
    Abstract base for code execution runtimes.

    Implement this to add new language support.
    """

    @property
    @abstractmethod
    def language(self) -> str:
        """Language identifier."""
        ...

    @property
    @abstractmethod
    def config(self) -> RuntimeConfig:
        """Runtime configuration."""
        ...

    @abstractmethod
    def run(self, code: str, timeout: int = None) -> ExecutionResult:
        """Execute code and return results."""
        ...

    @abstractmethod
    def run_tests(self, code: str, test_code: str) -> ExecutionResult:
        """Execute code with tests."""
        ...

    def is_available(self) -> bool:
        """Check if this runtime is available."""
        return True


# Runtime registry
_runtimes: Dict[str, Runtime] = {}


def register_runtime(runtime: Runtime) -> None:
    """Register a runtime."""
    _runtimes[runtime.language] = runtime


def get_runtime(language: str) -> Runtime:
    """Get a runtime by language."""
    if language not in _runtimes:
        raise ValueError(f"Unknown runtime: {language}. Available: {list(_runtimes.keys())}")
    return _runtimes[language]


def list_runtimes() -> list:
    """List available runtimes."""
    return list(_runtimes.keys())
