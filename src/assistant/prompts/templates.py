"""Prompt templates for various tools."""

GENERATE_CODE = """Generate Python code based on the following description:

{description}

{with_tests}

Requirements:
- Write clean, well-documented code
- Follow Python best practices
- Include type hints where appropriate
- Wrap code in ```python``` code blocks
- Generate ONLY ONE implementation (the most optimal and efficient approach)
- Do NOT provide multiple alternative implementations (e.g., both recursive and iterative)
- If tests are requested, ensure ALL test cases call the same implementation

Provide only the code, no additional explanation."""


ANALYZE_CODE = """Analyze the following Python code and provide a detailed analysis:

```python
{code}
```

Provide analysis including:
- Functions and classes defined
- Imports used
- Code complexity
- Potential issues or improvements
- Code quality assessment"""


EXPLAIN_CODE = """Explain what the following Python code does:

```python
{code}
```

Provide:
- A high-level summary
- Step-by-step explanation of the logic
- Purpose of each major component
- Any important patterns or techniques used

Be clear and concise."""


FIX_ERROR = """Fix the following Python code that has an error:

```python
{code}
```

Error message:
{error}

Provide:
- The corrected code wrapped in ```python``` code blocks
- Brief explanation of what was wrong and how you fixed it"""
