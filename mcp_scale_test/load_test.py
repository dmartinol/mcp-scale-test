"""Load testing functionality for MCP servers."""

import asyncio
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .client import MCPClient, create_client
from .config import Config
from .variables import VariableExpander


@dataclass
class LoadTestStats:
    """Statistics for a load test run."""

    requests_sent: int = 0
    requests_received: int = 0
    successes: int = 0
    failures: int = 0
    response_times: List[float] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    sessions_created: int = 0

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

    def add_session_created(self) -> None:
        """Record that a new MCP session was created."""
        self.sessions_created += 1

    def to_dict(self) -> Dict[str, Any]:
        """Convert stats to dictionary for YAML output."""
        result: Dict[str, Any] = {
            "requests_sent": self.requests_sent,
            "requests_received": self.requests_received,
            "successes": self.successes,
            "failures": self.failures,
            "sessions_created": self.sessions_created,
        }

        # Add execution time information
        if self.start_time is not None and self.end_time is not None:
            execution_time_seconds = self.end_time - self.start_time
            result["execution_time"] = {
                "total_seconds": round(execution_time_seconds, 3),
                "start_time": self.start_time,
                "end_time": self.end_time,
            }

        if self.response_times:
            response_times_dict: Dict[str, float] = {
                "min_ms": min(self.response_times) * 1000,
                "max_ms": max(self.response_times) * 1000,
                "avg_ms": sum(self.response_times) / len(self.response_times) * 1000,
            }
        else:
            response_times_dict = {
                "min_ms": 0.0,
                "max_ms": 0.0,
                "avg_ms": 0.0,
            }
        result["response_times"] = response_times_dict

        if self.errors:
            error_summary: Dict[str, int] = {}
            for error in self.errors:
                error_summary[error] = error_summary.get(error, 0) + 1
            result["error_summary"] = error_summary

        # Add throughput metrics if we have execution time
        if (
            self.start_time is not None
            and self.end_time is not None
            and self.execution_time_seconds > 0
        ):
            result["throughput"] = {
                "requests_per_second": round(
                    self.requests_sent / self.execution_time_seconds, 2
                ),
                "successes_per_second": round(
                    self.successes / self.execution_time_seconds, 2
                ),
            }

        return result

    @property
    def execution_time_seconds(self) -> float:
        """Get execution time in seconds."""
        if self.start_time is not None and self.end_time is not None:
            return self.end_time - self.start_time
        return 0.0


class LoadTester:
    """Load tester for MCP servers."""

    def __init__(self, config: Config):
        self.config = config
        self.stats = LoadTestStats()
        self._stop_event = asyncio.Event()
        self._variable_expander = VariableExpander()

    async def run_test(self) -> Dict[str, Any]:
        """Run the load test and return results."""
        print(
            f"Starting load test with {self.config.test.concurrent_requests} "
            f"concurrent requests for {self.config.test.duration_seconds} seconds..."
        )

        # Record start time
        self.stats.start_time = time.time()

        # Start the timer
        asyncio.create_task(self._timer())

        session_mode = (
            "shared session per worker"
            if self.config.test.shared_session
            else "new connection per request"
        )
        print(f"Using {session_mode}")

        # Create and start concurrent workers
        tasks = []
        for i in range(self.config.test.concurrent_requests):
            task = asyncio.create_task(self._worker(f"worker-{i}"))
            tasks.append(task)

        # Wait for all workers to complete
        await asyncio.gather(*tasks, return_exceptions=True)

        # Record end time
        self.stats.end_time = time.time()

        execution_time = self.stats.execution_time_seconds
        print(
            f"Test completed in {execution_time:.2f}s. "
            f"Sent: {self.stats.requests_sent}, "
            f"Received: {self.stats.requests_received}, "
            f"Successes: {self.stats.successes}, Failures: {self.stats.failures}, "
            f"Sessions: {self.stats.sessions_created}"
        )
        if execution_time > 0:
            success_rate = (
                (self.stats.successes / self.stats.requests_sent * 100)
                if self.stats.requests_sent > 0
                else 0
            )
            print(
                f"Throughput: {self.stats.requests_sent / execution_time:.1f} req/s, "
                f"Success rate: {success_rate:.1f}%"
            )

        return self.stats.to_dict()

    async def _timer(self) -> None:
        """Timer to stop the test after the specified duration."""
        await asyncio.sleep(self.config.test.duration_seconds)
        self._stop_event.set()

    async def _worker(self, worker_id: str) -> None:
        """Worker coroutine that sends requests until stopped."""
        try:
            if self.config.test.shared_session:
                # Create one client connection for this worker and reuse it
                client = create_client(self.config.server)
                await client.connect()
                self.stats.add_session_created()  # Track session creation

                # Use the client as an async context manager
                async with client:
                    await self._run_worker_loop_with_shared_session(client, worker_id)
            else:
                # Create new connection for each request
                await self._run_worker_loop_without_shared_session(worker_id)

        except asyncio.TimeoutError:
            self.stats.add_failure(f"Worker {worker_id} connection timeout")
        except Exception as e:
            self.stats.add_failure(f"Worker {worker_id} error: {str(e)}")

    async def _run_worker_loop_with_shared_session(
        self, client: MCPClient, worker_id: str
    ) -> None:
        """Run worker loop with shared session - reuse same client connection."""
        # Keep sending requests until stopped
        while not self._stop_event.is_set():
            await self._send_request_with_client(client, worker_id)

            # Small delay to prevent overwhelming the server
            await asyncio.sleep(0.01)

    async def _run_worker_loop_without_shared_session(self, worker_id: str) -> None:
        """Run worker loop without shared session - new connection per request."""
        # Keep sending requests until stopped
        while not self._stop_event.is_set():
            await self._send_request_with_new_connection(worker_id)

            # Small delay to prevent overwhelming the server
            await asyncio.sleep(0.01)

    async def _send_request_with_client(
        self, client: MCPClient, _worker_id: str
    ) -> None:
        """Send a single request using provided client connection."""
        start_time = time.time()

        try:
            # Expand variables in tool arguments for each request
            expanded_args = self._variable_expander.expand_arguments(
                self.config.test.tool_args
            )

            await client.call_tool(self.config.test.tool_name, expanded_args)

            end_time = time.time()
            response_time = end_time - start_time

            # MCP client raises exceptions for errors, success if we get here
            self.stats.add_success(response_time)

        except asyncio.CancelledError:
            # Worker was cancelled, this is expected during shutdown
            pass

        except Exception as e:
            end_time = time.time()
            response_time = end_time - start_time
            self.stats.add_failure(f"Request error: {str(e)}", response_time)

    async def _send_request_with_new_connection(self, _worker_id: str) -> None:
        """Send a single request creating a new connection each time."""
        start_time = time.time()

        try:
            # Create new client for this single request
            client = create_client(self.config.server)
            await client.connect()
            self.stats.add_session_created()  # Track session creation

            # Use the client as an async context manager
            async with client:
                # Expand variables in tool arguments for each request
                expanded_args = self._variable_expander.expand_arguments(
                    self.config.test.tool_args
                )

                await client.call_tool(self.config.test.tool_name, expanded_args)

            end_time = time.time()
            response_time = end_time - start_time

            # MCP client raises exceptions for errors, success if we get here
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
