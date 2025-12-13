# Intelligent Coding Assistant - Learning Blueprint v2

**Purpose**: A first-time agent builder's guide to creating an AI coding assistant
**Philosophy**: Build incrementally, learn deeply, ship working software at each step
**Date**: 2025-12-12

---

## Design Principles for This Project

1. **Start Small, Expand Later**: Python only → multi-language later
2. **Working Software First**: Each phase produces something you can demo
3. **Learn the Fundamentals**: Understand why before adding complexity
4. **Local First**: Run everything locally before thinking about deployment
5. **Single File Start**: Begin with monoliths, extract services when needed

---

## What We're Building

An AI assistant that can:
1. **Understand** Python code you give it
2. **Guide** you with suggestions and explanations
3. **Generate** code from natural language
4. **Execute** code safely in isolation

```
┌─────────────────────────────────────────────────────────┐
│                    Your Coding Assistant                 │
│                                                          │
│   "Write a function    ──►  [LLM Brain]  ──►  Generated │
│    to sort a list"          (Claude)          Code      │
│                                  │                       │
│                                  ▼                       │
│                         [Safe Sandbox]                   │
│                          Run & Test                      │
│                              │                           │
│                              ▼                           │
│                      ✓ Result: Works!                   │
└─────────────────────────────────────────────────────────┘
```

---

## Simplified Architecture

### Core Components (What You'll Build)

```
┌────────────────────────────────────────────────────────┐
│                      CLI Interface                      │
│              (How users interact with you)              │
└────────────────────────────────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│                     Agent Core                          │
│                                                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │   Prompts   │  │  LLM Client │  │   Router    │    │
│  │  (Templates)│  │  (Anthropic)│  │ (Decisions) │    │
│  └─────────────┘  └─────────────┘  └─────────────┘    │
└────────────────────────────────────────────────────────┘
                           │
           ┌───────────────┼───────────────┐
           ▼               ▼               ▼
    ┌───────────┐   ┌───────────┐   ┌───────────┐
    │  Analyze  │   │  Generate │   │  Execute  │
    │   Tool    │   │   Tool    │   │   Tool    │
    └───────────┘   └───────────┘   └───────────┘
                                          │
                                          ▼
                                   ┌───────────┐
                                   │  Docker   │
                                   │  Sandbox  │
                                   └───────────┘
```

### What Each Component Does

| Component | Purpose | Complexity |
|-----------|---------|------------|
| CLI Interface | Accept user input, display results | Easy |
| Agent Core | Orchestrate tools, manage conversation | Medium |
| LLM Client | Talk to Claude API | Easy |
| Prompts | Templates for different tasks | Easy |
| Router | Decide which tool to use | Medium |
| Analyze Tool | Parse and understand code | Medium |
| Generate Tool | Create code from prompts | Easy |
| Execute Tool | Run code in Docker | Medium |
| Docker Sandbox | Isolated execution environment | Medium |

---

## Learning Path: 5 Phases

### Phase 0: Foundation (Day 1)
**Goal**: Set up environment, make first API call

### Phase 1: Simple Chat (Days 2-3)
**Goal**: CLI that talks to Claude about code

### Phase 2: Code Generation (Days 4-6)
**Goal**: Generate Python code from descriptions

### Phase 3: Safe Execution (Days 7-10)
**Goal**: Run generated code in Docker sandbox

### Phase 4: Intelligent Agent (Days 11-14)
**Goal**: Agent that decides when to generate vs execute

### Phase 5: Analysis & Polish (Days 15-20)
**Goal**: Add code analysis, improve prompts, refine UX

---

## Phase 0: Foundation

**Duration**: 1 day
**Learning Focus**: Environment setup, API basics

### Tasks

```
Phase 0: Foundation
├── 0.1 Environment Setup
│   ├── 0.1.1 Create virtual environment
│   ├── 0.1.2 Install dependencies (anthropic, docker, rich)
│   └── 0.1.3 Verify Docker is running
│
├── 0.2 API Verification
│   ├── 0.2.1 Test Anthropic API key
│   ├── 0.2.2 Make first Claude API call
│   └── 0.2.3 Understand request/response structure
│
└── 0.3 Project Structure
    ├── 0.3.1 Create directory structure
    ├── 0.3.2 Set up basic configuration
    └── 0.3.3 Create main entry point
```

### Deliverable: Project Skeleton

