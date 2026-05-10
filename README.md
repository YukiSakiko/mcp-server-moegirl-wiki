# mcp-server-moegirl-wiki

[![PyPI version](https://img.shields.io/pypi/v/mcp-server-moegirl-wiki.svg)](https://pypi.org/project/mcp-server-moegirl-wiki/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Python implementation of an MCP server for **[萌娘百科 (Moegirl Wiki)](https://zh.moegirl.org.cn/)**, exposing two tools to LLM agents: search Moegirl entries and fetch page summaries via the public MediaWiki API.

> Drop-in replacement for the npm package `moegirl-wiki-mcp` (which is currently abandoned).

## Why

The original npm package [`moegirl-wiki-mcp`](https://www.npmjs.com/package/moegirl-wiki-mcp) is abandonware:

- The author's GitHub account is gone (`yokami618`); the source repo `yokami618/wiki_mcp` returns 404.
- Last release was December 2025.
- It uses two MediaWiki APIs that no longer work reliably on Moegirl Wiki:
  - `action=parse` — now blocked for anonymous users (`action-notallowed`).
  - `list=search` (full-text index) — near-zero hit rate on character/work pages.

This Python implementation uses APIs that have been **verified to work** as of 2026:

| Tool | Strategy |
|---|---|
| `search_moegirl` | `generator=search` first (rich results) → falls back to `opensearch` (high title-match hit rate) on empty result |
| `get_page` | `query+prop=extracts+info` with `redirects=1, exintro=1, explaintext=1` |

Tool names and parameter shapes match the npm package, so prompts and configurations work unchanged after switching the binary.

## Install

```bash
# Recommended — uv (run without installing globally)
uvx mcp-server-moegirl-wiki

# Alternative — pipx
pipx run mcp-server-moegirl-wiki

# Alternative — pip
pip install mcp-server-moegirl-wiki
mcp-server-moegirl-wiki
```

## Tools

### `search_moegirl`

Search for entries on Moegirl Wiki.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `keyword` | string | required | Search keyword |
| `limit` | integer | `5` | Maximum number of results |

Returns:

```json
{
  "results": [
    {"title": "丰川祥子", "url": "https://mzh.moegirl.org.cn/丰川祥子", "snippet": "..."},
    {"title": "丰川祥子(明日方舟)", "url": "...", "snippet": ""}
  ],
  "count": 2
}
```

### `get_page`

Fetch the introductory plain-text summary of a wiki page. Auto-follows redirects.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `title` | string | required | Page title |
| `max_length` | integer | `1500` | Maximum characters returned in `summary` |

Returns on success:

```json
{
  "title": "三角初华",
  "summary": "三角初华（日语：三角（みすみ） 初華（ういか））是由日本娱乐公司Bushiroad策划的次世代少女乐队企划...",
  "url": "https://mzh.moegirl.org.cn/三角初华",
  "page_id": 570366
}
```

On failure:

```json
{"error": "页面不存在", "title": "..."}
```

## MCP client configuration

### Claude Desktop

Edit `claude_desktop_config.json` (`~/Library/Application Support/Claude/` on macOS, `%APPDATA%/Claude/` on Windows):

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

### MaiBot

In `config/bot_config.toml`:

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

If `uvx` is not on `PATH`, replace `command`/`args` with:

```toml
command = "pipx", args = ["run", "mcp-server-moegirl-wiki"]
```

…or any path to a Python interpreter that has the package installed:

```toml
command = "/path/to/venv/bin/mcp-server-moegirl-wiki", args = []
```

## Development

```bash
git clone https://github.com/XXXxx7258/mcp-server-moegirl-wiki
cd mcp-server-moegirl-wiki
uv sync --group dev
uv run mcp-server-moegirl-wiki   # blocks reading stdin → ready

# Network smoke tests (hit the live Moegirl API)
uv run pytest -m network

# Lint
uv run ruff check .
```

## Known limitations

- **Anonymous-only.** No login support. Some advanced API actions (`action=parse`, full-page wikitext) are blocked by Moegirl for anonymous users; we work around this by using `prop=extracts` instead.
- **Intro section only.** `get_page` returns the plain-text introduction, not the full page. This is enough for most "what is X" lookups; for deeper content, follow the returned `url`.
- **Mirror.** Uses `mzh.moegirl.org.cn` (the static/mobile mirror) which has been more stable in our tests than the main site.

## Credits

API client logic adapted from MaiBot's [`moegirl_wiki_plugin`](https://github.com/Mai-with-u/MaiBot/tree/main/plugins/moegirl_wiki_plugin), where the `generator=search` → `opensearch` fallback strategy was originally proven.

## License

[MIT](LICENSE)
