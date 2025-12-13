# Security Features

This document outlines the security hardening measures implemented in the runtime system.

## Docker Container Security

### 1. Network Isolation
- **Default**: Network disabled (`network_mode="none"`)
- Containers cannot make outbound connections
- Can be explicitly enabled per-runtime if needed

### 2. Resource Limits
- **Memory**: 256MB default limit (configurable)
- **CPU**: 50% of one CPU core (cpu_quota=50000)
- **PIDs**: Maximum 50 processes
- **Temporary Storage**: /tmp limited to 10MB

### 3. Capability Restrictions
- **All Linux capabilities dropped** (`cap_drop=["ALL"]`)
- Containers run with minimal permissions
- Cannot perform privileged operations

### 4. Privilege Escalation Prevention
- `no-new-privileges` security option enabled
- Prevents processes from gaining additional privileges
- Blocks setuid/setgid executables

### 5. Seccomp Syscall Filtering
- Custom seccomp profile restricts system calls
- Only allows essential syscalls for Python execution
- Blocks dangerous operations (e.g., kernel module loading, mount)
- Profile: `docker/seccomp-profile.json`

### 6. Read-Only Filesystem
- Container filesystem mounted read-only
- Only /tmp is writable (with size limit)
- Prevents malicious code from persisting changes

### 7. Non-Root User
- Containers run as unprivileged `sandbox` user
- Defined in Dockerfile, not root
- Additional layer of isolation

### 8. Execution Timeouts
- Default 30-second timeout per execution
- Prevents runaway processes
- Configurable per-runtime

## Threat Model

### Protected Against:
- ✅ Network-based attacks (no network access)
- ✅ Resource exhaustion (CPU/memory/storage limits)
- ✅ Privilege escalation (capabilities dropped, no-new-privileges)
- ✅ Container escape attempts (seccomp, read-only filesystem)
- ✅ Persistent malware (ephemeral containers, read-only FS)
- ✅ Fork bombs (PID limit)

### Additional Considerations:
- Docker daemon must be properly secured
- Host system should be hardened
- Regular security updates for base images
- Monitor container activity in production

## Configuration

Security settings are configurable through `RuntimeConfig`:

```python
from src.assistant.runtimes.base import RuntimeConfig

config = RuntimeConfig(
    language="python",
    image="assistant-python:latest",
    command=["python", "-c"],
    file_extension=".py",
    timeout_seconds=30,      # Execution timeout
    memory_limit="256m",     # Memory limit
    cpu_quota=50000,         # CPU quota (50% of 1 core)
)
```

## Verification

Test the security features:

```bash
# Verify network is disabled (should timeout/fail)
python -c "from src.assistant.runtimes.python import PythonRuntime; \
rt = PythonRuntime(); \
result = rt.run('import socket; socket.create_connection((\"google.com\", 80), timeout=5)'); \
print('Success' if not result.success else 'FAILED - network should be blocked')"

# Verify resource limits work
python -c "from src.assistant.runtimes.python import PythonRuntime; \
rt = PythonRuntime(); \
result = rt.run('x = [0] * (1024**3)'); \
print('Memory limit enforced' if not result.success else 'FAILED')"
```

## Updates

**Last reviewed**: 2025-12-13
**Version**: Phase 3 - Runtime System