```
platform/
├── src/
│   └── assistant/
│       ├── __init__.py
│       ├── main.py          # Entry point
│       ├── config.py        # Configuration
│       └── llm.py           # Claude API client
├── tests/
│   └── test_llm.py
├── requirements.txt
├── .env                      # API keys (gitignored)
└── README.md
```

### Key Files to Create

**requirements.txt**:
```
anthropic>=0.39.0
python-dotenv>=1.0.0
rich>=13.0.0
docker>=7.0.0
pytest>=8.0.0
```

**src/assistant/config.py**:
```python
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    MODEL = "claude-sonnet-4-20250514"
    MAX_TOKENS = 4096
```

**src/assistant/llm.py**:
```python
import anthropic
from .config import Config

class LLMClient:
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=Config.ANTHROPIC_API_KEY)

    def ask(self, prompt: str) -> str:
        """Send a prompt to Claude and get a response."""
        message = self.client.messages.create(
            model=Config.MODEL,
            max_tokens=Config.MAX_TOKENS,
            messages=[{"role": "user", "content": prompt}]
        )
        return message.content[0].text
```

### Success Criteria
- [ ] `python -c "from src.assistant.llm import LLMClient; print(LLMClient().ask('Say hello'))"` works
- [ ] `docker ps` runs without errors
- [ ] Project structure matches skeleton

---

## Phase 1: Simple Chat

**Duration**: 2 days
**Learning Focus**: Conversation management, CLI design

### Tasks

```
Phase 1: Simple Chat
├── 1.1 CLI Shell
│   ├── 1.1.1 Create REPL loop (read-eval-print)
│   ├── 1.1.2 Add colored output with Rich
│   ├── 1.1.3 Handle keyboard interrupt gracefully
│   └── 1.1.4 Add /help and /quit commands
│
├── 1.2 Conversation Memory
│   ├── 1.2.1 Store message history
│   ├── 1.2.2 Send history with each request
│   ├── 1.2.3 Add /clear command
│   └── 1.2.4 Limit context length (avoid token overflow)
│
└── 1.3 System Prompt
    ├── 1.3.1 Create coding assistant persona
    ├── 1.3.2 Add Python expertise context
    └── 1.3.3 Test with coding questions
```

### New Files

**src/assistant/cli.py**:
```python
from rich.console import Console
from rich.markdown import Markdown
from .conversation import Conversation

console = Console()

def main():
    """Main CLI loop."""
    conv = Conversation()
    console.print("[bold green]Coding Assistant[/] - Type /help for commands")

    while True:
        try:
            user_input = console.input("[bold blue]You:[/] ").strip()

            if not user_input:
                continue
            if user_input == "/quit":
                break
            if user_input == "/help":
                show_help()
                continue
            if user_input == "/clear":
                conv.clear()
                console.print("[dim]Conversation cleared[/]")
                continue

            response = conv.send(user_input)
            console.print("[bold green]Assistant:[/]")
            console.print(Markdown(response))

        except KeyboardInterrupt:
            console.print("\n[dim]Use /quit to exit[/]")

def show_help():
    console.print("""
[bold]Commands:[/]
  /help  - Show this help
  /clear - Clear conversation history
  /quit  - Exit the assistant
    """)
```

**src/assistant/conversation.py**:
```python
from .llm import LLMClient

SYSTEM_PROMPT = """You are an expert Python coding assistant. You help users:
- Write clean, idiomatic Python code
- Debug and fix issues
- Explain concepts clearly
- Suggest best practices

Keep responses concise but complete. Use code blocks for code."""

class Conversation:
    def __init__(self):
        self.client = LLMClient()
        self.messages = []

    def send(self, user_message: str) -> str:
        """Send a message and get a response."""
        self.messages.append({"role": "user", "content": user_message})

        response = self.client.chat(
            system=SYSTEM_PROMPT,
            messages=self.messages
        )

        self.messages.append({"role": "assistant", "content": response})
        return response

    def clear(self):
        """Clear conversation history."""
        self.messages = []
```

### Update LLMClient

```python
# Add to llm.py
def chat(self, system: str, messages: list) -> str:
    """Send a conversation to Claude."""
    message = self.client.messages.create(
        model=Config.MODEL,
        max_tokens=Config.MAX_TOKENS,
        system=system,
        messages=messages
    )
    return message.content[0].text
```

### Success Criteria
- [ ] Can have a back-and-forth conversation about code
- [ ] Assistant remembers context from earlier in conversation
- [ ] `/help`, `/clear`, `/quit` commands work
- [ ] Markdown renders nicely in terminal

---

