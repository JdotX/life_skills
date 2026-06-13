#!/usr/bin/env python3
"""
从文本文件中提取所有 URL。
支持 .md, .txt, .html 等格式。
输出 JSON 格式的 URL 列表，包含链接和上下文。
"""

import re
import sys
import json
from pathlib import Path


def extract_urls(filepath: str) -> list[dict]:
    """从文件中提取所有 URL，返回列表包含 url 和上下文文本。"""
    path = Path(filepath)
    if not path.exists():
        print(f"错误：文件不存在 - {filepath}", file=sys.stderr)
        sys.exit(1)

    text = path.read_text(encoding="utf-8")

    # 匹配 markdown 链接 [text](url) 和裸 URL
    markdown_pattern = re.compile(r'\[([^\]]*)\]\(([^)]+)\)')
    bare_url_pattern = re.compile(
        r'https?://[^\s<>"\'\)\]]+'
    )

    results = []

    # 1. 提取 markdown 链接
    for match in markdown_pattern.finditer(text):
        url = match.group(2).strip()
        context = match.group(1).strip()
        if url.startswith(('http://', 'https://')):
            results.append({"url": url, "context": context, "type": "markdown"})

    # 2. 提取裸 URL（不在 markdown 链接中的）
    # 先移除已匹配的 markdown 链接中的 URL 部分
    text_without_md = re.sub(r'\[([^\]]*)\]\(([^)]+)\)', '', text)
    for match in bare_url_pattern.finditer(text_without_md):
        url = match.group(0).rstrip('.,;:!?)"\'>')
        # 检查是否已被 markdown 模式捕获
        if not any(r["url"] == url for r in results):
            results.append({"url": url, "context": "", "type": "bare"})

    return results


def guess_recipe_link(url: str, context: str) -> bool:
    """启发式判断一个 URL 是否为菜谱链接。"""
    recipe_keywords = [
        "recipe", "cook", "food", "菜谱", "食谱", "烹饪",
        "美食", "eating", "cooking",
        "食材", "调料", "做法",
    ]
    combined = (url + " " + context).lower()
    return any(kw.lower() in combined for kw in recipe_keywords)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python3 extract_urls.py <文件路径>", file=sys.stderr)
        sys.exit(1)

    urls = extract_urls(sys.argv[1])

    # 标记是否为菜谱链接
    for item in urls:
        item["is_recipe"] = guess_recipe_link(item["url"], item["context"])

    print(json.dumps(urls, ensure_ascii=False, indent=2))
    print(f"\n共找到 {len(urls)} 个链接，其中 {sum(1 for u in urls if u['is_recipe'])} 个可能是菜谱。", file=sys.stderr)
