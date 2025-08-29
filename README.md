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
  tool_args:                 # Arguments for the tool (supports variables)
    message: "Request {{counter}} at {{timestamp}}"
    priority: "{{random.randint(1,5)}}"
  concurrent_requests: 5     # Number of concurrent workers
  duration_seconds: 30       # Test duration
  shared_session: false      # Use shared session for all workers (default: false)
```

## Dynamic Variables

Tool arguments support built-in variables that are expanded for each request:

- **`{{timestamp}}`**: Current Unix timestamp (float)
- **`{{counter}}`**: Incrementing request counter (starts at 1)
- **`{{random.randint(min,max)}}`**: Random integer in specified range

Variables work in nested structures and preserve types when used alone:

```yaml
tool_args:
  # Mixed text and variables
  message: "User {{counter}} at {{timestamp}}"
  
  # Type preservation - these become actual int/float values
  user_id: "{{counter}}"
  timestamp: "{{timestamp}}"
  priority: "{{random.randint(1,10)}}"
  
  # Nested structures
  metadata:
    request_id: "req-{{counter}}-{{random.randint(1000,9999)}}"
    config:
      timeout: "{{random.randint(5,30)}}"
      
  # Arrays
  tags: ["test_{{counter}}", "priority_{{random.randint(1,3)}}"]
```

Each request gets unique values, enabling realistic load testing with varied data.

## Session Management

Control how MCP connections are managed within each worker:

### Shared Session Per Worker (default: false)
```yaml
test:
  shared_session: true   # Each worker reuses one connection for all requests
```

**Benefits:**
- More realistic application usage (persistent connections)
- Better performance due to connection reuse
- Tests session-level concurrency handling
- Lower connection overhead

### New Connection Per Request (default)
```yaml
test:
  shared_session: false  # Each request creates a new connection
```

**Benefits:**
- Tests connection establishment overhead  
- Simulates serverless/stateless scenarios
- Higher isolation between requests
- Tests server's connection handling under load

**Use shared sessions when:**
- Simulating persistent client applications
- Testing session concurrency limits
- Optimizing for performance

**Use new connections when:**
- Testing connection pooling and limits
- Simulating high-churn scenarios (serverless, etc.)
- Measuring connection establishment costs

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
  sessions_created: 5
  execution_time:
    total_seconds: 30.125
    start_time: 1640995200.0
    end_time: 1640995230.125
  response_times:
    min_ms: 12.5
    max_ms: 234.7
    avg_ms: 45.2
  throughput:
    requests_per_second: 4.98
    successes_per_second: 4.81
  error_summary:
    "Connection timeout": 2
    "Tool error: Invalid input": 1
```

## Output Metrics

The tool provides comprehensive performance metrics:

- **Request Counts**: Total sent/received, successes, failures
- **Execution Time**: Precise timing with start/end timestamps and total duration
- **Response Times**: Min, max, and average response times in milliseconds
- **Throughput**: Requests per second and success rate calculations
- **Error Analysis**: Categorized error summary with occurrence counts

## Requirements

- Python 3.10+
- MCP Python library
- Target MCP server implementing the tool being tested

## Troubleshooting

- **Connection timeouts**: Verify the MCP server is running and accessible at the specified endpoint
- **Tool not found**: Ensure the specified tool_name exists on the target MCP server
- **Protocol errors**: Check that the server implements the MCP protocol correctly for the chosen transport