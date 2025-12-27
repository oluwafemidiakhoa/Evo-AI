"""Base MCP server class."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Callable, Dict, List

from evo_ai.infrastructure.observability.logging import get_logger

logger = get_logger(__name__)


@dataclass
class MCPServerMetadata:
    """Metadata describing an MCP server."""

    name: str
    version: str  # Semantic versioning (e.g., "1.0.0")
    description: str
    available_tools: List[str]
    connection_config: Dict[str, Any]


class BaseMCPServer(ABC):
    """
    Base class for MCP servers.

    All MCP servers must inherit from this and implement:
    - get_metadata(): Return server metadata
    - get_tools(): Return available tools as callable functions
    - Any server-specific initialization

    MCP servers provide external system access with:
    - Version management
    - Access logging
    - Error handling
    - Tool registration
    """

    @abstractmethod
    def get_metadata(self) -> MCPServerMetadata:
        """
        Return server metadata.

        Returns:
            MCPServerMetadata with name, version, description, tools
        """
        pass

    @abstractmethod
    def get_tools(self) -> Dict[str, Callable]:
        """
        Return available tools as callable functions.

        Returns:
            Dictionary mapping tool names to callable functions

        Example:
            {
                "read_file": self.read_file,
                "search_code": self.search_code,
            }
        """
        pass

    def _log_tool_call(
        self,
        tool_name: str,
        params: Dict[str, Any],
        trace_id: str | None = None
    ) -> None:
        """
        Log tool call (for debugging and monitoring).

        Note: Actual access logging happens in MCPRegistry.
        This is just for server-level logging.
        """
        logger.info(
            "mcp_tool_called",
            server=self.get_metadata().name,
            version=self.get_metadata().version,
            tool=tool_name,
            trace_id=trace_id,
        )

    def _validate_tool_params(
        self,
        tool_name: str,
        params: Dict[str, Any],
        required_params: List[str]
    ) -> None:
        """
        Validate tool parameters.

        Args:
            tool_name: Name of the tool
            params: Provided parameters
            required_params: List of required parameter names

        Raises:
            ValueError: If required parameters are missing
        """
        missing = set(required_params) - set(params.keys())
        if missing:
            raise ValueError(
                f"Tool {tool_name} missing required parameters: {missing}"
            )
