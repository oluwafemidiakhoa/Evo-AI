"""Database MCP server for read-only SQL queries."""

from typing import Any, Callable, Dict, List

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from evo_ai.infrastructure.database.connection import get_session
from evo_ai.mcp.base_server import BaseMCPServer, MCPServerMetadata


class DatabaseMCPServer(BaseMCPServer):
    """
    Database MCP server for executing read-only queries.

    Tools:
    - query: Execute SELECT query
    - explain_plan: Get query execution plan
    - table_info: Get table schema information

    Security: Only SELECT queries allowed. Whitelisted tables only.
    """

    def __init__(self, allowed_tables: List[str]):
        """
        Initialize database MCP server.

        Args:
            allowed_tables: Whitelist of allowed table names

        Example:
            server = DatabaseMCPServer(
                allowed_tables=["campaigns", "rounds", "variants"]
            )
        """
        self.allowed_tables = allowed_tables

    def _validate_query(self, query: str) -> None:
        """
        Validate query is read-only and accesses allowed tables.

        Raises:
            ValueError: If query is not allowed
        """
        # Convert to uppercase for checking
        query_upper = query.strip().upper()

        # Only SELECT queries allowed
        if not query_upper.startswith("SELECT"):
            raise ValueError("Only SELECT queries are allowed")

        # Check for dangerous keywords
        dangerous = ["INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE", "TRUNCATE"]
        if any(keyword in query_upper for keyword in dangerous):
            raise ValueError(f"Query contains forbidden keywords: {dangerous}")

        # Validate table names (basic check)
        # Note: This is a simple check, production should use SQL parser
        for table in self.allowed_tables:
            if table.upper() in query_upper:
                return  # At least one allowed table found

        raise ValueError(
            f"Query must access allowed tables: {self.allowed_tables}"
        )

    def get_metadata(self) -> MCPServerMetadata:
        """Return server metadata."""
        return MCPServerMetadata(
            name="database",
            version="1.0.0",
            description="Read-only database query execution",
            available_tools=["query", "explain_plan", "table_info"],
            connection_config={
                "allowed_tables": self.allowed_tables,
                "read_only": True,
            }
        )

    def get_tools(self) -> Dict[str, Callable]:
        """Return available tools."""
        return {
            "query": self.query,
            "explain_plan": self.explain_plan,
            "table_info": self.table_info,
        }

    async def query(
        self,
        sql: str,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        Execute read-only SQL query.

        Args:
            sql: SQL SELECT query
            limit: Maximum rows to return (default: 100, max: 1000)

        Returns:
            Dictionary with columns and rows

        Example:
            result = await db_server.query(
                sql="SELECT id, name, status FROM campaigns WHERE status = 'active'",
                limit=10
            )
        """
        self._validate_tool_params("query", locals(), ["sql"])
        self._log_tool_call("query", {"sql": sql[:100]})  # Log first 100 chars
        self._validate_query(sql)

        # Enforce maximum limit
        limit = min(limit, 1000)

        # Add LIMIT if not present
        if "LIMIT" not in sql.upper():
            sql = f"{sql.rstrip(';')} LIMIT {limit}"

        async with get_session() as session:
            result = await session.execute(text(sql))
            rows = result.fetchall()

            # Get column names
            columns = list(result.keys()) if rows else []

            return {
                "columns": columns,
                "rows": [dict(zip(columns, row)) for row in rows],
                "row_count": len(rows),
                "query": sql,
            }

    async def explain_plan(self, sql: str) -> Dict[str, Any]:
        """
        Get query execution plan.

        Args:
            sql: SQL query to explain

        Returns:
            Query execution plan
        """
        self._validate_tool_params("explain_plan", locals(), ["sql"])
        self._log_tool_call("explain_plan", {"sql": sql[:100]})
        self._validate_query(sql)

        explain_query = f"EXPLAIN (FORMAT JSON) {sql}"

        async with get_session() as session:
            result = await session.execute(text(explain_query))
            plan = result.scalar()

            return {
                "query": sql,
                "plan": plan,
            }

    async def table_info(self, table_name: str) -> Dict[str, Any]:
        """
        Get table schema information.

        Args:
            table_name: Name of the table

        Returns:
            Table schema details (columns, types, constraints)
        """
        self._validate_tool_params("table_info", locals(), ["table_name"])
        self._log_tool_call("table_info", {"table_name": table_name})

        if table_name not in self.allowed_tables:
            raise ValueError(
                f"Table '{table_name}' not in allowed tables: {self.allowed_tables}"
            )

        # Query information schema
        query = text("""
            SELECT
                column_name,
                data_type,
                is_nullable,
                column_default
            FROM information_schema.columns
            WHERE table_name = :table_name
            ORDER BY ordinal_position
        """)

        async with get_session() as session:
            result = await session.execute(query, {"table_name": table_name})
            columns = [
                {
                    "name": row.column_name,
                    "type": row.data_type,
                    "nullable": row.is_nullable == "YES",
                    "default": row.column_default,
                }
                for row in result
            ]

            return {
                "table_name": table_name,
                "columns": columns,
                "column_count": len(columns),
            }
