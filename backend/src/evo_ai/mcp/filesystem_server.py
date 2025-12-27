"""Filesystem MCP server for local file access."""

import os
from pathlib import Path
from typing import Any, Callable, Dict, List

from evo_ai.mcp.base_server import BaseMCPServer, MCPServerMetadata


class FilesystemMCPServer(BaseMCPServer):
    """
    Filesystem MCP server for accessing local files (sandboxed).

    Tools:
    - read_file: Read file contents
    - list_directory: List directory contents
    - search_files: Find files by pattern
    - file_exists: Check if file exists

    Security: Operations are restricted to allowed_paths only.
    """

    def __init__(self, allowed_paths: List[str]):
        """
        Initialize filesystem MCP server.

        Args:
            allowed_paths: List of allowed directory paths (whitelist)

        Example:
            server = FilesystemMCPServer(
                allowed_paths=[
                    "/app/workdir",
                    "/tmp/evo-ai"
                ]
            )
        """
        self.allowed_paths = [Path(p).resolve() for p in allowed_paths]

    def _is_path_allowed(self, path: str) -> bool:
        """Check if path is within allowed directories."""
        resolved_path = Path(path).resolve()
        return any(
            str(resolved_path).startswith(str(allowed))
            for allowed in self.allowed_paths
        )

    def _validate_path(self, path: str) -> Path:
        """
        Validate and resolve path.

        Raises:
            ValueError: If path is outside allowed directories
        """
        if not self._is_path_allowed(path):
            raise ValueError(
                f"Path '{path}' is outside allowed directories: {self.allowed_paths}"
            )
        return Path(path).resolve()

    def get_metadata(self) -> MCPServerMetadata:
        """Return server metadata."""
        return MCPServerMetadata(
            name="filesystem",
            version="1.0.0",
            description="Sandboxed local filesystem access",
            available_tools=["read_file", "list_directory", "search_files", "file_exists"],
            connection_config={
                "allowed_paths": [str(p) for p in self.allowed_paths],
                "sandboxed": True,
            }
        )

    def get_tools(self) -> Dict[str, Callable]:
        """Return available tools."""
        return {
            "read_file": self.read_file,
            "list_directory": self.list_directory,
            "search_files": self.search_files,
            "file_exists": self.file_exists,
        }

    def read_file(self, path: str, encoding: str = "utf-8") -> Dict[str, Any]:
        """
        Read file contents.

        Args:
            path: File path
            encoding: Text encoding (default: utf-8)

        Returns:
            Dictionary with file metadata and content

        Raises:
            ValueError: If path is not allowed
            FileNotFoundError: If file doesn't exist
        """
        self._validate_tool_params("read_file", locals(), ["path"])
        self._log_tool_call("read_file", {"path": path})

        file_path = self._validate_path(path)

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        if not file_path.is_file():
            raise ValueError(f"Path is not a file: {path}")

        content = file_path.read_text(encoding=encoding)

        return {
            "path": str(file_path),
            "name": file_path.name,
            "size": file_path.stat().st_size,
            "content": content,
            "encoding": encoding,
        }

    def list_directory(
        self,
        path: str,
        recursive: bool = False
    ) -> List[Dict[str, Any]]:
        """
        List directory contents.

        Args:
            path: Directory path
            recursive: If True, list recursively

        Returns:
            List of files and directories with metadata
        """
        self._validate_tool_params("list_directory", locals(), ["path"])
        self._log_tool_call("list_directory", {"path": path, "recursive": recursive})

        dir_path = self._validate_path(path)

        if not dir_path.exists():
            raise FileNotFoundError(f"Directory not found: {path}")

        if not dir_path.is_dir():
            raise ValueError(f"Path is not a directory: {path}")

        items = []

        if recursive:
            pattern = "**/*"
        else:
            pattern = "*"

        for item_path in dir_path.glob(pattern):
            items.append({
                "name": item_path.name,
                "path": str(item_path),
                "type": "directory" if item_path.is_dir() else "file",
                "size": item_path.stat().st_size if item_path.is_file() else None,
            })

        return sorted(items, key=lambda x: (x["type"] != "directory", x["name"]))

    def search_files(
        self,
        path: str,
        pattern: str,
        recursive: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Search for files matching a pattern.

        Args:
            path: Directory to search in
            pattern: Glob pattern (e.g., "*.py", "test_*.txt")
            recursive: If True, search recursively

        Returns:
            List of matching files with metadata
        """
        self._validate_tool_params("search_files", locals(), ["path", "pattern"])
        self._log_tool_call("search_files", {"path": path, "pattern": pattern})

        dir_path = self._validate_path(path)

        if not dir_path.exists():
            raise FileNotFoundError(f"Directory not found: {path}")

        if not dir_path.is_dir():
            raise ValueError(f"Path is not a directory: {path}")

        if recursive:
            search_pattern = f"**/{pattern}"
        else:
            search_pattern = pattern

        matches = []
        for match_path in dir_path.glob(search_pattern):
            if match_path.is_file():
                matches.append({
                    "name": match_path.name,
                    "path": str(match_path),
                    "size": match_path.stat().st_size,
                    "modified": match_path.stat().st_mtime,
                })

        return sorted(matches, key=lambda x: x["name"])

    def file_exists(self, path: str) -> Dict[str, Any]:
        """
        Check if file or directory exists.

        Args:
            path: Path to check

        Returns:
            Dictionary with existence info
        """
        self._validate_tool_params("file_exists", locals(), ["path"])
        self._log_tool_call("file_exists", {"path": path})

        try:
            file_path = self._validate_path(path)
            exists = file_path.exists()

            result = {
                "path": str(file_path),
                "exists": exists,
            }

            if exists:
                result.update({
                    "type": "directory" if file_path.is_dir() else "file",
                    "size": file_path.stat().st_size if file_path.is_file() else None,
                })

            return result

        except ValueError:
            # Path not allowed
            return {
                "path": path,
                "exists": False,
                "error": "Path not in allowed directories",
            }
