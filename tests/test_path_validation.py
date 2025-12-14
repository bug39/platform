"""Tests for Docker path validation."""

import pytest
import tempfile
from pathlib import Path
from src.assistant.utils.validation import (
    validate_docker_image_name,
    validate_dockerfile_path,
    validate_build_context,
)
from src.assistant.runtimes.docker import ContainerConfig


class TestValidateDockerImageName:
    """Test Docker image name validation."""

    def test_valid_simple_name(self):
        """Test that simple valid image name passes."""
        validate_docker_image_name("python")  # Should not raise

    def test_valid_name_with_tag(self):
        """Test that image name with tag passes."""
        validate_docker_image_name("python:3.12")

    def test_valid_name_with_registry(self):
        """Test that image name with registry passes."""
        validate_docker_image_name("docker.io/library/python:3.12")

    def test_valid_name_with_user(self):
        """Test that image name with user/repo passes."""
        validate_docker_image_name("user/repository:latest")

    def test_valid_name_with_hyphen(self):
        """Test that image name with hyphens passes."""
        validate_docker_image_name("assistant-python:latest")

    def test_valid_name_with_underscore(self):
        """Test that image name with underscores passes."""
        validate_docker_image_name("my_image:tag")

    def test_empty_name_rejected(self):
        """Test that empty image name is rejected."""
        with pytest.raises(ValueError, match="cannot be empty"):
            validate_docker_image_name("")

    def test_whitespace_only_rejected(self):
        """Test that whitespace-only name is rejected."""
        with pytest.raises(ValueError, match="cannot be empty"):
            validate_docker_image_name("   ")

    def test_path_traversal_rejected(self):
        """Test that path traversal in name is rejected."""
        with pytest.raises(ValueError, match="Path traversal"):
            validate_docker_image_name("../../../etc/passwd")

    def test_invalid_characters_rejected(self):
        """Test that invalid characters are rejected."""
        with pytest.raises(ValueError, match="Only alphanumeric"):
            validate_docker_image_name("image@name")

        with pytest.raises(ValueError, match="Only alphanumeric"):
            validate_docker_image_name("image name")  # Space

        with pytest.raises(ValueError, match="Only alphanumeric"):
            validate_docker_image_name("image;name")  # Semicolon


class TestValidateDockerfilePath:
    """Test Dockerfile path validation."""

    def test_valid_simple_path(self):
        """Test that simple valid path passes."""
        # Using current directory as build context
        result = validate_dockerfile_path("Dockerfile", ".")
        assert isinstance(result, Path)

    def test_valid_path_in_subdirectory(self):
        """Test that path in subdirectory passes."""
        result = validate_dockerfile_path("Dockerfile.python", "docker")
        assert isinstance(result, Path)

    def test_path_traversal_rejected(self):
        """Test that path traversal is rejected."""
        with pytest.raises(ValueError, match="Path traversal"):
            validate_dockerfile_path("../../../etc/passwd", "docker")

    def test_path_with_double_dot_rejected(self):
        """Test that paths with .. are rejected."""
        with pytest.raises(ValueError, match="Path traversal"):
            validate_dockerfile_path("../Dockerfile", "docker")

    def test_absolute_path_rejected(self):
        """Test that absolute paths are rejected."""
        with pytest.raises(ValueError, match="must be relative"):
            validate_dockerfile_path("/etc/passwd", "docker")

    def test_empty_path_rejected(self):
        """Test that empty path is rejected."""
        with pytest.raises(ValueError, match="cannot be empty"):
            validate_dockerfile_path("", "docker")

    def test_path_outside_context_rejected(self):
        """Test that paths resolving outside context are rejected."""
        # Create temporary directories
        with tempfile.TemporaryDirectory() as tmpdir:
            context_dir = Path(tmpdir) / "context"
            context_dir.mkdir()

            # This should be rejected as it escapes the context
            with pytest.raises(ValueError):
                validate_dockerfile_path("../../etc/passwd", str(context_dir))


class TestValidateBuildContext:
    """Test build context validation."""

    def test_valid_current_directory(self):
        """Test that current directory passes."""
        result = validate_build_context(".")
        assert isinstance(result, Path)
        assert result.exists()
        assert result.is_dir()

    def test_valid_existing_directory(self):
        """Test that existing directory passes."""
        result = validate_build_context("docker")
        assert isinstance(result, Path)
        assert result.exists()

    def test_nonexistent_directory_rejected(self):
        """Test that nonexistent directory is rejected."""
        with pytest.raises(ValueError, match="does not exist"):
            validate_build_context("/nonexistent/directory")

    def test_file_instead_of_directory_rejected(self):
        """Test that file path is rejected."""
        # Create a temporary file
        with tempfile.NamedTemporaryFile() as tmpfile:
            with pytest.raises(ValueError, match="must be a directory"):
                validate_build_context(tmpfile.name)

    def test_empty_path_rejected(self):
        """Test that empty path is rejected."""
        with pytest.raises(ValueError, match="cannot be empty"):
            validate_build_context("")


class TestContainerConfigImageValidation:
    """Test that ContainerConfig validates image names."""

    def test_valid_image_name_accepted(self):
        """Test that valid image name is accepted in ContainerConfig."""
        config = ContainerConfig(
            image="python:3.12",
            command=["python", "-c"]
        )
        assert config.image == "python:3.12"

    def test_invalid_image_name_rejected(self):
        """Test that invalid image name is rejected in ContainerConfig."""
        with pytest.raises(ValueError, match="Invalid Docker image name"):
            ContainerConfig(
                image="bad@image",
                command=["python"]
            )

    def test_path_traversal_in_image_rejected(self):
        """Test that path traversal in image is rejected."""
        with pytest.raises(ValueError, match="Path traversal"):
            ContainerConfig(
                image="../../../etc/passwd",
                command=["python"]
            )


class TestDockerManagerPathValidation:
    """Test that DockerManager validates paths."""

    def test_invalid_image_name_returns_false(self):
        """Test that invalid image name causes ensure_image to return False."""
        from src.assistant.runtimes.docker import DockerManager
        from src.assistant.config import SandboxConfig

        manager = DockerManager(SandboxConfig())

        # Invalid image name should return False
        result = manager.ensure_image("bad@image")
        assert result is False

    def test_path_traversal_in_dockerfile_returns_false(self):
        """Test that path traversal in dockerfile causes ensure_image to return False."""
        from src.assistant.runtimes.docker import DockerManager
        from src.assistant.config import SandboxConfig

        manager = DockerManager(SandboxConfig())

        # Path traversal should return False
        result = manager.ensure_image(
            "test-image",
            dockerfile_path="../../../etc/passwd",
            build_context="docker"
        )
        assert result is False

    def test_nonexistent_build_context_returns_false(self):
        """Test that nonexistent build context causes ensure_image to return False."""
        from src.assistant.runtimes.docker import DockerManager
        from src.assistant.config import SandboxConfig

        manager = DockerManager(SandboxConfig())

        # Nonexistent context should return False
        result = manager.ensure_image(
            "test-image",
            dockerfile_path="Dockerfile",
            build_context="/nonexistent/directory"
        )
        assert result is False
