"""MCP server registry with versioning and access logging."""

import time
from typing import Any, Dict, List, Optional
from uuid import UUID

from semver import Version

from evo_ai.infrastructure.database.connection import get_session
from evo_ai.infrastructure.database.models import MCPAccessLogDB
from evo_ai.infrastructure.observability.logging import get_logger
from evo_ai.infrastructure.observability.metrics import mcp_calls, mcp_duration
from evo_ai.mcp.base_server import BaseMCPServer, MCPServerMetadata

logger = get_logger(__name__)


class MCPRegistry:
    """
    Central registry for MCP servers.

    Responsibilities:
    - Server registration with version management
    - Tool discovery by server name + version
    - Access logging to database (non-negotiable)
    - Metrics collection
    - Error handling and retries

    NON-NEGOTIABLE: All MCP access must be versioned and logged.
    """

    def __init__(self) -> None:
        """Initialize MCP registry."""
        self._servers: Dict[str, BaseMCPServer] = {}
        logger.info("mcp_registry_initialized")

    def register(self, server: BaseMCPServer) -> None:
        """
        Register an MCP server.

        Args:
            server: MCP server instance

        Example:
            registry.register(GitHubMCPServer())
            registry.register(FilesystemMCPServer())
        """
        metadata = server.get_metadata()
        key = f"{metadata.name}@{metadata.version}"

        if key in self._servers:
            logger.warning(
                "mcp_server_already_registered",
                server=metadata.name,
                version=metadata.version
            )
            return

        self._servers[key] = server
        logger.info(
            "mcp_server_registered",
            server=metadata.name,
            version=metadata.version,
            tools=metadata.available_tools
        )

    def get_server(
        self,
        name: str,
        version: Optional[str] = None
    ) -> Optional[BaseMCPServer]:
        """
        Get MCP server by name and optional version.

        If version not specified, returns latest version.

        Args:
            name: Server name (e.g., "github")
            version: Optional semantic version (e.g., "1.0.0")

        Returns:
            MCP server instance or None if not found
        """
        if version:
            key = f"{name}@{version}"
            server = self._servers.get(key)
            if server:
                logger.debug("mcp_server_retrieved", server=name, version=version)
            else:
                logger.warning("mcp_server_not_found", server=name, version=version)
            return server

        # Return latest version
        matching = [
            (key, server)
            for key, server in self._servers.items()
            if server.get_metadata().name == name
        ]

        if not matching:
            logger.warning("mcp_server_not_found", server=name)
            return None

        # Sort by version and return latest
        latest = max(
            matching,
            key=lambda x: Version.parse(x[1].get_metadata().version)
        )
        logger.debug(
            "mcp_server_retrieved_latest",
            server=name,
            version=latest[1].get_metadata().version
        )
        return latest[1]

    def list_servers(self) -> List[MCPServerMetadata]:
        """
        List all registered servers.

        Returns:
            List of server metadata
        """
        return [server.get_metadata() for server in self._servers.values()]

    async def call_tool(
        self,
        server_name: str,
        tool_name: str,
        params: Dict[str, Any],
        version: Optional[str] = None,
        trace_id: Optional[UUID] = None,
    ) -> Any:
        """
        Call MCP server tool with logging.

        NON-NEGOTIABLE: All calls logged to mcp_access_logs table.

        Args:
            server_name: Name of MCP server
            tool_name: Name of tool to call
            params: Tool parameters
            version: Optional server version (uses latest if not specified)
            trace_id: OpenTelemetry trace ID for correlation

        Returns:
            Tool execution result

        Raises:
            ValueError: If server or tool not found
            Exception: If tool execution fails

        Example:
            result = await registry.call_tool(
                server_name="github",
                tool_name="read_file",
                params={"repo": "owner/repo", "path": "README.md"},
                trace_id=trace_context.trace_id
            )
        """
        start_time = time.time()
        status = "error"
        output_data = None
        error_message = None

        try:
            # Get server
            server = self.get_server(server_name, version)
            if not server:
                raise ValueError(
                    f"MCP server '{server_name}' not found"
                    + (f" (version {version})" if version else "")
                )

            metadata = server.get_metadata()

            # Get tool
            tools = server.get_tools()
            if tool_name not in tools:
                raise ValueError(
                    f"Tool '{tool_name}' not found in server '{server_name}'. "
                    f"Available tools: {list(tools.keys())}"
                )

            tool = tools[tool_name]

            # Execute tool
            logger.info(
                "mcp_tool_executing",
                server=server_name,
                version=metadata.version,
                tool=tool_name,
                trace_id=str(trace_id) if trace_id else None,
            )

            output_data = await tool(**params) if hasattr(tool, '__await__') else tool(**params)
            status = "success"

            # Update metrics
            mcp_calls.labels(
                server_name=server_name,
                tool_name=tool_name,
                status="success"
            ).inc()

            logger.info(
                "mcp_tool_completed",
                server=server_name,
                tool=tool_name,
                duration_ms=int((time.time() - start_time) * 1000),
                trace_id=str(trace_id) if trace_id else None,
            )

            return output_data

        except Exception as e:
            error_message = str(e)
            status = "error"

            # Update metrics
            mcp_calls.labels(
                server_name=server_name,
                tool_name=tool_name,
                status="error"
            ).inc()

            logger.error(
                "mcp_tool_failed",
                server=server_name,
                tool=tool_name,
                error=error_message,
                trace_id=str(trace_id) if trace_id else None,
            )
            raise

        finally:
            duration_ms = int((time.time() - start_time) * 1000)

            # Update duration metric
            mcp_duration.labels(
                server_name=server_name,
                tool_name=tool_name
            ).observe(duration_ms / 1000.0)

            # Log to database (NON-NEGOTIABLE)
            await self._log_access(
                trace_id=trace_id,
                server_name=server_name,
                server_version=server.get_metadata().version if server else "unknown",
                tool_name=tool_name,
                input_params=params,
                output_data=output_data,
                status=status,
                error_message=error_message,
                duration_ms=duration_ms,
            )

    async def _log_access(
        self,
        trace_id: Optional[UUID],
        server_name: str,
        server_version: str,
        tool_name: str,
        input_params: Dict[str, Any],
        output_data: Any,
        status: str,
        error_message: Optional[str],
        duration_ms: int,
    ) -> None:
        """
        Log MCP access to database.

        This is a non-negotiable requirement from AGENTS.md.
        """
        async with get_session() as session:
            log_entry = MCPAccessLogDB(
                trace_id=trace_id,
                mcp_server_name=server_name,
                mcp_server_version=server_version,
                tool_name=tool_name,
                input_params=input_params,
                output_data=output_data if status == "success" else None,
                status=status,
                error_message=error_message,
                duration_ms=duration_ms,
            )
            session.add(log_entry)
            await session.commit()

            logger.debug(
                "mcp_access_logged",
                server=server_name,
                tool=tool_name,
                status=status,
                trace_id=str(trace_id) if trace_id else None,
            )


# Global registry instance
mcp_registry = MCPRegistry()
