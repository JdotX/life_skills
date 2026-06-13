#!/usr/bin/env python3
"""
获取 URL 页面内容。支持三种模式：
  http         — 普通 HTTP 请求
  headless     — Playwright headless browser
  connect      — 连接到正在运行的 Chrome（复用登录状态）

用法：
  python3 fetch_recipes.py <url>
  python3 fetch_recipes.py <url> --headless
  python3 fetch_recipes.py <url> --connect http://localhost:9222
  python3 fetch_recipes.py --batch urls.txt --connect http://localhost:9222
"""

import sys
import json
import argparse
import time
import random
from typing import Optional

import requests
from bs4 import BeautifulSoup


def fetch_http(url: str) -> Optional[str]:
    """使用普通 HTTP 请求获取页面内容。"""
    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        }
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        print(f"  HTTP 请求失败: {e}", file=sys.stderr)
        return None


def fetch_via_cdp(url: str, cdp_endpoint: str) -> Optional[str]:
    """连接到正在运行的 Chrome 浏览器（复用登录状态）。"""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("  错误: 需要安装 playwright", file=sys.stderr)
        return None

    try:
        with sync_playwright() as p:
            browser = p.chromium.connect_over_cdp(cdp_endpoint)
            context = browser.contexts[0] if browser.contexts else browser.new_context()
            page = context.new_page()
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(2000)
            content = page.content()
            page.close()
            browser.close()
            return content
    except Exception as e:
        print(f"  CDP 获取失败: {e}", file=sys.stderr)
        return None


def is_slide_verification(html: str) -> bool:
    """检测页面是否触发了滑块验证。"""
    keywords = ["请滑动完成验证", "请按住滑块", "滑动验证"]
    return any(kw in html for kw in keywords)


def fetch_headless(url: str) -> Optional[str]:
    """使用 headless browser 获取页面内容（含滑块自动重试）。"""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("  错误: 需要安装 playwright", file=sys.stderr)
        return None

    retry_delays = [0, 5, 10, 20]  # 首次 + 3次重试
    for attempt, delay in enumerate(retry_delays):
        if delay > 0:
            print(f"  等待 {delay}s 后重试...", file=sys.stderr)
            time.sleep(delay)

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page(
                    viewport={"width": 1920, "height": 1080},
                    locale="zh-CN",
                )
                page.goto(url, wait_until="domcontentloaded", timeout=30000)
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                page.wait_for_timeout(2000)
                content = page.content()
                browser.close()

                if is_slide_verification(content):
                    print(f"  第 {attempt+1} 次触发滑块验证", file=sys.stderr)
                    if attempt < len(retry_delays) - 1:
                        continue
                    return None
                return content
        except Exception as e:
            print(f"  第 {attempt+1} 次失败: {e}", file=sys.stderr)
            if attempt < len(retry_delays) - 1:
                continue
            return None
    return None


def fetch_batch(urls: list[str], cdp_endpoint: str = "") -> dict[str, Optional[str]]:
    """批量获取页面，每个 URL 独立浏览器 + 随机间隔 5-15s。"""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("错误: 需要安装 playwright", file=sys.stderr)
        return {u: None for u in urls}

    results = {}
    for idx, url in enumerate(urls):
        result_html = None
        retry_delays = [0, 5, 10, 20]

        for attempt, delay in enumerate(retry_delays):
            if delay > 0:
                print(f"  [{idx+1}/{len(urls)}] 等待 {delay}s 后重试...", file=sys.stderr)
                time.sleep(delay)

            try:
                with sync_playwright() as p:
                    if cdp_endpoint:
                        browser = p.chromium.connect_over_cdp(cdp_endpoint)
                    else:
                        browser = p.chromium.launch(headless=True)

                    print(f"  [{idx+1}/{len(urls)}] 尝试 {attempt+1}: {url}", file=sys.stderr)
                    page = browser.new_page(
                        viewport={"width": 1920, "height": 1080},
                        locale="zh-CN",
                    )
                    page.goto(url, wait_until="domcontentloaded", timeout=30000)
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    page.wait_for_timeout(2000)
                    html = page.content()
                    page.close()
                    browser.close()

                    if is_slide_verification(html):
                        print(f"  触发滑块验证", file=sys.stderr)
                        continue
                    result_html = html
                    break
            except Exception as e:
                print(f"  获取失败: {e}", file=sys.stderr)
                if attempt < len(retry_delays) - 1:
                    continue
                break

        results[url] = result_html

        # URL 间随机间隔 5-15s
        if idx < len(urls) - 1:
            gap = 10 + random.randint(-5, 5)
            print(f"  [{idx+1}/{len(urls)}] 完成，等待 {gap}s 继续...", file=sys.stderr)
            time.sleep(gap)

    return results


def extract_page_info(html: str, url: str) -> dict:
    """从 HTML 中提取页面基本信息。"""
    soup = BeautifulSoup(html, "html.parser")

    title = ""
    for tag in ["h1", "h2", "title"]:
        el = soup.find(tag)
        if el and el.get_text(strip=True):
            title = el.get_text(strip=True)
            break

    for unwanted in soup.find_all(["script", "style", "nav", "footer", "header", "aside"]):
        unwanted.decompose()
    body = soup.find("body") or soup
    text_content = body.get_text(separator="\n", strip=True)

    return {
        "url": url,
        "title": title,
        "content_preview": text_content[:3000],
    }


def read_urls_from_file(filepath: str) -> list[str]:
    """从文件读取 URL 列表。"""
    urls = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith(("http://", "https://")):
                urls.append(line)
    return urls


def main():
    parser = argparse.ArgumentParser(description="获取页面内容")
    parser.add_argument("url", nargs="?", help="页面 URL")
    parser.add_argument("--headless", action="store_true", help="使用 headless browser")
    parser.add_argument("--connect", type=str, metavar="CDP_URL",
                        help="连接到正在运行的 Chrome，如 http://localhost:9222")
    parser.add_argument("--batch", type=str, metavar="FILE", help="批量获取，参数为 URL 文件路径")
    args = parser.parse_args()

    if args.batch:
        urls = read_urls_from_file(args.batch)
        print(f"批量获取 {len(urls)} 个链接...", file=sys.stderr)
        cdp = args.connect or ""
        mode = "cdp" if cdp else "headless"
        html_map = fetch_batch(urls, cdp_endpoint=cdp)
        results = [
            extract_page_info(html, url) if html
            else {"url": url, "error": "获取失败"}
            for url, html in html_map.items()
        ]
        for r in results:
            r["mode"] = mode
        print(json.dumps(results, ensure_ascii=False, indent=2))
        return

    if not args.url:
        parser.print_help()
        sys.exit(1)

    html = None
    mode = ""

    if args.connect:
        print(f"通过 Chrome CDP 获取: {args.url}", file=sys.stderr)
        html = fetch_via_cdp(args.url, args.connect)
        mode = "cdp"
    elif args.headless:
        print(f"使用 headless browser 获取: {args.url}", file=sys.stderr)
        html = fetch_headless(args.url)
        mode = "headless"
    else:
        print(f"HTTP 获取: {args.url}", file=sys.stderr)
        html = fetch_http(args.url)
        if html is None:
            print("HTTP 失败，尝试 headless browser...", file=sys.stderr)
            html = fetch_headless(args.url)
            mode = "headless"
        else:
            mode = "http"

    if html is None:
        print(json.dumps({"url": args.url, "error": "获取失败", "mode": mode}))
        sys.exit(1)

    result = extract_page_info(html, args.url)
    result["mode"] = mode
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
