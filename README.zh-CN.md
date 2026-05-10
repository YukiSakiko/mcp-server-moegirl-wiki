# mcp-server-moegirl-wiki

[![PyPI version](https://img.shields.io/pypi/v/mcp-server-moegirl-wiki.svg)](https://pypi.org/project/mcp-server-moegirl-wiki/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

[English](README.md) | 简体中文

[萌娘百科](https://zh.moegirl.org.cn/) 的 MCP 服务器。提供两个工具：搜索条目、获取条目摘要。

## 安装

```bash
uvx mcp-server-moegirl-wiki         # 推荐
pipx run mcp-server-moegirl-wiki
pip install mcp-server-moegirl-wiki
```

## 工具

### `search_moegirl(keyword: str, limit: int = 5)`

返回 `{"results": [{"title", "url", "snippet"}, ...], "count": int}`。

### `get_page(title: str, max_length: int = 1500)`

返回 `{"title", "summary", "url", "page_id"}`——开篇段落纯文本，自动跟随重定向。

## 配置

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

## 开发

```bash
git clone https://github.com/XXXxx7258/mcp-server-moegirl-wiki
cd mcp-server-moegirl-wiki
uv sync --group dev
uv run pytest -m network
uv run ruff check .
```

## 限制

- 仅支持匿名访问。`get_page` 仅返回开篇段落——完整 wikitext 需要登录。
- 使用 `mzh.moegirl.org.cn` 镜像。

## 许可证

[MIT](LICENSE)
