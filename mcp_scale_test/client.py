"""MCP client implementations using the official MCP library."""

import asyncio
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List

from mcp import ClientSession, StdioServerParameters, stdio_client
from mcp.client.sse import sse_client
from mcp.client.streamable_http import streamablehttp_client
from mcp.types import Tool

from .config import ServerConfig


class MCPClient(ABC):
    """Abstract base class for MCP clients."""
    
    def __init__(self, config: ServerConfig):
        self.config = config
        self.session: Optional[ClientSession] = None
        self.client_context = None
    
    @abstractmethod
    async def connect(self) -> None:
        """Establish connection to MCP server."""
        pass
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool on the MCP server."""
        if not self.session:
            raise RuntimeError("Not connected")
        
        result = await self.session.call_tool(tool_name, arguments)
        return {"success": True, "content": result.content} if result.content else {"success": True}
    
    async def list_tools(self) -> List[Tool]:
        """List available tools from the server."""
        if not self.session:
            raise RuntimeError("Not connected")
        
        result = await self.session.list_tools()
        return result.tools
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Close connection to MCP server."""
        pass


class StdioMCPClient(MCPClient):
    """MCP client using stdio transport."""
    
    def __init__(self, config: ServerConfig):
        super().__init__(config)
        self._context_manager = None
        self._streams = None
    
    async def connect(self) -> None:
        """Start the MCP server process and initialize session."""
        # For stdio, the host contains the command to run
        command_parts = self.config.host.split()
        
        server_params = StdioServerParameters(
            command=command_parts[0],
            args=command_parts[1:] if len(command_parts) > 1 else [],
            env=None
        )
        
        # Store the context manager and enter it
        self._context_manager = stdio_client(server_params)
        self._streams = await self._context_manager.__aenter__()
        read, write = self._streams
        
        self.session = ClientSession(read, write)
        await self.session.initialize()
    
    async def disconnect(self) -> None:
        """Close the session and transport."""
        if self._context_manager:
            try:
                await self._context_manager.__aexit__(None, None, None)
            except Exception:
                pass  # Ignore cleanup errors
        self._context_manager = None
        self._streams = None


class SseMCPClient(MCPClient):
    """MCP client using SSE (Server-Sent Events) transport."""
    
    def __init__(self, config: ServerConfig):
        super().__init__(config)
        self._connection = None
    
    async def connect(self) -> None:
        """Connect to MCP server via SSE endpoint."""
        url = self._build_url()
        print(f"SSE URL: {url}")
        
        # Create a connection wrapper that maintains the context
        self._connection = SSEConnection(url)
        await self._connection.connect()
        
        self.session = ClientSession(self._connection.read, self._connection.write)
        await asyncio.wait_for(self.session.initialize(), timeout=10.0)
    
    async def disconnect(self) -> None:
        """Close the session and transport."""
        if self._connection:
            await self._connection.disconnect()
        self._connection = None
    
    def _build_url(self) -> str:
        port_part = f":{self.config.port}" if self.config.port else ""
        path_part = self.config.path or ""
        return f"http://{self.config.host}{port_part}{path_part}"


class SSEConnection:
    """Wrapper to properly manage SSE connection lifecycle."""
    
    def __init__(self, url: str):
        self.url = url
        self._context = None
        self.read = None
        self.write = None
    
    async def connect(self) -> None:
        """Establish SSE connection."""
        self._context = sse_client(self.url, timeout=10.0)
        self.read, self.write = await self._context.__aenter__()
    
    async def disconnect(self) -> None:
        """Close SSE connection."""
        if self._context:
            try:
                await self._context.__aexit__(None, None, None)
            except Exception:
                pass


class StreamableHttpMCPClient(MCPClient):
    """MCP client using streamable HTTP transport."""
    
    def __init__(self, config: ServerConfig):
        super().__init__(config)
        self._context_manager = None
        self._streams = None
    
    async def connect(self) -> None:
        """Connect to MCP server via streamable HTTP endpoint."""
        url = self._build_url()
        
        # Store the context manager and enter it
        self._context_manager = streamablehttp_client(url, timeout=10.0)
        self._streams = await self._context_manager.__aenter__()
        read, write, _ = self._streams
        
        self.session = ClientSession(read, write)
        await self.session.initialize()
    
    async def disconnect(self) -> None:
        """Close the session and transport."""
        if self._context_manager:
            try:
                await self._context_manager.__aexit__(None, None, None)
            except Exception:
                pass  # Ignore cleanup errors
        self._context_manager = None
        self._streams = None
    
    def _build_url(self) -> str:
        port_part = f":{self.config.port}" if self.config.port else ""
        path_part = self.config.path or ""
        return f"http://{self.config.host}{port_part}{path_part}"


def create_client(config: ServerConfig) -> MCPClient:
    """Factory function to create the appropriate client based on transport type."""
    if config.transport == "stdio":
        return StdioMCPClient(config)
    elif config.transport == "sse":
        return SseMCPClient(config)
    elif config.transport == "streamable_http":
        return StreamableHttpMCPClient(config)
    else:
        raise ValueError(f"Unsupported transport type: {config.transport}. Supported types: stdio, sse, streamable_http")