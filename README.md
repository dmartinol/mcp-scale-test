# MCP Scale Test

CLI tool for load testing MCP (Model Context Protocol) servers to evaluate performance and scalability under concurrent requests.

## Features

- **Multiple MCP Transports**: Supports stdio, SSE, and streamable HTTP transports
- **Concurrent Load Testing**: Configurable number of concurrent workers
- **Comprehensive Metrics**: Request/response counts, success/failure ratios, response times
- **YAML Configuration**: Easy-to-use configuration files with examples
- **Flexible Output**: Console output or save results to YAML files

## Installation

```bash
# Using uv (recommended)
uv sync

# Or using pip
pip install -e .
```

## Quick Start

```bash
# Run a basic load test
uv run mcp-scale-test --config examples/stdio-config.yaml

# Save detailed results
uv run mcp-scale-test --config examples/sse-config.yaml --output results.yaml --verbose

# Test with custom parameters
uv run mcp-scale-test --config examples/streamable-http-config.yaml
```

## Configuration

Create YAML configuration files specifying the MCP server and test parameters:

```yaml
server:
  transport: "stdio" | "sse" | "streamable_http"
  host: "localhost"           # For stdio: command to execute
  port: 8080                  # Port for sse/streamable_http
  path: "/sse"               # Endpoint path (optional)

test:
  tool_name: "echo"          # MCP tool to test
  tool_args:                 # Arguments for the tool
    message: "test data"
  concurrent_requests: 5     # Number of concurrent workers
  duration_seconds: 30       # Test duration
```

## Transport Types

### stdio
For MCP servers that communicate via stdin/stdout:
```yaml
server:
  transport: stdio
  host: "python my_mcp_server.py"  # Command to run the server
```

### sse (Server-Sent Events)
For MCP servers using SSE over HTTP:
```yaml
server:
  transport: sse
  host: localhost
  port: 8080
  path: /sse
```

### streamable_http
For MCP servers using streamable HTTP transport:
```yaml
server:
  transport: streamable_http
  host: localhost
  port: 3000
  path: /mcp
```

## Example Output

```yaml
test_config:
  server:
    transport: sse
    host: localhost
    port: 8080
    path: /sse
  test:
    tool_name: echo
    concurrent_requests: 5
    duration_seconds: 30

results:
  requests_sent: 150
  requests_received: 148
  successes: 145
  failures: 3
  response_times:
    min_ms: 12.5
    max_ms: 234.7
    avg_ms: 45.2
  error_summary:
    "Connection timeout": 2
    "Tool error: Invalid input": 1
```

## Development

```bash
# Install with development dependencies
uv sync --dev

# Run tests
uv run pytest

# Code quality checks
uv run ruff check .
uv run ruff format .
uv run mypy .

# Or with pip
pip install -e ".[dev]"
pytest && ruff check . && mypy .
```

## Requirements

- Python 3.10+
- MCP Python library
- Target MCP server implementing the tool being tested

## Troubleshooting

- **Connection timeouts**: Verify the MCP server is running and accessible at the specified endpoint
- **Tool not found**: Ensure the specified tool_name exists on the target MCP server
- **Protocol errors**: Check that the server implements the MCP protocol correctly for the chosen transport