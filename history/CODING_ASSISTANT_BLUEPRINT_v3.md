# Intelligent Coding Assistant - Extensible Blueprint v3

**Purpose**: Build a coding assistant that grows with you
**Philosophy**: Simple core, extensible architecture, clear scaling paths
**Date**: 2025-12-12

---

## What's New in v3

| Improvement | Why It Matters |
|-------------|----------------|
| Abstract interfaces | Swap providers, add languages without rewriting |
| Tool registry | Add new tools as plugins |
| Hook system | Customize behavior without touching core |
| Configuration layer | Change settings without code changes |
| Clear scaling paths | Know exactly how to grow each component |

---

## Architecture Overview

### Layered Design (Start Simple, Scale When Needed)

```
┌─────────────────────────────────────────────────────────────────┐
│                        INTERFACE LAYER                          │
│   CLI  │  Web API (future)  │  IDE Plugin (future)             │
└────────┴────────────────────┴───────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                         CORE LAYER                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
│  │   Agent     │  │   Session   │  │   Event Bus (hooks)     │ │
│  │ Orchestrator│  │   Manager   │  │                         │ │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                      PROVIDER LAYER                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
│  │ LLM Provider│  │Tool Registry│  │   Runtime Registry      │ │
│  │  (Abstract) │  │  (Plugins)  │  │     (Sandboxes)         │ │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘ │
│        │                │                      │                │
│   ┌────┴────┐      ┌────┴────┐          ┌─────┴─────┐         │
│   │Anthropic│      │generate │          │  Python   │         │
│   │ OpenAI  │      │execute  │          │JavaScript │         │
│   │ Gemini  │      │analyze  │          │   Go      │         │
│   └─────────┘      │ custom  │          └───────────┘         │
│                    └─────────┘                                  │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                      STORAGE LAYER                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
│  │   Memory    │  │    File     │  │   Database (future)     │ │
│  │  (Default)  │  │   (JSON)    │  │   (PostgreSQL/SQLite)   │ │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### Key Abstractions

```python
# These interfaces allow swapping implementations

class LLMProvider(Protocol):
    """Any LLM provider must implement this."""
    def complete(self, messages: list, tools: list = None) -> Response: ...

class Tool(Protocol):
    """Any tool must implement this."""
    name: str
    description: str
    schema: dict
    def execute(self, inputs: dict) -> str: ...

class Runtime(Protocol):
    """Any code execution runtime must implement this."""
    language: str
    def run(self, code: str, timeout: int) -> ExecutionResult: ...

class Storage(Protocol):
    """Any storage backend must implement this."""
    def save(self, key: str, data: dict) -> None: ...
    def load(self, key: str) -> dict: ...
```

---

## Project Structure (Final)

```
platform/
├── src/
│   └── assistant/
│       │
│       │── __init__.py
│       ├── main.py                 # Entry point
│       ├── config.py               # Configuration management
│       │
│       ├── core/                   # Core orchestration
│       │   ├── __init__.py
│       │   ├── agent.py            # Agent loop
│       │   ├── session.py          # Conversation/session management
│       │   └── events.py           # Event bus for hooks
│       │
│       ├── providers/              # Abstract + implementations
│       │   ├── __init__.py
│       │   ├── base.py             # Abstract LLM provider
│       │   ├── anthropic.py        # Claude implementation
│       │   └── openai.py           # OpenAI implementation (future)
│       │
│       ├── tools/                  # Tool registry + tools
│       │   ├── __init__.py
│       │   ├── registry.py         # Tool registration system
│       │   ├── base.py             # Abstract tool class
│       │   ├── generate.py         # Code generation tool
│       │   ├── execute.py          # Code execution tool
│       │   ├── analyze.py          # Code analysis tool
│       │   └── explain.py          # Code explanation tool
│       │
│       ├── runtimes/               # Execution environments
│       │   ├── __init__.py
│       │   ├── base.py             # Abstract runtime
│       │   ├── docker.py           # Docker sandbox manager
│       │   └── languages/          # Language-specific configs
│       │       ├── python.py
│       │       └── javascript.py   # (future)
│       │
│       ├── storage/                # Persistence layer
│       │   ├── __init__.py
│       │   ├── base.py             # Abstract storage
│       │   ├── memory.py           # In-memory (default)
│       │   └── file.py             # File-based JSON
│       │
│       ├── interfaces/             # User interfaces
│       │   ├── __init__.py
│       │   └── cli.py              # CLI implementation
│       │
│       └── prompts/                # Prompt templates
│           ├── __init__.py
│           └── templates.py
│
├── docker/
│   ├── Dockerfile.python
│   └── Dockerfile.javascript      # (future)
│
├── plugins/                        # User-created plugins (optional)
│   └── example_tool.py
│
├── config/
│   └── default.yaml               # Default configuration
│
├── tests/
│   ├── unit/
│   │   ├── test_agent.py
│   │   ├── test_tools.py
│   │   └── test_sandbox.py
│   └── integration/
│       └── test_end_to_end.py
│
├── requirements.txt
├── pyproject.toml                 # Modern Python packaging
├── .env
├── .gitignore
└── README.md
```

---

## Phase 0: Foundation (Day 1)

**Goal**: Project setup with extensible structure

### Tasks

```
Phase 0: Foundation
├── 0.1 Environment Setup
│   ├── 0.1.1 Create virtual environment
│   ├── 0.1.2 Install core dependencies
│   ├── 0.1.3 Verify Docker is running
│   └── 0.1.4 Set up pyproject.toml for packaging
│
├── 0.2 Configuration System
│   ├── 0.2.1 Create config loader (YAML + env vars)
│   ├── 0.2.2 Define default configuration
│   └── 0.2.3 Validate configuration on startup
│
├── 0.3 Project Structure
│   ├── 0.3.1 Create all directories
│   ├── 0.3.2 Create __init__.py files
│   └── 0.3.3 Create abstract base classes (stubs)
│
└── 0.4 First API Call
    ├── 0.4.1 Implement AnthropicProvider
    └── 0.4.2 Test with simple prompt
