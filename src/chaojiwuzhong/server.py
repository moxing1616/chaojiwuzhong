#!/usr/bin/env python3
"""
超级物种 MCP Server — 自建搜索引擎，无限额度，为 AI Agent 提供无限搜索能力

基于 SearXNG 自建搜索实例，封装为 MCP (Model Context Protocol) Server，
让 AI Agent 可以无限制地搜索互联网内容。默认使用百度+搜狗双引擎，
支持多种搜索引擎组合，提供搜索和网页正文提取两大能力。

环境变量：
    CHAOJIWUZHONG_URL    超级物种 SearXNG 实例地址（默认 http://localhost:8080）
    CHAOJIWUZHONG_ENGINES 默认搜索引擎（默认 baidu,sogou）
    CHAOJIWUZHONG_TIMEOUT  请求超时秒数（默认 25）
"""

import json
import logging
import os
import re
import sys
import asyncio

import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# ── 日志配置 ──────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stderr,  # MCP 用 stdio 通信，日志打到 stderr
)
logger = logging.getLogger("chaojiwuzhong")

# ── 配置 ──────────────────────────────────────────────────
CHAOJIWUZHONG_URL = os.environ.get("CHAOJIWUZHONG_URL", "http://localhost:8080")
DEFAULT_ENGINES = os.environ.get("CHAOJIWUZHONG_ENGINES", "baidu,sogou")
TIMEOUT = float(os.environ.get("CHAOJIWUZHONG_TIMEOUT", "25"))
MAX_EXTRACT_CHARS = 8000

# 可选搜索引擎及说明
AVAILABLE_ENGINES = {
    "baidu": "百度 — 中文搜索最强",
    "sogou": "搜狗 — 微信/知乎内容收录好",
    "bing": "必应 — 英文搜索优秀，中文也不错",
    "google": "Google — 全球最全（需代理）",
    "duckduckgo": "DuckDuckGo — 隐私友好",
    "wikipedia": "维基百科 — 百科知识",
    "brave": "Brave — 独立索引，隐私优先",
    "qwant": "Qwant — 欧洲隐私搜索引擎",
}

# ── 可选依赖：BeautifulSoup ───────────────────────────────
try:
    from bs4 import BeautifulSoup

    HAS_BS4 = True
    logger.info("BeautifulSoup4 已安装，将使用高质量 HTML 解析")
except ImportError:
    HAS_BS4 = False
    logger.info("BeautifulSoup4 未安装，使用正则表达式解析（建议 pip install chaojiwuzhong[html]）")

# ── 创建 MCP Server ───────────────────────────────────────
server = Server("chaojiwuzhong")


# ══════════════════════════════════════════════════════════
#  工具定义
# ══════════════════════════════════════════════════════════

@server.list_tools()
async def list_tools() -> list[Tool]:
    """注册超级物种提供的工具列表"""
    return [
        Tool(
            name="search",
            description=(
                "🔍 超级物种搜索 — 百度+搜狗双引擎，无额度限制。"
                "搜索互联网内容，返回标题、URL和摘要。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "搜索关键词",
                    },
                    "engines": {
                        "type": "string",
                        "description": (
                            f"搜索引擎，逗号分隔。默认 {DEFAULT_ENGINES}。"
                            f"可选: {', '.join(AVAILABLE_ENGINES.keys())}"
                        ),
                    },
                    "language": {
                        "type": "string",
                        "description": (
                            "搜索语言代码，如 zh-CN（中文）、en-US（英文）、"
                            "ja-JP（日文）等。留空则不限制语言。"
                        ),
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "最大结果数，默认 15，最大 20",
                        "default": 15,
                    },
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="extract",
            description=(
                "📄 超级物种抓取 — 抓取网页全文内容，返回纯文本。"
                "用于获取搜索结果中文章的完整内容。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "要抓取的网页 URL（必须以 http:// 或 https:// 开头）",
                    }
                },
                "required": ["url"],
            },
        ),
    ]


# ══════════════════════════════════════════════════════════
#  工具调用分发
# ══════════════════════════════════════════════════════════

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """工具调用分发器"""
    logger.info(f"收到工具调用: {name}, 参数: {json.dumps(arguments, ensure_ascii=False)[:200]}")

    if name == "search":
        return await handle_search(arguments)
    elif name == "extract":
        return await handle_extract(arguments)
    else:
        return [TextContent(type="text", text=f"❌ 未知工具: {name}")]