## Phase 2: Code Generation

**Duration**: 3 days
**Learning Focus**: Structured output, prompt engineering

### Tasks

```
Phase 2: Code Generation
├── 2.1 Structured Prompts
│   ├── 2.1.1 Create prompt templates
│   ├── 2.1.2 Add function generation template
│   ├── 2.1.3 Add class generation template
│   └── 2.1.4 Add test generation template
│
├── 2.2 Code Extraction
│   ├── 2.2.1 Parse code blocks from response
│   ├── 2.2.2 Detect language from fence
│   ├── 2.2.3 Handle multiple code blocks
│   └── 2.2.4 Save generated code to file
│
├── 2.3 Generation Commands
│   ├── 2.3.1 Add /generate command
│   ├── 2.3.2 Add /save command
│   └── 2.3.3 Add /show command (display last code)
│
└── 2.4 Quality Checks
    ├── 2.4.1 Syntax validation (ast.parse)
    ├── 2.4.2 Basic linting hints
    └── 2.4.3 Error feedback loop
```

### New Files

**src/assistant/prompts.py**:
```python
"""Prompt templates for different generation tasks."""

GENERATE_FUNCTION = """Write a Python function based on this description:

{description}

Requirements:
- Include type hints
- Add a docstring
- Handle edge cases
- Keep it simple and readable

Return ONLY the code in a ```python code block."""

GENERATE_WITH_TESTS = """Write a Python function based on this description:

{description}

Then write pytest test cases for it.

Requirements:
- Include type hints and docstrings
- Cover normal cases and edge cases
- Use descriptive test names

Return the function first, then the tests, each in separate ```python code blocks."""

EXPLAIN_CODE = """Explain this Python code clearly and concisely:

```python
{code}
```

Cover:
1. What it does (one sentence)
2. How it works (step by step)
3. Any potential issues or improvements"""

FIX_ERROR = """This Python code has an error:

```python
{code}
```

Error message:
{error}

Explain the error and provide the corrected code."""
```

**src/assistant/generator.py**:
```python
import ast
import re
from .llm import LLMClient
from .prompts import GENERATE_FUNCTION, GENERATE_WITH_TESTS

class CodeGenerator:
    def __init__(self):
        self.client = LLMClient()
        self.last_generated = None

    def generate(self, description: str, with_tests: bool = False) -> dict:
        """Generate code from a description."""
        template = GENERATE_WITH_TESTS if with_tests else GENERATE_FUNCTION
        prompt = template.format(description=description)

        response = self.client.ask(prompt)
        code_blocks = self.extract_code_blocks(response)

        result = {
            "raw_response": response,
            "code_blocks": code_blocks,
            "is_valid": all(self.validate_syntax(cb["code"]) for cb in code_blocks)
        }

        if code_blocks:
            self.last_generated = code_blocks[0]["code"]

        return result

    def extract_code_blocks(self, text: str) -> list:
        """Extract code blocks from markdown."""
        pattern = r"```(\w+)?\n(.*?)```"
        matches = re.findall(pattern, text, re.DOTALL)
        return [{"language": m[0] or "python", "code": m[1].strip()} for m in matches]

    def validate_syntax(self, code: str) -> bool:
        """Check if Python code has valid syntax."""
        try:
            ast.parse(code)
            return True
        except SyntaxError:
            return False

    def save(self, filepath: str) -> bool:
        """Save last generated code to file."""
        if not self.last_generated:
            return False
        with open(filepath, "w") as f:
            f.write(self.last_generated)
        return True
```

### Update CLI

Add new commands to `cli.py`:

```python
# Add these command handlers

generator = CodeGenerator()

if user_input.startswith("/generate "):
    description = user_input[10:]
    console.print("[dim]Generating code...[/]")
    result = generator.generate(description)

    if result["is_valid"]:
        console.print("[green]✓ Generated valid Python code:[/]")
        for block in result["code_blocks"]:
            console.print(Syntax(block["code"], "python"))
    else:
        console.print("[yellow]⚠ Generated code may have issues[/]")
        console.print(Markdown(result["raw_response"]))
    continue

if user_input.startswith("/save "):
    filepath = user_input[6:]
    if generator.save(filepath):
        console.print(f"[green]✓ Saved to {filepath}[/]")
    else:
        console.print("[red]No code to save. Generate something first.[/]")
    continue
```

### Success Criteria
- [ ] `/generate "a function that calculates factorial"` produces valid code
- [ ] Code is properly syntax-checked before displaying
- [ ] `/save output.py` saves the generated code
- [ ] Multiple code blocks (function + tests) are extracted correctly