```

### Deliverables

**pyproject.toml**:
```toml
[project]
name = "coding-assistant"
version = "0.1.0"
description = "An intelligent, extensible coding assistant"
requires-python = ">=3.11"
dependencies = [
    "anthropic>=0.39.0",
    "python-dotenv>=1.0.0",
    "rich>=13.0.0",
    "docker>=7.0.0",
    "pyyaml>=6.0.0",
    "pydantic>=2.0.0",
]

[project.optional-dependencies]
dev = ["pytest>=8.0.0", "pytest-asyncio>=0.23.0", "ruff>=0.1.0"]

[project.scripts]
assist = "assistant.main:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

**src/assistant/config.py**:
```python
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


@dataclass
class SandboxConfig:
    enabled: bool = True
    timeout_seconds: int = 30
    memory_limit: str = "256m"
    cpu_quota: int = 50000
    network_enabled: bool = False


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

        if config_path and config_path.exists():
            with open(config_path) as f:
                config_data = yaml.safe_load(f) or {}

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
```

**config/default.yaml**:
```yaml
llm:
  provider: anthropic
  model: claude-sonnet-4-20250514
  max_tokens: 4096
  temperature: 0.7

sandbox:
  enabled: true
  timeout_seconds: 30
  memory_limit: "256m"
  cpu_quota: 50000
  network_enabled: false
```

### Success Criteria
- [ ] `pip install -e .` works
- [ ] `assist --version` prints version
- [ ] Configuration loads from YAML and env vars
- [ ] Project structure matches spec

---

## Phase 1: Core Abstractions (Days 2-4)

**Goal**: Build the extensible foundation

### Tasks

```
Phase 1: Core Abstractions
├── 1.1 LLM Provider Interface
│   ├── 1.1.1 Define LLMProvider protocol
│   ├── 1.1.2 Define Response dataclass
│   ├── 1.1.3 Implement AnthropicProvider
│   └── 1.1.4 Add provider factory function
│
├── 1.2 Tool System
│   ├── 1.2.1 Define Tool protocol
│   ├── 1.2.2 Create ToolRegistry class
│   ├── 1.2.3 Implement @tool decorator
│   └── 1.2.4 Add tool discovery (auto-register)
│
├── 1.3 Event System
│   ├── 1.3.1 Create EventBus class
│   ├── 1.3.2 Define core events (before_llm, after_llm, etc.)
│   ├── 1.3.3 Implement subscribe/emit pattern
│   └── 1.3.4 Add hook registration
│
└── 1.4 Session Management
    ├── 1.4.1 Create Session class
    ├── 1.4.2 Manage conversation history
    ├── 1.4.3 Handle context limits
    └── 1.4.4 Add session serialization
```

### Key Files

**src/assistant/providers/base.py**:
```python
"""Abstract LLM provider interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Any, Protocol


@dataclass
class Message:
    role: str  # "user" | "assistant"
    content: str


@dataclass
class ToolCall:
    id: str
    name: str
    inputs: dict


@dataclass
class Response:
    """Unified response format from any LLM provider."""
    content: str
    tool_calls: List[ToolCall]
    stop_reason: str  # "end_turn" | "tool_use"
    usage: dict  # token counts
    raw: Any  # original response for debugging


class LLMProvider(ABC):
    """
    Abstract base for LLM providers.

    Implement this to add new providers (OpenAI, Gemini, local models, etc.)
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider identifier."""
        ...

    @abstractmethod
    def complete(
        self,
        messages: List[Message],
        system: Optional[str] = None,
        tools: Optional[List[dict]] = None,
    ) -> Response:
        """
        Send messages to the LLM and get a response.

        Args:
            messages: Conversation history
            system: System prompt
            tools: Tool definitions (for function calling)

        Returns:
            Unified Response object
        """
        ...

    def supports_tools(self) -> bool:
        """Whether this provider supports tool/function calling."""
        return True

    def supports_streaming(self) -> bool:
        """Whether this provider supports streaming responses."""
        return False
```

