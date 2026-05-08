"""Brave Search API client for medical web search."""

import httpx
from typing import List, Optional

from src.core.config import settings
from src.core.logging import get_logger
from src.schemas.features.ai import BraveSearchResult

logger = get_logger(__name__)


class BraveSearchClient:
    """
    Client for Brave Search API.
    Handles site-restricted searches for medical information.
    """

    def __init__(self):
        self.api_key = settings.BRAVE_SEARCH_API_KEY
        self.base_url = "https://api.search.brave.com/res/v1/web/search"
        self.timeout = 10.0

        # Request configuration
        self.headers = {
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "X-Subscription-Token": self.api_key
        }

        # HTTP client with connection pooling
        self._client = httpx.AsyncClient(
            timeout=self.timeout,
            headers=self.headers,
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
        )

        if not self.api_key:
            logger.warning("Brave Search API key is missing. Search will fail.")

    async def close(self):
        """Cleanup HTTP client resources."""
        await self._client.aclose()

    async def search(
        self,
        query: str,
        count: int = 8,
        sites: Optional[List[str]] = None
    ) -> List[BraveSearchResult]:
        """
        Execute a web search, optionally restricted to specific domains.

        Args:
            query: Search query string
            count: Number of results to return (max 20)
            sites: Optional list of domains to restrict search to

        Returns:
            List of BraveSearchResult with full metadata
        """
        if not self.api_key:
            return []

        # Build query with site filters
        full_query = self._build_query(query, sites)

        params = {
            "q": full_query,
            "count": min(count, 20),
            "search_lang": "en",
            "text_decorations": False,
            "extra_snippets": True,
        }

        try:
            response = await self._client.get(self.base_url, params=params)
            response.raise_for_status()
            return self._parse_response(response.json())

        except httpx.HTTPError as e:
            logger.error(f"Brave API Error: {str(e)}")
            return []

    def _build_query(self, query: str, sites: Optional[List[str]]) -> str:
        """
        Appends site filters to the user query.
        Format: "query (site:a.com OR site:b.com)"
        """
        if not sites:
            return query

        # Clean and format site filters
        site_filters = " OR ".join([f"site:{site.strip()}" for site in sites if site.strip()])
        return f"{query} ({site_filters})"

    def _parse_response(self, data: dict) -> List[BraveSearchResult]:
        """
        Maps raw API JSON to BraveSearchResult Pydantic models.
        """
        raw_results = data.get("web", {}).get("results", [])
        parsed_results = []

        for item in raw_results:
            try:
                profile = item.get("profile", {})
                meta = item.get("meta_url", {})

                result = BraveSearchResult(
                    title=item.get("title", "Untitled"),
                    url=item.get("url", ""),
                    description=item.get("description", ""),
                    extra_snippets=item.get("extra_snippets", []),
                    profile_name=profile.get("name"),
                    profile_img=profile.get("img"),
                    hostname=meta.get("hostname")
                )
                parsed_results.append(result)

            except Exception as e:
                logger.warning(f"Failed to parse a search result item: {e}")
                continue

        return parsed_results