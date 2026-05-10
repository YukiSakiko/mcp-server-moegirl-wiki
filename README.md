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

- `get_page` returns rendered plain text (templates expanded, links resolved). Raw wikitext (`prop=revisions`, `action=parse`, `?action=raw`, `Special:Export`) is blocked by Moegirl Wiki's site-wide ACL — empirically verified that bot-password login does **not** unlock it; only `sysop`/staff groups can call these actions.
- Uses the `mzh.moegirl.org.cn` mirror.

## License

[MIT](LICENSE)