**src/assistant/providers/anthropic.py**:
```python
"""Anthropic Claude provider implementation."""

import anthropic
from typing import List, Optional
from .base import LLMProvider, Response, Message, ToolCall
from ..config import get_config


class AnthropicProvider(LLMProvider):
    """Claude via Anthropic API."""

    def __init__(self):
        config = get_config()
        self.client = anthropic.Anthropic(api_key=config.anthropic_api_key)
        self.model = config.llm.model
        self.max_tokens = config.llm.max_tokens

    @property
    def name(self) -> str:
        return "anthropic"

    def complete(
        self,
        messages: List[Message],
        system: Optional[str] = None,
        tools: Optional[List[dict]] = None,
    ) -> Response:
        """Send request to Claude."""

        # Convert to Anthropic format
        api_messages = [{"role": m.role, "content": m.content} for m in messages]

        kwargs = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "messages": api_messages,
        }

        if system:
            kwargs["system"] = system
        if tools:
            kwargs["tools"] = tools

        response = self.client.messages.create(**kwargs)

        # Parse response
        content = ""
        tool_calls = []

        for block in response.content:
            if hasattr(block, "text"):
                content = block.text
            elif block.type == "tool_use":
                tool_calls.append(ToolCall(
                    id=block.id,
                    name=block.name,
                    inputs=block.input
                ))

        return Response(
            content=content,
            tool_calls=tool_calls,
            stop_reason=response.stop_reason,
            usage={
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
            },
            raw=response
        )


# Provider factory
_providers = {
    "anthropic": AnthropicProvider,
}


def get_provider(name: str = None) -> LLMProvider:
    """Get an LLM provider by name."""
    config = get_config()
    provider_name = name or config.llm.provider

    if provider_name not in _providers:
        raise ValueError(f"Unknown provider: {provider_name}. Available: {list(_providers.keys())}")

    return _providers[provider_name]()


def register_provider(name: str, provider_class: type):
    """Register a new provider (for plugins)."""
    _providers[name] = provider_class
```

**src/assistant/tools/base.py**:
```python
"""Abstract tool interface and registry."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any, Callable, List


@dataclass
class ToolSchema:
    """JSON Schema for tool inputs."""
    type: str = "object"
    properties: Dict[str, Any] = None
    required: List[str] = None


class Tool(ABC):
    """
    Abstract base for all tools.

    Implement this to add new capabilities to the agent.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique tool identifier."""
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        """What this tool does (shown to LLM)."""
        ...

    @property
    @abstractmethod
    def schema(self) -> ToolSchema:
        """Input parameters schema."""
        ...

    @abstractmethod
    def execute(self, **kwargs) -> str:
        """
        Execute the tool with given inputs.

        Returns:
            String result to send back to LLM
        """
        ...

    def to_dict(self) -> dict:
        """Convert to Claude tool format."""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": {
                "type": self.schema.type,
                "properties": self.schema.properties or {},
                "required": self.schema.required or [],
            }
        }
```

**src/assistant/tools/registry.py**:
```python
"""Tool registration and discovery system."""

from typing import Dict, List, Optional, Type
from .base import Tool


class ToolRegistry:
    """
    Central registry for all available tools.

    Supports:
    - Manual registration
    - Decorator-based registration
    - Plugin discovery
    """

    _instance: Optional["ToolRegistry"] = None

    def __init__(self):
        self._tools: Dict[str, Tool] = {}

    @classmethod
    def get(cls) -> "ToolRegistry":
        """Get singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def register(self, tool: Tool) -> None:
        """Register a tool instance."""
        if tool.name in self._tools:
            raise ValueError(f"Tool '{tool.name}' already registered")
        self._tools[tool.name] = tool

    def get_tool(self, name: str) -> Optional[Tool]:
        """Get a tool by name."""
        return self._tools.get(name)

    def list_tools(self) -> List[Tool]:
        """Get all registered tools."""
        return list(self._tools.values())

    def to_dicts(self) -> List[dict]:
        """Get all tools in Claude format."""
        return [tool.to_dict() for tool in self._tools.values()]

    def execute(self, name: str, inputs: dict) -> str:
        """Execute a tool by name."""
        tool = self.get_tool(name)
        if not tool:
            return f"Error: Unknown tool '{name}'"

        try:
            return tool.execute(**inputs)
        except Exception as e:
            return f"Error executing {name}: {str(e)}"


def register_tool(tool_class: Type[Tool]) -> Type[Tool]:
    """Decorator to auto-register a tool class."""
    registry = ToolRegistry.get()
    registry.register(tool_class())
    return tool_class
```

**src/assistant/core/events.py**:
```python
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
                print(f"Warning: Event handler error: {e}")

    def clear(self) -> None:
        """Clear all handlers (useful for testing)."""
        self._handlers = {}
```

### Success Criteria
- [ ] Can swap LLM provider via config
- [ ] Tools auto-register with decorator
- [ ] Events fire at correct times
- [ ] Session manages conversation history

---

## Phase 2: Built-in Tools (Days 5-8)

**Goal**: Implement core tools using the new framework

### Tasks

```
Phase 2: Built-in Tools
├── 2.1 Generate Tool
│   ├── 2.1.1 Implement GenerateTool class
│   ├── 2.1.2 Add prompt templates
│   ├── 2.1.3 Extract code from responses
│   └── 2.1.4 Validate generated code
│
├── 2.2 Execute Tool
│   ├── 2.2.1 Implement ExecuteTool class
│   ├── 2.2.2 Wire up to Docker runtime
│   ├── 2.2.3 Format execution results
│   └── 2.2.4 Handle errors gracefully
│
├── 2.3 Analyze Tool
│   ├── 2.3.1 Implement AnalyzeTool class
│   ├── 2.3.2 Use AST for structure analysis
│   ├── 2.3.3 Calculate complexity metrics
│   └── 2.3.4 Detect common issues
│
├── 2.4 Explain Tool
│   ├── 2.4.1 Implement ExplainTool class
│   ├── 2.4.2 Use LLM for explanations
│   └── 2.4.3 Format output nicely
│
└── 2.5 Fix Tool
    ├── 2.5.1 Implement FixTool class
    ├── 2.5.2 Parse error messages
    └── 2.5.3 Generate corrected code
```

