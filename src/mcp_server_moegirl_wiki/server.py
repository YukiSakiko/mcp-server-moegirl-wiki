"""``MCPServer`` server exposing ``search_moegirl`` and ``get_page`` tools.

Requires MCP Python SDK 2.x: ``mcp.server.fastmcp.FastMCP`` was renamed to
``mcp.server.mcpserver.MCPServer`` in SDK 2.0, so this module imports from the
new location and declares ``mcp>=2.0,<3`` in ``pyproject.toml``.

The MCP stdio transport reserves stdout exclusively for JSON-RPC frames.
This module configures logging to stderr **before** importing the server class so
any stray log records cannot pollute the protocol stream. Tool names and parameter
shapes intentionally match the abandoned npm package ``moegirl-wiki-mcp`` so
existing client prompts and configurations work as drop-in replacements.

Environment variables:
    MOEGIRL_MAX_LENGTH  Default truncation length for ``get_page`` content
                        (positive integer; falls back to 6250 if unset/invalid).
"""
from __future__ import annotations

import logging
import os
import sys

logging.basicConfig(
    stream=sys.stderr,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

import httpx  # noqa: E402  — must follow logging.basicConfig
from mcp.server.mcpserver import MCPServer  # noqa: E402

from . import __version__  # noqa: E402
from .client import MoegirlApiClient, MoegirlApiError  # noqa: E402

logger = logging.getLogger("mcp-server-moegirl-wiki")


def _default_max_length() -> int:
    """Read ``MOEGIRL_MAX_LENGTH`` from env, fall back to 6250 on missing/invalid."""
    raw = os.environ.get("MOEGIRL_MAX_LENGTH", "").strip()
    if not raw:
        return 6250
    try:
        n = int(raw)
    except ValueError:
        logger.warning("MOEGIRL_MAX_LENGTH=%r is not a valid integer, using 6250", raw)
        return 6250
    if n <= 0:
        logger.warning("MOEGIRL_MAX_LENGTH=%d is not positive, using 6250", n)
        return 6250
    return n


DEFAULT_MAX_LENGTH = _default_max_length()
mcp: MCPServer = MCPServer("moegirl-wiki", version=__version__)
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
        try:
            results = await _client.opensearch(keyword, limit=limit)
        except (MoegirlApiError, httpx.HTTPError) as exc:
            # 网络/上游异常作为工具结果返回，模型能看到原因；SDK 2.x 会把未捕获异常
            # 变成只有 "Error executing tool" 的 isError，细节留在服务端。
            logger.warning("opensearch failed for %r: %s", keyword, exc)
            return {"error": f"搜索失败: {exc}", "keyword": keyword}

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
async def get_page(title: str, max_length: int = DEFAULT_MAX_LENGTH) -> dict:
    """Fetch the plain-text rendering of a Moegirl Wiki page (all sections).

    Args:
        title: Page title.
        max_length: Maximum characters returned in ``content``. Default comes
            from ``MOEGIRL_MAX_LENGTH`` env var (or 6250 if unset). 6250 covers
            a typical character page in full; pass larger (e.g. 20000) for very
            long pages, smaller for quick lookups.

    Returns:
        On success: ``{"title", "content", "url", "page_id"}``.
        On failure: ``{"error": "...", "title": title}``.
    """
    title = (title or "").strip()
    if not title:
        return {"error": "title 不能为空"}

    try:
        page = await _client.fetch_page(title)
    except (MoegirlApiError, httpx.HTTPError) as exc:
        # 同 search_moegirl：上游/网络异常作为工具结果返回，避免 SDK 2.x 只给出
        # "Error executing tool get_page" 这种没有信息量的 isError。
        logger.warning("fetch_page failed for %r: %s", title, exc)
        return {"error": f"获取条目失败: {exc}", "title": title}

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