---

## Phase 3: Safe Execution

**Duration**: 4 days
**Learning Focus**: Docker basics, security sandboxing

### Tasks

```
Phase 3: Safe Execution
├── 3.1 Docker Basics
│   ├── 3.1.1 Create Python sandbox Dockerfile
│   ├── 3.1.2 Build sandbox image locally
│   ├── 3.1.3 Test manual container run
│   └── 3.1.4 Understand resource limits
│
├── 3.2 Sandbox Manager
│   ├── 3.2.1 Create Docker client wrapper
│   ├── 3.2.2 Implement run_code() method
│   ├── 3.2.3 Add timeout handling
│   ├── 3.2.4 Add memory limits
│   ├── 3.2.5 Capture stdout/stderr
│   └── 3.2.6 Clean up containers after run
│
├── 3.3 Security Hardening
│   ├── 3.3.1 Disable network access
│   ├── 3.3.2 Drop all capabilities
│   ├── 3.3.3 Read-only filesystem
│   ├── 3.3.4 Non-root user in container
│   └── 3.3.5 Prevent fork bombs (PID limit)
│
├── 3.4 Execution Commands
│   ├── 3.4.1 Add /run command
│   ├── 3.4.2 Add /test command (run with pytest)
│   └── 3.4.3 Display execution results nicely
│
└── 3.5 Error Handling
    ├── 3.5.1 Handle timeout gracefully
    ├── 3.5.2 Parse error output
    ├── 3.5.3 Suggest fixes via LLM
    └── 3.5.4 Implement retry with fix
```

### New Files

**docker/Dockerfile.sandbox**:
```dockerfile
FROM python:3.12-slim

# Create non-root user
RUN useradd -m -s /bin/bash sandbox

# Install common packages
RUN pip install --no-cache-dir pytest numpy pandas

# Set up working directory
WORKDIR /sandbox
RUN chown sandbox:sandbox /sandbox

# Switch to non-root user
USER sandbox

# Default command
CMD ["python", "-c", "print('Sandbox ready')"]
```

**src/assistant/sandbox.py**:
```python
import docker
from docker.errors import ContainerError, ImageNotFound
from dataclasses import dataclass
from typing import Optional

@dataclass
class ExecutionResult:
    success: bool
    stdout: str
    stderr: str
    exit_code: int
    timed_out: bool
    error_message: Optional[str] = None

class Sandbox:
    IMAGE_NAME = "python-sandbox:latest"

    # Security limits
    MEMORY_LIMIT = "256m"
    CPU_QUOTA = 50000  # 0.5 CPU
    TIMEOUT_SECONDS = 30
    PID_LIMIT = 50

    def __init__(self):
        self.client = docker.from_env()
        self._ensure_image()

    def _ensure_image(self):
        """Build sandbox image if it doesn't exist."""
        try:
            self.client.images.get(self.IMAGE_NAME)
        except ImageNotFound:
            print("Building sandbox image (first time only)...")
            self.client.images.build(
                path="docker",
                dockerfile="Dockerfile.sandbox",
                tag=self.IMAGE_NAME
            )

    def run(self, code: str, timeout: int = None) -> ExecutionResult:
        """Run Python code in isolated container."""
        timeout = timeout or self.TIMEOUT_SECONDS

        container = None
        try:
            container = self.client.containers.run(
                self.IMAGE_NAME,
                command=["python", "-c", code],
                detach=True,
                mem_limit=self.MEMORY_LIMIT,
                cpu_quota=self.CPU_QUOTA,
                network_mode="none",           # No network
                read_only=True,                # Read-only filesystem
                pids_limit=self.PID_LIMIT,     # Prevent fork bombs
                cap_drop=["ALL"],              # Drop all capabilities
                security_opt=["no-new-privileges"],
                tmpfs={"/tmp": "size=10M"},    # Writable /tmp
            )

            # Wait for completion with timeout
            result = container.wait(timeout=timeout)
            exit_code = result["StatusCode"]

            logs = container.logs(stdout=True, stderr=True).decode()
            stdout = container.logs(stdout=True, stderr=False).decode()
            stderr = container.logs(stdout=False, stderr=True).decode()

            return ExecutionResult(
                success=(exit_code == 0),
                stdout=stdout,
                stderr=stderr,
                exit_code=exit_code,
                timed_out=False
            )

        except Exception as e:
            error_msg = str(e)
            timed_out = "timed out" in error_msg.lower() or "timeout" in error_msg.lower()

            return ExecutionResult(
                success=False,
                stdout="",
                stderr=error_msg if not timed_out else "",
                exit_code=-1,
                timed_out=timed_out,
                error_message="Execution timed out" if timed_out else error_msg
            )

        finally:
            if container:
                try:
                    container.remove(force=True)
                except:
                    pass

    def run_tests(self, code: str, test_code: str) -> ExecutionResult:
        """Run code with pytest tests."""
        combined = f"{code}\n\n{test_code}"
        # Write to temp file and run pytest
        wrapper = f'''
import sys
sys.path.insert(0, '/tmp')

# Write the code
with open('/tmp/test_module.py', 'w') as f:
    f.write("""{combined}""")

# Run pytest
import pytest
sys.exit(pytest.main(['/tmp/test_module.py', '-v']))
'''
        return self.run(wrapper)
```