### Key Files

**src/assistant/tools/generate.py**:
```python
"""Code generation tool."""

from .base import Tool, ToolSchema
from .registry import register_tool
from ..providers import get_provider
from ..prompts.templates import GENERATE_CODE


@register_tool
class GenerateTool(Tool):
    """Generate code from natural language descriptions."""

    @property
    def name(self) -> str:
        return "generate_code"

    @property
    def description(self) -> str:
        return "Generate Python code from a natural language description."

    @property
    def schema(self) -> ToolSchema:
        return ToolSchema(
            properties={
                "description": {
                    "type": "string",
                    "description": "What the code should do"
                },
                "include_tests": {
                    "type": "boolean",
                    "description": "Whether to generate test cases",
                    "default": False
                }
            },
            required=["description"]
        )

    def execute(self, description: str, include_tests: bool = False) -> str:
        """Generate code based on description."""
        from ..providers.base import Message

        prompt = GENERATE_CODE.format(
            description=description,
            with_tests="Include pytest test cases." if include_tests else ""
        )

        provider = get_provider()
        response = provider.complete([Message(role="user", content=prompt)])

        # Extract and validate code
        code = self._extract_code(response.content)

        if code and self._validate_syntax(code):
            return f"Generated code:\n```python\n{code}\n```"
        else:
            return f"Generated response:\n{response.content}"

    def _extract_code(self, text: str) -> str:
        """Extract code from markdown code blocks."""
        import re
        pattern = r"```python\n(.*?)```"
        matches = re.findall(pattern, text, re.DOTALL)
        return matches[0].strip() if matches else ""

    def _validate_syntax(self, code: str) -> bool:
        """Check if code has valid Python syntax."""
        import ast
        try:
            ast.parse(code)
            return True
        except SyntaxError:
            return False
```

**src/assistant/tools/execute.py**:
```python
"""Code execution tool."""

from .base import Tool, ToolSchema
from .registry import register_tool
from ..runtimes import get_runtime


@register_tool
class ExecuteTool(Tool):
    """Execute code in a safe sandbox."""

    @property
    def name(self) -> str:
        return "execute_code"

    @property
    def description(self) -> str:
        return "Run Python code in a safe sandbox and return the output."

    @property
    def schema(self) -> ToolSchema:
        return ToolSchema(
            properties={
                "code": {
                    "type": "string",
                    "description": "Python code to execute"
                },
                "timeout": {
                    "type": "integer",
                    "description": "Timeout in seconds (default: 30)",
                    "default": 30
                }
            },
            required=["code"]
        )

    def execute(self, code: str, timeout: int = 30) -> str:
        """Execute code and return results."""
        runtime = get_runtime("python")
        result = runtime.run(code, timeout=timeout)

        if result.success:
            output = result.stdout.strip()
            return f"Execution successful:\n{output}" if output else "Execution successful (no output)"
        elif result.timed_out:
            return f"Execution timed out after {timeout} seconds"
        else:
            return f"Execution failed:\n{result.stderr}"
```

**src/assistant/tools/analyze.py**:
```python
"""Code analysis tool."""

import ast
from dataclasses import dataclass
from typing import List

from .base import Tool, ToolSchema
from .registry import register_tool


@dataclass
class AnalysisResult:
    functions: List[str]
    classes: List[str]
    imports: List[str]
    line_count: int
    complexity: int
    issues: List[str]


@register_tool
class AnalyzeTool(Tool):
    """Analyze code structure and quality."""

    @property
    def name(self) -> str:
        return "analyze_code"

    @property
    def description(self) -> str:
        return "Analyze Python code structure, find functions, classes, and potential issues."

    @property
    def schema(self) -> ToolSchema:
        return ToolSchema(
            properties={
                "code": {
                    "type": "string",
                    "description": "Python code to analyze"
                }
            },
            required=["code"]
        )

    def execute(self, code: str) -> str:
        """Analyze code and return structured results."""
        result = self._analyze(code)

        return f"""Code Analysis:
- Functions: {', '.join(result.functions) or 'None'}
- Classes: {', '.join(result.classes) or 'None'}
- Imports: {', '.join(result.imports) or 'None'}
- Lines: {result.line_count}
- Cyclomatic Complexity: {result.complexity}
- Issues: {'; '.join(result.issues) or 'None found'}"""

    def _analyze(self, code: str) -> AnalysisResult:
        """Perform static analysis."""
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return AnalysisResult(
                functions=[], classes=[], imports=[],
                line_count=len(code.splitlines()),
                complexity=0,
                issues=[f"Syntax error at line {e.lineno}: {e.msg}"]
            )

        functions = []
        classes = []
        imports = []
        issues = []
        complexity = 1

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                functions.append(node.name)
                if not ast.get_docstring(node):
                    issues.append(f"Function '{node.name}' missing docstring")

            elif isinstance(node, ast.ClassDef):
                classes.append(node.name)

            elif isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)

            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)

            elif isinstance(node, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1

        return AnalysisResult(
            functions=functions,
            classes=classes,
            imports=imports,
            line_count=len(code.splitlines()),
            complexity=complexity,
            issues=issues
        )
```