# ══════════════════════════════════════════════════════════
#  search 工具实现
# ══════════════════════════════════════════════════════════

async def handle_search(args: dict) -> list[TextContent]:
    """执行搜索请求"""
    query = args.get("query", "").strip()
    if not query:
        return [TextContent(type="text", text="❌ 搜索关键词不能为空，请输入要搜索的内容。")]

    engines = args.get("engines", DEFAULT_ENGINES)
    max_results = min(args.get("max_results", 15), 20)
    language = args.get("language", "")

    # 验证引擎名称
    engine_list = [e.strip() for e in engines.split(",") if e.strip()]
    invalid_engines = [e for e in engine_list if e not in AVAILABLE_ENGINES]
    if invalid_engines:
        logger.warning(f"无效引擎被忽略: {invalid_engines}")
        engine_list = [e for e in engine_list if e in AVAILABLE_ENGINES]
        if not engine_list:
            engine_list = [e.strip() for e in DEFAULT_ENGINES.split(",")]
        engines = ",".join(engine_list)

    # 构建请求
    search_url = f"{CHAOJIWUZHONG_URL.rstrip('/')}/search"
    params = {
        "q": query,
        "format": "json",
        "engines": engines,
        "pageno": 1,
    }
    if language:
        params["language"] = language

    logger.info(f"搜索请求: {search_url} | q={query[:50]} | engines={engines}")

    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            resp = await client.get(search_url, params=params)
            resp.raise_for_status()
            data = resp.json()

        results = data.get("results", [])[:max_results]
        if not results:
            return [TextContent(
                type="text",
                text=f"🔍 搜索「{query}」未找到结果。\n"
                     f"引擎: {engines}\n"
                     f"提示: 尝试更换关键词或检查 SearXNG 实例是否正常运行。"
            )]

        # 格式化输出
        lines = [
            f"🔍 超级物种搜索",
            f"关键词: {query}",
            f"引擎: {engines}",
            f"结果: {len(results)} 条",
            f"",
        ]
        for i, r in enumerate(results, 1):
            title = r.get("title", "无标题").strip()
            url = r.get("url", "").strip()
            snippet = (r.get("content") or r.get("snippet") or "")[:250]
            engine = r.get("engine", "?")

            lines.append(f"[{i}] [{engine}] {title}")
            lines.append(f"    🔗 {url}")
            if snippet:
                lines.append(f"    📝 {snippet}")
            lines.append("")

        return [TextContent(type="text", text="\n".join(lines))]

    except httpx.ConnectError as e:
        logger.error(f"连接失败: {e}")
        return [TextContent(
            type="text",
            text=f"❌ 无法连接到超级物种搜索服务 ({CHAOJIWUZHONG_URL})\n"
                 f"请确认：\n"
                 f"  1. SearXNG 服务是否已启动\n"
                 f"  2. 地址是否正确（当前: {CHAOJIWUZHONG_URL}）\n"
                 f"  3. 环境变量 CHAOJIWUZHONG_URL 是否配置正确\n"
                 f"错误详情: {e}"
        )]
    except httpx.TimeoutException as e:
        logger.error(f"请求超时: {e}")
        return [TextContent(
            type="text",
            text=f"⏰ 搜索请求超时（{TIMEOUT}s）\n"
                 f"可通过环境变量 CHAOJIWUZHONG_TIMEOUT 调整超时时间。"
        )]
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP 错误: {e.response.status_code}")
        return [TextContent(
            type="text",
            text=f"❌ 搜索服务返回错误 (HTTP {e.response.status_code})\n"
                 f"请检查 SearXNG 实例状态。"
        )]
    except Exception as e:
        logger.exception("搜索异常")
        return [TextContent(type="text", text=f"❌ 搜索异常: {type(e).__name__}: {e}")]


# ══════════════════════════════════════════════════════════
#  extract 工具实现
# ══════════════════════════════════════════════════════════