### Update CLI

```python
# Add to cli.py

sandbox = Sandbox()

if user_input == "/run":
    if not generator.last_generated:
        console.print("[red]No code to run. Generate something first.[/]")
        continue

    console.print("[dim]Running in sandbox...[/]")
    result = sandbox.run(generator.last_generated)

    if result.success:
        console.print("[green]✓ Execution successful:[/]")
        console.print(result.stdout)
    elif result.timed_out:
        console.print("[red]✗ Execution timed out (30s limit)[/]")
    else:
        console.print("[red]✗ Execution failed:[/]")
        console.print(result.stderr)
    continue

if user_input.startswith("/run "):
    code = user_input[5:]
    result = sandbox.run(code)
    # ... same output handling
```

### Success Criteria
- [ ] `/run` executes the last generated code in Docker
- [ ] Output is captured and displayed
- [ ] Infinite loops timeout after 30 seconds
- [ ] No network access from sandbox (test with `import urllib`)
- [ ] Memory-intensive code is killed when exceeding limit

---

## Phase 4: Intelligent Agent

**Duration**: 4 days
**Learning Focus**: Tool use, agent loop, decision making

### Tasks

```
Phase 4: Intelligent Agent
├── 4.1 Tool Definitions
│   ├── 4.1.1 Define tool schemas (function signatures)
│   ├── 4.1.2 Create generate_code tool
│   ├── 4.1.3 Create execute_code tool
│   ├── 4.1.4 Create explain_code tool
│   └── 4.1.5 Create fix_error tool
│
├── 4.2 Claude Tool Use
│   ├── 4.2.1 Learn Claude's tool use API
│   ├── 4.2.2 Send tools with message
│   ├── 4.2.3 Parse tool use response
│   ├── 4.2.4 Execute requested tool
│   └── 4.2.5 Send result back to Claude
│
├── 4.3 Agent Loop
│   ├── 4.3.1 Implement think-act-observe cycle
│   ├── 4.3.2 Handle multi-step reasoning
│   ├── 4.3.3 Limit iterations (prevent infinite loops)
│   └── 4.3.4 Graceful termination
│
└── 4.4 Enhanced UX
    ├── 4.4.1 Show agent "thinking" status
    ├── 4.4.2 Display tool calls in progress
    ├── 4.4.3 Stream responses when possible
    └── 4.4.4 Add /auto mode toggle
```

### Core Concept: Agent Loop

```
┌─────────────────────────────────────────────────────────┐
│                    AGENT LOOP                           │
│                                                         │
│  User: "Create and test a fibonacci function"           │
│                          │                              │
│                          ▼                              │
│  ┌─────────────────────────────────────────────┐       │
│  │ THINK: "I need to:                           │       │
│  │  1. Generate fibonacci code                  │       │
│  │  2. Generate tests                           │       │
│  │  3. Run the tests"                           │       │
│  └─────────────────────────────────────────────┘       │
│                          │                              │
│                          ▼                              │
│  ┌─────────────────────────────────────────────┐       │
│  │ ACT: Call generate_code tool                 │       │
│  └─────────────────────────────────────────────┘       │
│                          │                              │
│                          ▼                              │
│  ┌─────────────────────────────────────────────┐       │
│  │ OBSERVE: Got code, now need to test         │       │
│  └─────────────────────────────────────────────┘       │
│                          │                              │
│                          ▼                              │
│  ┌─────────────────────────────────────────────┐       │
│  │ ACT: Call execute_code tool                  │       │
│  └─────────────────────────────────────────────┘       │
│                          │                              │
│                          ▼                              │
│  ┌─────────────────────────────────────────────┐       │
│  │ OBSERVE: Tests passed! Task complete.        │       │
│  └─────────────────────────────────────────────┘       │
│                          │                              │
│                          ▼                              │
│  Response: "Here's your fibonacci function..."          │
└─────────────────────────────────────────────────────────┘
```

