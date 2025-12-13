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

    def __post_init__(self):
        """Validate configuration values."""
        if self.max_tokens < 1 or self.max_tokens > 200000:
            raise ValueError(f"max_tokens must be between 1 and 200000, got {self.max_tokens}")
        if self.temperature < 0 or self.temperature > 1:
            raise ValueError(f"temperature must be between 0 and 1, got {self.temperature}")


@dataclass
class SandboxConfig:
    enabled: bool = True
    timeout_seconds: int = 30
    memory_limit: str = "256m"
    cpu_quota: int = 50000
    network_enabled: bool = False

    def __post_init__(self):
        """Validate configuration values."""
        if self.timeout_seconds < 1 or self.timeout_seconds > 300:
            raise ValueError(f"timeout_seconds must be between 1 and 300, got {self.timeout_seconds}")
        if self.cpu_quota < 1000 or self.cpu_quota > 1000000:
            raise ValueError(f"cpu_quota must be between 1000 and 1000000, got {self.cpu_quota}")


@dataclass
class Config:
    """Main configuration container."""
    llm: LLMConfig = field(default_factory=LLMConfig)
    sandbox: SandboxConfig = field(default_factory=SandboxConfig)

    # API Keys (from environment)
    anthropic_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None

    def __post_init__(self):
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")

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
        )


# Global config instance
_config: Optional[Config] = None


def get_config() -> Config:
    """Get the global config instance."""
    global _config
    if _config is None:
        _config = Config.load()
    return _config
