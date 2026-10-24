"""Hermetic stdio protocol smoke test.

Boots the packaged server as a subprocess — the way every MCP host does — and
drives it with raw JSON-RPC frames. Staying off the SDK client API keeps the test
valid across SDK majors, and the only tool call it makes needs no network.

Run with::

    pytest tests/test_server.py
"""
from __future__ import annotations

import asyncio
import json
import sys
from collections.abc import AsyncIterator
from typing import Any

import pytest

SERVER_MODULE = "mcp_server_moegirl_wiki"
PROTOCOL_VERSION = "2025-06-18"
TIMEOUT = 60.0


class StdioSession:
    """Minimal JSON-RPC over stdio client for driving the packaged server."""

    def __init__(self, process: asyncio.subprocess.Process) -> None:
        self._process = process
        self._next_id = 0

    @classmethod
    async def start(cls) -> StdioSession:
        """Spawn the server with piped stdio."""
        process = await asyncio.create_subprocess_exec(
            sys.executable,
            "-m",
            SERVER_MODULE,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        return cls(process)

    async def handshake(self) -> dict[str, Any]:
        """Run ``initialize`` + ``notifications/initialized`` and return the result."""
        result = await self.request(
            "initialize",
            {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {},
                "clientInfo": {"name": "pytest", "version": "0"},
            },
        )
        await self.notify("notifications/initialized")
        return result

    async def request(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        """Send a request and return its ``result`` block."""
        self._next_id += 1
        request_id = self._next_id
        await self._send({"jsonrpc": "2.0", "id": request_id, "method": method, "params": params})

        while True:
            message = await self._read_message()
            if message.get("id") == request_id:
                if "error" in message:
                    pytest.fail(f"{method} failed: {message['error']}")
                return message["result"]
            # Server-initiated notifications (log, progress, ...) are legal; skip them.

    async def notify(self, method: str, params: dict[str, Any] | None = None) -> None:
        """Send a one-way notification."""
        payload: dict[str, Any] = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            payload["params"] = params
        await self._send(payload)

    async def close(self) -> None:
        """Close stdin so the server exits, killing it if it hangs."""
        if self._process.stdin is not None and not self._process.stdin.is_closing():
            self._process.stdin.close()
        try:
            await asyncio.wait_for(self._process.wait(), timeout=TIMEOUT)
        except TimeoutError:
            self._process.kill()
            await self._process.wait()

    async def _send(self, payload: dict[str, Any]) -> None:
        assert self._process.stdin is not None
        self._process.stdin.write((json.dumps(payload) + "\n").encode())
        await self._process.stdin.drain()

    async def _read_message(self) -> dict[str, Any]:
        assert self._process.stdout is not None
        line = await asyncio.wait_for(self._process.stdout.readline(), timeout=TIMEOUT)
        if not line:
            stderr = b""
            if self._process.stderr is not None:
                stderr = await self._process.stderr.read()
            pytest.fail(f"server closed stdout before replying; stderr:\n{stderr.decode(errors='replace')}")
        # A non-JSON line here means the server polluted the protocol stream.
        return json.loads(line)


async def _start_session() -> tuple[StdioSession, dict[str, Any]]:
    """Spawn a server and complete the MCP handshake."""
    client = await StdioSession.start()
    return client, await client.handshake()


@pytest.fixture
async def session() -> AsyncIterator[tuple[StdioSession, dict[str, Any]]]:
    """An initialized MCP session against a freshly spawned server."""
    client, initialize_result = await _start_session()
    try:
        yield client, initialize_result
    finally:
        await client.close()


async def test_initialize_reports_package_version(
    session: tuple[StdioSession, dict[str, Any]],
) -> None:
    from mcp_server_moegirl_wiki import __version__

    _, initialize_result = session
    assert initialize_result["serverInfo"]["name"] == "moegirl-wiki"
    assert initialize_result["serverInfo"]["version"] == __version__
    assert initialize_result["capabilities"]["tools"] is not None


async def test_tools_list_exposes_both_tools(session: tuple[StdioSession, dict[str, Any]]) -> None:
    client, _ = session
    result = await client.request("tools/list", {})
    tools = {tool["name"]: tool for tool in result["tools"]}

    assert set(tools) == {"search_moegirl", "get_page"}

    search_params = tools["search_moegirl"]["inputSchema"]["properties"]
    assert set(search_params) == {"keyword", "limit"}
    assert tools["search_moegirl"]["inputSchema"]["required"] == ["keyword"]
    assert tools["search_moegirl"]["description"], "tool description must not be empty"

    page_params = tools["get_page"]["inputSchema"]["properties"]
    assert set(page_params) == {"title", "max_length"}
    assert tools["get_page"]["inputSchema"]["required"] == ["title"]
    assert page_params["max_length"]["default"] > 0


async def test_get_page_rejects_empty_title_without_network(
    session: tuple[StdioSession, dict[str, Any]],
) -> None:
    client, _ = session
    result = await client.request("tools/call", {"name": "get_page", "arguments": {"title": "   "}})
    assert not result.get("isError", False)
    payload = json.loads(result["content"][0]["text"])
    assert payload == {"error": "title 不能为空"}
