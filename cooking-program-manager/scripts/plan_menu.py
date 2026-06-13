#!/usr/bin/env python3
"""
编排下周菜单。
读取菜谱池、历史记录和黑名单，生成一周菜单。

用法：
  python3 plan_menu.py --recipes recipes.json [--history data/history.csv] [--blacklist data/blacklist.txt] [--output data/weekly_menu_<周次>.csv]
"""

import json
import csv
import sys
import argparse
from datetime import date, timedelta
from pathlib import Path


def next_week_dates() -> list[date]:
    """返回下周周一至周五的日期列表。"""
    today = date.today()
    # 下周一
    days_ahead = 7 - today.weekday()  # Monday=0
    next_monday = today + timedelta(days=days_ahead)
    return [next_monday + timedelta(days=i) for i in range(5)]


def load_history(history_path: str) -> list[dict]:
    """加载历史菜单。"""
    path = Path(history_path)
    if not path.exists():
        return []
    records = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            records.append(row)
    return records


def load_blacklist(blacklist_path: str) -> set[str]:
    """加载黑名单。"""
    path = Path(blacklist_path)
    if not path.exists():
        return set()
    return set(line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip())


def load_recipes(recipes_path: str) -> list[dict]:
    """加载菜谱池（JSON 格式）。"""
    path = Path(recipes_path)
    if not path.exists():
        print(f"错误: 菜谱文件不存在 - {recipes_path}", file=sys.stderr)
        sys.exit(1)
    return json.loads(path.read_text(encoding="utf-8"))


def get_last_week_records(history: list[dict]) -> set[str]:
    """从历史记录中获取上周的菜名。"""
    if not history:
        return set()
    # 按日期倒序
    sorted_records = sorted(history, key=lambda r: r.get("日期", ""), reverse=True)
    last_week_dates = set()
    for r in sorted_records:
        if len(last_week_dates) >= 5:
            break
        last_week_dates.add(r["日期"])

    return set(r["菜名"] for r in history if r["日期"] in last_week_dates)


def main():
    parser = argparse.ArgumentParser(description="编排下周菜单")
    parser.add_argument("--recipes", required=True, help="菜谱 JSON 文件路径")
    parser.add_argument("--history", default="data/history.csv", help="历史记录 CSV 路径")
    parser.add_argument("--blacklist", default="data/blacklist.txt", help="黑名单文件路径")
    parser.add_argument("--output", default=None, help="输出 CSV 路径")
    args = parser.parse_args()

    dates = next_week_dates()
    week_num = dates[0].strftime("%Y-W%W")
    output_path = args.output or f"data/weekly_menu_{week_num}.csv"

    history = load_history(args.history)
    blacklist = load_blacklist(args.blacklist)
    last_week_dishes = get_last_week_records(history)

    print(f"下周日期: {[str(d) for d in dates]}", file=sys.stderr)
    print(f"历史记录: {len(history)} 条", file=sys.stderr)
    print(f"黑名单: {blacklist}", file=sys.stderr)
    print(f"上周菜谱: {last_week_dishes}", file=sys.stderr)

    # 输出占位 CSV（实际选菜逻辑由 Claude 在 SKILL.md 中处理）
    # 这里提供一个空的骨架，提醒 Claude 来填充具体内容
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["日期", "index", "菜名", "链接"])
        # 占位，Claude 会填充具体内容
        writer.writerow(["# 请用 Claude 的编排逻辑填充此文件", "", "", ""])

    print(f"菜单骨架已创建: {output_path}", file=sys.stderr)
    print(json.dumps({
        "dates": [str(d) for d in dates],
        "week_number": week_num,
        "output_file": output_path,
        "history_count": len(history),
        "blacklist": list(blacklist),
        "last_week_dishes": list(last_week_dishes),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
