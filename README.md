# 🔍 超级物种 (Chaojiwuzhong)

> **SearXNG 的 MCP 封装工具** — 让你的 AI Agent 拥有搜索引擎能力。

[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![MCP](https://img.shields.io/badge/MCP-compatible-purple.svg)](https://modelcontextprotocol.io/)

**English** | [中文](#中文)

---

## What is this?

Chaojiwuzhong wraps your **self-hosted SearXNG** instance into an **MCP (Model Context Protocol)** server. 

AI agents (Claude Desktop, Cursor, Hermes, etc.) can then search the web and extract full page content — powered by your own SearXNG instance, with no third-party API keys or rate limits.

```
Your AI Agent ←→ MCP Protocol ←→ chaojiwuzhong ←→ Your SearXNG ←→ Baidu + Sogou + ...
```

## Why Chaojiwuzhong?

| Problem | Our Solution |
|---------|-------------|
| Search APIs have quotas & costs | Your SearXNG, your rules — no per-request billing |
| Most MCP search tools are English-only | **Baidu + Sogou dual-engine** for Chinese web, `.gov.cn` coverage |
| Other SearXNG MCPs only search | We provide **search + extract** (full page content) |
| Node.js / npx only | **Python** — fits the AI/ML ecosystem, works with `pip install` |

### vs Other SearXNG MCP Servers

| Feature | chaojiwuzhong | kevinwatt/mcp-server-searxng |
|---------|:-----------:|:---------------------------:|
| Language | 🐍 Python | JS (Node.js) |
| Search | ✅ | ✅ |
| Extract (full page) | ✅ | ❌ |
| Chinese engines (Baidu/Sogou) | ✅ | ❌ |
| CLI entry point | ✅ | ❌ |
| Multi-language README | ✅ 中英双语 | ❌ English only |
| Supported clients | Hermes, Claude, Cursor | Claude, Dive |

## Quick Start

### 1. Prerequisites: running SearXNG

You need a SearXNG instance. Quickest way:

```bash
docker run -d --name searxng \
  -p 8080:8080 \
  -v ./searxng:/etc/searxng \
  searxng/searxng
```

Verify:
```bash
curl "http://localhost:8080/search?q=hello&format=json"
```

### 2. Install chaojiwuzhong

```bash
pip install chaojiwuzhong
```

### 3. Configure your AI agent

**Hermes Agent** (`~/.hermes/config.yaml`):
```yaml
mcp_servers:
  chaojiwuzhong:
    command: python3
    args:
      - -m
      - chaojiwuzhong.server
    env:
      CHAOJIWUZHONG_URL: http://localhost:8080
      CHAOJIWUZHONG_ENGINES: baidu,sogou
      CHAOJIWUZHONG_TIMEOUT: "25"
```

**Claude Desktop** (`~/Library/Application Support/Claude/claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "chaojiwuzhong": {
      "command": "python3",
      "args": ["-m", "chaojiwuzhong.server"],
      "env": {
        "CHAOJIWUZHONG_URL": "http://localhost:8080",
        "CHAOJIWUZHONG_ENGINES": "baidu,sogou"
      }
    }
  }
}
```

**Cursor** — same MCP config format as Claude Desktop.

### 4. Done

Your AI agent now has `search` and `extract` tools available.

## Tools Provided

### `search` — Web Search

```python
# Agent calls:
search(query="AI 公安 接处警 site:gov.cn", max_results=10)
```

Parameters:
- `query` (required): search keywords
- `engines`: comma-separated engine list (default: `baidu,sogou`)
- `language`: language code (e.g., `zh-CN`, `en-US`)
- `max_results`: max results (default 15, max 20)

### `extract` — Full Page Content

```python
# Agent calls:
extract(url="https://www.gov.cn/example.html")
```

Returns clean text content from any webpage.

## Supported Search Engines

All engines available in your SearXNG instance. Tested and recommended:

| Engine | Best for |
|--------|----------|
| `baidu` | Chinese web, `.gov.cn` coverage |
| `sogou` | WeChat articles, Zhihu content |
| `bing` | English + Chinese mixed queries |
| `google` | Global coverage (may need proxy) |
| `duckduckgo` | Privacy-first search |
| `wikipedia` | Encyclopedia knowledge |

## Configuration

All via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `CHAOJIWUZHONG_URL` | `http://localhost:8080` | Your SearXNG instance URL |
| `CHAOJIWUZHONG_ENGINES` | `baidu,sogou` | Default search engines |
| `CHAOJIWUZHONG_TIMEOUT` | `25` | Request timeout in seconds |

## Optional: Better HTML parsing

```bash
pip install chaojiwuzhong[html]
```

Installs `beautifulsoup4` + `lxml` for higher quality content extraction.

---

## Disclaimer

- This tool is a **protocol adapter** — it translates MCP requests into SearXNG HTTP API calls. It does **not** scrape, cache, or redistribute search results.
- All search queries are routed through **your own SearXNG instance**. You are responsible for the SearXNG instance's compliance with applicable laws and terms of service.
- The `extract` function retrieves publicly accessible web pages for personal/AI-assisted reading purposes only. Do not republish extracted content without permission from the original source.
- This project is not affiliated with SearXNG, Baidu, Sogou, or any search engine provider.

## Get Listed

Want your SearXNG-based MCP tool to be discovered? Submit a PR to add it to **[awesome-mcp-servers](https://github.com/punkpeye/awesome-mcp-servers)** — the central directory of MCP tools (88k+ stars).

Example entry:
```markdown
- [Chaojiwuzhong](https://github.com/moxing1616/chaojiwuzhong) — SearXNG MCP with Baidu+Sogou dual-engine search &amp; full-page extraction
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT © [moxing1616](https://github.com/moxing1616)

---

# 中文

## 这是什么？

**超级物种** 把你的自建 SearXNG 搜索引擎封装成 MCP (模型上下文协议) 服务器。

AI Agent（如 Claude Desktop、Cursor、Hermes 等）可以通过 MCP 协议调用你的 SearXNG 实例，实现**无限搜索**和**网页正文抓取**。

## 为什么用 超级物种？

| 痛点 | 解决 |
|------|------|
| 搜索 API 有配额和费用 | 用自己的 SearXNG，无调用次数限制 |
| 大多数 MCP 搜索只支持英文 | **百度+搜狗双引擎**，中文搜索王者，`.gov.cn` 全覆盖 |
| 其他 SearXNG MCP 只能搜不能抓 | 我们提供 **search + extract**（全文抓取） |
| 只能用 npx（Node.js） | **Python**，AI/ML 生态原生，`pip install` 一条命令 |

### 与同类 SearXNG MCP 对比

| 功能 | chaojiwuzhong | kevinwatt/mcp-server-searxng |
|------|:-----------:|:---------------------------:|
| 语言 | 🐍 Python | JS (Node.js) |
| 搜索 | ✅ | ✅ |
| 网页全文抓取 | ✅ | ❌ |
| 中文引擎（百度/搜狗） | ✅ | ❌ |
| CLI 命令行 | ✅ | ❌ |
| 多语言文档 | ✅ 中英双语 | ❌ 仅英文 |
| 支持的客户端 | Hermes, Claude, Cursor | Claude, Dive |

## 快速开始

### 1. 准备 SearXNG 实例

```bash
docker run -d --name searxng \
  -p 8080:8080 \
  -v ./searxng:/etc/searxng \
  searxng/searxng
```

验证：
```bash
curl "http://localhost:8080/search?q=你好&format=json"
```

### 2. 安装

```bash
pip install chaojiwuzhong
```

### 3. 配置 AI Agent（见上方英文示例）

### 4. 使用

Agent 自动获得两个工具：
- `search` — 互联网搜索
- `extract` — 网页全文抓取

## 支持的搜索引擎

| 引擎 | 擅长领域 |
|------|---------|
| `baidu` | 中文搜索最强，`.gov.cn` 覆盖好 |
| `sogou` | 微信公众号、知乎内容 |
| `bing` | 中英文混合搜索 |
| `google` | 全球搜索（可能需要代理） |
| `duckduckgo` | 隐私友好 |
| `wikipedia` | 百科知识 |

## 可选增强

```bash
pip install chaojiwuzhong[html]
```

安装后抓取网页正文质量更高（使用 BeautifulSoup 智能提取文章主体）。

---

## 免责声明

- 本项目是一个**协议适配工具**——将 MCP 请求翻译为 SearXNG HTTP API 调用。不抓取、不缓存、不分发搜索结果。
- 所有搜索通过**你自建的 SearXNG 实例**完成。请自行确保 SearXNG 实例的合规性。
- `extract` 功能仅用于获取公开网页内容供个人/AI 辅助阅读。未经原作者许可，不得转载或重新发布提取的内容。
- 本项目与 SearXNG、百度、搜狗等搜索引擎提供商无任何关联。

## 开源协议

MIT © [moxing1616](https://github.com/moxing1616)
