"""Configuration management with validation."""

import os
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field
from dotenv import load_dotenv
import yaml

load_dotenv()


@dataclass
class LLMConfig:
    provider: str = "anthropic"
    model: str = "claude-sonnet-4-20250514"
    max_tokens: int = 4096
    temperature: float = 0.7

    # Timeout and retry configuration
    timeout_seconds: int = 60
    max_retries: int = 3
    retry_delay_base: float = 1.0  # Base delay in seconds for exponential backoff

    # Rate limiting
    rate_limit_requests_per_minute: int = 50

    def __post_init__(self):
        """Validate configuration values."""
        valid_providers = {"anthropic", "openai"}
        if self.provider not in valid_providers:
            raise ValueError(f"provider must be one of {valid_providers}, got '{self.provider}'")
        if self.max_tokens < 1 or self.max_tokens > 200000:
            raise ValueError(f"max_tokens must be between 1 and 200000, got {self.max_tokens}")
        if self.temperature < 0 or self.temperature > 1:
            raise ValueError(f"temperature must be between 0 and 1, got {self.temperature}")
        if self.timeout_seconds < 1 or self.timeout_seconds > 600:
            raise ValueError(f"timeout_seconds must be between 1 and 600, got {self.timeout_seconds}")
        if self.max_retries < 0 or self.max_retries > 10:
            raise ValueError(f"max_retries must be between 0 and 10, got {self.max_retries}")
        if self.retry_delay_base < 0.1 or self.retry_delay_base > 60:
            raise ValueError(f"retry_delay_base must be between 0.1 and 60, got {self.retry_delay_base}")
        if self.rate_limit_requests_per_minute < 1 or self.rate_limit_requests_per_minute > 1000:
            raise ValueError(f"rate_limit_requests_per_minute must be between 1 and 1000, got {self.rate_limit_requests_per_minute}")


@dataclass
class SessionConfig:
    """Session management configuration."""
    max_messages: int = 100  # Maximum messages to keep in session
    prune_strategy: str = "keep_first_and_last"  # How to prune when limit reached

    def __post_init__(self):
        """Validate configuration values."""
        if self.max_messages < 2:
            raise ValueError(f"max_messages must be at least 2, got {self.max_messages}")
        if self.max_messages > 10000:
            raise ValueError(f"max_messages must be at most 10000, got {self.max_messages}")

        valid_strategies = {"keep_first_and_last", "keep_last", "fifo"}
        if self.prune_strategy not in valid_strategies:
            raise ValueError(
                f"prune_strategy must be one of {valid_strategies}, got '{self.prune_strategy}'"
            )


@dataclass
class SandboxConfig:
    enabled: bool = True
    timeout_seconds: int = 30
    memory_limit: str = "256m"
    cpu_quota: int = 50000
    network_enabled: bool = False
    seccomp_profile_path: str = "docker/seccomp-profile.json"

    def __post_init__(self):
        """Validate configuration values."""
        if self.timeout_seconds < 1 or self.timeout_seconds > 300:
            raise ValueError(f"timeout_seconds must be between 1 and 300, got {self.timeout_seconds}")
        if self.cpu_quota < 1000 or self.cpu_quota > 1000000:
            raise ValueError(f"cpu_quota must be between 1000 and 1000000, got {self.cpu_quota}")

        # Validate memory_limit format (e.g., "256m", "1g")
        import re
        if not re.match(r'^\d+[kmg]$', self.memory_limit.lower()):
            raise ValueError(f"memory_limit must be in format like '256m' or '1g', got '{self.memory_limit}'")

        if not isinstance(self.seccomp_profile_path, str):
            raise ValueError(f"seccomp_profile_path must be a string, got {type(self.seccomp_profile_path)}")


@dataclass
class Config:
    """Main configuration container."""
    llm: LLMConfig = field(default_factory=LLMConfig)
    sandbox: SandboxConfig = field(default_factory=SandboxConfig)
    session: SessionConfig = field(default_factory=SessionConfig)

    # API Keys (from environment)
    anthropic_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None

    def __post_init__(self):
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")

    def __repr__(self) -> str:
        """
        Secure repr that masks API keys.

        Returns:
            String representation with masked sensitive data
        """
        def mask_key(key: Optional[str]) -> str:
            """Mask API key, showing only last 4 characters."""
            if not key:
                return "None"
            if len(key) <= 4:
                return "***"
            return f"***{key[-4:]}"

        return (
            f"Config("
            f"llm={self.llm!r}, "
            f"sandbox={self.sandbox!r}, "
            f"session={self.session!r}, "
            f"anthropic_api_key={mask_key(self.anthropic_api_key)}, "
            f"openai_api_key={mask_key(self.openai_api_key)})"
        )

    def __str__(self) -> str:
        """Secure string representation (delegates to __repr__)."""
        return self.__repr__()

    @classmethod
    def load(cls, config_path: Optional[Path] = None) -> "Config":
        """Load config from file, with env var overrides."""
        config_data = {}

        if config_path:
            # Validate path to prevent path traversal
            config_path = Path(config_path).resolve()
            if not config_path.exists():
                raise FileNotFoundError(f"Config file not found: {config_path}")
            if not config_path.is_file():
                raise ValueError(f"Config path is not a file: {config_path}")

            try:
                with open(config_path) as f:
                    config_data = yaml.safe_load(f) or {}
            except yaml.YAMLError as e:
                raise ValueError(f"Invalid YAML in config file: {e}")

        return cls(
            llm=LLMConfig(**config_data.get("llm", {})),
            sandbox=SandboxConfig(**config_data.get("sandbox", {})),
            session=SessionConfig(**config_data.get("session", {})),
        )


# Global config instance
_config: Optional[Config] = None


def get_config() -> Config:
    """Get the global config instance."""
    global _config
    if _config is None:
        _config = Config.load()
    return _config
