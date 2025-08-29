"""Tests for variable expansion functionality."""

import re
import time

from mcp_scale_test.variables import VariableExpander


def test_variable_expander_initialization() -> None:
    """Test VariableExpander initialization."""
    expander = VariableExpander()
    assert expander._counter == 0


def test_timestamp_variable() -> None:
    """Test {{timestamp}} variable expansion."""
    expander = VariableExpander()

    before = time.time()
    result = expander.expand_arguments({"time": "{{timestamp}}"})
    after = time.time()

    assert isinstance(result["time"], float)
    assert before <= result["time"] <= after


def test_counter_variable() -> None:
    """Test {{counter}} variable expansion."""
    expander = VariableExpander()

    result1 = expander.expand_arguments({"count": "{{counter}}"})
    result2 = expander.expand_arguments({"count": "{{counter}}"})
    result3 = expander.expand_arguments({"count": "{{counter}}"})

    assert result1["count"] == 1
    assert result2["count"] == 2
    assert result3["count"] == 3


def test_counter_reset() -> None:
    """Test counter reset functionality."""
    expander = VariableExpander()

    expander.expand_arguments({"count": "{{counter}}"})
    expander.expand_arguments({"count": "{{counter}}"})

    expander.reset_counter()
    result = expander.expand_arguments({"count": "{{counter}}"})

    assert result["count"] == 1


def test_random_randint() -> None:
    """Test {{random.randint(min,max)}} variable expansion."""
    expander = VariableExpander()

    # Test multiple calls to ensure randomness and range
    results = []
    for _ in range(50):
        result = expander.expand_arguments({"num": "{{random.randint(1,10)}}"})
        results.append(result["num"])

    # Check all values are in range
    for num in results:
        assert isinstance(num, int)
        assert 1 <= num <= 10

    # Check we got some variety (very unlikely to get all the same number)
    assert len(set(results)) > 1


def test_random_randint_larger_range() -> None:
    """Test random.randint with larger range."""
    expander = VariableExpander()

    result = expander.expand_arguments({"big_num": "{{random.randint(100,1000)}}"})

    assert isinstance(result["big_num"], int)
    assert 100 <= result["big_num"] <= 1000


def test_multiple_variables_same_string() -> None:
    """Test multiple variables in the same string."""
    expander = VariableExpander()

    result = expander.expand_arguments(
        {"message": "Request {{counter}} at {{timestamp}}"}
    )

    message = result["message"]
    assert "Request 1 at " in message
    assert re.search(r"Request 1 at \d+\.\d+", message)


def test_nested_data_structures() -> None:
    """Test variable expansion in nested dictionaries and lists."""
    expander = VariableExpander()

    args = {
        "user": {"id": "{{counter}}", "timestamp": "{{timestamp}}"},
        "data": [
            "{{counter}}",
            {"value": "{{random.randint(1,100)}}", "time": "{{timestamp}}"},
        ],
    }

    result = expander.expand_arguments(args)

    # Check nested dictionary
    assert result["user"]["id"] == 1
    assert isinstance(result["user"]["timestamp"], float)

    # Check list with nested data
    assert result["data"][0] == 2  # Counter incremented
    assert isinstance(result["data"][1]["value"], int)
    assert 1 <= result["data"][1]["value"] <= 100
    assert isinstance(result["data"][1]["time"], float)


def test_single_variable_type_preservation() -> None:
    """Test that single variables preserve their native types."""
    expander = VariableExpander()

    result = expander.expand_arguments(
        {
            "count": "{{counter}}",
            "time": "{{timestamp}}",
            "num": "{{random.randint(1,100)}}",
        }
    )

    # Should be actual types, not strings
    assert isinstance(result["count"], int)
    assert isinstance(result["time"], float)
    assert isinstance(result["num"], int)


def test_mixed_variables_and_text() -> None:
    """Test mixing variables with regular text."""
    expander = VariableExpander()

    result = expander.expand_arguments(
        {
            "message": (
                "User {{counter}} logged in at {{timestamp}} "
                "with priority {{random.randint(1,5)}}"
            )
        }
    )

    message = result["message"]
    assert "User 1 logged in at " in message
    assert re.search(r"with priority [1-5]", message)


def test_unknown_variable() -> None:
    """Test handling of unknown variables."""
    expander = VariableExpander()

    result = expander.expand_arguments({"test": "{{unknown_var}}"})

    assert result["test"] == "{{unknown:unknown_var}}"


def test_empty_arguments() -> None:
    """Test handling of empty arguments."""
    expander = VariableExpander()

    result = expander.expand_arguments({})
    assert result == {}

    result = expander.expand_arguments(None)  # type: ignore
    assert result == {}


def test_no_variables() -> None:
    """Test arguments without variables are unchanged."""
    expander = VariableExpander()

    args = {
        "message": "hello world",
        "count": 42,
        "data": ["a", "b", "c"],
        "nested": {"key": "value"},
    }

    result = expander.expand_arguments(args)
    assert result == args


def test_invalid_randint_format() -> None:
    """Test invalid randint expressions."""
    expander = VariableExpander()

    try:
        expander.expand_arguments({"bad": "{{random.randint(invalid)}}"})
        raise AssertionError("Should have raised ValueError")
    except ValueError as e:
        assert "Invalid randint expression" in str(e)


def test_complex_example() -> None:
    """Test a complex real-world example."""
    expander = VariableExpander()

    args = {
        "query": "search term {{counter}}",
        "metadata": {
            "timestamp": "{{timestamp}}",
            "request_id": "req-{{counter}}-{{random.randint(1000,9999)}}",
            "config": {
                "timeout": "{{random.randint(5,30)}}",
                "retries": "{{random.randint(1,3)}}",
            },
        },
        "filters": [
            "category_{{random.randint(1,5)}}",
            "priority_{{random.randint(1,10)}}",
        ],
    }

    result = expander.expand_arguments(args)

    # Verify structure and types
    assert result["query"] == "search term 1"
    assert isinstance(result["metadata"]["timestamp"], float)
    assert re.match(r"req-2-\d{4}", result["metadata"]["request_id"])
    assert isinstance(result["metadata"]["config"]["timeout"], int)
    assert isinstance(result["metadata"]["config"]["retries"], int)
    assert 5 <= result["metadata"]["config"]["timeout"] <= 30
    assert 1 <= result["metadata"]["config"]["retries"] <= 3
    assert re.match(r"category_[1-5]", result["filters"][0])
    assert re.match(r"priority_[1-9]|priority_10", result["filters"][1])
