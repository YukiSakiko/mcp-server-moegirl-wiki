# mcp-server-moegirl-wiki

[![PyPI version](https://img.shields.io/pypi/v/mcp-server-moegirl-wiki.svg)](https://pypi.org/project/mcp-server-moegirl-wiki/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

English | [简体中文](README.zh-CN.md)

MCP server for [萌娘百科 (Moegirl Wiki)](https://zh.moegirl.org.cn/). Two tools: search entries and fetch a page's intro.

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

Replace the existing `[mcp]` block (or add it if you don't have one) — copy-paste-ready, all required fields included:

```toml
[mcp]
enable = true
servers = [
  {name = "moegirl", enabled = true, transport = "stdio",
   command = "uvx", args = ["mcp-server-moegirl-wiki"],
   env = {MOEGIRL_MAX_LENGTH = "6250"},
   url = "", headers = {},
   http_timeout_seconds = 30.0, read_timeout_seconds = 300.0,
   authorization = {mode = "none", bearer_token = ""}},
]

[mcp.client]
client_name = "MaiBot"
client_version = "1.0.0"

[mcp.client.roots]
enable = false
items = []

[mcp.client.sampling]
enable = false
task_name = "planner"
include_context_support = false
tool_support = false

[mcp.client.elicitation]
enable = false
allow_form = true
allow_url = false
```

Tweak `MOEGIRL_MAX_LENGTH` to taste (default `6250` covers a typical character page; raise to `20000` for very long pages, lower to `1500` for quick lookups). Restart MaiBot after editing. If `uvx` is not on `PATH`, replace `command = "uvx", args = ["mcp-server-moegirl-wiki"]` with `command = "pipx", args = ["run", "mcp-server-moegirl-wiki"]` or any other invocation that produces the binary.

## Development

```bash
git clone https://github.com/XXXxx7258/mcp-server-moegirl-wiki
cd mcp-server-moegirl-wiki
uv sync --group dev
uv run pytest -m network
uv run ruff check .
```

## Limitations

- `get_page` returns rendered plain text (templates expanded, links resolved). Raw wikitext (`prop=revisions`, `action=parse`, `?action=raw`, `Special:Export`) is blocked by Moegirl Wiki's site-wide ACL — empirically verified that bot-password login does **not** unlock it; only `sysop`/staff groups can call these actions.
- Uses the `mzh.moegirl.org.cn` mirror.

## License

[MIT](LICENSE)
