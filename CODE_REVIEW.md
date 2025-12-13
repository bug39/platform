# Code Review - Security, Quality, and Refactoring Findings

**Date:** 2025-12-13
**Scope:** Comprehensive review of Phase 3 runtime system and tools
**Reviewer:** Automated analysis + manual inspection

---

## Executive Summary

Phase 3 core runtime is **functional and secure** with Docker sandboxing, but several **hardening improvements** are needed before production use. Found 10+ security/validation gaps, 5+ code quality issues, and significant logging gaps.

**Priority:**
- **P1 (Critical):** 2 security validation issues - fix immediately
- **P2 (High):** 6 security/quality issues - fix before production
- **P3 (Medium):** 3 cleanup/refactoring items - quality of life

---

## Security Concerns

### 🔴 P1 - Critical (Fix Immediately)

#### 1. ExecuteTool Input Validation (Platform-ktj)
**Risk:** DoS, resource exhaustion
**File:** `src/assistant/tools/execute.py`

**Issues:**
- No code length limit (malicious user could send 100MB string)
- No timeout bounds validation (could set timeout=999999)
- No rate limiting on execution requests

**Impact:** System DoS, resource exhaustion, excessive Docker container creation

**Fix:**
```python
# Add to execute() method
MAX_CODE_LENGTH = 50_000  # 50KB
MIN_TIMEOUT, MAX_TIMEOUT = 1, 300

if len(code) > MAX_CODE_LENGTH:
    return f"Error: Code too long (max {MAX_CODE_LENGTH} chars)"

if not (MIN_TIMEOUT <= timeout <= MAX_TIMEOUT):
    return f"Error: Timeout must be between {MIN_TIMEOUT}-{MAX_TIMEOUT}s"
```

#### 2. ContainerConfig Validation (Platform-3yf)
**Risk:** Resource exhaustion, container failures
**File:** `src/assistant/runtimes/docker.py:22-32`

**Issues:**
- No validation on memory_limit format/bounds
- No validation on cpu_quota range
- No validation on timeout_seconds range
- Negative values not prevented

**Impact:** Invalid Docker parameters, resource exhaustion, container failures

**Fix:**
```python
@dataclass
class ContainerConfig:
    # ... existing fields ...

    def __post_init__(self):
        """Validate configuration values."""
        import re

        # Validate memory_limit format
        if not re.match(r'^\d+[kmg]$', self.memory_limit.lower()):
            raise ValueError(f"Invalid memory_limit: {self.memory_limit}")

        # Validate cpu_quota range
        if not (1000 <= self.cpu_quota <= 1_000_000):
            raise ValueError(f"cpu_quota must be 1000-1000000: {self.cpu_quota}")

        # Validate timeout
        if not (1 <= self.timeout_seconds <= 300):
            raise ValueError(f"timeout must be 1-300s: {self.timeout_seconds}")
```

### 🟡 P2 - High (Fix Before Production)

#### 3. Tool Input Validation (Platform-vuf)
**Risk:** DoS, memory exhaustion
**Files:** `src/assistant/tools/{generate,fix,explain,analyze}.py`

**Issues:**
- GenerateTool: description has min but no max length
- FixTool: code and error have no length limits
- ExplainTool: code has no length limit
- AnalyzeTool: code has no length limit

**Impact:** Memory exhaustion from huge inputs

**Dependency:** Blocked by Platform-9qh (extract validation helpers first)

#### 4. Docker Path Validation (Platform-9mo)
**Risk:** Path traversal, malicious image names
**File:** `src/assistant/runtimes/docker.py:76-105`

**Issues:**
- No validation that image names are safe
- Dockerfile path not validated for path traversal (`../../../etc/passwd`)
- Build context path not validated

**Impact:** Path traversal attacks, arbitrary file access

**Fix:**
```python
import re

def validate_image_name(name: str) -> bool:
    # Only allow alphanumeric, :, /, -, _
    if not re.match(r'^[a-zA-Z0-9:/_-]+$', name):
        raise ValueError(f"Invalid image name: {name}")

def validate_dockerfile_path(path: str) -> str:
    # Prevent path traversal
    if '..' in path:
        raise ValueError("Path traversal not allowed")
    return Path(path).resolve()
```

#### 5. Seccomp Profile Hardening (Platform-6gi)
**Risk:** Silent security degradation
**File:** `src/assistant/runtimes/docker.py:65-74`

**Issues:**
- Relative path calculation fragile
- No validation that profile JSON is valid
- Silent failure if profile missing (just logs)
- Profile could be empty or malformed

**Impact:** Security features silently disabled

#### 6. Error Message Sanitization (Platform-zm5)
**Risk:** Information leakage
**Files:** All tool files

**Issues:**
- Full exception messages exposed to users
- Stack traces might leak internal paths
- Docker errors might reveal system info

**Impact:** Information disclosure, aids attackers

---

## Code Quality Issues

### 🔵 P2 - High (Improve Maintainability)

#### 7. Duplicate Validation Patterns (Platform-9qh)
**Type:** Code smell - DRY violation
**Files:** All tool files

