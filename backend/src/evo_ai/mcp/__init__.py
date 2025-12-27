"""MCP (Model Context Protocol) server framework."""

from evo_ai.mcp.base_server import BaseMCPServer, MCPServerMetadata
from evo_ai.mcp.database_server import DatabaseMCPServer
from evo_ai.mcp.filesystem_server import FilesystemMCPServer
from evo_ai.mcp.github_server import GitHubMCPServer
from evo_ai.mcp.registry import MCPRegistry, mcp_registry
from evo_ai.mcp.web_server import WebMCPServer

__all__ = [
    "BaseMCPServer",
    "MCPServerMetadata",
    "MCPRegistry",
    "mcp_registry",
    "GitHubMCPServer",
    "FilesystemMCPServer",
    "WebMCPServer",
    "DatabaseMCPServer",
]
