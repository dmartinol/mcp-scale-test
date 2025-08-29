"""Configuration handling for MCP scale testing."""

from typing import Any, Dict, Literal, Optional

import yaml
from pydantic import BaseModel, Field

TransportType = Literal["sse", "streamable_http"]


class ServerConfig(BaseModel):
    """MCP server connection configuration."""

    transport: TransportType
    host: str = "localhost"
    port: Optional[int] = None
    path: Optional[str] = None


class LoadTestConfig(BaseModel):
    """Load test configuration."""

    tool_name: str
    tool_args: Dict[str, Any] = Field(default_factory=dict)
    concurrent_requests: int = Field(ge=1, default=1)
    duration_seconds: int = Field(ge=1, default=60)


class Config(BaseModel):
    """Complete configuration for MCP scale testing."""

    server: ServerConfig
    test: LoadTestConfig


def load_config(config_path: str) -> Config:
    """Load configuration from YAML file."""
    with open(config_path) as f:
        data = yaml.safe_load(f)

    return Config(**data)


def save_results(results: Dict[str, Any], output_path: str) -> None:
    """Save test results to YAML file."""
    with open(output_path, "w") as f:
        yaml.dump(results, f, default_flow_style=False, indent=2)