async def handle_extract(args: dict) -> list[TextContent]:
    """抓取网页全文内容"""
    url = args.get("url", "").strip()
    if not url:
        return [TextContent(type="text", text="❌ 请提供要抓取的网页 URL。")]
    if not url.startswith(("http://", "https://")):
        return [TextContent(type="text", text="❌ URL 必须以 http:// 或 https:// 开头")]

    logger.info(f"抓取网页: {url[:80]}")

    try:
        async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
            resp = await client.get(
                url,
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/120.0.0.0 Safari/537.36"
                    ),
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                },
            )
            resp.raise_for_status()

        text = _extract_text_from_html(resp.text, url)

        # 截断
        if len(text) > MAX_EXTRACT_CHARS:
            text = text[:MAX_EXTRACT_CHARS] + "\n\n... (内容已截断)"

        logger.info(f"抓取成功: {url[:60]} -> {len(text)} 字符")
        return [TextContent(type="text", text=text)]

    except httpx.ConnectError as e:
        logger.error(f"抓取连接失败: {url[:60]} | {e}")
        return [TextContent(type="text", text=f"❌ 无法连接到 {url}\n错误: {e}")]
    except httpx.TimeoutException:
        logger.error(f"抓取超时: {url[:60]}")
        return [TextContent(type="text", text=f"⏰ 抓取超时: {url}\n请稍后重试或尝试其他网页。")]
    except httpx.HTTPStatusError as e:
        logger.error(f"抓取 HTTP {e.response.status_code}: {url[:60]}")
        return [TextContent(
            type="text",
            text=f"❌ 网页返回错误 (HTTP {e.response.status_code}): {url}"
        )]
    except Exception as e:
        logger.exception("抓取异常")
        return [TextContent(type="text", text=f"❌ 抓取异常: {type(e).__name__}: {e}"])


def _extract_text_from_html(html: str, source_url: str = "") -> str:
    """
    从 HTML 中提取纯文本。

    优先使用 BeautifulSoup（若已安装），否则使用正则表达式降级方案。
    """
    if HAS_BS4:
        return _extract_with_bs4(html, source_url)
    else:
        return _extract_with_regex(html)


def _extract_with_bs4(html: str, source_url: str = "") -> str:
    """使用 BeautifulSoup 高质量提取网页正文"""
    soup = BeautifulSoup(html, "lxml")

    # 移除不需要的元素
    for tag in soup.find_all(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()

    # 尝试提取正文（常见选择器）
    main_content = None
    for selector in ["article", "main", '[role="main"]', ".post-content", ".article-content", ".content"]:
        main_content = soup.select_one(selector)
        if main_content:
            break

    if main_content:
        text = main_content.get_text(separator="\n", strip=True)
    else:
        text = soup.get_text(separator="\n", strip=True)

    # 清理多余空行
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    return "\n".join(lines)


def _extract_with_regex(html: str) -> str:
    """使用正则表达式降级提取文本（不依赖 BeautifulSoup）"""
    text = html

    # 移除 script 和 style 标签及其内容
    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<noscript[^>]*>.*?</noscript>', '', text, flags=re.DOTALL | re.IGNORECASE)

    # 移除 HTML 标签
    text = re.sub(r'<[^>]+>', ' ', text)

    # 处理常见 HTML 实体
    text = re.sub(r'&nbsp;', ' ', text)
    text = re.sub(r'&amp;', '&', text)
    text = re.sub(r'&lt;', '<', text)
    text = re.sub(r'&gt;', '>', text)
    text = re.sub(r'&quot;', '"', text)
    text = re.sub(r'&#\d+;', ' ', text)
    text = re.sub(r'&#x[0-9a-fA-F]+;', ' ', text)

    # 压缩空白
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n\s*\n', '\n', text)
    text = text.strip()

    return text


# ══════════════════════════════════════════════════════════
#  入口
# ══════════════════════════════════════════════════════════

async def run_server():
    """启动 MCP server（通过 stdio）"""
    logger.info(f"🚀 超级物种 MCP Server 启动中...")
    logger.info(f"   SearXNG 地址: {CHAOJIWUZHONG_URL}")
    logger.info(f"   默认引擎: {DEFAULT_ENGINES}")
    logger.info(f"   超时: {TIMEOUT}s")
    logger.info(f"   HTML 解析: {'BeautifulSoup' if HAS_BS4 else '正则表达式 (降级)'}")

    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


if __name__ == "__main__":
    asyncio.run(run_server())
