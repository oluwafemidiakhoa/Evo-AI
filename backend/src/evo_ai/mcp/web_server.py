"""Web MCP server for HTTP requests and web scraping."""

from typing import Any, Callable, Dict, List, Optional
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from evo_ai.mcp.base_server import BaseMCPServer, MCPServerMetadata


class WebMCPServer(BaseMCPServer):
    """
    Web MCP server for HTTP requests and web scraping.

    Tools:
    - fetch_url: GET request to a URL
    - post_data: POST request with data
    - scrape_page: Extract structured data from HTML
    - extract_links: Extract all links from a page
    """

    def __init__(
        self,
        allowed_domains: Optional[List[str]] = None,
        timeout: int = 30
    ):
        """
        Initialize web MCP server.

        Args:
            allowed_domains: Whitelist of allowed domains (if None, all allowed)
            timeout: Request timeout in seconds
        """
        self.allowed_domains = allowed_domains
        self.timeout = timeout
        self.client = httpx.AsyncClient(
            timeout=timeout,
            follow_redirects=True,
        )

    def _is_domain_allowed(self, url: str) -> bool:
        """Check if URL domain is in allowed list."""
        if not self.allowed_domains:
            return True  # All domains allowed

        parsed = urlparse(url)
        domain = parsed.netloc

        return any(
            domain == allowed or domain.endswith(f".{allowed}")
            for allowed in self.allowed_domains
        )

    def _validate_url(self, url: str) -> None:
        """Validate URL is allowed."""
        if not self._is_domain_allowed(url):
            raise ValueError(
                f"Domain not allowed. Allowed domains: {self.allowed_domains}"
            )

    def get_metadata(self) -> MCPServerMetadata:
        """Return server metadata."""
        return MCPServerMetadata(
            name="web",
            version="1.0.0",
            description="HTTP requests and web scraping",
            available_tools=["fetch_url", "post_data", "scrape_page", "extract_links"],
            connection_config={
                "allowed_domains": self.allowed_domains or ["*"],
                "timeout": self.timeout,
            }
        )

    def get_tools(self) -> Dict[str, Callable]:
        """Return available tools."""
        return {
            "fetch_url": self.fetch_url,
            "post_data": self.post_data,
            "scrape_page": self.scrape_page,
            "extract_links": self.extract_links,
        }

    async def fetch_url(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Fetch URL with GET request.

        Args:
            url: URL to fetch
            headers: Optional HTTP headers

        Returns:
            Dictionary with status, headers, and content

        Example:
            result = await web_server.fetch_url(
                url="https://api.example.com/data",
                headers={"Authorization": "Bearer token"}
            )
        """
        self._validate_tool_params("fetch_url", locals(), ["url"])
        self._log_tool_call("fetch_url", {"url": url})
        self._validate_url(url)

        response = await self.client.get(url, headers=headers or {})

        return {
            "url": str(response.url),
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "content": response.text,
            "content_length": len(response.content),
        }

    async def post_data(
        self,
        url: str,
        data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        POST request with data.

        Args:
            url: URL to post to
            data: Form data (mutually exclusive with json)
            json: JSON data (mutually exclusive with data)
            headers: Optional HTTP headers

        Returns:
            Dictionary with response details
        """
        self._validate_tool_params("post_data", locals(), ["url"])
        self._log_tool_call("post_data", {"url": url})
        self._validate_url(url)

        if data and json:
            raise ValueError("Cannot provide both 'data' and 'json' parameters")

        response = await self.client.post(
            url,
            data=data,
            json=json,
            headers=headers or {}
        )

        return {
            "url": str(response.url),
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "content": response.text,
        }

    async def scrape_page(
        self,
        url: str,
        selectors: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Scrape structured data from HTML page.

        Args:
            url: URL to scrape
            selectors: CSS selectors to extract (name -> selector)

        Returns:
            Dictionary with extracted data

        Example:
            result = await web_server.scrape_page(
                url="https://example.com",
                selectors={
                    "title": "h1",
                    "description": "meta[name='description']",
                    "links": "a[href]"
                }
            )
        """
        self._validate_tool_params("scrape_page", locals(), ["url"])
        self._log_tool_call("scrape_page", {"url": url, "selectors": selectors})
        self._validate_url(url)

        response = await self.client.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        result = {
            "url": str(response.url),
            "title": soup.title.string if soup.title else None,
        }

        if selectors:
            extracted = {}
            for name, selector in selectors.items():
                elements = soup.select(selector)
                if len(elements) == 1:
                    extracted[name] = elements[0].get_text(strip=True)
                else:
                    extracted[name] = [
                        elem.get_text(strip=True) for elem in elements
                    ]
            result["extracted"] = extracted

        return result

    async def extract_links(
        self,
        url: str,
        base_url: Optional[str] = None
    ) -> List[Dict[str, str]]:
        """
        Extract all links from a page.

        Args:
            url: URL to extract links from
            base_url: Base URL for resolving relative links

        Returns:
            List of links with text and href
        """
        self._validate_tool_params("extract_links", locals(), ["url"])
        self._log_tool_call("extract_links", {"url": url})
        self._validate_url(url)

        response = await self.client.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        base = base_url or str(response.url)
        links = []

        for link in soup.find_all('a', href=True):
            href = link['href']
            absolute_url = urljoin(base, href)

            links.append({
                "text": link.get_text(strip=True),
                "href": absolute_url,
                "relative": href,
            })

        return links

    async def close(self) -> None:
        """Close HTTP client."""
        await self.client.aclose()