### New Files

**src/assistant/tools.py**:
```python
"""Tool definitions for the agent."""

TOOLS = [
    {
        "name": "generate_code",
        "description": "Generate Python code from a natural language description. Use this when the user wants you to write code.",
        "input_schema": {
            "type": "object",
            "properties": {
                "description": {
                    "type": "string",
                    "description": "What the code should do"
                },
                "include_tests": {
                    "type": "boolean",
                    "description": "Whether to also generate test cases",
                    "default": False
                }
            },
            "required": ["description"]
        }
    },
    {
        "name": "execute_code",
        "description": "Run Python code in a safe sandbox. Use this to test if code works or see its output.",
        "input_schema": {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "Python code to execute"
                }
            },
            "required": ["code"]
        }
    },
    {
        "name": "explain_code",
        "description": "Explain what a piece of code does. Use this when the user shares code and wants to understand it.",
        "input_schema": {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "The code to explain"
                }
            },
            "required": ["code"]
        }
    },
    {
        "name": "fix_error",
        "description": "Fix an error in code. Use this when code execution fails.",
        "input_schema": {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "The broken code"
                },
                "error": {
                    "type": "string",
                    "description": "The error message"
                }
            },
            "required": ["code", "error"]
        }
    }
]
```

**src/assistant/agent.py**:
```python
"""The main agent implementation."""

import anthropic
from .config import Config
from .tools import TOOLS
from .generator import CodeGenerator
from .sandbox import Sandbox

AGENT_SYSTEM = """You are an intelligent Python coding assistant with access to tools.

Your capabilities:
- generate_code: Write Python code from descriptions
- execute_code: Run code in a safe sandbox
- explain_code: Explain what code does
- fix_error: Fix broken code

Workflow:
1. Understand what the user wants
2. Use appropriate tools to help
3. If code fails, use fix_error and try again
4. Explain your actions clearly

Always test code before saying it works. Be concise but thorough."""

class Agent:
    MAX_ITERATIONS = 10

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=Config.ANTHROPIC_API_KEY)
        self.generator = CodeGenerator()
        self.sandbox = Sandbox()
        self.messages = []

    def run(self, user_input: str, on_thinking=None, on_tool_use=None):
        """Run the agent loop for a user request."""
        self.messages.append({"role": "user", "content": user_input})

        for iteration in range(self.MAX_ITERATIONS):
            response = self.client.messages.create(
                model=Config.MODEL,
                max_tokens=Config.MAX_TOKENS,
                system=AGENT_SYSTEM,
                tools=TOOLS,
                messages=self.messages
            )

            # Check if we're done
            if response.stop_reason == "end_turn":
                # Extract text response
                text = self._extract_text(response)
                self.messages.append({"role": "assistant", "content": response.content})
                return text

            # Handle tool use
            if response.stop_reason == "tool_use":
                tool_calls = self._extract_tool_calls(response)
                self.messages.append({"role": "assistant", "content": response.content})

                # Execute each tool and collect results
                tool_results = []
                for tool_call in tool_calls:
                    if on_tool_use:
                        on_tool_use(tool_call["name"], tool_call["input"])

                    result = self._execute_tool(tool_call["name"], tool_call["input"])
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_call["id"],
                        "content": result
                    })

                self.messages.append({"role": "user", "content": tool_results})

        return "I've reached my iteration limit. Please try rephrasing your request."

    def _extract_text(self, response) -> str:
        """Extract text content from response."""
        for block in response.content:
            if hasattr(block, "text"):
                return block.text
        return ""

    def _extract_tool_calls(self, response) -> list:
        """Extract tool use blocks from response."""
        calls = []
        for block in response.content:
            if block.type == "tool_use":
                calls.append({
                    "id": block.id,
                    "name": block.name,
                    "input": block.input
                })
        return calls

    def _execute_tool(self, name: str, inputs: dict) -> str:
        """Execute a tool and return the result."""
        if name == "generate_code":
            result = self.generator.generate(
                inputs["description"],
                with_tests=inputs.get("include_tests", False)
            )
            if result["is_valid"] and result["code_blocks"]:
                code = result["code_blocks"][0]["code"]
                return f"Generated code:\n```python\n{code}\n```"
            return f"Generation result:\n{result['raw_response']}"

        elif name == "execute_code":
            result = self.sandbox.run(inputs["code"])
            if result.success:
                return f"Execution successful:\n{result.stdout}"
            elif result.timed_out:
                return "Execution timed out (30 second limit)"
            else:
                return f"Execution failed:\n{result.stderr}"

        elif name == "explain_code":
            from .prompts import EXPLAIN_CODE
            prompt = EXPLAIN_CODE.format(code=inputs["code"])
            return self.generator.client.ask(prompt)

        elif name == "fix_error":
            from .prompts import FIX_ERROR
            prompt = FIX_ERROR.format(code=inputs["code"], error=inputs["error"])
            return self.generator.client.ask(prompt)

        return f"Unknown tool: {name}"

    def clear(self):
        """Clear conversation history."""
        self.messages = []
```

