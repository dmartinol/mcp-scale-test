"""Load testing functionality for MCP servers."""

import asyncio
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .client import MCPClient, create_client
from .config import Config


@dataclass
class TestStats:
    """Statistics for a load test run."""
    
    requests_sent: int = 0
    requests_received: int = 0
    successes: int = 0
    failures: int = 0
    response_times: List[float] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    
    def add_success(self, response_time: float) -> None:
        """Record a successful request."""
        self.requests_sent += 1
        self.requests_received += 1
        self.successes += 1
        self.response_times.append(response_time)
    
    def add_failure(self, error: str, response_time: Optional[float] = None) -> None:
        """Record a failed request."""
        self.requests_sent += 1
        self.failures += 1
        self.errors.append(error)
        if response_time is not None:
            self.requests_received += 1
            self.response_times.append(response_time)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert stats to dictionary for YAML output."""
        result = {
            "requests_sent": self.requests_sent,
            "requests_received": self.requests_received,
            "successes": self.successes,
            "failures": self.failures,
        }
        
        if self.response_times:
            result["response_times"] = {
                "min_ms": min(self.response_times) * 1000,
                "max_ms": max(self.response_times) * 1000,
                "avg_ms": sum(self.response_times) / len(self.response_times) * 1000,
            }
        else:
            result["response_times"] = {
                "min_ms": 0.0,
                "max_ms": 0.0,
                "avg_ms": 0.0,
            }
        
        if self.errors:
            result["error_summary"] = {}
            for error in self.errors:
                result["error_summary"][error] = result["error_summary"].get(error, 0) + 1
        
        return result


class LoadTester:
    """Load tester for MCP servers."""
    
    def __init__(self, config: Config):
        self.config = config
        self.stats = TestStats()
        self._stop_event = asyncio.Event()
    
    async def run_test(self) -> Dict[str, Any]:
        """Run the load test and return results."""
        print(f"Starting load test with {self.config.test.concurrent_requests} concurrent requests for {self.config.test.duration_seconds} seconds...")
        
        # Start the timer
        asyncio.create_task(self._timer())
        
        # Create and start concurrent workers
        tasks = []
        for i in range(self.config.test.concurrent_requests):
            task = asyncio.create_task(self._worker(f"worker-{i}"))
            tasks.append(task)
        
        # Wait for all workers to complete
        await asyncio.gather(*tasks, return_exceptions=True)
        
        print(f"Test completed. Sent: {self.stats.requests_sent}, Received: {self.stats.requests_received}, Successes: {self.stats.successes}, Failures: {self.stats.failures}")
        
        return self.stats.to_dict()
    
    async def _timer(self) -> None:
        """Timer to stop the test after the specified duration."""
        await asyncio.sleep(self.config.test.duration_seconds)
        self._stop_event.set()
    
    async def _worker(self, worker_id: str) -> None:
        """Worker coroutine that sends requests until stopped."""
        try:
            # Create client and use proper async context manager
            client = create_client(self.config.server)
            await client.connect()
            
            # Use the client as an async context manager for SSE clients
            if hasattr(client, '__aenter__'):
                async with client:
                    await self._run_worker_loop(client, worker_id)
            else:
                # For stdio clients that don't have context manager
                try:
                    await self._run_worker_loop(client, worker_id)
                finally:
                    await client.disconnect()
        
        except asyncio.TimeoutError:
            self.stats.add_failure(f"Worker {worker_id} connection timeout")
        except Exception as e:
            self.stats.add_failure(f"Worker {worker_id} error: {str(e)}")
    
    async def _run_worker_loop(self, client: MCPClient, worker_id: str) -> None:
        """Run the main worker loop for sending requests."""
        # Keep sending requests until stopped
        while not self._stop_event.is_set():
            await self._send_request(client, worker_id)
            
            # Small delay to prevent overwhelming the server
            await asyncio.sleep(0.01)
    
    async def _send_request(self, client: MCPClient, worker_id: str) -> None:
        """Send a single request and record the result."""
        start_time = time.time()
        
        try:
            result = await client.call_tool(
                self.config.test.tool_name,
                self.config.test.tool_args
            )
            
            end_time = time.time()
            response_time = end_time - start_time
            
            # MCP client will raise exceptions for errors, so if we get here it's a success
            self.stats.add_success(response_time)
        
        except asyncio.CancelledError:
            # Worker was cancelled, this is expected during shutdown
            pass
        
        except Exception as e:
            end_time = time.time()
            response_time = end_time - start_time
            self.stats.add_failure(f"Request error: {str(e)}", response_time)


async def run_load_test(config: Config) -> Dict[str, Any]:
    """Run a load test with the given configuration."""
    tester = LoadTester(config)
    return await tester.run_test()