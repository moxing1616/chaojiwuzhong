#!/usr/bin/env python3
"""
超级物种 CLI — 一条命令启动 MCP Server

用法:
    chaojiwuzhong                          # 使用默认配置启动
    chaojiwuzhong --url http://localhost:8080    # 指定 SearXNG 地址
    chaojiwuzhong --engines baidu,google        # 指定默认搜索引擎
    chaojiwuzhong --help                         # 显示帮助
"""

import argparse
import asyncio
import os
import sys


def main():
    """超级物种命令行入口"""
    parser = argparse.ArgumentParser(
        prog="chaojiwuzhong",
        description="🚀 超级物种 — AI Agent 的无限搜索引擎 MCP Server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  chaojiwuzhong                                          # 默认配置启动
  chaojiwuzhong --url http://192.168.1.100:8080         # 指定 SearXNG 地址
  chaojiwuzhong --engines baidu,google,bing             # 指定搜索引擎
  chaojiwuzhong --timeout 30                            # 设置超时

环境变量:
  CHAOJIWUZHONG_URL       SearXNG 实例地址（默认 http://localhost:8080）
  CHAOJIWUZHONG_ENGINES   默认搜索引擎（默认 baidu,sogou）
  CHAOJIWUZHONG_TIMEOUT   请求超时秒数（默认 25）

项目地址: https://github.com/moxing1616/chaojiwuzhong
        """,
    )

    parser.add_argument(
        "--url",
        default=None,
        help="SearXNG 实例地址（默认 http://localhost:8080，也可通过环境变量 CHAOJIWUZHONG_URL 设置）",
    )
    parser.add_argument(
        "--engines",
        default=None,
        help="默认搜索引擎，逗号分隔（默认 baidu,sogou，也可通过环境变量 CHAOJIWUZHONG_ENGINES 设置）",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=None,
        help="请求超时秒数（默认 25，也可通过环境变量 CHAOJIWUZHONG_TIMEOUT 设置）",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 1.0.0",
    )

    args = parser.parse_args()

    # 命令行参数优先级高于环境变量
    if args.url:
        os.environ["CHAOJIWUZHONG_URL"] = args.url
    if args.engines:
        os.environ["CHAOJIWUZHONG_ENGINES"] = args.engines
    if args.timeout is not None:
        os.environ["CHAOJIWUZHONG_TIMEOUT"] = str(args.timeout)

    # 导入并启动 server
    from chaojiwuzhong.server import run_server

    try:
        asyncio.run(run_server())
    except KeyboardInterrupt:
        print("\n👋 超级物种已停止", file=sys.stderr)
        sys.exit(0)


if __name__ == "__main__":
    main()
