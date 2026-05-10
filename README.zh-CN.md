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

### `get_page(title: str, max_length: int = 6250)`

返回 `{"title", "content", "url", "page_id"}`——条目纯文本全文（所有章节、模板已展开、链接已解析），自动跟随重定向。`content` 按 `max_length` 字符截断，默认 6250 通常足以覆盖一个角色页面全文；超长页面传更大值（如 20000）。

## 环境变量

| 变量 | 默认值 | 说明 |
|---|---|---|
| `MOEGIRL_MAX_LENGTH` | `6250` | `get_page` 调用方未指定 `max_length` 时使用的默认值。无需 fork 包即可按部署调整；非正整数将被忽略并打告警。|

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

MaiBot 的默认配置里已经有 `[mcp]` 块了——只要替换 `servers` 那一行：

```toml
servers = [{name = "moegirl", enabled = true, transport = "stdio", command = "uvx", args = ["mcp-server-moegirl-wiki"], env = {MOEGIRL_MAX_LENGTH = "6250"}, url = "", headers = {}, http_timeout_seconds = 30.0, read_timeout_seconds = 300.0, authorization = {mode = "none", bearer_token = ""}}]
```

按需改 `MOEGIRL_MAX_LENGTH`（超长条目调 `20000`，只要摘要调 `1500`）。如果 `uvx` 不在 `PATH` 上，把 `command`/`args` 换成 `command = "pipx", args = ["run", "mcp-server-moegirl-wiki"]`。

## 开发

```bash
git clone https://github.com/XXXxx7258/mcp-server-moegirl-wiki
cd mcp-server-moegirl-wiki
uv sync --group dev
uv run pytest -m network
uv run ruff check .
```

## 限制

- `get_page` 返回的是渲染后纯文本（模板已展开、链接已解析）。原始 wikitext（`prop=revisions`、`action=parse`、`?action=raw`、`Special:Export`）被萌娘百科站点级 ACL 屏蔽——实测 bot password 登录**也无法解锁**，只有 `sysop`/员工组可以调用这些 action。
- 使用 `mzh.moegirl.org.cn` 镜像。

## 许可证

[MIT](LICENSE)
