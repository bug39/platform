"""Docker container management for sandboxed code execution."""

import time
import logging
import os
from typing import Optional, Dict, List
from dataclasses import dataclass
from pathlib import Path

try:
    import docker
    from docker.errors import ImageNotFound, ContainerError, APIError, NotFound
    DOCKER_AVAILABLE = True
except ImportError:
    DOCKER_AVAILABLE = False

from .base import ExecutionResult, Runtime, RuntimeConfig

logger = logging.getLogger(__name__)


@dataclass
class ContainerConfig:
    """Configuration for running a container."""
    image: str
    command: List[str]
    timeout_seconds: int = 30
    memory_limit: str = "256m"
    cpu_quota: int = 50000  # 50% of one CPU
    network_enabled: bool = False
    read_only: bool = True
    pids_limit: int = 50


class DockerManager:
    """
    Manages Docker containers for sandboxed code execution.

    Features:
    - Image building and caching
    - Container lifecycle management
    - Resource limits and security hardening
    - Automatic cleanup of stopped containers
    """

    def __init__(self, seccomp_profile: Optional[str] = None):
        """
        Initialize Docker manager.

        Args:
            seccomp_profile: Path to seccomp profile JSON (default: docker/seccomp-profile.json)
        """
        if not DOCKER_AVAILABLE:
            raise ImportError("docker package not installed. Run: pip install docker")

        try:
            self.client = docker.from_env()
            # Test connection
            self.client.ping()
        except Exception as e:
            raise RuntimeError(f"Failed to connect to Docker daemon: {e}")

        self._image_cache: Dict[str, bool] = {}

        # Set up seccomp profile for syscall filtering
        if seccomp_profile is None:
            # Default to the included seccomp profile
            profile_path = Path(__file__).parent.parent.parent / "docker" / "seccomp-profile.json"
            self.seccomp_profile = str(profile_path) if profile_path.exists() else None
        else:
            self.seccomp_profile = seccomp_profile

        if self.seccomp_profile:
            logger.info(f"Using seccomp profile: {self.seccomp_profile}")

    def ensure_image(self, image_name: str, dockerfile_path: Optional[str] = None,
                    build_context: str = ".", force_rebuild: bool = False) -> bool:
        """
        Ensure Docker image exists, build if necessary.

        Args:
            image_name: Name of the Docker image
            dockerfile_path: Path to Dockerfile (relative to build_context)
            build_context: Build context directory
            force_rebuild: Force rebuild even if image exists

        Returns:
            True if image is ready, False otherwise
        """
        # Check cache first
        if not force_rebuild and image_name in self._image_cache:
            return True

        try:
            # Try to get existing image
            self.client.images.get(image_name)
            self._image_cache[image_name] = True
            logger.info(f"Image {image_name} found in cache")
            return True
        except ImageNotFound:
            if not dockerfile_path:
                logger.error(f"Image {image_name} not found and no Dockerfile provided")
                return False

            # Build the image
            logger.info(f"Building image {image_name} from {dockerfile_path}...")
            try:
                self.client.images.build(
                    path=build_context,
                    dockerfile=dockerfile_path,
                    tag=image_name,
                    rm=True,  # Remove intermediate containers
                    forcerm=True  # Always remove intermediate containers
                )
                self._image_cache[image_name] = True
                logger.info(f"Successfully built image {image_name}")
                return True
            except Exception as e:
                logger.error(f"Failed to build image {image_name}: {e}")
                return False

    def run_container(self, config: ContainerConfig, code_input: str) -> ExecutionResult:
        """
        Run code in a sandboxed Docker container.

        Args:
            config: Container configuration
            code_input: Code or input to pass to the container

        Returns:
            ExecutionResult with stdout, stderr, exit code, and metrics
        """
        container = None
        start_time = time.time()

        try:
            # Build security options
            security_opts = ["no-new-privileges"]  # Prevent privilege escalation

            # Add seccomp profile for syscall filtering
            if self.seccomp_profile and os.path.exists(self.seccomp_profile):
                security_opts.append(f"seccomp={self.seccomp_profile}")

            # Create and run container with security hardening
            container = self.client.containers.run(
                config.image,
                command=config.command + [code_input],
                detach=True,
                mem_limit=config.memory_limit,
                cpu_quota=config.cpu_quota,
                network_mode="bridge" if config.network_enabled else "none",
                read_only=config.read_only,
                pids_limit=config.pids_limit,
                # Security hardening
                cap_drop=["ALL"],  # Drop all Linux capabilities
                security_opt=security_opts,  # Security options (no-new-privileges + seccomp)
                tmpfs={"/tmp": "size=10M,mode=1777"},  # Writable tmp with size limit
            )

            # Wait for container to finish
            result = container.wait(timeout=config.timeout_seconds)
            execution_time_ms = int((time.time() - start_time) * 1000)

            # Get output
            stdout = container.logs(stdout=True, stderr=False).decode('utf-8', errors='replace')
            stderr = container.logs(stdout=False, stderr=True).decode('utf-8', errors='replace')

            # Get memory usage if available
            memory_used_mb = 0.0
            try:
                stats = container.stats(stream=False)
                if 'memory_stats' in stats and 'usage' in stats['memory_stats']:
                    memory_used_mb = stats['memory_stats']['usage'] / (1024 * 1024)
            except:
                pass  # Memory stats not critical

            return ExecutionResult(
                success=(result["StatusCode"] == 0),
                stdout=stdout,
                stderr=stderr,
                exit_code=result["StatusCode"],
                timed_out=False,
                execution_time_ms=execution_time_ms,
                memory_used_mb=memory_used_mb,
            )

        except docker.errors.ContainerError as e:
            # Container ran but exited with error
            execution_time_ms = int((time.time() - start_time) * 1000)
            return ExecutionResult(
                success=False,
                stdout=e.stdout.decode('utf-8', errors='replace') if e.stdout else "",
                stderr=e.stderr.decode('utf-8', errors='replace') if e.stderr else str(e),
                exit_code=e.exit_status,
                timed_out=False,
                execution_time_ms=execution_time_ms,
                error_message=str(e),
            )

        except Exception as e:
            # Execution failed or timed out
            execution_time_ms = int((time.time() - start_time) * 1000)
            is_timeout = "timed out" in str(e).lower() or "timeout" in str(e).lower()

            return ExecutionResult(
                success=False,
                stdout="",
                stderr="" if is_timeout else str(e),
                exit_code=-1,
                timed_out=is_timeout,
                execution_time_ms=execution_time_ms,
                error_message="Execution timed out" if is_timeout else str(e),
            )

        finally:
            # Always cleanup container
            if container:
                self._cleanup_container(container)

    def _cleanup_container(self, container) -> None:
        """Remove a container, force if necessary."""
        try:
            container.remove(force=True)
        except NotFound:
            pass  # Already removed
        except Exception as e:
            logger.warning(f"Failed to remove container {container.id}: {e}")

    def cleanup_stopped_containers(self, image_filter: Optional[str] = None) -> int:
        """
        Remove all stopped containers, optionally filtered by image.

        Args:
            image_filter: Only remove containers from this image

        Returns:
            Number of containers removed
        """
        removed_count = 0
        try:
            filters = {"status": "exited"}
            if image_filter:
                filters["ancestor"] = image_filter

            containers = self.client.containers.list(all=True, filters=filters)
            for container in containers:
                try:
                    container.remove()
                    removed_count += 1
                except Exception as e:
                    logger.warning(f"Failed to remove container {container.id}: {e}")

            if removed_count > 0:
                logger.info(f"Cleaned up {removed_count} stopped containers")

        except Exception as e:
            logger.error(f"Failed to cleanup containers: {e}")

        return removed_count

    def remove_image(self, image_name: str, force: bool = False) -> bool:
        """
        Remove a Docker image.

        Args:
            image_name: Name of the image to remove
            force: Force removal even if containers are using it

        Returns:
            True if removed, False otherwise
        """
        try:
            self.client.images.remove(image_name, force=force)
            self._image_cache.pop(image_name, None)
            logger.info(f"Removed image {image_name}")
            return True
        except ImageNotFound:
            logger.warning(f"Image {image_name} not found")
            return False
        except Exception as e:
            logger.error(f"Failed to remove image {image_name}: {e}")
            return False

    def list_images(self, name_filter: Optional[str] = None) -> List[str]:
        """
        List available Docker images.

        Args:
            name_filter: Filter images by name pattern

        Returns:
            List of image names
        """
        try:
            images = self.client.images.list()
            result = []
            for image in images:
                for tag in image.tags:
                    if not name_filter or name_filter in tag:
                        result.append(tag)
            return result
        except Exception as e:
            logger.error(f"Failed to list images: {e}")
            return []

    def is_available(self) -> bool:
        """Check if Docker daemon is available."""
        try:
            self.client.ping()
            return True
        except:
            return False

    def get_stats(self) -> Dict[str, any]:
        """
        Get Docker system statistics.

        Returns:
            Dictionary with system info
        """
        try:
            info = self.client.info()
            return {
                "containers_running": info.get("ContainersRunning", 0),
                "containers_stopped": info.get("ContainersStopped", 0),
                "images": info.get("Images", 0),
                "memory_total": info.get("MemTotal", 0),
                "cpus": info.get("NCPU", 0),
            }
        except Exception as e:
            logger.error(f"Failed to get Docker stats: {e}")
            return {}