### Success Criteria
- [ ] All tools register automatically on import
- [ ] Generate produces valid Python code
- [ ] Execute runs code in Docker sandbox
- [ ] Analyze extracts meaningful metrics

---

## Phase 3: Runtime System (Days 9-12)

**Goal**: Extensible code execution with Docker

### Tasks

```
Phase 3: Runtime System
├── 3.1 Abstract Runtime
│   ├── 3.1.1 Define Runtime protocol
│   ├── 3.1.2 Define ExecutionResult dataclass
│   └── 3.1.3 Create runtime factory
│
├── 3.2 Docker Manager
│   ├── 3.2.1 Create DockerManager class
│   ├── 3.2.2 Handle image building
│   ├── 3.2.3 Implement container pooling
│   └── 3.2.4 Add cleanup logic
│
├── 3.3 Python Runtime
│   ├── 3.3.1 Create Dockerfile.python
│   ├── 3.3.2 Implement PythonRuntime class
│   ├── 3.3.3 Add security constraints
│   └── 3.3.4 Handle test execution
│
├── 3.4 Language Configuration
│   ├── 3.4.1 Create language config format
│   ├── 3.4.2 Define Python config
│   └── 3.4.3 Stub JavaScript config (for future)
│
└── 3.5 Security Hardening
    ├── 3.5.1 Disable network
    ├── 3.5.2 Set resource limits
    ├── 3.5.3 Drop capabilities
    └── 3.5.4 Add seccomp profile
```

### Key Files

**src/assistant/runtimes/base.py**:
```python
"""Abstract runtime interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Dict, Any


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
```

**src/assistant/runtimes/docker.py**:
```python
"""Docker-based sandbox manager."""

import time
import docker
from docker.errors import ImageNotFound, ContainerError
from typing import Optional

from .base import Runtime, RuntimeConfig, ExecutionResult, register_runtime
from ..config import get_config


class DockerRuntime(Runtime):
    """Base class for Docker-based runtimes."""

    def __init__(self, config: RuntimeConfig):
        self._config = config
        self.client = docker.from_env()
        self._ensure_image()

    @property
    def language(self) -> str:
        return self._config.language

    @property
    def config(self) -> RuntimeConfig:
        return self._config

    def _ensure_image(self):
        """Build image if it doesn't exist."""
        try:
            self.client.images.get(self._config.image)
        except ImageNotFound:
            print(f"Building {self._config.image}...")
            self.client.images.build(
                path="docker",
                dockerfile=f"Dockerfile.{self._config.language}",
                tag=self._config.image
            )

    def run(self, code: str, timeout: int = None) -> ExecutionResult:
        """Execute code in container."""
        timeout = timeout or self._config.timeout_seconds
        app_config = get_config()

        container = None
        start_time = time.time()

        try:
            container = self.client.containers.run(
                self._config.image,
                command=self._config.command + [code],
                detach=True,
                mem_limit=self._config.memory_limit,
                cpu_quota=self._config.cpu_quota,
                network_mode="none" if not app_config.sandbox.network_enabled else "bridge",
                read_only=True,
                pids_limit=50,
                cap_drop=["ALL"],
                security_opt=["no-new-privileges"],
                tmpfs={"/tmp": "size=10M,mode=1777"},
            )

            result = container.wait(timeout=timeout)
            execution_time = int((time.time() - start_time) * 1000)

            stdout = container.logs(stdout=True, stderr=False).decode()
            stderr = container.logs(stdout=False, stderr=True).decode()

            return ExecutionResult(
                success=(result["StatusCode"] == 0),
                stdout=stdout,
                stderr=stderr,
                exit_code=result["StatusCode"],
                timed_out=False,
                execution_time_ms=execution_time,
            )

        except Exception as e:
            execution_time = int((time.time() - start_time) * 1000)
            is_timeout = "timed out" in str(e).lower()

            return ExecutionResult(
                success=False,
                stdout="",
                stderr="" if is_timeout else str(e),
                exit_code=-1,
                timed_out=is_timeout,
                execution_time_ms=execution_time,
                error_message="Execution timed out" if is_timeout else str(e),
            )

        finally:
            if container:
                try:
                    container.remove(force=True)
                except:
                    pass

    def run_tests(self, code: str, test_code: str) -> ExecutionResult:
        """Run code with tests."""
        # Subclasses should override for language-specific test runners
        combined = f"{code}\n\n{test_code}"
        return self.run(combined)

    def is_available(self) -> bool:
        """Check if Docker is available."""
        try:
            self.client.ping()
            return True
        except:
            return False
```

