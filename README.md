# MCP Scale Test

CLI tool for load testing MCP (Model Context Protocol) servers with configurable concurrent requests.

## Installation

```bash
# Using uv (recommended)
make install

# Or using pip
pip install -e .
```

## Quick Start

```bash
# Run example load test
uv run mcp-scale-test --config examples/scale.yaml --verbose
```

## Development

```bash
# Install development dependencies
make install-dev

# Run code formatting and checks
make format lint typecheck test

# Or individual commands
make format    # Format code
make lint      # Check code style  
make typecheck # Type checking
make test      # Run tests
```

## Configuration

Create YAML configuration files specifying the MCP server and test parameters:

```yaml
server:
  transport: "sse" | "streamable_http"
  host: "localhost"           # Server hostname
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


## Requirements

- Python 3.10+
- MCP Python library
- Target MCP server implementing the tool being tested

## Troubleshooting

- **Connection timeouts**: Verify the MCP server is running and accessible at the specified endpoint
- **Tool not found**: Ensure the specified tool_name exists on the target MCP server
- **Protocol errors**: Check that the server implements the MCP protocol correctly for the chosen transport