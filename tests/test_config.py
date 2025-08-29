"""Tests for configuration handling."""

import pytest

from mcp_scale_test.config import Config, LoadTestConfig, ServerConfig


def test_server_config_validation() -> None:
    """Test server configuration validation."""
    config = ServerConfig(transport="sse", host="localhost", port=8080, path="/sse")

    assert config.transport == "sse"
    assert config.host == "localhost"
    assert config.port == 8080
    assert config.path == "/sse"


def test_test_config_validation() -> None:
    """Test test configuration validation."""
    config = LoadTestConfig(
        tool_name="echo",
        tool_args={"message": "test"},
        concurrent_requests=5,
        duration_seconds=10,
    )

    assert config.tool_name == "echo"
    assert config.tool_args == {"message": "test"}
    assert config.concurrent_requests == 5
    assert config.duration_seconds == 10


def test_complete_config() -> None:
    """Test complete configuration."""
    config = Config(
        server=ServerConfig(transport="sse", host="localhost", port=8080, path="/sse"),
        test=LoadTestConfig(
            tool_name="echo",
            tool_args={"message": "test"},
            concurrent_requests=1,
            duration_seconds=1,
        ),
    )

    assert config.server.transport == "sse"
    assert config.test.tool_name == "echo"


def test_invalid_transport() -> None:
    """Test invalid transport type."""
    with pytest.raises(ValueError):
        ServerConfig(transport="invalid", host="localhost")  # type: ignore[arg-type]


def test_invalid_concurrent_requests() -> None:
    """Test invalid concurrent requests."""
    with pytest.raises(ValueError):
        LoadTestConfig(tool_name="test", concurrent_requests=0, duration_seconds=1)