**src/assistant/runtimes/languages/python.py**:
```python
"""Python runtime configuration."""

from ..base import RuntimeConfig, register_runtime
from ..docker import DockerRuntime


PYTHON_CONFIG = RuntimeConfig(
    language="python",
    image="assistant-python:latest",
    command=["python", "-c"],
    file_extension=".py",
    timeout_seconds=30,
    memory_limit="256m",
    packages=["pytest", "numpy", "pandas"],
)


class PythonRuntime(DockerRuntime):
    """Python execution runtime."""

    def __init__(self):
        super().__init__(PYTHON_CONFIG)

    def run_tests(self, code: str, test_code: str) -> ExecutionResult:
        """Run Python code with pytest."""
        wrapper = f'''
import sys
sys.path.insert(0, '/tmp')

with open('/tmp/test_module.py', 'w') as f:
    f.write("""{code}

{test_code}""")

import pytest
sys.exit(pytest.main(['/tmp/test_module.py', '-v', '--tb=short']))
'''
        return self.run(wrapper)


# Auto-register
register_runtime(PythonRuntime())
```

**docker/Dockerfile.python**:
```dockerfile
FROM python:3.12-slim

# Security: non-root user
RUN useradd -m -s /bin/bash sandbox

# Install common packages
RUN pip install --no-cache-dir \
    pytest \
    numpy \
    pandas \
    requests

WORKDIR /sandbox
RUN chown sandbox:sandbox /sandbox

USER sandbox

CMD ["python", "--version"]
```

### Success Criteria
- [ ] Runtime abstraction supports multiple languages
- [ ] Python code executes in Docker
- [ ] Security constraints enforced (no network, resource limits)
- [ ] Test execution works with pytest

---

## Phase 4: Agent Core (Days 13-16)

**Goal**: Build the intelligent agent loop

### Tasks

```
Phase 4: Agent Core
├── 4.1 Agent Implementation
│   ├── 4.1.1 Create Agent class
│   ├── 4.1.2 Implement think-act-observe loop
│   ├── 4.1.3 Handle tool calls
│   ├── 4.1.4 Manage conversation state
│   └── 4.1.5 Add iteration limits
│
├── 4.2 Session Management
│   ├── 4.2.1 Create Session class
│   ├── 4.2.2 Track messages
│   ├── 4.2.3 Serialize/deserialize
│   └── 4.2.4 Handle context limits
│
├── 4.3 Event Integration
│   ├── 4.3.1 Emit events at key points
│   ├── 4.3.2 Allow hooks to modify behavior
│   └── 4.3.3 Add logging hooks
│
└── 4.4 Error Recovery
    ├── 4.4.1 Handle LLM errors
    ├── 4.4.2 Handle tool failures
    ├── 4.4.3 Implement retry logic
    └── 4.4.4 Graceful degradation
```

### Key Files

**src/assistant/core/agent.py**:
```python
"""The intelligent agent implementation."""

from typing import Callable, Optional, List
from dataclasses import dataclass

from ..providers import get_provider
from ..providers.base import Message, Response
from ..tools.registry import ToolRegistry
from .events import EventBus, EventType
from .session import Session


@dataclass
class AgentConfig:
    max_iterations: int = 10
    system_prompt: str = None


DEFAULT_SYSTEM = """You are an intelligent Python coding assistant with access to tools.

Available tools:
- generate_code: Write Python code from descriptions
- execute_code: Run code in a safe sandbox
- analyze_code: Analyze code structure and quality
- explain_code: Explain what code does
- fix_error: Fix broken code

Workflow:
1. Understand what the user wants
2. Use appropriate tools to help
3. If code fails, fix and retry
4. Explain your actions clearly

Always test code before saying it works."""


class Agent:
    """
    The main agent that orchestrates tools and LLM.

    The agent loop:
    1. Receive user input
    2. Send to LLM with available tools
    3. If LLM requests tool use -> execute tool -> send result back
    4. Repeat until LLM gives final response or max iterations
    """

    def __init__(self, config: AgentConfig = None):
        self.config = config or AgentConfig()
        self.provider = get_provider()
        self.tools = ToolRegistry.get()
        self.events = EventBus.get()
        self.session = Session()

    def run(
        self,
        user_input: str,
        on_thinking: Callable[[], None] = None,
        on_tool_use: Callable[[str, dict], None] = None,
    ) -> str:
        """
        Run the agent loop for a user request.

        Args:
            user_input: The user's message
            on_thinking: Callback when agent is thinking
            on_tool_use: Callback when tool is used (name, inputs)

        Returns:
            The agent's final response
        """
        # Add user message
        self.session.add_message(Message(role="user", content=user_input))

        system = self.config.system_prompt or DEFAULT_SYSTEM
        tool_dicts = self.tools.to_dicts()

        for iteration in range(self.config.max_iterations):
            self.events.emit(EventType.AGENT_ITERATION_START, {
                "iteration": iteration,
                "messages": len(self.session.messages)
            })

            if on_thinking:
                on_thinking()

            # Get LLM response
            self.events.emit(EventType.BEFORE_LLM_CALL, {
                "messages": self.session.messages,
                "tools": tool_dicts
            })

            response = self.provider.complete(
                messages=self.session.messages,
                system=system,
                tools=tool_dicts if tool_dicts else None,
            )

            self.events.emit(EventType.AFTER_LLM_CALL, {
                "response": response
            })

            # Check if done
            if response.stop_reason == "end_turn":
                self.session.add_message(Message(
                    role="assistant",
                    content=response.content
                ))
                self.events.emit(EventType.AGENT_COMPLETE, {
                    "iterations": iteration + 1,
                    "response": response.content
                })
                return response.content

            # Handle tool calls
            if response.tool_calls:
                # Add assistant message with tool calls (for context)
                self.session.add_raw({
                    "role": "assistant",
                    "content": response.raw.content  # Keep original format
                })

                tool_results = []
                for tool_call in response.tool_calls:
                    self.events.emit(EventType.BEFORE_TOOL_EXECUTE, {
                        "tool": tool_call.name,
                        "inputs": tool_call.inputs
                    })

                    if on_tool_use:
                        on_tool_use(tool_call.name, tool_call.inputs)

                    result = self.tools.execute(tool_call.name, tool_call.inputs)

                    self.events.emit(EventType.AFTER_TOOL_EXECUTE, {
                        "tool": tool_call.name,
                        "result": result
                    })

                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_call.id,
                        "content": result
                    })

                # Add tool results
                self.session.add_raw({
                    "role": "user",
                    "content": tool_results
                })

            self.events.emit(EventType.AGENT_ITERATION_END, {
                "iteration": iteration
            })

        return "I've reached my iteration limit. Please try a simpler request."

    def clear(self):
        """Clear conversation history."""
        self.session.clear()
```

