# Coding Assistant Platform

An intelligent, extensible coding assistant that can generate and execute Python code in a sandboxed Docker environment.

## Quick Start: Code Generation Tool

The easiest way to get started is with the interactive code generation tool.

### One-Line Setup & Run

```bash
./run.sh
```

That's it! The script will:
- ✓ Check Python version (3.11+ required)
- ✓ Create a virtual environment
- ✓ Install all dependencies automatically
- ✓ Check if Docker is running
- ✓ Start the interactive tool

### Prerequisites

1. **Python 3.11 or higher**
   ```bash
   python3 --version  # Should be 3.11+
   ```

2. **Docker** (for code execution)
   ```bash
   docker --version
   ```
   Make sure Docker Desktop is running.

3. **Anthropic API Key**

   Get your API key from [Anthropic Console](https://console.anthropic.com/)

   Set it as an environment variable:
   ```bash
   export ANTHROPIC_API_KEY='your-api-key-here'
   ```

   Or create a `.env` file:
   ```bash
   echo "ANTHROPIC_API_KEY=your-api-key-here" > .env
   ```

### Manual Installation

If you prefer to install manually:

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e .

# Run the tool
python code_generation.py
```

## What Does It Do?

The code generation tool is an interactive CLI that:

1. **Asks you** what code you want to create
2. **Generates** Python code using Claude AI
3. **Executes** the code in a secure Docker sandbox
4. **Shows you** the results

### Example Session

```
What code would you like to generate?
>>> A function to calculate fibonacci numbers

Include test cases? (y/n) [n]: y

Step 1: Generating code...
Generated code:
```python
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

def test_fibonacci():
    assert fibonacci(0) == 0
    assert fibonacci(1) == 1
    assert fibonacci(10) == 55
```

Execute this code? (y/n) [y]: y

Step 3: Executing code in Docker sandbox...
Execution successful (completed in 145ms)

Output:
All tests passed!
```

## Project Structure

```
platform/
├── code_generation.py     # Interactive code generation tool
├── run.sh                 # One-line setup and run script
├── src/assistant/         # Core assistant code
│   ├── tools/            # AI tools (generate, execute, analyze, etc.)
│   ├── runtimes/         # Execution runtimes (Python + Docker)
│   ├── providers/        # LLM providers (Anthropic)
│   └── config.py         # Configuration management
├── tests/                # Test suite
└── pyproject.toml        # Dependencies and project metadata
```

## Development

### Running Tests

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run specific test file
pytest tests/test_runtime_basic.py
```

### Issue Tracking

This project uses [bd (beads)](https://github.com/steveyegge/beads) for issue tracking:

```bash
# See what's ready to work on
bd ready

# Create a new issue
bd create "Issue title" -t task -p 1

# Start working on an issue
bd update bd-123 --status in_progress

# Close when done
bd close bd-123 --reason "Completed"
```

## Security

Code execution happens in a **sandboxed Docker container** with:
- ✓ No network access
- ✓ Memory limits (256MB default)
- ✓ CPU quota limits
- ✓ Timeout enforcement (30s default)
- ✓ Seccomp profile for syscall filtering
- ✓ All capabilities dropped
- ✓ Read-only filesystem

## Features

### Built-in Tools

- **GenerateTool**: Create Python code from natural language descriptions
- **ExecuteTool**: Run code in sandboxed Docker environment
- **FixTool**: Automatically fix code errors
- **ExplainTool**: Get detailed code explanations
- **AnalyzeTool**: Analyze code quality and complexity

### Extensible Architecture

- Plugin system for custom tools
- Multiple LLM provider support (Anthropic, OpenAI)
- Event bus for hooks and monitoring
- Session management with persistence

## License

MIT

Issues and pull requests welcome! See beads tracker for current work:

```bash
bd list --json
```