### Update CLI for Agent Mode

```python
# cli.py with agent mode

from .agent import Agent

agent = Agent()
agent_mode = True  # Default to agent mode

if user_input == "/auto on":
    agent_mode = True
    console.print("[green]Agent mode enabled[/]")
    continue

if user_input == "/auto off":
    agent_mode = False
    console.print("[yellow]Agent mode disabled (simple chat)[/]")
    continue

# Handle messages
if agent_mode:
    with console.status("[bold green]Thinking..."):
        def on_tool(name, inputs):
            console.print(f"[dim]Using {name}...[/]")

        response = agent.run(
            user_input,
            on_tool_use=on_tool
        )
    console.print("[bold green]Assistant:[/]")
    console.print(Markdown(response))
else:
    # Simple chat mode
    response = conv.send(user_input)
    console.print(Markdown(response))
```

### Success Criteria
- [ ] Agent can generate code, run it, and report results in one request
- [ ] "Create and test a factorial function" works end-to-end
- [ ] Agent fixes code when execution fails and retries
- [ ] Tool usage is visible to user
- [ ] Agent doesn't loop infinitely

---

## Phase 5: Analysis & Polish

**Duration**: 6 days
**Learning Focus**: Code analysis, UX refinement, edge cases

### Tasks

```
Phase 5: Analysis & Polish
├── 5.1 Code Analysis Tool
│   ├── 5.1.1 Add analyze_code tool
│   ├── 5.1.2 Use ast module for parsing
│   ├── 5.1.3 Extract functions/classes/imports
│   ├── 5.1.4 Calculate basic complexity metrics
│   └── 5.1.5 Detect common issues
│
├── 5.2 Better Error Messages
│   ├── 5.2.1 Parse Python tracebacks
│   ├── 5.2.2 Highlight error location
│   ├── 5.2.3 Suggest common fixes
│   └── 5.2.4 Link to documentation
│
├── 5.3 File Operations
│   ├── 5.3.1 Add /load command (load file)
│   ├── 5.3.2 Add /save command (save with prompt)
│   ├── 5.3.3 Add /edit command (modify existing)
│   └── 5.3.4 Watch file changes (optional)
│
├── 5.4 Session Management
│   ├── 5.4.1 Save conversation history
│   ├── 5.4.2 Load previous sessions
│   ├── 5.4.3 Export to markdown
│   └── 5.4.4 Manage code snippets
│
├── 5.5 Quality of Life
│   ├── 5.5.1 Tab completion
│   ├── 5.5.2 Command history (arrow keys)
│   ├── 5.5.3 Syntax highlighting in output
│   ├── 5.5.4 Progress indicators
│   └── 5.5.5 Configuration file support
│
└── 5.6 Documentation & Testing
    ├── 5.6.1 Write README with examples
    ├── 5.6.2 Add unit tests for each tool
    ├── 5.6.3 Add integration tests
    ├── 5.6.4 Create demo video/gif
    └── 5.6.5 Clean up code, add docstrings
```

### New: Analysis Tool