**src/assistant/core/session.py**:
```python
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
        with open(path) as f:
            data = json.load(f)

        session = cls(id=data["id"])
        session._raw_messages = data["messages"]
        session.metadata = data.get("metadata", {})

        # Reconstruct typed messages
        for raw in session._raw_messages:
            if isinstance(raw.get("content"), str):
                session.messages.append(Message(
                    role=raw["role"],
                    content=raw["content"]
                ))

        return session

    def token_estimate(self) -> int:
        """Rough estimate of tokens in conversation."""
        text = "".join(str(m) for m in self._raw_messages)
        return len(text) // 4  # ~4 chars per token
```

### Success Criteria
- [ ] Agent completes multi-step tasks
- [ ] "Create and test a factorial function" works end-to-end
- [ ] Agent retries when code fails
- [ ] Events fire at correct times
- [ ] Session saves/loads correctly

---

## Phase 5: CLI & Polish (Days 17-20)

**Goal**: User interface and finishing touches

### Tasks

```
Phase 5: CLI & Polish
├── 5.1 CLI Implementation
│   ├── 5.1.1 Create main CLI with Rich
│   ├── 5.1.2 Add command parsing
│   ├── 5.1.3 Display tool usage
│   ├── 5.1.4 Show streaming output
│   └── 5.1.5 Add /help, /clear, /save, /load
│
├── 5.2 Quality of Life
│   ├── 5.2.1 Syntax highlighting
│   ├── 5.2.2 Progress indicators
│   ├── 5.2.3 Error formatting
│   └── 5.2.4 Command history
│
├── 5.3 Testing
│   ├── 5.3.1 Unit tests for tools
│   ├── 5.3.2 Unit tests for agent
│   ├── 5.3.3 Integration tests
│   └── 5.3.4 Mock LLM for testing
│
└── 5.4 Documentation
    ├── 5.4.1 Write README
    ├── 5.4.2 Add docstrings
    ├── 5.4.3 Create examples
    └── 5.4.4 Document extension points
```

### CLI Implementation

**src/assistant/interfaces/cli.py**:
```python
"""Command-line interface."""

from pathlib import Path
from rich.console import Console
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich.panel import Panel

from ..core.agent import Agent
from ..core.events import EventBus, EventType


console = Console()


def main():
    """Main CLI entry point."""
    agent = Agent()

    # Set up event handlers for UI
    events = EventBus.get()

    @events.on(EventType.BEFORE_TOOL_EXECUTE)
    def show_tool_use(event):
        console.print(f"[dim]Using {event.data['tool']}...[/]")

    console.print(Panel.fit(
        "[bold green]Coding Assistant[/]\n"
        "Type [bold]/help[/] for commands, [bold]/quit[/] to exit",
        border_style="green"
    ))

    while True:
        try:
            user_input = console.input("\n[bold blue]You:[/] ").strip()

            if not user_input:
                continue

            # Handle commands
            if user_input.startswith("/"):
                if handle_command(user_input, agent):
                    continue
                if user_input == "/quit":
                    break

            # Run agent
            with console.status("[bold green]Thinking..."):
                response = agent.run(user_input)

            console.print("\n[bold green]Assistant:[/]")
            console.print(Markdown(response))

        except KeyboardInterrupt:
            console.print("\n[dim]Use /quit to exit[/]")
        except Exception as e:
            console.print(f"[red]Error: {e}[/]")


def handle_command(cmd: str, agent: Agent) -> bool:
    """Handle slash commands. Returns True if handled."""

    if cmd == "/help":
        console.print("""
[bold]Commands:[/]
  /help      - Show this help
  /clear     - Clear conversation
  /save FILE - Save session to file
  /load FILE - Load session from file
  /tools     - List available tools
  /quit      - Exit
        """)
        return True

    if cmd == "/clear":
        agent.clear()
        console.print("[dim]Conversation cleared[/]")
        return True

    if cmd.startswith("/save "):
        path = Path(cmd[6:].strip())
        agent.session.save(path)
        console.print(f"[green]Session saved to {path}[/]")
        return True

    if cmd.startswith("/load "):
        from ..core.session import Session
        path = Path(cmd[6:].strip())
        agent.session = Session.load(path)
        console.print(f"[green]Session loaded from {path}[/]")
        return True

    if cmd == "/tools":
        from ..tools.registry import ToolRegistry
        tools = ToolRegistry.get().list_tools()
        console.print("[bold]Available tools:[/]")
        for tool in tools:
            console.print(f"  [cyan]{tool.name}[/]: {tool.description}")
        return True

    return False


if __name__ == "__main__":
    main()
```

