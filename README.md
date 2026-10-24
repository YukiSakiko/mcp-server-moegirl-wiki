# mcp-server-moegirl-wiki

[![PyPI version](https://img.shields.io/pypi/v/mcp-server-moegirl-wiki.svg)](https://pypi.org/project/mcp-server-moegirl-wiki/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

English | [简体中文](README.zh-CN.md)

MCP server for [萌娘百科 (Moegirl Wiki)](https://zh.moegirl.org.cn/). Two tools: search entries and fetch a page's intro.

Requires the MCP Python SDK **2.x** (`mcp>=2,<3`); see [Compatibility](#compatibility) if you are still on `0.2.x`.

## Install

```bash
uvx mcp-server-moegirl-wiki         # recommended
pipx run mcp-server-moegirl-wiki
pip install mcp-server-moegirl-wiki
```

## Tools

### `search_moegirl(keyword: str, limit: int = 5)`

Returns `{"results": [{"title", "url", "snippet"}, ...], "count": int}`.

### `get_page(title: str, max_length: int = 6250)`

Returns `{"title", "content", "url", "page_id"}` — full plain-text rendering of the page (all sections, templates expanded, links resolved). Auto-follows redirects. `content` is truncated to `max_length` characters; default 6250 covers a typical character page in full, pass larger (e.g. 20000) for very long pages.

## Environment variables

| Variable | Default | Description |
|---|---|---|
| `MOEGIRL_MAX_LENGTH` | `6250` | Default `max_length` for `get_page` when the caller does not specify one. Useful for tuning per-deployment without forking the package. Invalid/non-positive values are ignored with a warning. |

## Configuration

### Claude Desktop

```json
{
  "mcpServers": {
    "moegirl-wiki": {
      "command": "uvx",
      "args": ["mcp-server-moegirl-wiki"]
    }
  }
}
```

### MaiBot (`config/bot_config.toml`)

MaiBot's default config already has the `[mcp]` block — just replace the `servers` line:

```toml
servers = [{name = "moegirl", enabled = true, transport = "stdio", command = "uvx", args = ["mcp-server-moegirl-wiki"], env = {MOEGIRL_MAX_LENGTH = "6250"}, url = "", headers = {}, http_timeout_seconds = 30.0, read_timeout_seconds = 300.0, authorization = {mode = "none", bearer_token = ""}}]
```

Tweak `MOEGIRL_MAX_LENGTH` to taste (raise to `20000` for very long pages, lower to `1500` for quick lookups). If `uvx` is not on `PATH`, swap `command`/`args` for `command = "pipx", args = ["run", "mcp-server-moegirl-wiki"]`.

## Development

```bash
git clone https://github.com/XXXxx7258/mcp-server-moegirl-wiki
cd mcp-server-moegirl-wiki
uv sync --group dev
uv run pytest -m network
uv run ruff check .
```

## Compatibility

| Server version | MCP Python SDK | Notes |
|---|---|---|
| `0.3.x` | `mcp>=2,<3` | SDK 2.0 renamed `FastMCP` to `mcp.server.mcpserver.MCPServer`, so 0.2.x could not run on it. Hosts whose *client* still uses SDK 1.x work fine — the stdio handshake negotiates a shared protocol version (verified: 1.29.1 client ↔ 2.3.0 server). |
| `0.2.x` | `mcp>=1.0` | Crashes at startup on SDK 2.x (`No module named 'mcp.server.fastmcp'`). That is what `0.3.0` fixes; pin `mcp<2` only if you must stay on 0.2.x. |

## Limitations

- `get_page` returns rendered plain text (templates expanded, links resolved). Raw wikitext (`prop=revisions`, `action=parse`, `?action=raw`, `Special:Export`) is blocked by Moegirl Wiki's site-wide ACL — empirically verified that bot-password login does **not** unlock it; only `sysop`/staff groups can call these actions.
- Uses the `mzh.moegirl.org.cn` mirror.
- Proxy variables are honoured via `httpx`'s `trust_env`. Some `NO_PROXY` values are valid for curl but unparseable for `httpx` (e.g. a bare `::1` next to `[::1]`); in that case the server logs a warning and issues direct requests instead of failing every tool call.

## License

[MIT](LICENSE)
