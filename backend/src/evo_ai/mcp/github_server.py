"""GitHub MCP server for repository access."""

from typing import Any, Callable, Dict, List, Optional

import httpx

from evo_ai.mcp.base_server import BaseMCPServer, MCPServerMetadata


class GitHubMCPServer(BaseMCPServer):
    """
    GitHub MCP server for accessing GitHub repositories.

    Tools:
    - read_file: Get file contents from a repository
    - search_code: Search code across repositories
    - list_commits: Get commit history
    - get_pr_diff: Retrieve pull request changes
    """

    def __init__(
        self,
        api_token: Optional[str] = None,
        base_url: str = "https://api.github.com"
    ):
        """
        Initialize GitHub MCP server.

        Args:
            api_token: GitHub API token (optional, increases rate limits)
            base_url: GitHub API base URL
        """
        self.api_token = api_token
        self.base_url = base_url
        self.client = httpx.AsyncClient(
            base_url=base_url,
            headers=self._get_headers(),
            timeout=30.0
        )

    def _get_headers(self) -> Dict[str, str]:
        """Get HTTP headers for GitHub API requests."""
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self.api_token:
            headers["Authorization"] = f"Bearer {self.api_token}"
        return headers

    def get_metadata(self) -> MCPServerMetadata:
        """Return server metadata."""
        return MCPServerMetadata(
            name="github",
            version="1.0.0",
            description="GitHub repository access for code analysis",
            available_tools=["read_file", "search_code", "list_commits", "get_pr_diff"],
            connection_config={
                "base_url": self.base_url,
                "authenticated": bool(self.api_token),
            }
        )

    def get_tools(self) -> Dict[str, Callable]:
        """Return available tools."""
        return {
            "read_file": self.read_file,
            "search_code": self.search_code,
            "list_commits": self.list_commits,
            "get_pr_diff": self.get_pr_diff,
        }

    async def read_file(
        self,
        repo: str,
        path: str,
        ref: str = "main"
    ) -> Dict[str, Any]:
        """
        Read file contents from a GitHub repository.

        Args:
            repo: Repository in format "owner/name"
            path: File path within the repository
            ref: Branch, tag, or commit SHA (default: "main")

        Returns:
            Dictionary with file metadata and content

        Example:
            result = await github_server.read_file(
                repo="anthropics/claude-code",
                path="README.md",
                ref="main"
            )
        """
        self._validate_tool_params("read_file", locals(), ["repo", "path"])
        self._log_tool_call("read_file", {"repo": repo, "path": path, "ref": ref})

        response = await self.client.get(
            f"/repos/{repo}/contents/{path}",
            params={"ref": ref}
        )
        response.raise_for_status()

        data = response.json()
        return {
            "name": data["name"],
            "path": data["path"],
            "sha": data["sha"],
            "size": data["size"],
            "content": data.get("content", ""),
            "encoding": data.get("encoding", "base64"),
        }

    async def search_code(
        self,
        query: str,
        repo: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search code across GitHub repositories.

        Args:
            query: Search query
            repo: Optional repository filter (format: "owner/name")
            limit: Maximum results to return

        Returns:
            List of search results with file paths and snippets
        """
        self._validate_tool_params("search_code", locals(), ["query"])
        self._log_tool_call("search_code", {"query": query, "repo": repo, "limit": limit})

        full_query = f"{query}"
        if repo:
            full_query += f" repo:{repo}"

        response = await self.client.get(
            "/search/code",
            params={"q": full_query, "per_page": limit}
        )
        response.raise_for_status()

        data = response.json()
        return [
            {
                "name": item["name"],
                "path": item["path"],
                "repository": item["repository"]["full_name"],
                "html_url": item["html_url"],
                "sha": item["sha"],
            }
            for item in data.get("items", [])[:limit]
        ]

    async def list_commits(
        self,
        repo: str,
        path: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get commit history for a repository or file.

        Args:
            repo: Repository in format "owner/name"
            path: Optional file path to filter commits
            limit: Maximum commits to return

        Returns:
            List of commits with metadata
        """
        self._validate_tool_params("list_commits", locals(), ["repo"])
        self._log_tool_call("list_commits", {"repo": repo, "path": path, "limit": limit})

        params = {"per_page": limit}
        if path:
            params["path"] = path

        response = await self.client.get(
            f"/repos/{repo}/commits",
            params=params
        )
        response.raise_for_status()

        commits = response.json()
        return [
            {
                "sha": commit["sha"],
                "message": commit["commit"]["message"],
                "author": commit["commit"]["author"]["name"],
                "date": commit["commit"]["author"]["date"],
                "html_url": commit["html_url"],
            }
            for commit in commits[:limit]
        ]

    async def get_pr_diff(
        self,
        repo: str,
        pr_number: int
    ) -> Dict[str, Any]:
        """
        Get pull request diff.

        Args:
            repo: Repository in format "owner/name"
            pr_number: Pull request number

        Returns:
            Dictionary with PR metadata and diff
        """
        self._validate_tool_params("get_pr_diff", locals(), ["repo", "pr_number"])
        self._log_tool_call("get_pr_diff", {"repo": repo, "pr_number": pr_number})

        # Get PR metadata
        pr_response = await self.client.get(f"/repos/{repo}/pulls/{pr_number}")
        pr_response.raise_for_status()
        pr_data = pr_response.json()

        # Get PR files
        files_response = await self.client.get(
            f"/repos/{repo}/pulls/{pr_number}/files"
        )
        files_response.raise_for_status()
        files_data = files_response.json()

        return {
            "number": pr_data["number"],
            "title": pr_data["title"],
            "state": pr_data["state"],
            "created_at": pr_data["created_at"],
            "merged_at": pr_data.get("merged_at"),
            "files_changed": len(files_data),
            "files": [
                {
                    "filename": f["filename"],
                    "status": f["status"],
                    "additions": f["additions"],
                    "deletions": f["deletions"],
                    "patch": f.get("patch", ""),
                }
                for f in files_data
            ],
        }

    async def close(self) -> None:
        """Close HTTP client."""
        await self.client.aclose()
