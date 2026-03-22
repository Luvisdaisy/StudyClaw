"""
Web search tool using Brave Search API.

Brave Search API documentation: https://api.search.brave.com/docs/introduction
"""

import os
import logging
from langchain_core.tools import tool

logger = logging.getLogger(__name__)


class WebSearchError(Exception):
    """Raised when web search fails."""
    pass


def _get_brave_api_key() -> str:
    """Get Brave Search API key from environment."""
    api_key = os.environ.get("BRAVE_SEARCH_API_KEY", "")
    if not api_key:
        raise WebSearchError(
            "BRAVE_SEARCH_API_KEY environment variable not set. "
            "Please set it in .env file."
        )
    return api_key


def _search_brave(query: str, count: int = 5) -> list[dict]:
    """
    Perform web search using Brave Search API.

    Args:
        query: Search query string
        count: Number of results to return (default: 5, max: 20)

    Returns:
        List of search results with title, url, description, etc.
    """
    import requests

    api_key = _get_brave_api_key()
    url = "https://api.search.brave.com/res/v1/web/search"

    headers = {
        "X-Subscription-Token": api_key,
        "Accept": "application/json",
    }

    params = {
        "q": query,
        "count": min(count, 20),
    }

    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        results = []
        web_results = data.get("web", {}).get("results", [])
        for item in web_results[:count]:
            results.append({
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "description": item.get("description", ""),
                "age": item.get("age", ""),
            })

        return results

    except requests.exceptions.Timeout:
        raise WebSearchError("Brave Search API request timed out")
    except requests.exceptions.RequestException as e:
        raise WebSearchError(f"Brave Search API request failed: {str(e)}")
    except Exception as e:
        raise WebSearchError(f"Unexpected error during web search: {str(e)}")


@tool(description="Search the web for information using Brave Search. Use this when the user's question cannot be fully answered from the project documents alone and internet search is needed.")
def web_search(query: str, count: int = 5) -> str:
    """
    Search the web for information using Brave Search.

    Args:
        query: The search query string - formulate a clear, specific search query
        count: Number of search results to return (default: 5, max: 20)

    Returns:
        A formatted string containing the search results with titles, URLs, and descriptions
    """
    try:
        results = _search_brave(query, count)

        if not results:
            return "No search results found."

        output = f"Found {len(results)} search results:\n\n"
        for i, result in enumerate(results, 1):
            output += f"【Result {i}】\n"
            output += f"Title: {result['title']}\n"
            output += f"URL: {result['url']}\n"
            output += f"Description: {result['description']}\n\n"

        return output

    except WebSearchError as e:
        logger.error(f"Web search failed: {e}")
        return f"Web search error: {str(e)}"
    except Exception as e:
        logger.error(f"Unexpected web search error: {e}", exc_info=True)
        return f"Web search failed with unexpected error: {str(e)}"