**src/assistant/analyzer.py**:
```python
import ast
from dataclasses import dataclass
from typing import List, Dict, Any

@dataclass
class CodeAnalysis:
    functions: List[str]
    classes: List[str]
    imports: List[str]
    line_count: int
    complexity: int  # Basic cyclomatic complexity
    issues: List[str]

class CodeAnalyzer:
    """Analyze Python code structure and quality."""

    def analyze(self, code: str) -> CodeAnalysis:
        """Analyze Python code and return structured info."""
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return CodeAnalysis(
                functions=[], classes=[], imports=[],
                line_count=len(code.splitlines()),
                complexity=0,
                issues=[f"Syntax error: {e.msg} at line {e.lineno}"]
            )

        functions = []
        classes = []
        imports = []
        issues = []
        complexity = 1

        for node in ast.walk(tree):
            # Collect functions
            if isinstance(node, ast.FunctionDef):
                functions.append(node.name)
                # Check for missing docstring
                if not ast.get_docstring(node):
                    issues.append(f"Function '{node.name}' has no docstring")

            # Collect classes
            elif isinstance(node, ast.ClassDef):
                classes.append(node.name)

            # Collect imports
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                imports.append(f"{node.module}.{node.names[0].name}")

            # Count branches for complexity
            elif isinstance(node, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1

        # Check for common issues
        if not functions and not classes:
            issues.append("No functions or classes defined")

        return CodeAnalysis(
            functions=functions,
            classes=classes,
            imports=imports,
            line_count=len(code.splitlines()),
            complexity=complexity,
            issues=issues
        )
```

### Add Analysis Tool to Agent

```python
# Add to tools.py
{
    "name": "analyze_code",
    "description": "Analyze Python code structure, find functions, classes, and potential issues.",
    "input_schema": {
        "type": "object",
        "properties": {
            "code": {
                "type": "string",
                "description": "Python code to analyze"
            }
        },
        "required": ["code"]
    }
}

# Add to agent.py _execute_tool
elif name == "analyze_code":
    from .analyzer import CodeAnalyzer
    analyzer = CodeAnalyzer()
    analysis = analyzer.analyze(inputs["code"])
    return f"""Code Analysis:
- Functions: {', '.join(analysis.functions) or 'None'}
- Classes: {', '.join(analysis.classes) or 'None'}
- Imports: {', '.join(analysis.imports) or 'None'}
- Lines: {analysis.line_count}
- Complexity: {analysis.complexity}
- Issues: {'; '.join(analysis.issues) or 'None found'}"""
```

### Final Project Structure

```
platform/
├── src/
│   └── assistant/
│       ├── __init__.py
│       ├── main.py          # Entry point
│       ├── cli.py           # CLI interface
│       ├── config.py        # Configuration
│       ├── llm.py           # Claude API client
│       ├── conversation.py  # Simple chat
│       ├── prompts.py       # Prompt templates
│       ├── generator.py     # Code generation
│       ├── sandbox.py       # Docker execution
│       ├── tools.py         # Tool definitions
│       ├── agent.py         # Agent loop
│       └── analyzer.py      # Code analysis
├── docker/
│   └── Dockerfile.sandbox
├── tests/
│   ├── test_llm.py
│   ├── test_generator.py
│   ├── test_sandbox.py
│   ├── test_agent.py
│   └── test_analyzer.py
├── requirements.txt
├── .env
├── .gitignore
├── README.md
└── history/
    └── *.md  # Planning docs
```

### Success Criteria (Final)
- [ ] Full agent loop working with all tools
- [ ] Code analysis provides useful feedback
- [ ] All edge cases handled gracefully
- [ ] Tests pass with 80%+ coverage
- [ ] README has clear usage examples
- [ ] Can be installed with `pip install -e .`

---

## Summary: Key Concepts You'll Learn

| Phase | Key Concepts |
|-------|-------------|
| 0 | API clients, environment setup, project structure |
| 1 | REPL design, conversation state, system prompts |
| 2 | Prompt engineering, structured output, code parsing |
| 3 | Docker containers, security sandboxing, resource limits |
| 4 | Tool use, agent loops, multi-step reasoning |
| 5 | Code analysis (AST), UX polish, testing |

## Common Pitfalls to Avoid

1. **Don't skip sandboxing**: Even "simple" code can crash your system
2. **Limit agent iterations**: Agents can loop forever without guards
3. **Handle API errors**: Rate limits, network issues happen
4. **Test with malicious input**: Users will try to break it
5. **Start simple**: Add features only when the base works

## Next Steps After This Project

Once you complete this learning project, consider:
1. **Multi-language support**: Add JavaScript, Go, etc.
2. **Web interface**: Build a React/Vue frontend
3. **Codebase awareness**: Index and search entire projects
4. **Team features**: Share sessions, collaborate
5. **Custom models**: Fine-tune for your domain

---

**Document Version**: 2.0 (Learning Edition)
**Created**: 2025-12-12
**Philosophy**: Learn by building, ship working software, iterate
