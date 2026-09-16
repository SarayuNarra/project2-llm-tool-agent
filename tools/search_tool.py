from typing import Any, Dict
import requests
from bs4 import BeautifulSoup


SEARCH_URL = "https://html.duckduckgo.com/html/"

HEADERS = {
    "User-Agent": "AI-Engineer-Tool-Agent/1.0"
}


def search_tool(query: str) -> Dict[str, Any]:
    """
    Search the web and return a structured search result.

    Expected by:
        nodes/search.py

    Returns:
        {
            "title": str,
            "content": str,
            "url": str
        }
    """

    query = str(query).strip()

    if not query:
        return {
            "title": "Search",
            "content": "No search query was provided.",
            "url": "",
        }

    try:
        response = requests.get(
            SEARCH_URL,
            params={
                "q": query,
            },
            headers=HEADERS,
            timeout=15,
        )

        response.raise_for_status()

        soup = BeautifulSoup(
            response.text,
            "html.parser",
        )

        results = soup.select(".result")

        if not results:
            return {
                "title": f"Search results for {query}",
                "content": "No search results were found.",
                "url": "",
            }

        collected = []

        first_title = ""
        first_url = ""

        for result in results[:5]:

            title_element = result.select_one(
                ".result__title"
            )

            link_element = result.select_one(
                ".result__a"
            )

            snippet_element = result.select_one(
                ".result__snippet"
            )

            title = (
                title_element.get_text(
                    " ",
                    strip=True,
                )
                if title_element
                else ""
            )

            url = (
                link_element.get("href", "")
                if link_element
                else ""
            )

            snippet = (
                snippet_element.get_text(
                    " ",
                    strip=True,
                )
                if snippet_element
                else ""
            )

            if title or snippet:

                if not first_title:
                    first_title = title

                if not first_url:
                    first_url = url

                collected.append(
                    f"{title}\n{snippet}"
                )

        content = "\n\n".join(
            collected
        ).strip()

        if not content:
            content = (
                "No useful search information "
                "was found."
            )

        return {
            "title": (
                first_title
                or f"Search results for {query}"
            ),
            "content": content,
            "url": first_url,
        }

    except requests.RequestException as exc:
        raise RuntimeError(
            f"Search request failed: {exc}"
        )

    except Exception as exc:
        raise RuntimeError(
            f"Search failed: {exc}"
        )