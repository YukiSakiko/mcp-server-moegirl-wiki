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

### `get_page(title: str, max_length: int = 1500)`

Returns `{"title", "summary", "url", "page_id"}` — intro plain text, follows redirects.

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

```toml
[mcp]
enable = true
servers = [
  {name = "moegirl", enabled = true, transport = "stdio",
   command = "uvx", args = ["mcp-server-moegirl-wiki"],
   env = {}, url = "", headers = {},
   http_timeout_seconds = 30.0, read_timeout_seconds = 300.0,
   authorization = {mode = "none", bearer_token = ""}},
]
```

## Development

```bash
git clone https://github.com/XXXxx7258/mcp-server-moegirl-wiki
cd mcp-server-moegirl-wiki
uv sync --group dev
uv run pytest -m network
uv run ruff check .
```

## Limitations

- `get_page` returns intro plain text only. Full wikitext (`prop=revisions`, `action=parse`, `?action=raw`) is blocked by Moegirl Wiki's site-wide ACL for all non-privileged user groups — empirically verified that bot-password login does **not** unlock it; only `sysop`/staff groups can call these actions.
- Uses the `mzh.moegirl.org.cn` mirror.

## License

[MIT](LICENSE)