**Pattern repeated 5+ times:**
```python
if not X or not X.strip():
    return "Error..."

provider = get_provider()
response = provider.complete([Message(role="user", content=prompt)])

code = extract_code(response.content)
if validate_syntax(code):
    ...
```

**Fix:** Extract to base helpers:
- `validate_non_empty(value, field_name)`
- `validate_length(value, max_len, field_name)`
- `call_llm(prompt) -> str`
- `extract_and_validate_code(response) -> tuple[str, bool]`

#### 8. Logging Gaps (Platform-xgw)
**Type:** Debugging/observability issue
**Files:** Most files lack logging

**Current state:**
- Only 3 files have logging: execute.py, docker.py, events.py
- No logging in: config.py, session.py, most tools
- No structured logging (no request IDs, context)

**Missing:**
- Config loading/validation failures
- Session operations
- Tool execution start/end
- LLM API calls
- Error conditions

**Impact:** Hard to debug issues, no observability

### 🟢 P3 - Medium (Nice to Have)

#### 9. ExecuteTool Output Formatting (Platform-o3t)
**Type:** Code smell - long method
**File:** `src/assistant/tools/execute.py:86-112`

**Issue:** Complex nested if/else for formatting (27 lines)

**Fix:** Extract `ExecutionResultFormatter` class

#### 10. Code Cleanup (Platform-otw)
**Type:** Minor issues
**Files:** Various

**Issues:**
- Unused import: `Optional` in execute.py line 5
- Inconsistent quotes (' vs ")
- Missing type hints in some functions

---

## Testing Gaps

### Runtime Testing (Platform-sja)
**Current:** Only 20 tests, none for runtime
**Needed:** 20+ runtime-specific tests

**Categories:**
1. **Basic execution** (5 tests)
2. **Security** (6 tests) - network, filesystem, resources, timeout, capabilities, seccomp
3. **Error handling** (5 tests)
4. **pytest integration** (4 tests)

### Tool Testing (Platform-hrk)
**Current:** No tests for GenerateTool, ExplainTool, FixTool
**Needed:** 18+ tests

**Categories:**
1. **GenerateTool** (6 tests)
2. **ExplainTool** (6 tests)
3. **FixTool** (6 tests)

---

## Task Organization

### New Epics Created

1. **Platform-bsj: Security & Validation Hardening** (P1)
   - Comprehensive security improvements
   - 6 subtasks (2 P1, 3 P2, 1 P3)

2. **Platform-j98: Code Quality & Maintainability** (P2)
   - Reduce duplication, improve logging
   - 4 subtasks (2 P2, 2 P3)

### Refined Existing Tasks

1. **Platform-sja: Runtime Testing**
   - Broken into 4 test files, 20+ test cases
   - Detailed test scenarios

2. **Platform-sgh: Language Configuration System**
   - Expanded with implementation details
   - Clear deliverables and benefits

3. **Platform-hrk: Tool Testing**
   - Broken into 3 test files, 18 test cases
   - Mocking strategy defined

### Dependencies Added

- Platform-vuf depends on Platform-9qh (extract helpers first)
- Platform-vuf depends on Platform-ktj (pattern established)

---

## Priority Matrix

### Immediate Action (This Sprint)
1. ✅ Platform-ktj: ExecuteTool validation (P1)
2. ✅ Platform-3yf: ContainerConfig validation (P1)

### Before Production
3. Platform-9qh: Extract validation helpers (P2)
4. Platform-vuf: Tool input validation (P2) - *blocked*
5. Platform-9mo: Path validation (P2)
6. Platform-6gi: Seccomp hardening (P2)

### Quality Improvements (Next Sprint)
7. Platform-xgw: Comprehensive logging (P2)
8. Platform-hrk: Tool tests (P2)
9. Platform-sja: Runtime tests (P2)
10. Platform-sgh: Language configs (P2)

### Polish (Future)
11. Platform-zm5: Error sanitization (P3)
12. Platform-o3t: Refactor formatting (P3)
13. Platform-otw: Code cleanup (P3)

---

## Statistics

- **Total issues created:** 10 new tasks
- **Epics created:** 2
- **Tasks refined:** 3
- **Dependencies added:** 2
- **Open issues:** 29
- **Blocked issues:** 1
- **Files reviewed:** 30+ Python files
- **Security issues:** 6 (2 critical, 4 high)
- **Quality issues:** 4
- **Estimated effort:** 40-60 hours

---

## Recommendations

### Immediate (Today)
1. Fix Platform-ktj (ExecuteTool validation) - 1 hour
2. Fix Platform-3yf (ContainerConfig validation) - 1 hour

### This Week
3. Extract validation helpers (Platform-9qh) - 3 hours
4. Add path validation (Platform-9mo) - 2 hours
5. Harden seccomp (Platform-6gi) - 2 hours

### Next Week
6. Add comprehensive logging (Platform-xgw) - 6 hours
7. Write runtime tests (Platform-sja) - 8 hours
8. Write tool tests (Platform-hrk) - 6 hours

### Future
- Complete remaining P3 tasks
- Add language configuration system
- Implement error sanitization

---

**Next Action:** Start with Platform-ktj (ExecuteTool validation) - highest priority, fastest fix.
