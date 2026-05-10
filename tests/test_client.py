"""Smoke tests against the live Moegirl Wiki API.

Run with::

    pytest -m network

These tests hit ``mzh.moegirl.org.cn`` and require internet access.
"""
from __future__ import annotations

import pytest

from mcp_server_moegirl_wiki.client import MoegirlApiClient

pytestmark = pytest.mark.network


async def test_opensearch_finds_character() -> None:
    client = MoegirlApiClient()
    results = await client.opensearch("丰川祥子", limit=5)
    assert results, "opensearch returned no candidates"
    assert any("丰川祥子" in r.title for r in results)


async def test_fetch_page_returns_summary() -> None:
    client = MoegirlApiClient()
    page = await client.fetch_page("三角初华")
    assert page is not None, "fetch_page returned None for an existing page"
    assert page.title == "三角初华"
    assert len(page.summary) > 50
    assert page.url.startswith("http")


async def test_fetch_page_missing_returns_none() -> None:
    client = MoegirlApiClient()
    page = await client.fetch_page("此页面绝不可能存在_xyzzy_unique_token_42")
    assert page is None


async def test_search_or_fallback_chain() -> None:
    """Combined-strategy invariant: at least one of the two search backends must
    return results for an extant character page."""
    client = MoegirlApiClient()
    g_results = await client.search("三角初华", limit=5)
    o_results = await client.opensearch("三角初华", limit=5)
    assert g_results or o_results, (
        "both generator=search and opensearch returned 0 — one of them should hit"
    )
