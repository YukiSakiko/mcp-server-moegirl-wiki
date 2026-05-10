"""FastMCP server exposing ``search_moegirl`` and ``get_page`` tools.

The MCP stdio transport reserves stdout exclusively for JSON-RPC frames.
This module configures logging to stderr **before** importing FastMCP so any
stray log records cannot pollute the protocol stream. Tool names and parameter
shapes intentionally match the abandoned npm package ``moegirl-wiki-mcp`` so
existing client prompts and configurations work as drop-in replacements.
"""
from __future__ import annotations

import logging
import sys

logging.basicConfig(
    stream=sys.stderr,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

from mcp.server.fastmcp import FastMCP  # noqa: E402  — must follow logging.basicConfig

from .client import MoegirlApiClient  # noqa: E402

logger = logging.getLogger("mcp-server-moegirl-wiki")
mcp: FastMCP = FastMCP("moegirl-wiki")
_client = MoegirlApiClient()


@mcp.tool(
    description=(
        "搜索萌娘百科条目。先用 generator=search 全文索引（命中时同时返回摘要片段），"
        "0 命中或异常时退回 opensearch 标题模糊匹配以保命中率。"
    )
)
async def search_moegirl(keyword: str, limit: int = 5) -> dict:
    """Search Moegirl Wiki entries.

    Args:
        keyword: Search term.
        limit: Maximum number of results (default 5).

    Returns:
        ``{"results": [{"title", "url", "snippet"}, ...], "count": int}``
    """
    keyword = (keyword or "").strip()
    if not keyword:
        return {"results": [], "count": 0}

    try:
        results = await _client.search(keyword, limit=limit)
    except Exception as exc:
        # generator=search 偶发失败时不阻塞 fallback；记录到 stderr 便于排查
        logger.warning("generator=search failed for %r: %s", keyword, exc)
        results = []

    if not results:
        results = await _client.opensearch(keyword, limit=limit)

    return {
        "results": [
            {"title": r.title, "url": r.url, "snippet": r.snippet}
            for r in results
        ],
        "count": len(results),
    }


@mcp.tool(
    description="获取萌娘百科条目的纯文本全文（所有章节、模板已展开、链接已解析、自动跟随重定向、按 max_length 截断）。"
)
async def get_page(title: str, max_length: int = 6250) -> dict:
    """Fetch the plain-text rendering of a Moegirl Wiki page (all sections).

    Args:
        title: Page title.
        max_length: Maximum characters returned in ``content`` (default 6250,
            roughly covers a typical character page in full). Pass larger
            (e.g. 20000) for very long pages; smaller for quick lookups.

    Returns:
        On success: ``{"title", "content", "url", "page_id"}``.
        On failure: ``{"error": "...", "title": title}``.
    """
    title = (title or "").strip()
    if not title:
        return {"error": "title 不能为空"}

    page = await _client.fetch_page(title)
    if page is None:
        return {"error": "页面不存在", "title": title}

    return {
        "title": page.title,
        "content": page.content[:max_length],
        "url": page.url,
        "page_id": page.page_id,
    }


def main() -> None:
    """Console entry point — runs the MCP server over stdio."""
    mcp.run("stdio")


if __name__ == "__main__":
    main()
