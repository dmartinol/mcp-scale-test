"""CLI interface for MCP scale testing."""

import asyncio
import sys
from pathlib import Path
from typing import Optional

import click

from . import __version__
from .config import load_config, save_results
from .load_test import run_load_test


@click.command()
@click.option(
    "--config",
    "-c",
    required=True,
    type=click.Path(exists=True, path_type=Path),
    help="Path to YAML configuration file",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    help="Path to save results YAML file (default: print to stdout)",
)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.version_option(version=__version__)
def main(config: Path, output: Optional[Path], verbose: bool) -> None:
    """
    MCP Scale Test - CLI tool for testing MCP server scalability.

    This tool loads a YAML configuration file specifying the MCP server
    connection details and test parameters, then runs a concurrent load
    test against the server and outputs performance statistics.
    """
    try:
        # Load configuration
        if verbose:
            click.echo(f"Loading configuration from {config}")

        test_config = load_config(str(config))

        if verbose:
            click.echo(
                f"Server: {test_config.server.transport}://{test_config.server.host}:{test_config.server.port}"
            )
            click.echo(f"Tool: {test_config.test.tool_name}")
            click.echo(f"Concurrent requests: {test_config.test.concurrent_requests}")
            click.echo(f"Duration: {test_config.test.duration_seconds}s")

        # Run the load test
        results = asyncio.run(run_load_test(test_config))

        # Add metadata to results
        full_results = {
            "test_config": {
                "server": test_config.server.dict(),
                "test": test_config.test.dict(),
            },
            "results": results,
        }

        # Output results
        if output:
            save_results(full_results, str(output))
            if verbose:
                click.echo(f"Results saved to {output}")
        else:
            import yaml

            click.echo(yaml.dump(full_results, default_flow_style=False, indent=2))

    except FileNotFoundError as e:
        click.echo(f"Error: Configuration file not found: {e}", err=True)
        sys.exit(1)

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        if verbose:
            import traceback

            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