### Success Criteria
- [ ] CLI is polished and user-friendly
- [ ] All commands work correctly
- [ ] Tests pass with 80%+ coverage
- [ ] README documents all features and extension points

---

## Scaling Paths

### How to Add a New LLM Provider

```python
# src/assistant/providers/openai.py

from .base import LLMProvider, Response, Message
from .anthropic import register_provider

class OpenAIProvider(LLMProvider):
    @property
    def name(self) -> str:
        return "openai"

    def complete(self, messages, system=None, tools=None) -> Response:
        # Implement OpenAI-specific logic
        ...

# Register it
register_provider("openai", OpenAIProvider)
```

**Config change**: `llm.provider: openai`

---

### How to Add a New Tool

```python
# plugins/my_tool.py (or src/assistant/tools/my_tool.py)

from assistant.tools.base import Tool, ToolSchema
from assistant.tools.registry import register_tool

@register_tool
class MyCustomTool(Tool):
    @property
    def name(self) -> str:
        return "my_tool"

    @property
    def description(self) -> str:
        return "Does something useful"

    @property
    def schema(self) -> ToolSchema:
        return ToolSchema(
            properties={"input": {"type": "string"}},
            required=["input"]
        )

    def execute(self, input: str) -> str:
        return f"Processed: {input}"
```

**Usage**: Just import the file, tool auto-registers.

---

### How to Add a New Language Runtime

```python
# src/assistant/runtimes/languages/javascript.py

from ..base import RuntimeConfig, register_runtime
from ..docker import DockerRuntime

JS_CONFIG = RuntimeConfig(
    language="javascript",
    image="assistant-js:latest",
    command=["node", "-e"],
    file_extension=".js",
    packages=["jest"],
)

class JavaScriptRuntime(DockerRuntime):
    def __init__(self):
        super().__init__(JS_CONFIG)

    def run_tests(self, code: str, test_code: str) -> ExecutionResult:
        # Jest-specific test running
        ...

register_runtime(JavaScriptRuntime())
```

**Also needed**: `docker/Dockerfile.javascript`

---

### How to Add Custom Behavior with Hooks

```python
# plugins/logging_hook.py

from assistant.core.events import EventBus, EventType
import logging

bus = EventBus.get()

@bus.on(EventType.BEFORE_TOOL_EXECUTE)
def log_tool_calls(event):
    logging.info(f"Tool: {event.data['tool']}, Inputs: {event.data['inputs']}")

@bus.on(EventType.AFTER_LLM_CALL)
def log_token_usage(event):
    usage = event.data['response'].usage
    logging.info(f"Tokens: {usage['input_tokens']} in, {usage['output_tokens']} out")
```

---

### How to Add Web API (Future)

```python
# src/assistant/interfaces/api.py

from fastapi import FastAPI
from ..core.agent import Agent

app = FastAPI()
agent = Agent()

@app.post("/chat")
async def chat(message: str):
    response = agent.run(message)
    return {"response": response}
```

---

### How to Add Database Storage (Future)

```python
# src/assistant/storage/postgres.py

from .base import Storage
import asyncpg

class PostgresStorage(Storage):
    def __init__(self, connection_string: str):
        self.conn_string = connection_string

    async def save(self, key: str, data: dict):
        # Implement postgres save
        ...

    async def load(self, key: str) -> dict:
        # Implement postgres load
        ...
```

---

## Summary: Extension Points

| Want to... | Implement... | Register via... |
|------------|--------------|-----------------|
| Add LLM provider | `LLMProvider` | `register_provider()` |
| Add new tool | `Tool` | `@register_tool` decorator |
| Add language | `Runtime` + Dockerfile | `register_runtime()` |
| Add custom behavior | Event handler | `@events.on()` decorator |
| Add storage backend | `Storage` | Config change |
| Add UI (web/IDE) | Interface module | Entry point |

---

## Quick Start Checklist

After completing all phases, you should be able to:

- [ ] `pip install -e .` - Install the package
- [ ] `assist` - Start the CLI
- [ ] "Create a function to check if a number is prime" - Agent generates and tests code
- [ ] `/tools` - See all available tools
- [ ] `/save mysession.json` - Save conversation
- [ ] Add a new tool in `plugins/` and have it work immediately
- [ ] Change `config/default.yaml` to adjust behavior

---

## Key Differences: v2 → v3

| Aspect | v2 | v3 |
|--------|----|----|
| Tool system | Functions in agent.py | Plugin registry with decorators |
| LLM provider | Hardcoded Anthropic | Abstract interface, swappable |
| Runtimes | Single Python sandbox | Multi-language with registry |
| Configuration | Basic env vars | YAML + env with validation |
| Events | None | Full pub/sub system |
| Structure | Flat files | Layered architecture |
| Extensibility | Requires core changes | Plugin-based, no core changes |

---

**Document Version**: 3.0 (Extensible Edition)
**Created**: 2025-12-12
**Philosophy**: Simple core, infinite extensibility, clear growth paths
