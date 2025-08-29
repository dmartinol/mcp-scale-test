# CLAUDE.md

This file provides guidance to Claude Code when working with this MCP scale testing tool.

## Project Overview

Python CLI tool for load testing MCP (Model Context Protocol) servers. Uses the official Python MCP client library to establish connections via SSE or streamable HTTP transports and measures performance under concurrent load.

## Key Architecture Components

- **`mcp_scale_test/client.py`**: MCP client implementations for each transport type using official MCP library
- **`mcp_scale_test/load_test.py`**: Concurrent worker orchestration and statistics collection  
- **`mcp_scale_test/config.py`**: YAML configuration parsing with Pydantic models
- **`mcp_scale_test/cli.py`**: Click-based CLI interface

## Development Commands

```bash
# Install dependencies (prefer uv)
uv sync --dev

# Run the tool
uv run mcp-scale-test --config examples/sse-config.yaml --verbose

# Development workflow
uv run ruff check . && uv run ruff format . && uv run mypy .
uv run pytest

# Package installation
pip install -e .
```

## Transport Implementation Notes

**sse**: HTTP Server-Sent Events using `sse_client()` 
**streamable_http**: HTTP streaming using `streamablehttp_client()`

All transports use the official MCP Python library context managers.

## Common Issues

**MCP Session Initialization Timeout**: The most common issue is when `session.initialize()` hangs. This indicates:
- Server not implementing MCP initialize handshake correctly
- Protocol version mismatch between client and server
- Server not responding to MCP protocol messages

**Context Manager Cleanup Errors**: MCP client library context managers can have cleanup issues when connections fail. These are generally safe to ignore.

## Configuration Examples

Located in `examples/` directory:
- `sse-config.yaml`: HTTP SSE servers  
- `streamable-http-config.yaml`: HTTP streaming servers

## Testing Strategy

The tool establishes MCP connections, initializes sessions, then repeatedly calls specified tools with concurrent workers for a duration. Statistics track request counts, response times, and error patterns.

Timeouts are configured at multiple levels:
- Transport connection: 10s
- Session initialization: 10s  
- Worker connection: 25s
- Individual requests: based on tool complexity