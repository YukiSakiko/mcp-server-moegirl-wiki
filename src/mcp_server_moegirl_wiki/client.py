"""Async HTTP client for Moegirl Wiki's MediaWiki API.

Why this exists: the abandoned npm package ``moegirl-wiki-mcp`` uses APIs that
no longer work reliably (``action=parse`` is blocked for anonymous users; the
full-text ``list=search`` index has near-zero hit rate on character pages).
This client uses the API combinations that have been verified to work today:

- ``action=opensearch`` for title-prefix/fuzzy search
- ``action=query&generator=search&prop=info|extracts`` for full-text + summary
  in one request (used as the preferred path; falls back to opensearch on miss)
- ``action=query&prop=extracts|info`` with ``redirects=1, exintro=1, explaintext=1``
  for fetching a page's introductory plain text
"""
from __future__ import annotations

import html
import re
from dataclasses import dataclass
from typing import Any

import httpx

API_BASE = "https://mzh.moegirl.org.cn/api.php"
PAGE_BASE = "https://mzh.moegirl.org.cn/"
USER_AGENT = "mcp-server-moegirl-wiki/0.2.1 (+https://github.com/XXXxx7258/mcp-server-moegirl-wiki)"
DEFAULT_TIMEOUT = 10.0


class MoegirlApiError(RuntimeError):
    """Raised when the Moegirl API returns an error envelope or invalid payload."""


@dataclass(slots=True)
class Candidate:
    """A search result candidate."""

    title: str
    url: str
    snippet: str = ""


@dataclass(slots=True)
class PageSummary:
    """A page's plain-text content (all sections, templates expanded, links resolved)."""

    title: str
    content: str
    url: str
    page_id: int | None = None


def _strip_html(text: Any) -> str:
    """Remove HTML tags and unescape entities — used to clean MediaWiki search snippets."""
    s = str(text or "")
    s = re.sub(r"<[^>]+>", "", s)
    return html.unescape(s).strip()


def _page_url(title: str) -> str:
    return PAGE_BASE + title


class MoegirlApiClient:
    """Async client. Each call opens a fresh ``httpx.AsyncClient`` for simplicity;
    request volume from a single MCP server process is low enough that pooling
    overhead is negligible.
    """

    def __init__(self, base_url: str = API_BASE, timeout: float = DEFAULT_TIMEOUT) -> None:
        self.base_url = base_url
        self.timeout = timeout

    async def _request(self, params: dict[str, str]) -> Any:
        async with httpx.AsyncClient(
            timeout=self.timeout,
            headers={"User-Agent": USER_AGENT},
            follow_redirects=True,
        ) as client:
            response = await client.get(self.base_url, params=params)
            response.raise_for_status()
            data = response.json()
        if isinstance(data, dict) and isinstance(data.get("error"), dict):
            err = data["error"]
            raise MoegirlApiError(f"{err.get('code', 'unknown')}: {err.get('info', 'unknown error')}")
        return data

    async def opensearch(self, query: str, limit: int = 5) -> list[Candidate]:
        """Title-based search. Returns title + URL only (no snippet)."""
        payload = await self._request({
            "action": "opensearch",
            "search": query,
            "limit": str(limit),
            "namespace": "0",
            "format": "json",
        })
        if not isinstance(payload, list) or len(payload) < 4:
            raise MoegirlApiError("opensearch: malformed payload")
        titles = payload[1] if isinstance(payload[1], list) else []
        urls = payload[3] if isinstance(payload[3], list) else []
        candidates: list[Candidate] = []
        for index, title in enumerate(titles):
            if not isinstance(title, str):
                continue
            url = urls[index] if index < len(urls) and isinstance(urls[index], str) else _page_url(title)
            candidates.append(Candidate(title=title, url=url))
        return candidates

    async def search(self, query: str, limit: int = 5) -> list[Candidate]:
        """Full-text search via ``generator=search``. Returns title + URL + intro snippet
        in a single request. NOTE: Moegirl's full-text index has poor coverage of
        character pages — callers should fall back to ``opensearch`` on empty results.
        """
        payload = await self._request({
            "action": "query",
            "generator": "search",
            "gsrsearch": query,
            "gsrlimit": str(limit),
            "gsrnamespace": "0",
            "prop": "info|extracts",
            "inprop": "url",
            "exintro": "1",
            "explaintext": "1",
            "format": "json",
        })
        if not isinstance(payload, dict):
            raise MoegirlApiError("search: malformed payload")
        query_block = payload.get("query")
        if not isinstance(query_block, dict):
            return []
        pages = query_block.get("pages")
        if not isinstance(pages, dict):
            return []

        # Preserve search ranking when available; pageids is in ranked order.
        ordered: list[dict[str, Any]] = []
        page_ids = query_block.get("pageids")
        if isinstance(page_ids, list) and page_ids:
            for pid in page_ids:
                page = pages.get(str(pid))
                if isinstance(page, dict):
                    ordered.append(page)
        else:
            ordered = [p for p in pages.values() if isinstance(p, dict)]

        results: list[Candidate] = []
        for page in ordered:
            title = str(page.get("title", "")).strip()
            if not title:
                continue
            results.append(Candidate(
                title=title,
                url=str(page.get("fullurl") or _page_url(title)),
                snippet=_strip_html(page.get("extract", "")),
            ))
        return results

    async def fetch_page(self, title: str) -> PageSummary | None:
        """Fetch the full plain-text rendering of a page (all sections; templates
        expanded; links resolved). Returns ``None`` if the page does not exist.

        Note: Moegirl Wiki blocks ``prop=revisions``/``action=parse``/``?action=raw``
        even for authenticated users, so raw wikitext is unavailable; this method
        uses ``prop=extracts&explaintext=1`` which is the most complete content
        path Moegirl exposes to non-privileged users.
        """
        payload = await self._request({
            "action": "query",
            "prop": "extracts|info",
            "inprop": "url",
            "redirects": "1",
            "explaintext": "1",
            "titles": title,
            "format": "json",
        })
        if not isinstance(payload, dict):
            raise MoegirlApiError("fetch_page: malformed payload")
        pages = payload.get("query", {}).get("pages", {})
        if not isinstance(pages, dict) or not pages:
            return None
        page = next(iter(pages.values()))
        if not isinstance(page, dict):
            return None
        if "missing" in page:
            return None
        page_id = page.get("pageid") if isinstance(page.get("pageid"), int) else None
        resolved_title = str(page.get("title", title))
        return PageSummary(
            title=resolved_title,
            content=str(page.get("extract", "")),
            url=str(page.get("fullurl") or _page_url(resolved_title)),
            page_id=page_id,
        )