class DockerRuntime(Runtime):
    """
    Base class for Docker-based language runtimes.

    Provides Docker execution using DockerManager with automatic
    image building and container lifecycle management.
    """

    def __init__(self, config: RuntimeConfig, manager: Optional[DockerManager] = None):
        """
        Initialize Docker runtime.

        Args:
            config: Runtime configuration
            manager: Optional DockerManager instance (creates new if None)
        """
        self._config = config
        self._manager = manager or DockerManager()

        # Ensure the Docker image exists
        dockerfile_path = f"Dockerfile.{config.language}"
        success = self._manager.ensure_image(
            config.image,
            dockerfile_path=dockerfile_path,
            build_context="docker"
        )
        if not success:
            logger.warning(f"Failed to ensure image {config.image}")

    @property
    def language(self) -> str:
        """Language identifier."""
        return self._config.language

    @property
    def config(self) -> RuntimeConfig:
        """Runtime configuration."""
        return self._config

    def run(self, code: str, timeout: int = None) -> ExecutionResult:
        """
        Execute code in Docker container.

        Args:
            code: Code to execute
            timeout: Optional timeout override

        Returns:
            ExecutionResult with execution details
        """
        container_config = ContainerConfig(
            image=self._config.image,
            command=self._config.command,
            timeout_seconds=timeout or self._config.timeout_seconds,
            memory_limit=self._config.memory_limit,
            cpu_quota=self._config.cpu_quota,
            network_enabled=False,
            read_only=True,
            pids_limit=50,
        )

        return self._manager.run_container(container_config, code)

    def run_tests(self, code: str, test_code: str) -> ExecutionResult:
        """
        Execute code with tests.

        Default implementation: concatenate code and tests.
        Override in subclasses for language-specific test frameworks.

        Args:
            code: Main code
            test_code: Test code

        Returns:
            ExecutionResult with test execution details
        """
        combined = f"{code}\n\n{test_code}"
        return self.run(combined)

    def is_available(self) -> bool:
        """Check if Docker runtime is available."""
        return self._manager.is_available()
