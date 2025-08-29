"""Tests for load testing functionality."""

from mcp_scale_test.load_test import LoadTestStats


def test_test_stats_initialization() -> None:
    """Test TestStats initialization."""
    stats = LoadTestStats()

    assert stats.requests_sent == 0
    assert stats.requests_received == 0
    assert stats.successes == 0
    assert stats.failures == 0
    assert stats.response_times == []
    assert stats.errors == []
    assert stats.start_time is None
    assert stats.end_time is None


def test_test_stats_add_success() -> None:
    """Test adding successful requests."""
    stats = LoadTestStats()

    stats.add_success(0.1)
    stats.add_success(0.2)

    assert stats.requests_sent == 2
    assert stats.requests_received == 2
    assert stats.successes == 2
    assert stats.failures == 0
    assert stats.response_times == [0.1, 0.2]


def test_test_stats_add_failure() -> None:
    """Test adding failed requests."""
    stats = LoadTestStats()

    stats.add_failure("Connection error", 0.05)
    stats.add_failure("Timeout")

    assert stats.requests_sent == 2
    assert stats.requests_received == 1  # Only first failure had response time
    assert stats.successes == 0
    assert stats.failures == 2
    assert stats.response_times == [0.05]
    assert stats.errors == ["Connection error", "Timeout"]


def test_test_stats_to_dict() -> None:
    """Test converting stats to dictionary."""
    stats = LoadTestStats()
    stats.add_success(0.1)
    stats.add_success(0.3)
    stats.add_failure("Error", 0.2)

    result = stats.to_dict()

    assert result["requests_sent"] == 3
    assert result["requests_received"] == 3
    assert result["successes"] == 2
    assert result["failures"] == 1
    assert result["response_times"]["min_ms"] == 100.0
    assert result["response_times"]["max_ms"] == 300.0
    assert abs(result["response_times"]["avg_ms"] - 200.0) < 0.001
    assert result["error_summary"]["Error"] == 1


def test_test_stats_to_dict_empty() -> None:
    """Test converting empty stats to dictionary."""
    stats = LoadTestStats()
    result = stats.to_dict()

    assert result["requests_sent"] == 0
    assert result["response_times"]["min_ms"] == 0.0
    assert result["response_times"]["max_ms"] == 0.0
    assert result["response_times"]["avg_ms"] == 0.0
    # No execution time info without start/end times
    assert "execution_time" not in result
    assert "throughput" not in result


def test_test_stats_execution_time() -> None:
    """Test execution time tracking."""
    stats = LoadTestStats()
    stats.start_time = 1000.0
    stats.end_time = 1005.5
    stats.add_success(0.1)
    stats.add_success(0.2)

    result = stats.to_dict()

    assert result["execution_time"]["total_seconds"] == 5.5
    assert result["execution_time"]["start_time"] == 1000.0
    assert result["execution_time"]["end_time"] == 1005.5
    assert (
        result["throughput"]["requests_per_second"] == 0.36
    )  # 2 requests / 5.5 seconds
    assert (
        result["throughput"]["successes_per_second"] == 0.36
    )  # 2 successes / 5.5 seconds
